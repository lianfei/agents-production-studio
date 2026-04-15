from __future__ import annotations

import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from .capability import build_capability_catalog
from .corpus import CorpusScanner
from .generation import AgentsGenerator
from .labels import RuleLabeler, build_label_schema
from .llm import (
    AdaptiveBatchPlanner,
    BaseSemanticClient,
    NoopSemanticClient,
    build_semantic_client_from_env,
    persisted_default_client,
    semantic_client_summary,
    validate_semantic_config,
)
from .logging_utils import ArtifactLogger
from .models import (
    AgentProfile,
    BatchRequestRecord,
    BatchResponseRecord,
    CapabilityCatalog,
    GenerationRequest,
    GenerationResponse,
    IntakeSession,
    QuestionItem,
    QuestionOption,
    agent_profile_from_dict,
    capability_catalog_from_dict,
    json_ready,
)
from .time_utils import iso_now, timestamp_now


TEMPLATE_LABELS = {
    "http_service": "HTTP 服务 / Web 应用",
    "cli_tool": "CLI / 工具链",
    "automation_workflow": "自动化工作流",
    "data_processing": "数据分析 / 处理",
    "api_integration": "API / 集成服务",
    "custom": "自定义任务",
}

DEFERRED_ANSWER_PREFIX = "待确认："

PATH_QUESTION_IDS = {
    "project_root",
    "local_workdir",
    "output_paths",
    "remote_workdir",
    "atlas_yaml_path",
    "docker_assets_path",
}


def _simple_yaml(value: object, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(_simple_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {json.dumps(item, ensure_ascii=False)}")
        return "\n".join(lines)
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.append(_simple_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {json.dumps(item, ensure_ascii=False)}")
        return "\n".join(lines)
    return f"{prefix}{json.dumps(value, ensure_ascii=False)}"


class WorkflowService:
    def __init__(
        self,
        source_root: str | Path,
        output_dir: str | Path,
        initial_batch_size: int = 50,
    ) -> None:
        self.source_root = Path(source_root)
        self.output_dir = Path(output_dir)
        self.run_id = timestamp_now()
        self.logger = ArtifactLogger(self.output_dir, self.run_id)
        self.scanner = CorpusScanner(self.source_root)
        self.labeler = RuleLabeler()
        self.generator = AgentsGenerator(self.labeler)
        self._persisted_default_model_config = self._read_default_model_config()
        self.semantic_client = self._build_effective_semantic_client()
        self.batch_planner = AdaptiveBatchPlanner(initial_batch_size=initial_batch_size)
        self._cached_profiles: list[AgentProfile] | None = None
        self._cached_profile_source: str = ""
        self._cached_capability_catalog: CapabilityCatalog | None = None
        self._cached_capability_catalog_source: str = ""
        self.logger.write_text(self.logger.batch_log_path, "")
        self.logger.record_decision(
            decision="Initialize workflow service",
            reason="Start a timestamped execution for corpus analysis and generation.",
            impact=(
                f"Artifacts will be written under {self.output_dir}; "
                f"default_model_runtime={json.dumps(semantic_client_summary(self.semantic_client), ensure_ascii=False)}"
            ),
            rollback="Discard the generated run-specific files if this run should be ignored.",
        )

    def default_model_config_path(self) -> Path:
        return self.output_dir / "default_model_config.json"

    def _read_default_model_config(self) -> dict[str, object]:
        path = self.default_model_config_path()
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _write_default_model_config(self, payload: dict[str, object]) -> Path:
        path = self.default_model_config_path()
        self.logger.write_json(path, payload)
        self._persisted_default_model_config = dict(payload)
        return path

    @staticmethod
    def _normalize_persisted_mode(value: object) -> str:
        mode = str(value or "default").strip().lower()
        if mode in {"default", "custom", "disabled"}:
            return mode
        return "default"

    @staticmethod
    def _has_custom_model_fields(payload: object) -> bool:
        data = payload if isinstance(payload, dict) else {}
        return all(str(data.get(field, "") or "").strip() for field in ("base_url", "api_key", "model"))

    def _system_default_runtime(self) -> dict[str, object]:
        return semantic_client_summary(build_semantic_client_from_env())

    def _build_effective_semantic_client(self) -> BaseSemanticClient:
        data = self._persisted_default_model_config if isinstance(self._persisted_default_model_config, dict) else {}
        mode = self._normalize_persisted_mode(data.get("mode", "default"))
        enabled = bool(data.get("enabled", False))
        if data and (not enabled or mode == "disabled"):
            client, _, _ = persisted_default_client(data)
            if client is not None:
                return client
        if data and enabled and mode == "default":
            return build_semantic_client_from_env()
        client, _, error = persisted_default_client(data)
        if client is not None and not error:
            return client
        return build_semantic_client_from_env()

    def refresh_default_model_client(self) -> dict[str, object]:
        self._persisted_default_model_config = self._read_default_model_config()
        self.semantic_client = self._build_effective_semantic_client()
        return semantic_client_summary(self.semantic_client)

    def _public_default_model_config(self) -> dict[str, object]:
        data = self._persisted_default_model_config if isinstance(self._persisted_default_model_config, dict) else {}
        if not data:
            return {}
        enabled = bool(data.get("enabled", False))
        mode = self._normalize_persisted_mode(data.get("mode", "default"))
        return {
            "enabled": enabled and mode != "disabled",
            "mode": mode,
            "provider_label": str(data.get("provider_label", "") or ""),
            "base_url": str(data.get("base_url", "") or ""),
            "model": str(data.get("model", "") or ""),
            "wire_api": str(data.get("wire_api", "") or ""),
            "has_custom_config": self._has_custom_model_fields(data),
            "updated_at": str(data.get("updated_at", "") or ""),
            "last_validated_at": str(data.get("last_validated_at", "") or ""),
            "last_validation_status": str(data.get("last_validation_status", "") or ""),
            "last_validation_error": str(data.get("last_validation_error", "") or ""),
        }

    def get_model_settings(self, *, admin_configured: bool = False) -> dict[str, object]:
        runtime = semantic_client_summary(self.semantic_client)
        system_default_runtime = self._system_default_runtime()
        saved = self._public_default_model_config()
        switch_enabled = saved["enabled"] if saved else bool(system_default_runtime.get("enabled"))
        status_text = "禁用模型增强功能" if not switch_enabled else "已启用模型优化"
        return {
            "status_text": status_text,
            "admin_configured": admin_configured,
            "model_enabled": switch_enabled,
            "effective_default_runtime": runtime,
            "system_default_runtime": system_default_runtime,
            "saved_default_model": saved,
            "default_model_configured": bool(saved),
            "default_model_config_path": self.default_model_config_path().name,
        }

    def validate_default_model_candidate(self, raw_config: object) -> tuple[dict[str, object], str]:
        summary, error = validate_semantic_config(raw_config)
        result = {
            "validated_at": iso_now(),
            "model_runtime": summary,
        }
        return result, error

    def save_default_model_candidate(
        self,
        raw_config: object,
        *,
        validated_at: str,
    ) -> dict[str, object]:
        data = raw_config if isinstance(raw_config, dict) else {}
        payload = {
            "enabled": True,
            "mode": "custom",
            "provider_label": str(data.get("provider_label", "") or "服务端默认模型").strip(),
            "base_url": str(data.get("base_url", "") or "").strip(),
            "api_key": str(data.get("api_key", "") or "").strip(),
            "model": str(data.get("model", "") or "").strip(),
            "wire_api": str(data.get("wire_api", "chat_completions") or "chat_completions").strip(),
            "updated_at": iso_now(),
            "last_validated_at": str(validated_at or iso_now()),
            "last_validation_status": "ok",
            "last_validation_error": "",
        }
        self._write_default_model_config(payload)
        runtime = self.refresh_default_model_client()
        self.logger.record_decision(
            decision="Persist default model configuration",
            reason="Validated model configuration was promoted to service default.",
            impact=f"default_model_runtime={json.dumps(runtime, ensure_ascii=False)}",
            rollback="Use the disable action or replace the saved default model configuration.",
        )
        return self.get_model_settings()

    def enable_default_model_enhancement(self) -> tuple[dict[str, object], str]:
        existing = self._persisted_default_model_config if isinstance(self._persisted_default_model_config, dict) else {}
        system_runtime = self._system_default_runtime()
        payload = dict(existing)
        payload["enabled"] = True
        payload["updated_at"] = iso_now()
        if bool(system_runtime.get("enabled")):
            payload["mode"] = "default"
            payload["last_validation_status"] = "system_default"
            payload["last_validation_error"] = ""
            self._write_default_model_config(payload)
            runtime = self.refresh_default_model_client()
            self.logger.record_decision(
                decision="Enable model enhancement with system default",
                reason="Administrator enabled model optimization and the service detected a usable system default model.",
                impact=f"default_model_runtime={json.dumps(runtime, ensure_ascii=False)}",
                rollback="Disable model enhancement again or save a custom model configuration.",
            )
            return self.get_model_settings(), ""
        if self._has_custom_model_fields(existing):
            payload["mode"] = "custom"
            self._write_default_model_config(payload)
            runtime = self.refresh_default_model_client()
            self.logger.record_decision(
                decision="Enable model enhancement with saved custom model",
                reason="Administrator enabled model optimization and restored the saved custom model configuration.",
                impact=f"default_model_runtime={json.dumps(runtime, ensure_ascii=False)}",
                rollback="Disable model enhancement again or replace the saved custom model configuration.",
            )
            return self.get_model_settings(), ""
        return self.get_model_settings(), "未检测到系统默认模型，请先配置自定义模型接口。"

    def disable_default_model_enhancement(self) -> dict[str, object]:
        existing = self._persisted_default_model_config if isinstance(self._persisted_default_model_config, dict) else {}
        payload = {
            "enabled": False,
            "mode": "disabled",
            "provider_label": str(existing.get("provider_label", "") or ""),
            "base_url": str(existing.get("base_url", "") or ""),
            "api_key": str(existing.get("api_key", "") or ""),
            "model": str(existing.get("model", "") or ""),
            "wire_api": str(existing.get("wire_api", "") or ""),
            "updated_at": iso_now(),
            "last_validated_at": str(existing.get("last_validated_at", "") or ""),
            "last_validation_status": "disabled",
            "last_validation_error": "",
        }
        self._write_default_model_config(payload)
        runtime = self.refresh_default_model_client()
        self.logger.record_decision(
            decision="Disable model enhancement by default",
            reason="Administrator explicitly disabled default model usage for the service.",
            impact=f"default_model_runtime={json.dumps(runtime, ensure_ascii=False)}",
            rollback="Save a new validated default model configuration to re-enable model enhancement.",
        )
        return self.get_model_settings()

    def build_schema(self) -> Path:
        started = time.perf_counter()
        schema = build_label_schema()
        path = self.logger.timestamped_path("label_schema", "yaml")
        self.logger.write_text(path, _simple_yaml(schema) + "\n")
        self.logger.record_run(
            stage="schema",
            action="build_label_schema",
            input_basis="static schema definitions",
            output_path=str(path),
            status="ok",
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        return path

    def scan_corpus(self, max_files: int | None = None) -> tuple[list[object], Path]:
        started = time.perf_counter()
        records = self.scanner.scan(max_files=max_files)
        path = self.logger.timestamped_path("corpus_manifest", "jsonl")
        self.logger.write_jsonl(path, records)
        self.logger.record_run(
            stage="scan",
            action="scan_corpus",
            input_basis=str(self.source_root / "agents_process"),
            output_path=str(path),
            status="ok",
            duration_ms=int((time.perf_counter() - started) * 1000),
            notes=f"records={len(records)}",
        )
        return records, path

    def label_corpus(
        self,
        records: list[object],
        *,
        semantic_client: BaseSemanticClient | None = None,
    ) -> tuple[list[AgentProfile], Path]:
        started = time.perf_counter()
        profiles = [self.labeler.label_record(record) for record in records]
        batch_records = self._apply_semantic_batches(profiles, semantic_client=semantic_client)
        if batch_records:
            for row in batch_records:
                self.logger.append_jsonl(self.logger.batch_log_path, row)
        path = self.logger.timestamped_path("labeled_agents", "jsonl")
        self.logger.write_jsonl(path, profiles)
        index_path = self.write_generation_index(profiles)
        capability_path = self.write_capability_catalog(profiles, run_id=self.run_id)
        self._cached_profiles = profiles
        self._cached_profile_source = str(path)
        self.logger.record_run(
            stage="label",
            action="label_corpus",
            input_basis="manifest records",
            output_path=f"{path}, {index_path}, {capability_path}",
            status="ok",
            duration_ms=int((time.perf_counter() - started) * 1000),
            notes=f"profiles={len(profiles)}",
        )
        return profiles, path

    def review_labels(self, profiles: list[AgentProfile]) -> tuple[Path, Path]:
        started = time.perf_counter()
        summary_path = self.logger.timestamped_path("analysis_summary", "md")
        review_path = self.logger.timestamped_path("review_samples", "jsonl")
        summary = self._build_summary(profiles)
        review_rows = self._build_review_rows(profiles)
        self.logger.write_text(summary_path, summary)
        self.logger.write_jsonl(review_path, review_rows)
        self.logger.record_run(
            stage="review",
            action="review_labels",
            input_basis="labeled profiles",
            output_path=f"{summary_path}, {review_path}",
            status="ok",
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
        self.logger.append_markdown(
            self.logger.evaluation_path,
            "Stage Summary",
            "\n".join(
                [
                    "- stage: review_labels",
                    "- input_basis: labeled profiles",
                    f"- output_paths: {summary_path}, {review_path}",
                    "- validation: low-confidence and sparse-label samples extracted",
                    f"- result_count: {len(review_rows)}",
                ]
            ),
        )
        return summary_path, review_path

    def analyze_corpus(self, max_files: int | None = None) -> dict[str, str]:
        schema_path = self.build_schema()
        records, manifest_path = self.scan_corpus(max_files=max_files)
        profiles, labeled_path = self.label_corpus(records)
        summary_path, review_path = self.review_labels(profiles)
        return {
            "schema_path": str(schema_path),
            "manifest_path": str(manifest_path),
            "labeled_path": str(labeled_path),
            "capability_catalog_path": str(self.capability_catalog_path(self.run_id)),
            "summary_path": str(summary_path),
            "review_path": str(review_path),
            "run_log_path": str(self.logger.run_log_path),
            "decision_log_path": str(self.logger.decision_log_path),
            "batch_log_path": str(self.logger.batch_log_path),
            "evaluation_path": str(self.logger.evaluation_path),
        }

    @staticmethod
    def _option(value: str, label: str, description: str = "") -> QuestionOption:
        return QuestionOption(value=value, label=label, description=description)

    @staticmethod
    def _question(
        question_id: str,
        title: str,
        prompt: str,
        *,
        kind: str = "free_text",
        required: bool = False,
        source_rule: str = "",
        options: list[QuestionOption] | None = None,
        depends_on: dict[str, list[str]] | None = None,
        placeholder: str = "",
        help_text: str = "",
        suggestions: list[str] | None = None,
    ) -> QuestionItem:
        return QuestionItem(
            question_id=question_id,
            title=title,
            prompt=prompt,
            kind=kind,
            required=required,
            source_rule=source_rule,
            options=options or [],
            depends_on=depends_on or {},
            placeholder=placeholder,
            help_text=help_text,
            suggestions=[str(item).strip() for item in (suggestions or []) if str(item).strip()],
        )

    def _intake_session_path(self, session_id: str) -> Path:
        return self.output_dir / f"intake_session_{session_id}.json"

    def _intake_plan_path(self, session_id: str) -> Path:
        return self.output_dir / f"plan_preview_{session_id}.md"

    def start_intake_session(
        self,
        request: GenerationRequest,
        *,
        semantic_client: BaseSemanticClient | None = None,
    ) -> IntakeSession:
        session_id = self._next_artifact_id("intake_session", ("json", "md"))
        rule_questions = self._build_intake_questions(request)
        effective_client = semantic_client or self.semantic_client
        questions, question_generation_mode, question_generation_note = self._optimize_intake_questions(
            request,
            rule_questions,
            semantic_client=effective_client,
        )
        session = IntakeSession(
            session_id=session_id,
            created_at=iso_now(),
            updated_at=iso_now(),
            phase="collecting",
            base_request=json_ready(request),
            questions=questions,
            answers=self._seed_intake_answers(request, questions),
            question_generation_mode=question_generation_mode,
            question_generation_note=question_generation_note,
            next_action="answer_questions",
        )
        self._refresh_intake_session(session)
        self._write_intake_session(session)
        self.logger.record_run(
            stage="intake",
            action="start_intake_session",
            input_basis=request.task_description,
            output_path=str(self._intake_session_path(session_id)),
            status="ok",
            duration_ms=0,
            notes=(
                f"questions={len(session.questions)}, "
                f"question_generation_mode={question_generation_mode}, "
                f"model_source={semantic_client_summary(effective_client).get('source', 'unknown')}"
            ),
        )
        return session

    def _seed_intake_answers(self, request: GenerationRequest, questions: list[QuestionItem] | None = None) -> dict[str, object]:
        answers: dict[str, object] = {}
        task_description = str(request.task_description or "").strip()
        if task_description:
            answers["goal_definition"] = task_description
        acceptance_suggestions = self._suggestions_for_question("acceptance_criteria", questions or [])
        if acceptance_suggestions:
            answers["acceptance_criteria"] = self._suggested_bullet_text(acceptance_suggestions)
        normalized_environment = str(request.environment or "").lower()
        target_platform: list[str] = []
        if "browser_service" in normalized_environment:
            target_platform.append("browser_http")
        if "local_plus_remote" in normalized_environment or "remote" in normalized_environment:
            target_platform.append("local_and_server")
        if "local_only" in normalized_environment:
            target_platform.append("local_only")
        if "docker" in normalized_environment or "container" in normalized_environment:
            target_platform.append("docker_or_container")
        if "kubernetes" in normalized_environment or "atlas" in normalized_environment or "k8s" in normalized_environment:
            target_platform.append("k8s_or_atlas")
        if "mixed" in normalized_environment:
            target_platform.append("cross_platform")
        if target_platform:
            answers["target_platform"] = self._unique_strings(target_platform)
        return answers

    @staticmethod
    def _suggestions_for_question(question_id: str, questions: list[QuestionItem]) -> list[str]:
        for question in questions:
            if question.question_id == question_id:
                return [str(item).strip() for item in question.suggestions if str(item).strip()]
        return []

    @staticmethod
    def _suggested_bullet_text(items: list[str]) -> str:
        return "\n".join(f"- {str(item).strip()}" for item in items if str(item).strip())

    def _build_acceptance_suggestions(self, request: GenerationRequest) -> list[str]:
        task_text = " ".join(
            [
                str(request.task_description or ""),
                str(request.environment or ""),
                " ".join(str(item) for item in request.constraints),
                " ".join(str(item) for item in request.preferred_stack),
            ]
        ).lower()
        suggestions: list[str] = []

        def add(item: str) -> None:
            text = str(item or "").strip()
            if not text:
                return
            if text.lower() in {existing.lower() for existing in suggestions}:
                return
            suggestions.append(text)

        add("最终 AGENTS.md 与当前任务直接相关，并完整覆盖显式目标、环境、约束和验证要求。")
        if request.template_type == "http_service" or any(token in task_text for token in ("browser", "页面", "web", "http")):
            add("页面可以完成必要信息收集，并驱动后续 PLAN.md 与 AGENTS.md 生成流程。")
        if any(token in task_text for token in ("plan.md", "plan", "计划稿", "预览")) or request.template_type in {
            "http_service",
            "automation_workflow",
            "api_integration",
        }:
            add("生成最终结果前，可以查看并校对 PLAN.md 计划稿。")
        if any(token in task_text for token in ("copy", "复制", "result", "结果页")):
            add("结果页支持查看生成结果，并提供一键复制或下载能力。")
        if any(token in task_text for token in ("docker", "容器", "compose", "镜像")):
            add("如任务涉及 Docker，需要给出可执行的容器方案，或明确后续生成 Docker 资源的路径与方式。")
        if any("时间戳" in str(item) for item in request.constraints):
            add("关键过程、决策和执行结果需要保留带时间戳的记录。")
        if any("验证" in str(item) or "测试" in str(item) for item in request.constraints) or request.risk_tolerance == "low":
            add("关键路径具备明确的验证步骤，生成与修改结果不可跳过校验。")
        if any("供应商必须可替换" in str(item) for item in request.constraints):
            add("若涉及第三方模型或服务，方案必须保持供应商可替换。")
        return suggestions[:5]

    def _optimize_intake_questions(
        self,
        request: GenerationRequest,
        questions: list[QuestionItem],
        *,
        semantic_client: BaseSemanticClient | None = None,
    ) -> tuple[list[QuestionItem], str, str]:
        client = semantic_client or self.semantic_client
        if isinstance(client, NoopSemanticClient):
            return questions, "rule", "补充问答当前按规则生成；未配置模型优化。"
        raw = client.generate_agents(self._build_intake_question_optimization_prompt(request, questions))
        payload = self._extract_json_payload(raw)
        if not isinstance(payload, dict):
            return questions, "rule", "补充问答已按规则生成；模型优化没有返回可用结构，因此回退到规则结果。"
        raw_questions = payload.get("questions", [])
        if not isinstance(raw_questions, list):
            return questions, "rule", "补充问答已按规则生成；模型优化返回格式异常，因此回退到规则结果。"
        original_order = {question.question_id: index for index, question in enumerate(questions)}
        updates: dict[str, dict[str, object]] = {}
        display_order: dict[str, int] = {}
        known_ids = set(original_order)
        for index, item in enumerate(raw_questions):
            if not isinstance(item, dict):
                continue
            question_id = str(item.get("question_id", "") or "").strip()
            if not question_id or question_id not in known_ids:
                continue
            updates[question_id] = item
            try:
                display_order[question_id] = int(item.get("display_order", index))
            except (TypeError, ValueError):
                display_order[question_id] = index
        if not updates:
            return questions, "rule", "补充问答已按规则生成；模型优化未给出有效更新，因此保留规则结果。"
        optimized: list[QuestionItem] = []
        for question in questions:
            update = updates.get(question.question_id, {})
            optimized.append(
                QuestionItem(
                    question_id=question.question_id,
                    title=str(update.get("title", "") or question.title).strip() or question.title,
                    prompt=str(update.get("prompt", "") or question.prompt).strip() or question.prompt,
                    kind=question.kind,
                    required=question.required,
                    source_rule=question.source_rule,
                    options=question.options,
                    depends_on=question.depends_on,
                    placeholder=str(update.get("placeholder", "") or question.placeholder).strip(),
                    help_text=str(update.get("help_text", "") or question.help_text).strip(),
                    suggestions=self._unique_strings(
                        [str(item).strip() for item in update.get("suggestions", []) if str(item).strip()]
                    )
                    or question.suggestions,
                )
            )
        optimized.sort(key=lambda item: display_order.get(item.question_id, original_order.get(item.question_id, 999)))
        note = str(payload.get("note", "") or "").strip() or "补充问答已在规则结果基础上做了一轮模型优化，当前展示的是优化后的版本。"
        return optimized, "rule_plus_model", note

    def _build_intake_question_optimization_prompt(self, request: GenerationRequest, questions: list[QuestionItem]) -> str:
        payload = {
            "instructions": {
                "task": "Refine the rule-generated intake questionnaire for an AGENTS.md production workflow.",
                "return_format": {
                    "note": "string",
                    "questions": [
                        {
                            "question_id": "existing id only",
                            "title": "optimized title",
                            "prompt": "optimized prompt",
                            "help_text": "optimized help text",
                            "placeholder": "optimized placeholder",
                            "display_order": 1,
                            "suggestions": ["optional bullet suggestions"],
                        }
                    ],
                },
                "requirements": [
                    "Keep the same question_id set. Do not invent new ids and do not remove questions.",
                    "You may improve title, prompt, help_text, placeholder, and display_order only.",
                    "Do not change kind, depends_on, option values, or execution semantics.",
                    "Reduce repetition and make the wording more direct and production-oriented.",
                    "For acceptance_criteria, provide 3-5 concrete suggestion bullets in suggestions.",
                    "Do not invent environment facts, paths, tools, or constraints that are not present in the request.",
                    "Return JSON only.",
                ],
            },
            "request": json_ready(request),
            "questions": json_ready(questions),
        }
        return "\n".join(
            [
                "Optimize this intake questionnaire for clarity and usability.",
                json.dumps(payload, ensure_ascii=False, indent=2),
            ]
        )

    @staticmethod
    def _extract_json_payload(raw: str) -> object:
        text = str(raw or "").strip()
        if not text:
            return {}
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", text, re.DOTALL)
        if fenced_match:
            text = fenced_match.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            object_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if object_match:
                try:
                    return json.loads(object_match.group(1))
                except json.JSONDecodeError:
                    return {}
        return {}

    def answer_intake_session(self, session_id: str, answers: dict[str, object]) -> IntakeSession | None:
        session = self._read_intake_session(session_id)
        if session is None:
            return None
        for question_id, raw_value in dict(answers or {}).items():
            session.answers[question_id] = self._normalize_answer_value(raw_value)
        session.updated_at = iso_now()
        self._refresh_intake_session(session)
        self._write_intake_session(session)
        self.logger.record_run(
            stage="intake",
            action="answer_intake_session",
            input_basis=session.base_request.get("task_description", "") if isinstance(session.base_request, dict) else "",
            output_path=str(self._intake_session_path(session_id)),
            status="ok",
            duration_ms=0,
            notes=f"answers={len(session.answers)}, ready_for_plan={session.ready_for_plan}",
        )
        return session

    def get_intake_session(self, session_id: str) -> IntakeSession | None:
        session = self._read_intake_session(session_id)
        if session is None:
            return None
        self._refresh_intake_session(session)
        self._write_intake_session(session)
        return session

    def build_generation_request_from_session(self, session_id: str) -> GenerationRequest | None:
        session = self.get_intake_session(session_id)
        if session is None or not session.ready_for_plan:
            return None
        base = self._normalize_request_dict(session.base_request)
        answers = session.answers
        constraints = list(base.get("constraints", []))
        preferred_stack = [str(item) for item in base.get("preferred_stack", []) if str(item).strip()]
        if answers.get("private_dependencies") == "has_private":
            constraints.append("涉及私有依赖或协议，执行前必须先确认访问方式与安全边界")
        if answers.get("vendor_replaceability") == "must_replaceable":
            constraints.append("供应商必须可替换")
        if answers.get("remote_access_mode") in {"ssh_key_ready", "ssh_password_only"}:
            constraints.append("涉及远程主机操作，必须先核对 SSH 与目标目录")
        environment_detail = "\n".join(
            item
            for item in [
                f"目标平台：{self._answer_text(answers.get('target_platform'))}",
                f"远程访问：{self._answer_text(answers.get('remote_access_mode'))}",
                f"Docker 策略：{self._answer_text(answers.get('docker_requirement'))}",
                f"Kubernetes/Atlas：{self._answer_text(answers.get('kubernetes_namespace'))}",
            ]
            if item and not item.endswith("：")
        )
        paths = {
            key: str(value)
            for key, value in answers.items()
            if key in PATH_QUESTION_IDS and str(value or "").strip()
        }
        permissions = {
            "allowed_operations": answers.get("allowed_operations", []),
            "private_dependencies": answers.get("private_dependencies", ""),
            "remote_access_mode": answers.get("remote_access_mode", ""),
        }
        resource_constraints = {
            "docker_requirement": answers.get("docker_requirement", ""),
            "kubernetes_namespace": answers.get("kubernetes_namespace", ""),
            "atlas_yaml_path": answers.get("atlas_yaml_path", ""),
            "dataset_paths": answers.get("dataset_paths", ""),
            "model_usage": answers.get("model_usage", ""),
            "model_or_data_paths": answers.get("model_or_data_paths", ""),
            "batching_rules": answers.get("batching_rules", ""),
            "deadline": answers.get("deadline", ""),
        }
        acceptance_lines = self._split_rich_text(answers.get("acceptance_criteria", ""))
        if answers.get("test_requirements"):
            acceptance_lines.extend(self._split_rich_text(answers.get("test_requirements", "")))
        return GenerationRequest(
            template_type=str(base.get("template_type", "")),
            industry=str(base.get("industry", "")),
            task_description=str(base.get("task_description", "")),
            target_user=str(base.get("target_user", "general")),
            output_language=str(base.get("output_language", "zh")),
            environment=str(base.get("environment", "")),
            constraints=self._unique_strings(constraints),
            preferred_stack=self._unique_strings(preferred_stack),
            risk_tolerance=str(base.get("risk_tolerance", "medium")),
            session_id=session.session_id,
            current_state=str(answers.get("current_state", "")),
            goal_definition=str(answers.get("goal_definition", "") or base.get("task_description", "")),
            acceptance_criteria=self._unique_strings(acceptance_lines),
            paths=paths,
            environment_detail=environment_detail,
            permissions=permissions,
            resource_constraints=resource_constraints,
            question_answers=dict(answers),
            plan_markdown=session.plan_markdown,
        )

    def _build_intake_questions(self, request: GenerationRequest) -> list[QuestionItem]:
        text = " ".join(
            [
                request.template_type,
                request.industry,
                request.task_description,
                request.environment,
                " ".join(request.constraints),
                " ".join(request.preferred_stack),
            ]
        ).lower()
        remote_signal = request.environment == "local_plus_remote" or any(token in text for token in ("remote", "ssh", "server", "cluster", "远程", "集群"))
        docker_signal = request.environment == "docker" or any(token in text for token in ("docker", "container", "镜像", "容器"))
        kubernetes_signal = request.environment == "kubernetes" or any(token in text for token in ("kubernetes", "k8s", "kubectl", "atlas", "pod", "namespace"))
        model_signal = request.industry == "ai_ml" or request.template_type == "api_integration" or any(
            token in text for token in ("model", "llm", "gpt", "claude", "openai", "训练", "推理", "模型", "batch", "批处理", "embedding", "inference")
        )
        data_signal = request.template_type == "data_processing" or any(token in text for token in ("dataset", "data", "语料", "标注", "清洗", "数据"))
        goal_prefilled = bool(str(request.task_description or "").strip())
        goal_title = "任务目标细化（可选）" if goal_prefilled else "任务目标"
        goal_prompt = (
            "前面已经收集到基础任务描述。这里不是重复填写任务，而是给执行阶段补充更具体、更可衡量的目标；如果前面的描述已经足够清楚，可以直接保留不改。"
            if goal_prefilled
            else "请把这次任务的目标写具体，尽量包含目标对象、预期结果和衡量方式。"
        )
        goal_help_text = (
            "“任务描述”用于定义整体需求范围；这里更偏执行目标细化。系统已先用前面填写的任务描述作为默认值，通常不需要重复填写。"
            if goal_prefilled
            else ""
        )
        acceptance_suggestions = self._build_acceptance_suggestions(request)
        questions: list[QuestionItem] = [
            self._question(
                "goal_definition",
                goal_title,
                goal_prompt,
                required=not goal_prefilled,
                source_rule="task.agent.md#目标",
                placeholder="例如：在 /abs/project 下产出一个可上线的 HTTP 服务，并让最终 AGENTS.md 明确执行步骤、验证标准和回退方案。",
                help_text=goal_help_text,
            ),
            self._question(
                "acceptance_criteria",
                "验收标准",
                "请写出这次任务完成后必须满足的验收标准。",
                required=True,
                source_rule="task.agent.md#目标",
                placeholder="例如：页面可完成问答收集；生成前展示 PLAN.md；最终 AGENTS.md 与任务强相关；所有过程有时间戳记录。",
                help_text="系统会先根据任务描述、模板、环境和约束自动生成一组建议，你可以直接微调，不必从空白开始写。",
                suggestions=acceptance_suggestions,
            ),
            self._question(
                "current_state",
                "当前状态",
                "这是一个全新任务，还是基于现有工程/进行中的工作？",
                kind="single_choice",
                required=True,
                source_rule="task.agent.md#现状",
                options=[
                    self._option("new_project", "全新开始", "还没有现成工程或只需新建输出。"),
                    self._option("existing_project", "基于现有项目", "已有项目目录，需要在现有工程上继续。"),
                    self._option("in_progress_task", "基于进行中的任务", "已有任务和阶段性结果，需要继续推进。"),
                ],
            ),
            self._question(
                "project_root",
                "项目根目录",
                "请提供当前项目根目录的绝对路径。",
                required=True,
                source_rule="task.agent.md#现状",
                depends_on={"current_state": ["existing_project", "in_progress_task"]},
                placeholder="/abs/path/to/project",
                help_text="必须使用绝对路径。",
            ),
            self._question(
                "current_gap",
                "当前问题与差距",
                "当前已经做到什么程度？还差什么？目前最明显的问题是什么？",
                required=True,
                source_rule="task.agent.md#现状",
                depends_on={"current_state": ["existing_project", "in_progress_task"]},
                placeholder="例如：已有浏览器界面和结果页，但没有问答式信息收集与 PLAN.md 阶段。",
            ),
            self._question(
                "local_workdir",
                "本地工作目录",
                "如需在本地执行，请提供主要工作目录或相关产物目录的绝对路径。",
                required=False,
                source_rule="task.agent.md#路径",
                placeholder="/abs/path/to/workdir",
                help_text="可写多个路径，换行分隔。",
            ),
            self._question(
                "output_paths",
                "输出路径",
                "最终计划稿、AGENTS.md、日志或结果文档准备保存到哪些绝对路径？",
                required=True,
                source_rule="task.agent.md#路径",
                placeholder="/abs/path/to/output\n/abs/path/to/logs",
                help_text="必须使用绝对路径，可写多个路径，换行分隔。",
            ),
            self._question(
                "target_platform",
                "目标环境",
                "主要在哪些环境中开发、验证和交付？可多选，支持本地、远程、Docker、Kubernetes 等组合。",
                kind="multi_choice",
                required=True,
                source_rule="task.agent.md#环境",
                options=[
                    self._option("browser_http", "浏览器 + HTTP 服务", "需要通过浏览器访问服务或页面。"),
                    self._option("local_only", "仅本地环境", "开发、验证和交付都在本地完成。"),
                    self._option("local_and_server", "本地 + 远程服务器", "本地开发，远程验证或部署。"),
                    self._option("docker_or_container", "Docker / 容器环境", "以镜像或容器为主。"),
                    self._option("k8s_or_atlas", "Kubernetes / Atlas 集群", "涉及集群或资源配额。"),
                    self._option("cross_platform", "多平台 / 跨环境", "需要兼容多个操作系统或运行环境。"),
                ],
            ),
            self._question(
                "allowed_operations",
                "允许的操作范围",
                "为了避免后续执行越权，请选择当前允许的操作。",
                kind="multi_choice",
                required=True,
                source_rule="permission.agent.md#权限默认设定",
                options=[
                    self._option("read_only_review", "只读审查", "允许只读检查代码、文档、日志。"),
                    self._option("create_new_files", "新增文件", "允许在指定目录新增文件。"),
                    self._option("modify_existing_files", "修改现有文件", "允许修改指定目录内已有文件。"),
                    self._option("docker_runtime", "Docker/构建", "允许构建镜像、运行容器或构建项目。"),
                    self._option("remote_ssh", "SSH/远程操作", "允许连接远程机器或远程目录。"),
                ],
            ),
            self._question(
                "private_dependencies",
                "私有依赖与资源",
                "是否会涉及私有软件、私有模型、私有数据、专有协议或受限资源？",
                kind="single_choice",
                required=True,
                source_rule="safe.agent.md#安全相关设定",
                options=[
                    self._option("no_private", "没有", "只使用公开资源或当前仓库已有资源。"),
                    self._option("has_private", "有", "存在私有依赖、凭证、模型或受限资源。"),
                    self._option("not_sure", "暂不确定", "需要在计划中保留待确认项。"),
                ],
            ),
            self._question(
                "private_dependency_notes",
                "私有依赖说明",
                "请说明这些私有依赖或受限资源的类型、来源和使用限制。",
                required=True,
                source_rule="task.agent.md#资源和约束",
                depends_on={"private_dependencies": ["has_private", "not_sure"]},
                placeholder="例如：需要访问公司内部 API，文档在 /abs/docs/api.md，测试环境通过 VPN 访问。",
            ),
            self._question(
                "test_requirements",
                "验证方式",
                "请说明这次任务至少要通过哪些验证方式或测试要求。",
                required=True,
                source_rule="test.agent.md#测试基本要求",
                placeholder="例如：lint + 编译通过；关键路径有测试；手工验证问答流程与结果页展示。",
            ),
            self._question(
                "deadline",
                "时间边界",
                "如果这次任务有明确时间边界，请补充截止时间或期望节奏。",
                required=False,
                source_rule="task.agent.md#目标",
                placeholder="例如：今天内给出可运行版本；本周内完成生产化。",
            ),
            self._question(
                "safety_constraints",
                "额外安全边界",
                "如果有额外的安全、权限、稳定性或合规限制，请补充说明。",
                required=False,
                source_rule="safe.agent.md#安全相关设定",
                placeholder="例如：不能访问生产数据库；不能重启共享服务；必须使用商业友好依赖。",
            ),
        ]
        if remote_signal:
            questions.extend(
                [
                    self._question(
                        "remote_access_mode",
                        "远程访问方式",
                        "远程环境目前准备到什么程度？",
                        kind="single_choice",
                        required=True,
                        source_rule="ssh.agent.md#SSH连接管理",
                        options=[
                            self._option("ssh_key_ready", "SSH 免密已就绪", "可以直接通过 SSH key 连接。"),
                            self._option("ssh_password_only", "需要密码或待配置", "可连接但未完成免密。"),
                            self._option("non_ssh_remote", "通过其他方式访问", "例如控制台、跳板或管理平台。"),
                            self._option("remote_not_ready", "远程环境还没准备好", "先做本地方案与待确认项。"),
                        ],
                    ),
                    self._question(
                        "remote_hosts",
                        "远程主机信息",
                        "请提供远程主机、端口、用户或命名空间等必要信息。",
                        required=True,
                        source_rule="ssh.agent.md#SSH连接管理",
                        depends_on={"remote_access_mode": ["ssh_key_ready", "ssh_password_only", "non_ssh_remote"]},
                        placeholder="例如：user@10.0.0.8:22；namespace=tts。",
                    ),
                    self._question(
                        "remote_workdir",
                        "远程工作目录",
                        "请提供远程执行或部署目录的绝对路径。",
                        required=True,
                        source_rule="task.agent.md#路径",
                        depends_on={"remote_access_mode": ["ssh_key_ready", "ssh_password_only", "non_ssh_remote"]},
                        placeholder="/abs/remote/path",
                        help_text="必须使用绝对路径。",
                    ),
                ]
            )
        if docker_signal:
            questions.extend(
                [
                    self._question(
                        "docker_requirement",
                        "Docker 使用要求",
                        "Docker 在这次任务里属于必须、优先还是可选？",
                        kind="single_choice",
                        required=True,
                        source_rule="docker.agent.md#Docker 基本操作",
                        options=[
                            self._option("must_use", "必须使用", "交付物必须包含镜像或容器方案。"),
                            self._option("preferred", "优先使用", "优先给出 Docker 方案，但允许非 Docker 回退。"),
                            self._option("optional", "可选", "可以只做本地方案。"),
                        ],
                    ),
                    self._question(
                        "docker_assets_path",
                        "Docker 相关路径（如已存在）",
                        "如果当前已经有 Dockerfile、compose 文件或构建上下文，请提供它们的绝对路径；如果还没有，希望系统后续自动生成，可以留空。",
                        required=False,
                        source_rule="docker.agent.md#镜像操作",
                        depends_on={"docker_requirement": ["must_use", "preferred"]},
                        placeholder="/abs/path/to/Dockerfile",
                        help_text="已有文件时必须使用绝对路径，可写多个路径，换行分隔；留空表示后续按任务自动生成。",
                    ),
                ]
            )
        if kubernetes_signal:
            questions.extend(
                [
                    self._question(
                        "kubernetes_namespace",
                        "Kubernetes / Atlas 命名空间",
                        "如果涉及 Kubernetes 或 Atlas，请提供 namespace。",
                        required=True,
                        source_rule="atlas.agent.md#namespace 说明",
                        placeholder="例如：tts / default",
                    ),
                    self._question(
                        "atlas_yaml_path",
                        "YAML 配置路径",
                        "如果需要 apply/delete 资源，请提供相关 YAML 的绝对路径。",
                        required=True,
                        source_rule="atlas.agent.md#Atlas && Kubectl 基本命令",
                        placeholder="/abs/path/to/job.yaml",
                        help_text="必须使用绝对路径，可写多个路径，换行分隔。",
                    ),
                ]
            )
        if model_signal:
            questions.extend(
                [
                    self._question(
                        "model_usage",
                        "模型使用方式",
                        "这次任务里模型能力如何参与？",
                        kind="single_choice",
                        required=True,
                        source_rule="task.agent.md#资源和约束",
                        options=[
                            self._option("external_api", "调用外部模型 API", "例如 OpenAI、Anthropic、其他云模型。"),
                            self._option("local_model", "使用本地/开源模型", "模型在本地或自有环境运行。"),
                            self._option("hybrid_model", "两者都用", "既用外部 API 也用本地/开源模型。"),
                            self._option("no_model", "不涉及模型", "不依赖模型能力。"),
                        ],
                    ),
                    self._question(
                        "vendor_replaceability",
                        "供应商可替换要求",
                        "对供应商可替换性有什么要求？",
                        kind="single_choice",
                        required=True,
                        source_rule="safe.agent.md#安全相关设定",
                        depends_on={"model_usage": ["external_api", "local_model", "hybrid_model"]},
                        options=[
                            self._option("must_replaceable", "必须可替换", "设计上要保留供应商替换能力。"),
                            self._option("single_vendor_ok", "可接受单一供应商", "当前阶段可以绑定单一供应商。"),
                            self._option("undecided", "暂未确定", "计划里要列为待确认项。"),
                        ],
                    ),
                    self._question(
                        "batching_rules",
                        "批处理规则",
                        "如果模型参与处理，请说明批处理策略、批大小和降低调用次数的要求。",
                        required=True,
                        source_rule="task.agent.md#资源和约束",
                        depends_on={"model_usage": ["external_api", "local_model", "hybrid_model"]},
                        placeholder="例如：默认每批 50 条；若单次请求压力不大可增大批次；结果需保持样本映射关系。",
                    ),
                    self._question(
                        "model_or_data_paths",
                        "模型/资源位置",
                        "如果使用本地模型或需要额外模型资源，请说明模型名称、目录或来源。",
                        required=True,
                        source_rule="task.agent.md#资源和约束",
                        depends_on={"model_usage": ["local_model", "hybrid_model"]},
                        placeholder="例如：使用 GPT-5.4；本地模型目录为 /abs/models/foo；或 HuggingFace 模型名。",
                    ),
                ]
            )
        if data_signal:
            questions.append(
                self._question(
                    "dataset_paths",
                    "数据位置",
                    "如果任务涉及数据、语料或样本，请提供数据所在位置或获取来源。",
                    required=True,
                    source_rule="task.agent.md#资源和约束",
                    placeholder="例如：/abs/data/train.jsonl 或 https://example.com/dataset.zip",
                )
            )
        return questions

    def _refresh_intake_session(self, session: IntakeSession) -> None:
        active_questions = [item for item in session.questions if self._question_is_active(item, session.answers)]
        validation_errors: dict[str, str] = {}
        missing_required_ids: list[str] = []
        answered_count = 0
        plan_path = self._intake_plan_path(session.session_id)
        for item in active_questions:
            error = self._validate_question_answer(item, session.answers.get(item.question_id))
            if error:
                validation_errors[item.question_id] = error
            value = session.answers.get(item.question_id)
            if self._answer_has_value(value) and not error:
                answered_count += 1
            elif item.required:
                missing_required_ids.append(item.question_id)
        active_count = len(active_questions)
        session.active_question_ids = [item.question_id for item in active_questions]
        session.validation_errors = validation_errors
        session.missing_required_ids = missing_required_ids
        session.completion_percent = 100 if active_count == 0 else int((answered_count / active_count) * 100)
        session.ready_for_plan = not missing_required_ids and not validation_errors
        if session.ready_for_plan:
            session.phase = "plan_ready"
            session.next_action = "generate_agents"
            session.plan_markdown = self._build_plan_markdown(session)
            session.plan_summary = self._build_plan_summary(session)
            session.plan_output_path = str(plan_path)
            self.logger.write_text(session.plan_output_path, session.plan_markdown)
        else:
            session.phase = "collecting"
            session.next_action = "answer_questions"
            session.plan_markdown = ""
            session.plan_summary = []
            session.plan_output_path = ""
            try:
                if plan_path.exists():
                    plan_path.unlink()
            except OSError:
                pass

    def _write_intake_session(self, session: IntakeSession) -> Path:
        return self.logger.write_json(self._intake_session_path(session.session_id), session)

    def _read_intake_session(self, session_id: str) -> IntakeSession | None:
        safe_id = session_id.strip()
        if not safe_id or "/" in safe_id or "\\" in safe_id:
            return None
        path = self._intake_session_path(safe_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return self._intake_session_from_dict(payload)

    @staticmethod
    def _intake_session_from_dict(data: dict[str, object]) -> IntakeSession:
        return IntakeSession(
            session_id=str(data.get("session_id", "")),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            phase=str(data.get("phase", "collecting")),
            base_request=dict(data.get("base_request", {})),
            questions=[
                QuestionItem(
                    question_id=str(item.get("question_id", "")),
                    title=str(item.get("title", "")),
                    prompt=str(item.get("prompt", "")),
                    kind=str(item.get("kind", "free_text")),
                    required=bool(item.get("required", False)),
                    source_rule=str(item.get("source_rule", "")),
                    options=[
                        QuestionOption(
                            value=str(option.get("value", "")),
                            label=str(option.get("label", "")),
                            description=str(option.get("description", "")),
                        )
                        for option in item.get("options", [])
                    ],
                    depends_on={str(key): [str(value) for value in values] for key, values in dict(item.get("depends_on", {})).items()},
                    placeholder=str(item.get("placeholder", "")),
                    help_text=str(item.get("help_text", "")),
                    suggestions=[str(suggestion) for suggestion in item.get("suggestions", []) if str(suggestion).strip()],
                )
                for item in data.get("questions", [])
            ],
            answers={str(key): value for key, value in dict(data.get("answers", {})).items()},
            question_generation_mode=str(data.get("question_generation_mode", "rule") or "rule"),
            question_generation_note=str(data.get("question_generation_note", "") or ""),
            active_question_ids=[str(item) for item in data.get("active_question_ids", [])],
            missing_required_ids=[str(item) for item in data.get("missing_required_ids", [])],
            validation_errors={str(key): str(value) for key, value in dict(data.get("validation_errors", {})).items()},
            completion_percent=int(data.get("completion_percent", 0) or 0),
            ready_for_plan=bool(data.get("ready_for_plan", False)),
            next_action=str(data.get("next_action", "")),
            plan_markdown=str(data.get("plan_markdown", "")),
            plan_summary=[str(item) for item in data.get("plan_summary", [])],
            plan_output_path=str(data.get("plan_output_path", "")),
        )

    @staticmethod
    def _normalize_answer_value(raw: object) -> object:
        if isinstance(raw, list):
            values = [str(item).strip() for item in raw if str(item).strip()]
            seen: set[str] = set()
            normalized: list[str] = []
            for value in values:
                key = value.lower()
                if key in seen:
                    continue
                seen.add(key)
                normalized.append(value)
            return normalized
        return str(raw or "").strip()

    @staticmethod
    def _question_is_active(question: QuestionItem, answers: dict[str, object]) -> bool:
        if not question.depends_on:
            return True
        for key, values in question.depends_on.items():
            current = answers.get(key)
            allowed = {str(item) for item in values}
            if isinstance(current, list):
                if not any(str(item) in allowed for item in current):
                    return False
                continue
            if str(current or "") not in allowed:
                return False
        return True

    def _validate_question_answer(self, question: QuestionItem, value: object) -> str:
        if not question.required and not self._answer_has_value(value):
            return ""
        if question.required and not self._answer_has_value(value):
            return "该项为必填，请先补充。"
        if self._is_deferred_answer(value):
            return ""
        if question.question_id in PATH_QUESTION_IDS and self._answer_has_value(value):
            if not self._looks_like_absolute_paths(str(value)):
                return "请提供绝对路径，可多个路径用换行或逗号分隔。"
        return ""

    @staticmethod
    def _answer_has_value(value: object) -> bool:
        if isinstance(value, list):
            return any(str(item).strip() for item in value)
        return bool(str(value or "").strip())

    @staticmethod
    def _is_deferred_answer(value: object) -> bool:
        if isinstance(value, list):
            return any(WorkflowService._is_deferred_answer(item) for item in value)
        text = str(value or "").strip()
        return bool(text) and text.startswith(DEFERRED_ANSWER_PREFIX)

    @staticmethod
    def _looks_like_absolute_paths(text: str) -> bool:
        tokens = [token.strip() for token in re.split(r"[\n,]+", text) if token.strip()]
        if not tokens:
            return False
        for token in tokens:
            normalized = token.replace("\\", "/")
            if not (normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized)):
                return False
        return True

    @staticmethod
    def _split_rich_text(value: object) -> list[str]:
        text = str(value or "").strip()
        if not text:
            return []
        items = []
        for line in text.splitlines():
            cleaned = line.strip().lstrip("-").strip()
            if cleaned:
                items.append(cleaned)
        if items:
            return items
        return [item.strip() for item in re.split(r"[;/；]+", text) if item.strip()]

    @staticmethod
    def _unique_strings(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in values:
            text = str(item or "").strip()
            key = text.lower()
            if not text or key in seen:
                continue
            seen.add(key)
            result.append(text)
        return result

    @staticmethod
    def _answer_text(value: object) -> str:
        if isinstance(value, list):
            return ", ".join(str(item) for item in value if str(item).strip())
        return str(value or "").strip()

    def _build_plan_markdown(self, session: IntakeSession) -> str:
        base = self._normalize_request_dict(session.base_request)
        answers = session.answers
        acceptance = self._split_rich_text(answers.get("acceptance_criteria", "")) or ["待补充更明确的验收标准"]
        tests = self._split_rich_text(answers.get("test_requirements", "")) or ["待补充验证方式"]
        deferred_items = [
            item.title
            for item in session.questions
            if self._question_is_active(item, answers) and self._is_deferred_answer(answers.get(item.question_id))
        ]
        constraints = self._unique_strings(
            [str(item) for item in base.get("constraints", []) if str(item).strip()]
            + ([str(answers.get("safety_constraints", "")).strip()] if str(answers.get("safety_constraints", "")).strip() else [])
        )
        paths = self._unique_strings(
            [str(answers.get("project_root", "")).strip(), str(answers.get("local_workdir", "")).strip(), str(answers.get("output_paths", "")).strip(), str(answers.get("remote_workdir", "")).strip()]
        )
        steps = self._plan_steps(base, answers)
        return "\n".join(
            [
                "# PLAN.md",
                "",
                "## 任务概述",
                "",
                f"- 原始任务：`{base.get('task_description', '') or '未填写'}`",
                f"- 执行目标：{answers.get('goal_definition', '') or base.get('task_description', '') or '未填写'}",
                f"- 当前状态：{self._answer_text(answers.get('current_state')) or '未填写'}",
                f"- 时间边界：{self._answer_text(answers.get('deadline')) or '未明确'}",
                f"- 目标用户：`{base.get('target_user', 'general')}`",
                f"- 运行环境：`{base.get('environment', '') or '未填写'}`",
                "",
                "## 已确认信息",
                "",
                f"- 项目根目录：{self._answer_text(answers.get('project_root')) or '待新建或未提供'}",
                f"- 当前差距：{self._answer_text(answers.get('current_gap')) or '未填写'}",
                f"- 允许操作：{self._answer_text(answers.get('allowed_operations')) or '未填写'}",
                f"- 私有依赖：{self._answer_text(answers.get('private_dependencies')) or '未填写'}",
                f"- 远程访问：{self._answer_text(answers.get('remote_access_mode')) or '未涉及'}",
                f"- Docker 要求：{self._answer_text(answers.get('docker_requirement')) or '未涉及'}",
                f"- 模型使用：{self._answer_text(answers.get('model_usage')) or '未涉及'}",
                "",
                "## 验收标准",
                "",
                *[f"- {item}" for item in acceptance],
                "",
                "## 测试与验证",
                "",
                *[f"- {item}" for item in tests],
                "",
                "## 关键路径与产物",
                "",
                *(f"- {item}" for item in paths if item),
                *(["- 待补充绝对路径"] if not any(paths) else []),
                "",
                "## 约束与风险",
                "",
                *(f"- {item}" for item in constraints if item),
                *(
                    [f"- 私有依赖说明：{self._answer_text(answers.get('private_dependency_notes'))}"]
                    if self._answer_text(answers.get("private_dependency_notes"))
                    else []
                ),
                *(
                    [f"- 批处理规则：{self._answer_text(answers.get('batching_rules'))}"]
                    if self._answer_text(answers.get("batching_rules"))
                    else []
                ),
                *([f"- 待后续补充：{', '.join(deferred_items)}"] if deferred_items else []),
                "",
                "## 执行计划",
                "",
                *steps,
                "",
                "## 说明",
                "",
                "- 本计划稿基于 `agent_first_hand/docs/init.md` 与 `task.agent.md` 的问答收集结果生成。",
                "- 当前页面会展示该计划稿，然后自动继续进入 AGENTS.md 草稿与最终稿生成。",
                "- 若后续输入发生变化，应重新收集问答并重新生成计划稿。",
                "",
            ]
        ).rstrip() + "\n"

    def _build_plan_summary(self, session: IntakeSession) -> list[str]:
        base = self._normalize_request_dict(session.base_request)
        answers = session.answers
        deferred_count = sum(
            1
            for item in session.questions
            if self._question_is_active(item, answers) and self._is_deferred_answer(answers.get(item.question_id))
        )
        return [
            f"目标：{str(answers.get('goal_definition', '') or base.get('task_description', '')).strip()}",
            f"状态：{self._answer_text(answers.get('current_state')) or '未填写'}",
            f"环境：{str(base.get('environment', '') or '未填写')}",
            f"验证：{self._answer_text(answers.get('test_requirements')) or '未填写'}",
            *([f"待补充：{deferred_count} 项"] if deferred_count else []),
        ]

    def _plan_steps(self, base: dict[str, object], answers: dict[str, object]) -> list[str]:
        output_paths = self._answer_text(answers.get("output_paths")) or "待补充输出路径"
        project_root = self._answer_text(answers.get("project_root")) or self._answer_text(answers.get("local_workdir")) or "待补充项目目录"
        steps = [
            "### 1. 只读审查与事实确认",
            f"- 输入依据：当前任务描述、现有目录 `{project_root}`、已回答的问答信息。",
            "- 操作内容：只读检查现状、补齐缺失事实、确认环境与执行边界。",
            f"- 产物路径：`{output_paths}` 中的审查记录与时间戳日志。",
            "- 验证方法：核对目录、文档、配置、日志与任务描述是否一致。",
            "- 验证标准：形成可执行事实清单，明确已确认事实、待验证假设和缺失项。",
            "",
            "### 2. 执行方案与风险控制",
            "- 输入依据：验收标准、测试要求、权限边界、私有依赖与安全约束。",
            "- 操作内容：确定最小改动方案、风险点、回退路径和验证顺序。",
            f"- 产物路径：`{output_paths}` 中的 PLAN.md、CHECKLIST 或中间说明文档。",
            "- 验证方法：逐条映射显式约束与验收要求。",
            "- 验证标准：每条关键约束都能在执行方案中找到对应动作和验证方式。",
            "",
            "### 3. 实施与生成",
            "- 输入依据：确认后的计划稿、能力模式参考、用户显式输入。",
            "- 操作内容：先生成 AGENTS 草稿，再进行第二阶段优化并写入最终产物。",
            f"- 产物路径：`{output_paths}` 中的草稿、最终稿、日志与元数据。",
            "- 验证方法：检查草稿与最终稿是否覆盖任务目标、环境、路径、约束和验证要求。",
            "- 验证标准：最终 AGENTS.md 与当前任务直接相关，且不丢失任何关键约束。",
            "",
            "### 4. 测试、复盘与交付",
            "- 输入依据：测试要求、时间戳记录、执行结果与回退方案。",
            "- 操作内容：运行验证、整理结果、补齐复盘文档并归档关键产物。",
            f"- 产物路径：`{output_paths}` 中的验证记录、复盘记录和最终交付文件。",
            "- 验证方法：检查关键路径测试结果、失败处理和回退说明。",
            "- 验证标准：产物可复盘、可追踪、可回退。",
        ]
        if self._answer_text(answers.get("remote_access_mode")):
            steps.extend(
                [
                    "",
                    "### 5. 远程环境核对",
                    f"- 输入依据：远程主机 `{self._answer_text(answers.get('remote_hosts')) or '待补充'}` 与远程目录 `{self._answer_text(answers.get('remote_workdir')) or '待补充'}`。",
                    "- 操作内容：核对 SSH、远程目录、网络与权限边界，避免直接进入高风险操作。",
                    "- 验证方法：通过只读检查确认连接方式、目录存在性和资源边界。",
                    "- 验证标准：远程环境信息完整、路径明确，且不会越权执行。",
                ]
            )
        if self._answer_text(answers.get("docker_requirement")):
            docker_input_basis = self._answer_text(answers.get("docker_assets_path")) or "当前没有现成 Docker 资源，后续按任务生成新的 Dockerfile / compose / 构建上下文"
            steps.extend(
                [
                    "",
                    "### 6. Docker / 运行时准备",
                    f"- 输入依据：{docker_input_basis}。",
                    "- 操作内容：若已有 Docker 资源则先核对；若没有，则按任务需要生成镜像、构建上下文、运行方式和回退方案。",
                    "- 验证方法：核对 Docker 资源位置或新生成方案是否满足使用要求。",
                    "- 验证标准：Docker 方案与任务目标一致，并保留非 Docker 回退说明。",
                ]
            )
        if self._answer_text(answers.get("model_usage")) and self._answer_text(answers.get("model_usage")) != "no_model":
            steps.extend(
                [
                    "",
                    "### 7. 模型与批处理策略核对",
                    "- 输入依据：模型使用方式、供应商可替换要求、批处理规则。",
                    "- 操作内容：明确模型接入边界、批处理规模、结果映射关系和供应商替换策略。",
                    "- 验证方法：检查调用次数、批处理映射和回退策略是否清晰。",
                    "- 验证标准：模型处理链路可追踪、可替换、可批处理。",
                ]
            )
        return steps

    def generate_agents_document(
        self,
        request: GenerationRequest,
        catalog: CapabilityCatalog | None = None,
        max_files: int | None = None,
        progress_callback: Callable[[str, str, int], None] | None = None,
        semantic_client: BaseSemanticClient | None = None,
        model_runtime: dict[str, object] | None = None,
    ) -> GenerationResponse:
        started = time.perf_counter()
        effective_client = semantic_client or self.semantic_client
        effective_model_runtime = dict(model_runtime or semantic_client_summary(effective_client))
        if progress_callback is not None:
            progress_callback("prepare_catalog", "正在准备能力目录…", 12)
        catalog = catalog or self.load_or_build_capability_catalog(max_files=max_files, prefer_existing=max_files is None)
        response_plan_markdown = str(request.plan_markdown or "").strip()
        if progress_callback is not None:
            progress_callback("generate_draft", "阶段 1/2：正在生成草稿…", 32)
        response = self.generator.generate(request, catalog)
        artifact_id = self._next_artifact_id("generated_agents", ("md", "json"))
        draft_path = self.output_dir / f"generated_agents_{artifact_id}.draft.md"
        final_path = self.output_dir / f"generated_agents_{artifact_id}.final.md"
        path = self.output_dir / f"generated_agents_{artifact_id}.md"
        metadata_path = self.output_dir / f"generated_agents_{artifact_id}.json"
        plan_path = self.output_dir / f"generated_agents_{artifact_id}.plan.md"
        response.intake_session_id = request.session_id
        response.plan_markdown = response_plan_markdown
        if response.plan_markdown:
            self.logger.write_text(plan_path, response.plan_markdown)
            response.plan_output_path = str(plan_path)
        else:
            response.plan_output_path = ""
        draft_markdown = response.draft_markdown or response.agents_markdown
        response.draft_markdown = draft_markdown
        response.draft_output_path = str(draft_path)
        self.logger.write_text(draft_path, draft_markdown)
        if progress_callback is not None:
            progress_callback("draft_ready", "草稿已生成，正在准备最终优化…", 54)
        self.logger.record_run(
            stage="generate_draft",
            action="generate_draft_agents_document",
            input_basis=request.task_description,
            output_path=str(draft_path),
            status="ok",
            duration_ms=int((time.perf_counter() - started) * 1000),
            notes=f"references={len(response.references)}",
        )
        final_markdown, finalization_status, finalization_error, attempted_model = self._finalize_generated_document(
            request=request,
            draft_response=response,
            catalog=catalog,
            progress_callback=progress_callback,
            semantic_client=effective_client,
        )
        response.used_model_optimization = attempted_model
        response.model_runtime = effective_model_runtime
        response.finalization_status = finalization_status
        response.finalization_error = finalization_error
        response.final_markdown = final_markdown if finalization_status == "finalized" else ""
        if response.final_markdown:
            self.logger.write_text(final_path, response.final_markdown)
            response.final_output_path = str(final_path)
            response.display_markdown = response.final_markdown
        else:
            response.final_output_path = ""
            response.display_markdown = draft_markdown
        response.agents_markdown = response.display_markdown
        if progress_callback is not None:
            progress_callback("write_artifacts", "正在写入结果与元数据…", 90)
        self.logger.write_text(path, response.display_markdown)
        response.output_path = str(path)
        response.display_output_path = str(path)
        metadata = self._build_generated_document_metadata(
            request=request,
            response=response,
            artifact_id=artifact_id,
            output_path=path,
            model_runtime=effective_model_runtime,
        )
        self.logger.write_json(
            metadata_path,
            metadata,
        )
        response.artifact_id = artifact_id
        response.created_at = str(metadata.get("created_at", ""))
        response.title = str(metadata.get("title", ""))
        response.summary = str(metadata.get("summary", ""))
        response.template_type = str(metadata.get("template_type", ""))
        response.task_excerpt = str(metadata.get("task_excerpt", ""))
        if progress_callback is not None:
            completion_message = "生成完成，结果已写入案例库。" if finalization_status == "finalized" else "草稿已完成，最终优化未通过，已回退到草稿版本。"
            progress_callback("completed", completion_message, 100)
        self.logger.record_run(
            stage="generate_final",
            action="finalize_agents_document",
            input_basis=request.task_description,
            output_path=str(path),
            status="ok" if finalization_status == "finalized" else "fallback",
            duration_ms=int((time.perf_counter() - started) * 1000),
            notes=f"finalization_status={finalization_status}, references={len(response.references)}, metadata={metadata_path.name}",
        )
        self.logger.append_markdown(
            self.logger.evaluation_path,
            "Draft Generation Result",
            "\n".join(
                [
                    f"- artifact_timestamp: {artifact_id}",
                    f"- request_industry: {request.industry}",
                    f"- output_language: {request.output_language}",
                    f"- draft_output_path: {draft_path}",
                    f"- metadata_path: {metadata_path}",
                    f"- references: {', '.join(Path(item).name for item in response.references[:6]) or 'none'}",
                    f"- open_questions: {len(response.open_questions)}",
                ]
            ),
        )
        self.logger.append_markdown(
            self.logger.evaluation_path,
            "Finalization Result",
            "\n".join(
                [
                    f"- artifact_timestamp: {artifact_id}",
                    f"- finalization_status: {finalization_status}",
                    f"- used_model_optimization: {attempted_model}",
                    f"- model_runtime: {json.dumps(effective_model_runtime, ensure_ascii=False)}",
                    f"- display_output_path: {path}",
                    f"- final_output_path: {response.final_output_path or 'none'}",
                    f"- finalization_error: {finalization_error or 'none'}",
                    f"- reference_files: {len(response.reference_files)}",
                ]
            ),
        )
        return response

    def _finalize_generated_document(
        self,
        request: GenerationRequest,
        draft_response: GenerationResponse,
        catalog: CapabilityCatalog,
        progress_callback: Callable[[str, str, int], None] | None = None,
        semantic_client: BaseSemanticClient | None = None,
    ) -> tuple[str, str, str, bool]:
        client = semantic_client or self.semantic_client
        if isinstance(client, NoopSemanticClient):
            if progress_callback is not None:
                progress_callback("final_fallback", "阶段 2/2：未配置模型优化，使用草稿作为最终结果。", 76)
            return "", "fallback_to_draft", "Model optimization unavailable; using draft output.", False
        if progress_callback is not None:
            progress_callback("optimize_final", "阶段 2/2：正在优化最终稿…", 70)
        prompt = self._build_finalization_prompt(request, draft_response, catalog)
        raw = client.generate_agents(prompt)
        if progress_callback is not None:
            progress_callback("validate_final", "正在校验最终稿格式与引用…", 82)
        cleaned = self._extract_markdown_output(raw)
        attempted_model = True
        if not cleaned:
            if progress_callback is not None:
                progress_callback("final_fallback", "模型未返回可用结果，正在回退到草稿版本…", 86)
            return "", "fallback_to_draft", "Model optimization returned empty content.", attempted_model
        finalized = self._normalize_final_markdown(cleaned, request, draft_response)
        if not self._looks_like_agents_markdown(finalized):
            if progress_callback is not None:
                progress_callback("final_fallback", "最终稿校验未通过，正在回退到草稿版本…", 86)
            return "", "fallback_to_draft", "Model optimization returned invalid markdown.", attempted_model
        if progress_callback is not None:
            progress_callback("final_ready", "最终稿优化完成。", 88)
        return finalized, "finalized", "", attempted_model

    def _build_finalization_prompt(
        self,
        request: GenerationRequest,
        draft_response: GenerationResponse,
        catalog: CapabilityCatalog,
    ) -> str:
        payload = {
            "instructions": {
                "task": "Optimize the provided AGENTS.md draft into a stronger final AGENTS.md.",
                "return_format": "Return markdown only. Do not wrap the answer in JSON or prose.",
                "requirements": [
                    "Keep the document aligned with the explicit user request.",
                    "Do not invent commands, file paths, repository structures, APIs, or environment facts.",
                    "Preserve the concrete constraints, validation expectations, logging expectations, and rollback awareness from the draft.",
                    "Improve clarity, organization, precision, and actionability.",
                    "If a plan_markdown is provided, keep the final AGENTS.md aligned with that plan.",
                    "Keep or improve the Reference Files section and use only the provided references.",
                    "If the output language is bilingual, keep the result bilingual.",
                ],
            },
            "request": json_ready(request),
            "catalog_summary": {
                "card_count": catalog.card_count,
                "profile_count": catalog.profile_count,
                "source_run_id": catalog.source_run_id,
            },
            "matched_labels": draft_response.matched_labels,
            "open_questions": draft_response.open_questions,
            "reference_files": json_ready(draft_response.reference_files),
            "capability_matches": json_ready(draft_response.capability_matches),
            "draft_markdown": draft_response.draft_markdown or draft_response.agents_markdown,
        }
        return "\n".join(
            [
                "You are refining an AGENTS.md draft for production use.",
                "Use the structured context below and return only the final AGENTS.md markdown.",
                json.dumps(payload, ensure_ascii=False, indent=2),
            ]
        )

    @staticmethod
    def _extract_markdown_output(raw: str) -> str:
        text = raw.strip()
        if not text:
            return ""
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    def _normalize_final_markdown(
        self,
        value: str,
        request: GenerationRequest,
        draft_response: GenerationResponse,
    ) -> str:
        text = value.replace("\r\n", "\n").strip()
        if not text:
            return ""
        heading_matches = list(re.finditer(r"# AGENTS\.md\s*(?:\n|$)", text))
        if heading_matches:
            text = text[heading_matches[-1].start():].strip()
        if not text.startswith("#"):
            text = "# AGENTS.md\n\n" + text
        elif text.startswith("# AGENTS.md") and not text.startswith("# AGENTS.md\n"):
            text = text.replace("# AGENTS.md", "# AGENTS.md\n\n", 1)
        if draft_response.reference_files and "Reference Files" not in text:
            text = text.rstrip() + "\n\n## Reference Files\n\n" + self._render_reference_files_for_markdown(draft_response.reference_files)
        return self._sanitize_markdown_reference_section(text).rstrip() + "\n"

    @staticmethod
    def _looks_like_agents_markdown(value: str) -> bool:
        text = value.strip()
        if not text or len(text) < 120:
            return False
        if text.startswith("{") or text.startswith("["):
            return False
        if not text.startswith("#"):
            return False
        if "# AGENTS.md##" in text:
            return False
        return text.count("\n## ") >= 3

    @staticmethod
    def _render_reference_files_for_markdown(reference_files: list[object]) -> str:
        lines: list[str] = []
        for item in reference_files[:6]:
            path = str(getattr(item, "path", "") or "")
            title = str(getattr(item, "title", "") or "")
            reason = str(getattr(item, "reason", "") or "")
            if not path:
                continue
            path = WorkflowService._safe_reference_label(path)
            label = title or "Reference"
            lines.append(f"- `{path}` ({label})")
            if reason:
                lines.append(f"  - {reason}")
        return "\n".join(lines) or "- No close references found."

    @staticmethod
    def _public_artifact_name(value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        normalized = text.replace("\\", "/")
        name = normalized.rsplit("/", 1)[-1].strip()
        return name or normalized

    @staticmethod
    def _safe_reference_label(path: str) -> str:
        text = str(path or "").strip()
        if not text:
            return "AGENTS.md"
        normalized = text.replace("\\", "/")
        parts = [part for part in normalized.split("/") if part]
        base = parts[-1].strip() if parts else normalized.strip()
        if "__" in base:
            name_parts = [part for part in base.split("__") if part]
            if len(name_parts) >= 3:
                owner = name_parts[0]
                repo = name_parts[1]
                filename = "__".join(name_parts[2:])
                return f"{owner}/{repo}/{filename}"
        if parts and len(parts) >= 3 and base.lower().endswith(".md"):
            return "/".join(parts[-3:])
        return base or "AGENTS.md"

    @staticmethod
    def _looks_like_reference_path(value: str) -> bool:
        text = str(value or "").strip()
        if not text:
            return False
        normalized = text.replace("\\", "/")
        return (
            normalized.startswith("/")
            or bool(re.match(r"^[A-Za-z]:/", normalized))
            or normalized.lower().endswith(".md")
            or normalized.count("/") >= 2
            or "__" in normalized
        )

    def _sanitize_markdown_reference_section(self, value: str) -> str:
        text = value.replace("\r\n", "\n")
        if "Reference Files" not in text and "参考文件" not in text:
            return text
        lines = text.split("\n")
        sanitized: list[str] = []
        in_reference_section = False
        for line in lines:
            stripped = line.strip()
            if re.match(r"^##\s+(Reference Files|参考文件)\s*$", stripped, re.IGNORECASE):
                in_reference_section = True
                sanitized.append(line)
                continue
            if in_reference_section and re.match(r"^##\s+", stripped):
                in_reference_section = False
            if in_reference_section and stripped.startswith("-"):
                line = re.sub(
                    r"`([^`]+)`",
                    lambda match: f"`{self._safe_reference_label(match.group(1))}`"
                    if self._looks_like_reference_path(match.group(1))
                    else match.group(0),
                    line,
                )
                bare_match = re.match(r"^(\s*-\s+)([A-Za-z]:[\\/][^\s)`]+|/(?:[^\s)`]+))(.*)$", line)
                if bare_match and self._looks_like_reference_path(bare_match.group(2)):
                    line = f"{bare_match.group(1)}{self._safe_reference_label(bare_match.group(2))}{bare_match.group(3)}"
            sanitized.append(line)
        return "\n".join(sanitized)

    def _sanitize_reference_strings(self, raw: object) -> list[str]:
        items = raw if isinstance(raw, list) else []
        sanitized: list[str] = []
        seen: set[str] = set()
        for item in items:
            label = self._safe_reference_label(str(item or ""))
            if not label or label in seen:
                continue
            seen.add(label)
            sanitized.append(label)
        return sanitized

    def _sanitize_reference_files(self, raw: object) -> list[dict[str, str]]:
        items = raw if isinstance(raw, list) else []
        sanitized: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in items:
            if isinstance(item, dict):
                path = str(item.get("path", "") or "")
                title = str(item.get("title", "") or "")
                reason = str(item.get("reason", "") or "")
                source_type = str(item.get("source_type", "") or "capability_exemplar")
            else:
                path = str(getattr(item, "path", "") or "")
                title = str(getattr(item, "title", "") or "")
                reason = str(getattr(item, "reason", "") or "")
                source_type = str(getattr(item, "source_type", "") or "capability_exemplar")
            label = self._safe_reference_label(path)
            if not label or label in seen:
                continue
            seen.add(label)
            sanitized.append(
                {
                    "path": label,
                    "title": title,
                    "reason": reason,
                    "source_type": source_type,
                }
            )
        return sanitized

    def _artifact_file_path(self, value: str, fallback: Path | None = None) -> Path | None:
        text = str(value or "").strip()
        if not text:
            return fallback
        candidate = Path(text)
        if not candidate.is_absolute():
            candidate = self.output_dir / candidate.name
        return candidate

    def _sanitize_generated_artifact(self, path: Path, metadata: dict[str, object]) -> dict[str, object]:
        if not metadata:
            return metadata
        metadata_path = path.with_suffix(".json")
        sanitized_references = self._sanitize_reference_strings(metadata.get("references", []))
        sanitized_reference_files = self._sanitize_reference_files(metadata.get("reference_files", []))
        metadata_changed = False
        if sanitized_references != metadata.get("references", []):
            metadata["references"] = sanitized_references
            metadata_changed = True
        if sanitized_reference_files != metadata.get("reference_files", []):
            metadata["reference_files"] = sanitized_reference_files
            metadata_changed = True
        if metadata_changed:
            self.logger.write_json(metadata_path, metadata)
        candidates: set[Path] = {path}
        for raw_value in (
            metadata.get("output_path", ""),
            metadata.get("display_output_path", ""),
            metadata.get("draft_output_path", ""),
            metadata.get("final_output_path", ""),
        ):
            candidate = self._artifact_file_path(str(raw_value or ""))
            if candidate is not None:
                candidates.add(candidate)
        for candidate in candidates:
            if not candidate.exists() or not candidate.is_file():
                continue
            original = candidate.read_text(encoding="utf-8", errors="ignore")
            sanitized = self._sanitize_markdown_reference_section(original)
            if sanitized != original:
                self.logger.write_text(candidate, sanitized)
        return metadata

    def load_or_build_profiles(self, max_files: int | None = None, prefer_existing: bool = True) -> list[AgentProfile]:
        if prefer_existing and max_files is None:
            existing = self.load_latest_profiles()
            if existing is not None:
                return existing
        records, _ = self.scan_corpus(max_files=max_files)
        profiles, _ = self.label_corpus(records)
        self._cached_profiles = profiles
        self._cached_profile_source = "fresh_run"
        return profiles

    def load_or_build_capability_catalog(
        self,
        max_files: int | None = None,
        prefer_existing: bool = True,
    ) -> CapabilityCatalog:
        if prefer_existing and max_files is None:
            existing = self.load_latest_capability_catalog()
            if existing is not None:
                return existing
        profiles = self.load_or_build_profiles(max_files=max_files, prefer_existing=prefer_existing)
        catalog = build_capability_catalog(profiles, source_run_id=self.run_id)
        path = self.write_capability_catalog(profiles, run_id=self.run_id, catalog=catalog)
        self._cached_capability_catalog = catalog
        self._cached_capability_catalog_source = str(path)
        return catalog

    def load_latest_profiles(self) -> list[AgentProfile] | None:
        latest = self.get_latest_run()
        source_path = latest.get("generation_index_path", "") or latest.get("labeled_path", "")
        if not source_path:
            return None
        if self._cached_profiles is not None and self._cached_profile_source == source_path:
            return self._cached_profiles
        path = Path(source_path)
        if not path.exists():
            return None
        profiles: list[AgentProfile] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                profiles.append(agent_profile_from_dict(json.loads(line)))
        self._cached_profiles = profiles
        self._cached_profile_source = source_path
        return profiles

    def load_latest_capability_catalog(self) -> CapabilityCatalog | None:
        latest = self.get_latest_run()
        run_id = str(latest.get("run_id", ""))
        if not run_id:
            return None
        source_path = str(latest.get("capability_catalog_path", "")) or str(self.capability_catalog_path(run_id))
        if self._cached_capability_catalog is not None and self._cached_capability_catalog_source == source_path:
            return self._cached_capability_catalog
        path = Path(source_path)
        if path.exists():
            catalog = capability_catalog_from_dict(json.loads(path.read_text(encoding="utf-8")))
            self._cached_capability_catalog = catalog
            self._cached_capability_catalog_source = source_path
            return catalog
        profiles = self.load_latest_profiles()
        if not profiles:
            return None
        catalog = build_capability_catalog(profiles, source_run_id=run_id)
        self._write_capability_catalog_file(path, catalog)
        self._cached_capability_catalog = catalog
        self._cached_capability_catalog_source = source_path
        return catalog

    def write_generation_index(self, profiles: list[AgentProfile]) -> Path:
        path = self.logger.timestamped_path("generation_index", "jsonl")
        rows = [
            {
                "record": json_ready(profile.record),
                "labels": json_ready(profile.labels),
                "parse_notes": profile.parse_notes,
            }
            for profile in profiles
        ]
        self.logger.write_jsonl(path, rows)
        return path

    def capability_catalog_path(self, run_id: str) -> Path:
        return self.output_dir / f"capability_catalog_{run_id}.json"

    def write_capability_catalog(
        self,
        profiles: list[AgentProfile],
        run_id: str,
        catalog: CapabilityCatalog | None = None,
    ) -> Path:
        catalog = catalog or build_capability_catalog(profiles, source_run_id=run_id)
        path = self.capability_catalog_path(run_id)
        self._write_capability_catalog_file(path, catalog)
        self._cached_capability_catalog = catalog
        self._cached_capability_catalog_source = str(path)
        return path

    def _write_capability_catalog_file(self, path: Path, catalog: CapabilityCatalog) -> None:
        payload = json.dumps(json_ready(catalog), ensure_ascii=False, indent=2)
        self.logger.write_text(path, payload + "\n")

    def get_overview(self) -> dict[str, object]:
        latest = self.get_latest_run()
        preview = self.list_generated_documents(limit=8)
        return {
            "service_name": "Agents Production Studio",
            "service_mode": "production",
            "model_enabled": self.semantic_client.is_enabled(),
            "default_model_runtime": semantic_client_summary(self.semantic_client),
            "latest_run": {
                "run_id": str(latest.get("run_id", "")),
                "profile_count": int(latest.get("profile_count", 0) or 0),
            }
            if latest
            else {},
            "library_total": self._generated_document_count(),
            "library_preview": preview,
            "generation_history": preview,
        }

    def list_generated_documents(self, limit: int | None = 8) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for path in sorted(self.output_dir.glob("generated_agents_*.md"), reverse=True):
            if not self._is_primary_generated_document(path):
                continue
            row = self._generated_document_record(path, include_content=False)
            if row:
                rows.append(row)
            if limit is not None and len(rows) >= limit:
                break
        return rows

    def get_generated_document(self, artifact_id: str) -> dict[str, object] | None:
        safe_id = artifact_id.strip()
        if not safe_id or "/" in safe_id or "\\" in safe_id:
            return None
        path = self.output_dir / f"generated_agents_{safe_id}.md"
        if not path.exists() or not path.is_file():
            return None
        return self._generated_document_record(path, include_content=True)

    def get_latest_run(self) -> dict[str, object]:
        candidates: list[dict[str, object]] = []
        for path in sorted(self.output_dir.glob("run_log_*.jsonl")):
            run_id = path.stem.replace("run_log_", "")
            info = self._read_run_log(path, run_id)
            if info:
                candidates.append(info)
        if not candidates:
            return {}
        candidates.sort(key=lambda item: (int(item.get("profile_count", 0)), str(item.get("run_id", ""))), reverse=True)
        best = candidates[0]
        return best

    def _read_run_log(self, path: Path, run_id: str) -> dict[str, object] | None:
        stage_map: dict[str, dict[str, object]] = {}
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                stage_map[str(record.get("stage", ""))] = record
        if "label" not in stage_map:
            return None
        profile_count = 0
        notes = str(stage_map["label"].get("notes", ""))
        if notes.startswith("profiles="):
            try:
                profile_count = int(notes.split("=", 1)[1])
            except ValueError:
                profile_count = 0
        result = {
            "run_id": run_id,
            "profile_count": profile_count,
            "schema_path": str(self.output_dir / f"label_schema_{run_id}.yaml"),
            "manifest_path": str(self.output_dir / f"corpus_manifest_{run_id}.jsonl"),
            "labeled_path": str(self.output_dir / f"labeled_agents_{run_id}.jsonl"),
            "generation_index_path": str(self.output_dir / f"generation_index_{run_id}.jsonl"),
            "capability_catalog_path": str(self.capability_catalog_path(run_id)),
            "summary_path": str(self.output_dir / f"analysis_summary_{run_id}.md"),
            "review_path": str(self.output_dir / f"review_samples_{run_id}.jsonl"),
            "run_log_path": str(path),
            "decision_log_path": str(self.output_dir / f"decision_log_{run_id}.md"),
            "batch_log_path": str(self.output_dir / f"batch_runs_{run_id}.jsonl"),
            "evaluation_path": str(self.output_dir / f"evaluation_{run_id}.md"),
            "top_metrics": self._top_metrics_from_summary(self.output_dir / f"analysis_summary_{run_id}.md"),
        }
        return result

    @staticmethod
    def _build_capability_library_summary(catalog: CapabilityCatalog | None) -> dict[str, object]:
        if catalog is None:
            return {}
        return {
            "source_run_id": catalog.source_run_id,
            "profile_count": catalog.profile_count,
            "card_count": catalog.card_count,
            "taxonomy_snapshot": catalog.taxonomy_snapshot,
            "featured_cards": [
                {
                    "capability_id": card.capability_id,
                    "title": card.title,
                    "summary": card.summary,
                    "profile_count": card.profile_count,
                    "top_labels": card.top_labels,
                    "exemplar_filenames": card.exemplar_filenames[:3],
                }
                for card in catalog.cards[:6]
            ],
        }

    def _recent_generated_documents(self, limit: int = 12) -> list[dict[str, object]]:
        return self.list_generated_documents(limit=limit)

    def _generated_document_record(self, path: Path, include_content: bool) -> dict[str, object] | None:
        timestamp = path.stem.removeprefix("generated_agents_")
        try:
            stat = path.stat()
        except OSError:
            return None
        metadata = self._sanitize_generated_artifact(path, self._read_generated_metadata(path.with_suffix(".json")))
        request = self._normalize_request_dict(metadata.get("request", {}))
        template_type = str(metadata.get("template_type", "") or request.get("template_type", "")).strip()
        if not template_type:
            template_type = self._infer_template_type(request)
        references = metadata.get("references", [])
        reference_files = metadata.get("reference_files", [])
        open_questions = metadata.get("open_questions", [])
        matched_labels = metadata.get("matched_labels", {})
        finalization_status = str(metadata.get("finalization_status", "") or "draft_only")
        finalization_error = str(metadata.get("finalization_error", "") or "")
        used_model_optimization = bool(metadata.get("used_model_optimization", False))
        model_runtime = metadata.get("model_runtime", {})
        draft_output_path = str(metadata.get("draft_output_path", "") or "")
        final_output_path = str(metadata.get("final_output_path", "") or "")
        display_output_path = str(metadata.get("display_output_path", "") or metadata.get("output_path", "") or path)
        public_display_output = self._public_artifact_name(display_output_path) or path.name
        public_draft_output = self._public_artifact_name(draft_output_path)
        public_final_output = self._public_artifact_name(final_output_path)
        public_plan_output = self._public_artifact_name(str(metadata.get("plan_output_path", "") or ""))
        row = {
            "artifact_id": timestamp,
            "timestamp": timestamp,
            "created_at": str(metadata.get("created_at", "")),
            "filename": path.name,
            "path": path.name,
            "output_path": public_display_output,
            "display_output_path": public_display_output,
            "draft_output_path": public_draft_output,
            "final_output_path": public_final_output,
            "plan_output_path": public_plan_output,
            "metadata_path": path.with_suffix(".json").name,
            "size_bytes": stat.st_size,
            "modified_at": int(stat.st_mtime),
            "request": request,
            "template_type": template_type,
            "template_label": self._template_label(template_type),
            "title": str(metadata.get("title", "") or self._generated_document_title(request, template_type)),
            "summary": str(metadata.get("summary", "") or self._generated_document_summary(request, template_type)),
            "task_excerpt": str(metadata.get("task_excerpt", "") or self._truncate_text(request.get("task_description", ""), 160)),
            "reference_count": len(references) if isinstance(references, list) else 0,
            "open_questions_count": len(open_questions) if isinstance(open_questions, list) else 0,
            "finalization_status": finalization_status,
            "finalization_error": finalization_error,
            "used_model_optimization": used_model_optimization,
            "model_runtime": model_runtime if isinstance(model_runtime, dict) else {},
            "intake_session_id": str(metadata.get("intake_session_id", "") or ""),
        }
        if include_content:
            display_path = self._artifact_file_path(display_output_path, fallback=path) or path
            draft_path = self._artifact_file_path(draft_output_path)
            final_path = self._artifact_file_path(final_output_path)
            plan_path = self._artifact_file_path(str(metadata.get("plan_output_path", "") or ""))
            display_markdown = self._sanitize_markdown_reference_section(
                self._read_text_if_exists(display_path) or path.read_text(encoding="utf-8", errors="ignore")
            )
            draft_markdown = self._sanitize_markdown_reference_section(self._read_text_if_exists(draft_path or Path("")))
            final_markdown = self._sanitize_markdown_reference_section(self._read_text_if_exists(final_path or Path("")))
            row["agents_markdown"] = display_markdown
            row["display_markdown"] = display_markdown
            row["draft_markdown"] = draft_markdown or display_markdown
            row["final_markdown"] = final_markdown or ""
            row["references"] = self._sanitize_reference_strings(references)
            row["reference_files"] = self._sanitize_reference_files(reference_files)
            row["open_questions"] = open_questions if isinstance(open_questions, list) else []
            row["matched_labels"] = matched_labels if isinstance(matched_labels, dict) else {}
            row["plan_markdown"] = self._read_text_if_exists(plan_path or Path("")) or str(metadata.get("plan_markdown", "") or "")
            row["plan_output_path"] = self._public_artifact_name(str(metadata.get("plan_output_path", "") or ""))
            row["intake_session_id"] = str(metadata.get("intake_session_id", "") or "")
        return row

    def _generated_document_count(self) -> int:
        return sum(1 for path in self.output_dir.glob("generated_agents_*.md") if self._is_primary_generated_document(path))

    @staticmethod
    def _read_generated_metadata(path: Path) -> dict[str, object]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _build_generated_document_metadata(
        self,
        request: GenerationRequest,
        response: GenerationResponse,
        artifact_id: str,
        output_path: Path,
        model_runtime: dict[str, object] | None = None,
    ) -> dict[str, object]:
        template_type = request.template_type.strip() or self._infer_template_type(json_ready(request))
        return {
            "timestamp": artifact_id,
            "created_at": iso_now(),
            "request": request,
            "model_runtime": dict(model_runtime or {}),
            "output_path": str(output_path),
            "display_output_path": response.display_output_path or str(output_path),
            "draft_output_path": response.draft_output_path,
            "final_output_path": response.final_output_path,
            "references": response.references,
            "reference_files": response.reference_files,
            "matched_labels": response.matched_labels,
            "open_questions": response.open_questions,
            "capability_matches": response.capability_matches,
            "template_type": template_type,
            "title": self._generated_document_title(json_ready(request), template_type),
            "summary": self._generated_document_summary(json_ready(request), template_type),
            "task_excerpt": self._truncate_text(request.task_description, 160),
            "finalization_status": response.finalization_status,
            "finalization_error": response.finalization_error,
            "used_model_optimization": response.used_model_optimization,
            "plan_markdown": response.plan_markdown,
            "plan_output_path": response.plan_output_path,
            "intake_session_id": response.intake_session_id,
        }

    @staticmethod
    def _normalize_request_dict(raw: object) -> dict[str, object]:
        data = raw if isinstance(raw, dict) else {}
        return {
            "template_type": str(data.get("template_type", "") or ""),
            "industry": str(data.get("industry", "") or ""),
            "task_description": str(data.get("task_description", "") or ""),
            "target_user": str(data.get("target_user", "general") or "general"),
            "output_language": str(data.get("output_language", "zh") or "zh"),
            "environment": str(data.get("environment", "") or ""),
            "constraints": [str(item) for item in data.get("constraints", []) if str(item).strip()],
            "preferred_stack": [str(item) for item in data.get("preferred_stack", []) if str(item).strip()],
            "risk_tolerance": str(data.get("risk_tolerance", "medium") or "medium"),
            "session_id": str(data.get("session_id", "") or ""),
            "current_state": str(data.get("current_state", "") or ""),
            "goal_definition": str(data.get("goal_definition", "") or ""),
            "acceptance_criteria": [str(item) for item in data.get("acceptance_criteria", []) if str(item).strip()],
            "paths": {str(key): str(value) for key, value in dict(data.get("paths", {})).items() if str(value).strip()},
            "environment_detail": str(data.get("environment_detail", "") or ""),
            "permissions": dict(data.get("permissions", {})),
            "resource_constraints": dict(data.get("resource_constraints", {})),
            "question_answers": dict(data.get("question_answers", {})),
            "plan_markdown": str(data.get("plan_markdown", "") or ""),
        }

    def _generated_document_title(self, request: dict[str, object], template_type: str) -> str:
        template_label = self._template_label(template_type)
        industry = str(request.get("industry", "") or "").strip()
        if industry:
            return f"{template_label} · {industry}"
        task = self._truncate_text(str(request.get("task_description", "") or ""), 44)
        return task or template_label

    def _generated_document_summary(self, request: dict[str, object], template_type: str) -> str:
        task = self._truncate_text(str(request.get("task_description", "") or ""), 120)
        if task:
            return task
        parts = [self._template_label(template_type)]
        target_user = str(request.get("target_user", "") or "").strip()
        environment = str(request.get("environment", "") or "").strip()
        if target_user:
            parts.append(f"目标用户：{target_user}")
        if environment:
            parts.append(f"环境：{environment}")
        return "，".join(parts)

    def _infer_template_type(self, request: dict[str, object]) -> str:
        explicit = str(request.get("template_type", "") or "").strip()
        if explicit:
            return explicit
        text = " ".join(
            [
                str(request.get("task_description", "") or ""),
                str(request.get("environment", "") or ""),
                " ".join(str(item) for item in request.get("constraints", []) if str(item).strip()),
                " ".join(str(item) for item in request.get("preferred_stack", []) if str(item).strip()),
            ]
        ).lower()
        if any(token in text for token in ("browser", "web", "页面", "前端", "http service", "网站")):
            return "http_service"
        if any(token in text for token in ("api", "接口", "integration", "集成", "webhook")):
            return "api_integration"
        if any(token in text for token in ("cli", "command", "终端", "shell", "工具")):
            return "cli_tool"
        if any(token in text for token in ("data", "分析", "etl", "汇总", "report", "dataset")):
            return "data_processing"
        if any(token in text for token in ("workflow", "automation", "pipeline", "批处理", "工作流", "自动化")):
            return "automation_workflow"
        return "custom"

    @staticmethod
    def _template_label(template_type: str) -> str:
        return TEMPLATE_LABELS.get(template_type, TEMPLATE_LABELS["custom"])

    @staticmethod
    def _truncate_text(value: str, max_length: int) -> str:
        text = " ".join(value.split())
        if len(text) <= max_length:
            return text
        return text[: max(0, max_length - 1)].rstrip() + "…"

    def _next_artifact_id(self, prefix: str, suffixes: tuple[str, ...]) -> str:
        base = timestamp_now()
        candidate = base
        counter = 2
        while any((self.output_dir / f"{prefix}_{candidate}.{suffix}").exists() for suffix in suffixes):
            candidate = f"{base}_{counter:02d}"
            counter += 1
        return candidate

    @staticmethod
    def _is_primary_generated_document(path: Path) -> bool:
        stem = path.stem.removeprefix("generated_agents_")
        return bool(stem) and "." not in stem

    @staticmethod
    def _read_text_if_exists(path: Path) -> str:
        if not path or not str(path).strip():
            return ""
        if not path.exists() or not path.is_file():
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")

    @staticmethod
    def _top_metrics_from_summary(path: Path) -> list[str]:
        if not path.exists():
            return []
        metrics: list[str] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line.startswith("- total_profiles:") or line.startswith("- source_lang_distribution:") or line.startswith("- pair_status_distribution:"):
                    metrics.append(line.removeprefix("- ").strip())
                    continue
                if line.startswith("## "):
                    if len(metrics) >= 6:
                        break
        return metrics[:6]

    def _apply_semantic_batches(
        self,
        profiles: list[AgentProfile],
        *,
        semantic_client: BaseSemanticClient | None = None,
    ) -> list[object]:
        if not profiles:
            return []
        client = semantic_client or self.semantic_client
        if isinstance(client, NoopSemanticClient):
            note = {
                "timestamp": timestamp_now(),
                "mode": "skipped",
                "reason": "No semantic model client configured; rule-based labels only.",
                "profile_count": len(profiles),
            }
            self.logger.append_jsonl(self.logger.batch_log_path, note)
            return []
        batches, tuning_records = self.batch_planner.plan(profiles, use_full_text=True)
        log_rows: list[object] = list(tuning_records)
        for index, batch in enumerate(batches, start=1):
            batch_id = f"{self.run_id}_batch_{index:04d}"
            requests = [
                BatchRequestRecord(
                    batch_id=batch_id,
                    sample_id=profile.record.sample_id,
                    source_path=profile.record.source_path,
                    prompt_fragment=profile.prompt_excerpt[:500],
                    batch_size=len(batch),
                )
                for profile in batch
            ]
            for row in requests:
                log_rows.append(row)
            responses = client.classify_batch(batch_id, batch)
            response_map = {row.sample_id: row for row in responses}
            for profile in batch:
                response = response_map.get(profile.record.sample_id)
                if not response:
                    continue
                profile.labels.extend(response.parsed_labels)
                deduped: list = []
                seen: set[tuple[str, str, str]] = set()
                for label in profile.labels:
                    key = (label.label_type, label.canonical_value, label.freeform_value)
                    if key in seen:
                        continue
                    seen.add(key)
                    deduped.append(label)
                profile.labels = deduped
                log_rows.append(response)
        return log_rows

    @staticmethod
    def _build_review_rows(profiles: list[AgentProfile]) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for profile in profiles:
            label_count = len(profile.labels)
            low_confidence = [label for label in profile.labels if label.confidence < 0.6]
            if label_count <= 3 or low_confidence:
                rows.append(
                    {
                        "sample_id": profile.record.sample_id,
                        "filename": profile.record.filename,
                        "source_path": profile.record.source_path,
                        "label_count": label_count,
                        "low_confidence_labels": [json_ready(label) for label in low_confidence[:10]],
                        "pair_status": profile.record.pair_status,
                        "quality_score": profile.record.evaluation_avg_score,
                    }
                )
        return rows[:500]

    @staticmethod
    def _build_summary(profiles: list[AgentProfile]) -> str:
        source_counter = Counter(profile.record.source_lang for profile in profiles)
        pair_counter = Counter(profile.record.pair_status for profile in profiles)
        label_counter: dict[str, Counter[str]] = defaultdict(Counter)
        for profile in profiles:
            for label in profile.labels:
                if label.label_type == "freeform_tag":
                    continue
                label_counter[label.label_type][label.canonical_value] += 1
        lines = ["# Analysis Summary", ""]
        lines.append(f"- total_profiles: {len(profiles)}")
        lines.append(f"- source_lang_distribution: {dict(source_counter)}")
        lines.append(f"- pair_status_distribution: {dict(pair_counter)}")
        lines.append("")
        for label_type in sorted(label_counter):
            lines.append(f"## {label_type}")
            for value, count in label_counter[label_type].most_common(10):
                lines.append(f"- {value}: {count}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"
