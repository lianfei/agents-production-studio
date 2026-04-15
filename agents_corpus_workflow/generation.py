from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from .labels import RuleLabeler
from .models import CapabilityCard, CapabilityCatalog, CapabilityMatch, GenerationRequest, GenerationResponse, LabelRecord, ReferenceFile


STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "using",
    "use",
    "build",
    "create",
    "make",
    "task",
    "tasks",
    "workflow",
    "agent",
    "agents",
    "should",
    "must",
    "need",
    "needs",
    "require",
    "requires",
    "required",
    "keep",
    "have",
    "has",
    "into",
    "through",
    "provide",
    "generation",
}

ENVIRONMENT_HINTS = {
    "browser_service": ["browser_webapp", "api_service"],
    "local_only": ["local_cli"],
    "local_plus_remote": ["local_cli", "ssh_remote"],
    "docker": ["docker", "api_service"],
    "kubernetes": ["kubernetes", "api_service", "cloud"],
    "mixed": ["local_cli", "api_service", "browser_webapp"],
}

ENVIRONMENT_LABELS_ZH = {
    "browser_service": "浏览器 + HTTP 服务",
    "local_only": "仅本地环境",
    "local_plus_remote": "本地 + 远程环境",
    "docker": "Docker 环境",
    "kubernetes": "Kubernetes 环境",
    "mixed": "混合环境",
}

ENVIRONMENT_LABELS_EN = {
    "browser_service": "browser + HTTP service",
    "local_only": "local-only environment",
    "local_plus_remote": "local + remote environment",
    "docker": "Docker environment",
    "kubernetes": "Kubernetes environment",
    "mixed": "mixed environment",
}


class AgentsGenerator:
    def __init__(self, labeler: RuleLabeler) -> None:
        self.labeler = labeler

    def rank_capabilities(
        self,
        request: GenerationRequest,
        catalog: CapabilityCatalog,
        top_k: int = 6,
    ) -> list[tuple[float, CapabilityCard]]:
        request_labels = self._request_labels(request)
        scored: list[tuple[float, CapabilityCard]] = []
        for card in catalog.cards:
            score = self._score_capability(request, request_labels, card)
            if score > 0:
                scored.append((score, card))
        scored.sort(key=lambda item: (item[0], item[1].profile_count, item[1].average_quality_score), reverse=True)
        return scored[:top_k]

    def retrieve_capabilities(
        self,
        request: GenerationRequest,
        catalog: CapabilityCatalog,
        top_k: int = 6,
    ) -> list[CapabilityCard]:
        return [card for _, card in self.rank_capabilities(request, catalog, top_k=top_k)]

    def generate(self, request: GenerationRequest, catalog: CapabilityCatalog) -> GenerationResponse:
        request_labels = self._request_labels(request)
        ranked = self.rank_capabilities(request, catalog)
        capabilities = [card for _, card in ranked]
        capability_matches = self._build_capability_matches(request_labels, ranked)
        reference_files = self._build_reference_files(request, capability_matches)
        aggregated = self._aggregate_capability_labels(capabilities)
        markdown = self._render_markdown(request, capabilities, aggregated, catalog, reference_files)
        open_questions = self._open_questions(request)
        matched = defaultdict(list)
        for label in request_labels:
            matched[label.label_type].append(label.canonical_value or label.freeform_value)
        references = [item.path for item in reference_files]
        return GenerationResponse(
            agents_markdown=markdown,
            draft_markdown=markdown,
            final_markdown=markdown,
            display_markdown=markdown,
            references=references,
            matched_labels=dict(matched),
            open_questions=open_questions,
            reference_files=reference_files,
            capability_matches=capability_matches,
        )

    def _request_labels(self, request: GenerationRequest) -> list[LabelRecord]:
        pieces = [
            request.industry,
            request.task_description,
            request.goal_definition,
            request.current_state,
            request.environment,
            request.environment_detail,
            " ".join(request.constraints),
            " ".join(request.preferred_stack),
            " ".join(request.acceptance_criteria),
            " ".join(f"{key} {value}" for key, value in request.paths.items()),
            " ".join(f"{key} {value}" for key, value in request.question_answers.items()),
        ]
        text = "\n".join(piece for piece in pieces if piece)
        if not text.strip():
            return []
        fake = self.labeler.label_request_text(text, language_hint=request.output_language)
        labels = list(fake)
        labels.append(
            LabelRecord(
                label_type="industry",
                canonical_value=request.industry.strip().lower().replace(" ", "_"),
                source_method="input",
                confidence=1.0,
                evidence="request.industry",
            )
        )
        return labels

    @staticmethod
    def _score_capability(request: GenerationRequest, request_labels: list[LabelRecord], card: CapabilityCard) -> float:
        request_map: dict[str, set[str]] = defaultdict(set)
        for label in request_labels:
            request_map[label.label_type].add(label.canonical_value)
        capability_map = {label_type: set(values) for label_type, values in card.top_labels.items()}
        score = 0.0
        weights = {
            "industry": 4.0,
            "task_type": 4.0,
            "programming_language": 2.0,
            "runtime": 2.0,
            "tool_dependency": 1.0,
            "collaboration_mode": 1.0,
        }
        for label_type, values in request_map.items():
            score += len(values & capability_map.get(label_type, set())) * weights.get(label_type, 0.5)
        explicit_industry = AgentsGenerator._canonicalize(request.industry)
        industry_labels = card.top_labels.get("industry", [])
        if explicit_industry:
            if industry_labels[:1] == [explicit_industry]:
                score += 5.0
            elif explicit_industry in industry_labels:
                score += 2.5
            elif industry_labels:
                score -= 0.35
        environment_hints = set(AgentsGenerator._environment_hints(request.environment))
        runtime_labels = set(card.top_labels.get("runtime", []))
        if environment_hints:
            score += len(environment_hints & runtime_labels) * 2.5
            if runtime_labels and not (environment_hints & runtime_labels):
                score -= 0.25
        preferred_terms = {AgentsGenerator._canonicalize(item) for item in request.preferred_stack if item.strip()}
        language_labels = set(card.top_labels.get("programming_language", []))
        tool_labels = set(card.top_labels.get("tool_dependency", []))
        score += len(preferred_terms & language_labels) * 2.5
        score += len(preferred_terms & tool_labels) * 1.5
        score += AgentsGenerator._keyword_overlap_score(AgentsGenerator._request_keywords(request), card)
        if request.output_language == "zh" and card.source_languages.get("zh", 0) >= card.source_languages.get("en", 0):
            score += 1.0
        if request.output_language == "en" and card.source_languages.get("en", 0) >= card.source_languages.get("zh", 0):
            score += 1.0
        if request.output_language == "bilingual" and card.pair_statuses.get("paired", 0) > 0:
            score += 1.5
        if card.average_quality_score:
            score += min(card.average_quality_score / 100.0, 1.0)
        score += min(card.profile_count / 200.0, 1.5)
        return score

    @staticmethod
    def _aggregate_capability_labels(capabilities: list[CapabilityCard]) -> dict[str, list[str]]:
        counts: dict[str, Counter[str]] = defaultdict(Counter)
        for card in capabilities:
            for label_type, value_counts in card.label_counts.items():
                for value, count in value_counts.items():
                    counts[label_type][value] += count
        return {label_type: [value for value, _ in counter.most_common(5)] for label_type, counter in counts.items()}

    def _render_markdown(
        self,
        request: GenerationRequest,
        capabilities: list[CapabilityCard],
        aggregated: dict[str, list[str]],
        catalog: CapabilityCatalog,
        reference_files: list[ReferenceFile],
    ) -> str:
        language = request.output_language.lower()
        if language == "en":
            return self._render_english(request, capabilities, aggregated, catalog, reference_files)
        if language == "bilingual":
            return self._render_bilingual(request, capabilities, aggregated, catalog, reference_files)
        return self._render_chinese(request, capabilities, aggregated, catalog, reference_files)

    def _render_chinese(
        self,
        request: GenerationRequest,
        capabilities: list[CapabilityCard],
        aggregated: dict[str, list[str]],
        catalog: CapabilityCatalog,
        reference_files: list[ReferenceFile],
    ) -> str:
        explicit_stack = ", ".join(request.preferred_stack) or "未显式指定"
        reference_stack = ", ".join(self._supplemented_values(request.preferred_stack, aggregated.get("programming_language", []), limit=5))
        tools = ", ".join(aggregated.get("tool_dependency", [])[:6] or ["git", "python"])
        runtime_text = self._environment_display(request.environment, language="zh")
        runtime_refs = ", ".join(self._environment_hints(request.environment) or aggregated.get("runtime", [])[:4] or ["local_cli"])
        catalog_coverage = f"{catalog.card_count} 张能力卡，覆盖 {catalog.profile_count} 份已整理 profile"
        capability_list = "\n".join(f"- `{card.title}`: {card.summary}" for card in capabilities[:3])
        ref_list = self._render_reference_files(reference_files, language="zh")
        constraints = "\n".join(f"- {item}" for item in request.constraints) or "- 不得跳过验证与记录"
        deliverables = "\n".join(f"- {item}" for item in self._deliverables_zh(request))
        acceptance = "\n".join(f"- {item}" for item in self._acceptance_checks_zh(request))
        execution = "\n".join(f"- {item}" for item in self._execution_priorities_zh(request))
        task_focus = (request.goal_definition or request.task_description).strip() or "未提供具体任务描述。"
        current_state = request.current_state.strip() or "未明确"
        acceptance_input = "\n".join(f"- {item}" for item in request.acceptance_criteria) or "- 未单独提供，需沿用任务描述与验收要求。"
        path_lines = "\n".join(f"- `{key}`: `{value}`" for key, value in request.paths.items()) or "- 尚未提供结构化路径信息。"
        environment_detail = request.environment_detail.strip() or "未补充更细的环境说明。"
        return f"""# AGENTS.md

## 任务定位

- 当前任务：`{task_focus}`
- 当前状态：`{current_state}`
- 主要行业：`{request.industry or "未指定"}`
- 目标用户：`{request.target_user}`
- 输出语言：`{request.output_language}`
- 运行环境：`{runtime_text}`
- 风险容忍度：`{request.risk_tolerance}`

## 显式输入优先级

- 用户明确给出的任务描述、环境、约束、技术栈优先于语料中的通用模式。
- 能力目录只用于补充参考、避免遗漏，不得覆盖用户的显式要求。
- 如果语料推荐与当前任务冲突，先指出冲突，再按当前任务目标执行。

## 交付清单

{deliverables}

## 已确认环境与路径

- 环境补充说明：{environment_detail}

{path_lines}

## 执行要求

- 先审查现状，再进入修改或生成阶段。
- 所有关键步骤必须留下记录，包含时间戳、输入依据、输出路径、验证结果。
- 所有结论区分为：已确认事实、基于证据的推断、待验证假设。
- 默认使用绝对路径，避免隐藏状态和模糊引用。
- 需要模型时优先走批处理与结构化返回，保证可追溯性。
{execution}

## 适配偏好

- 显式技术栈：`{explicit_stack}`
- 语料补充参考：`{reference_stack or "无额外补充"}`
- 典型工具参考：`{tools}`
- 运行时标签参考：`{runtime_refs}`
- 风险容忍度：`{request.risk_tolerance}`

## 约束与安全

{constraints}

- 禁止跳过日志记录、批处理映射、失败重试说明和结果复核。
- 如果信息不足或与现有工程冲突，必须先指出缺失项或冲突点，再继续。

## 验收标准

{acceptance}

## 已收集的任务验收输入

{acceptance_input}

## 参考能力模式

- 当前能力目录规模：`{catalog_coverage}`
- 优先命中的能力模式：
{capability_list or "- 暂无明显命中能力卡"}

## Reference Files

{ref_list or "- 暂无明显参考文件。"}
"""

    def _render_english(
        self,
        request: GenerationRequest,
        capabilities: list[CapabilityCard],
        aggregated: dict[str, list[str]],
        catalog: CapabilityCatalog,
        reference_files: list[ReferenceFile],
    ) -> str:
        explicit_stack = ", ".join(request.preferred_stack) or "not explicitly specified"
        reference_stack = ", ".join(self._supplemented_values(request.preferred_stack, aggregated.get("programming_language", []), limit=5))
        tools = ", ".join(aggregated.get("tool_dependency", [])[:6] or ["git", "python"])
        runtime_text = self._environment_display(request.environment, language="en")
        runtime_refs = ", ".join(self._environment_hints(request.environment) or aggregated.get("runtime", [])[:4] or ["local_cli"])
        capability_list = "\n".join(f"- `{card.title}`: {card.summary}" for card in capabilities[:3])
        ref_list = self._render_reference_files(reference_files, language="en")
        constraints = "\n".join(f"- {item}" for item in request.constraints) or "- Do not skip validation or execution records."
        deliverables = "\n".join(f"- {item}" for item in self._deliverables_en(request))
        acceptance = "\n".join(f"- {item}" for item in self._acceptance_checks_en(request))
        execution = "\n".join(f"- {item}" for item in self._execution_priorities_en(request))
        task_focus = (request.goal_definition or request.task_description).strip() or "No specific task description was provided."
        current_state = request.current_state.strip() or "unspecified"
        acceptance_input = "\n".join(f"- {item}" for item in request.acceptance_criteria) or "- No structured acceptance criteria were provided."
        path_lines = "\n".join(f"- `{key}`: `{value}`" for key, value in request.paths.items()) or "- No structured path details were provided."
        environment_detail = request.environment_detail.strip() or "No finer-grained environment notes were collected."
        return f"""# AGENTS.md

## Task Brief

- Current task: `{task_focus}`
- Current state: `{current_state}`
- Industry: `{request.industry or "unspecified"}`
- Target user: `{request.target_user}`
- Output language: `{request.output_language}`
- Environment: `{runtime_text}`
- Risk tolerance: `{request.risk_tolerance}`

## Explicit Request Priority

- The user's explicit task description, environment, constraints, and preferred stack override corpus defaults.
- The capability catalog is reference material, not the source of truth for request-specific requirements.
- If corpus guidance conflicts with the active request, surface the conflict and follow the active request.

## Deliverables

{deliverables}

## Confirmed Environment And Paths

- Environment detail: {environment_detail}

{path_lines}

## Operating Requirements

- Inspect the current state before editing, generating, or proposing fixes.
- Keep timestamped records for decisions, actions, outputs, and validation results.
- Separate confirmed facts, evidence-based inferences, and open assumptions.
- Use absolute paths and explicit commands.
- When model assistance is used, keep batch mappings and structured responses.
{execution}

## Task Preferences

- Target user: `{request.target_user}`
- Output language: `{request.output_language}`
- Explicit stack: `{explicit_stack}`
- Catalog-supported stack hints: `{reference_stack or "no extra hints"}`
- Typical tools: `{tools}`
- Runtime hints: `{runtime_refs}`
- Risk tolerance: `{request.risk_tolerance}`

## Constraints

{constraints}

- Never skip logging, batch mapping, failure notes, or result review.
- If information is missing or conflicts with the repo state, stop and surface the gap first.

## Acceptance Checks

{acceptance}

## Collected Acceptance Inputs

{acceptance_input}

## Capability Reference

- Active capability inventory: `{catalog.card_count}` cards derived from `{catalog.profile_count}` structured profiles.
- Closest capability matches:
{capability_list or "- No strong capability cards matched."}

## Reference Files

{ref_list or "- No close references found."}
"""

    def _render_bilingual(
        self,
        request: GenerationRequest,
        capabilities: list[CapabilityCard],
        aggregated: dict[str, list[str]],
        catalog: CapabilityCatalog,
        reference_files: list[ReferenceFile],
    ) -> str:
        chinese = self._render_chinese(request, capabilities, aggregated, catalog, reference_files)
        english = self._render_english(request, capabilities, aggregated, catalog, reference_files)
        return f"{english}\n\n---\n\n{chinese}"

    @staticmethod
    def _build_capability_matches(
        request_labels: list[LabelRecord],
        ranked: list[tuple[float, CapabilityCard]],
    ) -> list[CapabilityMatch]:
        request_map: dict[str, set[str]] = defaultdict(set)
        for label in request_labels:
            request_map[label.label_type].add(label.canonical_value)
        matches: list[CapabilityMatch] = []
        for score, card in ranked:
            matched_dimensions: list[str] = []
            for label_type in ("industry", "task_type", "programming_language", "runtime", "tool_dependency"):
                overlap = sorted(request_map.get(label_type, set()) & set(card.top_labels.get(label_type, [])))
                if overlap:
                    matched_dimensions.append(f"{label_type}={', '.join(overlap[:2])}")
            matches.append(
                CapabilityMatch(
                    capability_id=card.capability_id,
                    title=card.title,
                    summary=card.summary,
                    score=round(score, 3),
                    profile_count=card.profile_count,
                    matched_dimensions=matched_dimensions,
                    exemplar_paths=card.exemplar_paths[:3],
                )
            )
        return matches

    def _build_reference_files(
        self,
        request: GenerationRequest,
        capability_matches: list[CapabilityMatch],
        limit: int = 6,
    ) -> list[ReferenceFile]:
        references: list[ReferenceFile] = []
        seen: set[str] = set()
        language = request.output_language.lower()
        for match in capability_matches:
            for path in match.exemplar_paths:
                normalized = path.strip()
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                references.append(
                    ReferenceFile(
                        path=self._safe_reference_label(normalized),
                        title=match.title,
                        reason=self._reference_reason(match, language=language),
                        source_type="capability_exemplar",
                    )
                )
                if len(references) >= limit:
                    return references
        return references

    @staticmethod
    def _reference_reason(match: CapabilityMatch, language: str) -> str:
        details = ", ".join(match.matched_dimensions[:3]) or "general capability overlap"
        if language == "en":
            return f"Matched capability pattern `{match.title}` via {details}."
        return f"命中能力模式 `{match.title}`，相关维度：{details}。"

    @staticmethod
    def _safe_reference_label(path: str) -> str:
        name = Path(path).name.strip()
        if not name:
            return "AGENTS.md"
        parts = [part for part in name.split("__") if part]
        if len(parts) >= 3:
            owner = parts[0]
            repo = parts[1]
            filename = "__".join(parts[2:])
            return f"{owner}/{repo}/{filename}"
        return name

    @staticmethod
    def _render_reference_files(reference_files: list[ReferenceFile], language: str) -> str:
        if not reference_files:
            return ""
        lines: list[str] = []
        for item in reference_files[:6]:
            path = item.path.strip()
            title = item.title.strip()
            reason = item.reason.strip()
            if language == "en":
                label = title or "Reference"
                lines.append(f"- `{path}` ({label})")
                if reason:
                    lines.append(f"  - {reason}")
            else:
                label = title or "参考来源"
                lines.append(f"- `{path}`（{label}）")
                if reason:
                    lines.append(f"  - {reason}")
        return "\n".join(lines)

    @staticmethod
    def _open_questions(request: GenerationRequest) -> list[str]:
        questions: list[str] = []
        if not request.environment:
            questions.append("运行环境还未明确，后续应补充本地、远程或混合环境约束。")
        if not request.constraints:
            questions.append("缺少显式任务约束，建议补充安全、权限、测试或时限要求。")
        if not request.preferred_stack:
            questions.append("缺少技术栈偏好，生成结果会使用语料中的通用模式。")
        if not request.goal_definition:
            questions.append("建议补充更明确的任务目标描述，以便让草稿与最终稿更贴近真实任务。")
        if not request.acceptance_criteria:
            questions.append("建议补充结构化验收标准，避免后续只生成泛化要求。")
        return questions

    @staticmethod
    def _canonicalize(value: str) -> str:
        return value.strip().lower().replace(" ", "_").replace("-", "_")

    @staticmethod
    def _environment_keys(environment: str) -> list[str]:
        raw = str(environment or "").strip()
        if not raw:
            return []
        parts = [
            AgentsGenerator._canonicalize(item)
            for item in re.split(r"[,;\n+]+", raw)
            if item.strip()
        ]
        seen: set[str] = set()
        keys: list[str] = []
        for item in parts:
            if not item or item in seen:
                continue
            seen.add(item)
            keys.append(item)
        return keys

    @staticmethod
    def _environment_hints(environment: str) -> list[str]:
        keys = AgentsGenerator._environment_keys(environment)
        hints: list[str] = []
        seen: set[str] = set()
        for key in keys:
            for hint in ENVIRONMENT_HINTS.get(key, [key] if key else []):
                if not hint or hint in seen:
                    continue
                seen.add(hint)
                hints.append(hint)
        return hints

    @staticmethod
    def _request_keywords(request: GenerationRequest) -> set[str]:
        text = " ".join(
            [
                request.industry,
                request.task_description,
                request.goal_definition,
                request.current_state,
                request.target_user,
                request.output_language,
                request.environment,
                request.environment_detail,
                " ".join(request.constraints),
                " ".join(request.preferred_stack),
                " ".join(request.acceptance_criteria),
                request.risk_tolerance,
                " ".join(str(value) for value in request.question_answers.values()),
            ]
        ).lower()
        tokens: set[str] = set()
        for raw in re.findall(r"[a-z0-9_./#+-]{3,}", text):
            for piece in re.split(r"[_./#+-]+", raw):
                token = piece.strip()
                if len(token) < 3 or token in STOPWORDS:
                    continue
                tokens.add(token)
        return tokens

    @staticmethod
    def _keyword_overlap_score(keywords: set[str], card: CapabilityCard) -> float:
        if not keywords:
            return 0.0
        card_terms: set[str] = set()
        text_chunks = [card.title, card.summary, *card.exemplar_filenames]
        for values in card.top_labels.values():
            text_chunks.extend(values)
        for chunk in text_chunks:
            lowered = chunk.lower()
            for raw in re.findall(r"[a-z0-9_./#+-]{3,}", lowered):
                for piece in re.split(r"[_./#+-]+", raw):
                    token = piece.strip()
                    if len(token) >= 3:
                        card_terms.add(token)
        overlap = keywords & card_terms
        return min(len(overlap) * 0.45, 4.0)

    @staticmethod
    def _supplemented_values(explicit_values: list[str], fallback_values: list[str], limit: int = 5) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in explicit_values + fallback_values:
            text = item.strip()
            key = text.lower()
            if not text or key in seen:
                continue
            seen.add(key)
            result.append(text)
            if len(result) >= limit:
                break
        return result

    @staticmethod
    def _environment_display(environment: str, language: str) -> str:
        keys = AgentsGenerator._environment_keys(environment)
        if not keys:
            return "未明确" if language == "zh" else "unspecified"
        labels = ENVIRONMENT_LABELS_ZH if language == "zh" else ENVIRONMENT_LABELS_EN
        rendered = [labels.get(key, key) for key in keys]
        return " + ".join(rendered)

    @staticmethod
    def _deliverables_zh(request: GenerationRequest) -> list[str]:
        text = request.task_description.lower()
        items = ["生成或更新与当前任务直接对应的 `AGENTS.md` 主文档"]
        if any(token in text for token in ("browser", "页面", "ui", "web")):
            items.append("提供可通过浏览器访问的交互页面或前端界面")
        if any(token in text for token in ("http", "api", "service", "服务", "接口", "server")):
            items.append("提供可运行的 HTTP 服务或接口入口")
        if any(token in text for token in ("history", "记录", "日志", "report", "summary", "汇总")):
            items.append("输出可复盘的带时间戳记录、汇总或历史信息")
        if any(token in text for token in ("batch", "批处理", "model", "llm", "模型")):
            items.append("保留批处理策略、请求映射和失败处理说明")
        if any(token in text for token in ("test", "验证", "验收", "校验")):
            items.append("提供可执行的验证步骤或自动化测试入口")
        return items

    @staticmethod
    def _deliverables_en(request: GenerationRequest) -> list[str]:
        text = request.task_description.lower()
        items = ["Generate or update the `AGENTS.md` document for the active task"]
        if any(token in text for token in ("browser", "page", "ui", "web")):
            items.append("Provide a browser-accessible UI or front-end interaction surface")
        if any(token in text for token in ("http", "api", "service", "server", "endpoint")):
            items.append("Provide a runnable HTTP service or API entry point")
        if any(token in text for token in ("history", "log", "report", "summary", "record")):
            items.append("Produce timestamped records, summaries, or history artifacts for review")
        if any(token in text for token in ("batch", "model", "llm")):
            items.append("Preserve batch strategy, request mapping, and failure-handling notes")
        if any(token in text for token in ("test", "verify", "validation", "acceptance")):
            items.append("Provide executable validation steps or automated test coverage")
        return items

    @staticmethod
    def _execution_priorities_zh(request: GenerationRequest) -> list[str]:
        priorities = [
            "先输出与当前任务直接对应的执行方案、交付物和验证标准，再补充通用原则。",
            "优先使用用户显式指定的环境与技术栈；只有在输入缺失时才退回语料推荐。",
        ]
        if request.preferred_stack:
            priorities.append(f"实现时优先围绕 `{', '.join(request.preferred_stack)}` 组织结构、命令和示例。")
        if request.environment:
            priorities.append(f"执行路径必须适配 `{AgentsGenerator._environment_display(request.environment, 'zh')}`。")
        return priorities

    @staticmethod
    def _execution_priorities_en(request: GenerationRequest) -> list[str]:
        priorities = [
            "Start with the task-specific execution path, deliverables, and validation criteria before adding generic guidance.",
            "Prefer the user's explicit environment and stack; fall back to corpus defaults only when inputs are missing.",
        ]
        if request.preferred_stack:
            priorities.append(f"Structure implementation guidance around `{', '.join(request.preferred_stack)}` first.")
        if request.environment:
            priorities.append(f"The execution path must fit `{AgentsGenerator._environment_display(request.environment, 'en')}`.")
        return priorities

    @staticmethod
    def _acceptance_checks_zh(request: GenerationRequest) -> list[str]:
        checks = [
            "输出内容必须与当前任务描述直接对应，而不是仅复述通用模板。",
            "关键步骤、关键决策、输出路径和验证结果都要带时间戳记录。",
        ]
        if request.environment:
            checks.append(f"最终产物应可在 `{AgentsGenerator._environment_display(request.environment, 'zh')}` 下落地执行或访问。")
        if request.preferred_stack:
            checks.append(f"生成内容应优先采用 `{', '.join(request.preferred_stack)}`，除非明确说明偏离原因。")
        if request.constraints:
            checks.append("所有显式约束必须在方案、实现或验证中逐条得到响应。")
        return checks

    @staticmethod
    def _acceptance_checks_en(request: GenerationRequest) -> list[str]:
        checks = [
            "The output must respond directly to the current task instead of restating a generic template.",
            "Key steps, decisions, output paths, and validation results must be recorded with timestamps.",
        ]
        if request.environment:
            checks.append(f"The final artifact should be runnable or accessible in `{AgentsGenerator._environment_display(request.environment, 'en')}`.")
        if request.preferred_stack:
            checks.append(f"The generated guidance should prioritize `{', '.join(request.preferred_stack)}` unless a deviation is explained.")
        if request.constraints:
            checks.append("Every explicit constraint must be addressed in the plan, implementation, or validation.")
        return checks
