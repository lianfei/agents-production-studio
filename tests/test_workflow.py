from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from importlib import util as importlib_util
from pathlib import Path
from unittest.mock import patch

from agents_corpus_workflow.llm import resolve_semantic_client
from agents_corpus_workflow.models import GenerationRequest
from agents_corpus_workflow.service import WorkflowService
from agents_corpus_workflow.web_ui import render_index_html


SAMPLE_EN = """<!-- AGENTS.md EVALUATION METADATA
REPO: example/devtools
FILE: example/devtools/AGENTS.md
AVG_SCORE: 72
-->
# Example Agent

Use Python, FastAPI, React, Docker, and pytest.

```bash
pytest
npm run test
```
"""

SAMPLE_ZH = """# 示例代理

这是一个数据分析和工作流自动化文档，强调 Python、CLI、日志记录和用户确认。
"""


class StubFinalizationClient:
    def classify_batch(self, batch_id, profiles):
        return []

    def generate_agents(self, prompt):
        if "Refine the rule-generated intake questionnaire" in prompt:
            return json.dumps(
                {
                    "note": "补充问答已由模型优化问法与验收建议。",
                    "questions": [
                        {
                            "question_id": "acceptance_criteria",
                            "title": "验收标准建议",
                            "prompt": "请确认系统生成的验收标准建议，并按需要修改。",
                            "help_text": "这些建议由规则生成后再经模型优化，可直接继续微调。",
                            "placeholder": "按需修改系统建议后的验收标准。",
                            "display_order": 2,
                            "suggestions": [
                                "生成前可以查看并校对 PLAN.md。",
                                "最终 AGENTS.md 与当前任务直接相关。",
                                "关键过程保留时间戳记录。",
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            )
        return """# AGENTS.md

## Task Brief

- Finalized task: `Create a Python CLI and API workflow with logging and tests.`

## Operating Requirements

- Keep timestamped execution records.
- Preserve validation and rollback notes.

## Reference Files

- `/tmp/reference-a.md` (Example Capability)
  - Matched capability pattern `Example Capability` via task_type=backend_api.
"""

    def is_enabled(self):
        return True


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["AGENTS_WORKFLOW_DISABLE_CODEX_CONFIG"] = "1"
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        (root / "agents_process" / "contents").mkdir(parents=True)
        (root / "agents_process" / "contents_zh").mkdir(parents=True)
        (root / "tmp").mkdir()
        (root / "agents_process" / "contents" / "example__repo__AGENTS.md").write_text(SAMPLE_EN, encoding="utf-8")
        (root / "agents_process" / "contents_zh" / "example__repo__AGENTS.md").write_text(SAMPLE_ZH, encoding="utf-8")
        self.root = root

    def tearDown(self) -> None:
        os.environ.pop("AGENTS_WORKFLOW_DISABLE_CODEX_CONFIG", None)
        self.tempdir.cleanup()

    @staticmethod
    def _pick_free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def test_analyze_and_generate(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        result = service.analyze_corpus()
        self.assertTrue(Path(result["manifest_path"]).exists())
        self.assertTrue(Path(result["labeled_path"]).exists())
        self.assertTrue(Path(result["capability_catalog_path"]).exists())
        request = GenerationRequest(
            template_type="cli_tool",
            industry="devtools",
            task_description="Create a Python CLI and API workflow with logging and tests.",
            environment="local_only",
            preferred_stack=["python", "fastapi"],
            output_language="en",
        )
        response = service.generate_agents_document(request)
        self.assertIn("# AGENTS.md", response.agents_markdown)
        self.assertIn("Task Brief", response.agents_markdown)
        self.assertIn("Create a Python CLI and API workflow with logging and tests.", response.agents_markdown)
        self.assertIn("Explicit stack: `python, fastapi`", response.agents_markdown)
        self.assertTrue(Path(response.output_path).exists())
        self.assertTrue(Path(response.draft_output_path).exists())
        self.assertEqual(response.finalization_status, "fallback_to_draft")
        self.assertFalse(response.final_output_path)
        self.assertTrue(response.reference_files)
        metadata_path = Path(response.output_path).with_suffix(".json")
        self.assertTrue(metadata_path.exists())
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(metadata["request"]["industry"], "devtools")
        self.assertEqual(metadata["output_path"], response.output_path)
        self.assertEqual(metadata["draft_output_path"], response.draft_output_path)
        self.assertEqual(metadata["finalization_status"], "fallback_to_draft")
        self.assertEqual(metadata["template_type"], "cli_tool")
        self.assertTrue(metadata["title"])
        self.assertTrue(metadata["summary"])
        second = service.generate_agents_document(request)
        self.assertNotEqual(response.output_path, second.output_path)
        self.assertTrue(Path(second.output_path).with_suffix(".json").exists())
        overview = service.get_overview()
        self.assertTrue(overview["library_preview"])
        self.assertEqual(overview["library_preview"][0]["request"]["industry"], "devtools")
        library = service.list_generated_documents(limit=None)
        self.assertEqual(library[0]["template_type"], "cli_tool")
        detail = service.get_generated_document(response.artifact_id)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertIn("# AGENTS.md", detail["agents_markdown"])
        self.assertEqual(detail["artifact_id"], response.artifact_id)
        self.assertIn("draft_markdown", detail)
        self.assertIn("reference_files", detail)

    def test_generated_library_fallback_metadata(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        output_path = self.root / "tmp" / "generated_agents_20991231235959.md"
        output_path.write_text("# AGENTS.md\\n\\nFallback body\\n", encoding="utf-8")
        metadata_path = output_path.with_suffix(".json")
        metadata_path.write_text(
            json.dumps(
                {
                    "timestamp": "20991231235959",
                    "created_at": "2099-12-31T23:59:59+08:00",
                    "request": {
                        "industry": "finance",
                        "task_description": "Create a browser-based HTTP workflow for analysts.",
                        "output_language": "en",
                        "environment": "browser_service",
                        "constraints": ["记录所有关键过程并带时间戳"],
                        "preferred_stack": ["python", "fastapi"],
                    },
                    "output_path": str(output_path),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        library = service.list_generated_documents(limit=None)
        self.assertEqual(library[0]["artifact_id"], "20991231235959")
        self.assertEqual(library[0]["template_type"], "http_service")
        self.assertTrue(library[0]["title"])
        self.assertTrue(library[0]["summary"])
        detail = service.get_generated_document("20991231235959")
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertIn("Fallback body", detail["agents_markdown"])

    def test_generated_library_sanitizes_reference_paths_and_public_output_names(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        output_path = self.root / "tmp" / "generated_agents_20990101010101.md"
        output_path.write_text(
            "# AGENTS.md\n\n## Reference Files\n\n- `/home/private/agents/example__repo__AGENTS.md` (Example Capability)\n"
            "  - Matched capability pattern `Example Capability` via task_type=backend_api.\n",
            encoding="utf-8",
        )
        metadata_path = output_path.with_suffix(".json")
        metadata_path.write_text(
            json.dumps(
                {
                    "timestamp": "20990101010101",
                    "created_at": "2099-01-01T01:01:01+08:00",
                    "request": {
                        "industry": "devtools",
                        "task_description": "Create a production HTTP workflow.",
                        "output_language": "en",
                        "environment": "browser_service",
                    },
                    "output_path": str(output_path),
                    "display_output_path": str(output_path),
                    "draft_output_path": str(output_path),
                    "references": ["/home/private/agents/example__repo__AGENTS.md"],
                    "reference_files": [
                        {
                            "path": "/home/private/agents/example__repo__AGENTS.md",
                            "title": "Example Capability",
                            "reason": "Matched capability pattern.",
                            "source_type": "capability_exemplar",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        library = service.list_generated_documents(limit=None)
        self.assertEqual(library[0]["output_path"], output_path.name)
        self.assertEqual(library[0]["draft_output_path"], output_path.name)
        self.assertEqual(library[0]["path"], output_path.name)
        self.assertEqual(library[0]["metadata_path"], metadata_path.name)
        detail = service.get_generated_document("20990101010101")
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["reference_files"][0]["path"], "example/repo/AGENTS.md")
        self.assertEqual(detail["references"][0], "example/repo/AGENTS.md")
        self.assertNotIn("/home/private/agents", detail["agents_markdown"])
        self.assertIn("example/repo/AGENTS.md", detail["agents_markdown"])
        persisted = output_path.read_text(encoding="utf-8")
        self.assertNotIn("/home/private/agents", persisted)
        self.assertIn("example/repo/AGENTS.md", persisted)

    def test_generate_with_model_finalization(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        service.analyze_corpus()
        service.semantic_client = StubFinalizationClient()
        request = GenerationRequest(
            template_type="cli_tool",
            industry="devtools",
            task_description="Create a Python CLI and API workflow with logging and tests.",
            environment="local_only",
            preferred_stack=["python", "fastapi"],
            output_language="en",
        )
        response = service.generate_agents_document(request)
        self.assertEqual(response.finalization_status, "finalized")
        self.assertTrue(response.used_model_optimization)
        self.assertTrue(response.final_markdown)
        self.assertIn("Finalized task", response.final_markdown)
        self.assertIn("Reference Files", response.final_markdown)
        self.assertNotIn("/tmp/reference-a.md", response.final_markdown)
        self.assertIn("reference-a.md", response.final_markdown)
        self.assertEqual(response.agents_markdown, response.display_markdown)
        self.assertEqual(response.agents_markdown, response.final_markdown)
        self.assertTrue(Path(response.final_output_path).exists())
        detail = service.get_generated_document(response.artifact_id)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertIn("final_markdown", detail)
        self.assertIn("Reference Files", detail["final_markdown"])
        self.assertNotIn("/tmp/reference-a.md", detail["final_markdown"])
        library = service.list_generated_documents(limit=None)
        self.assertEqual(len(library), 1)

    def test_generate_with_request_scoped_model_runtime_summary(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        service.analyze_corpus()
        request = GenerationRequest(
            template_type="cli_tool",
            industry="devtools",
            task_description="Create a Python CLI and API workflow with logging and tests.",
            environment="local_only",
            preferred_stack=["python", "fastapi"],
            output_language="en",
        )
        response = service.generate_agents_document(
            request,
            semantic_client=StubFinalizationClient(),
            model_runtime={
                "enabled": True,
                "mode": "custom",
                "source": "request",
                "provider": "openai_compatible",
                "provider_label": "OpenRouter",
                "model": "gpt-5.4",
                "wire_api": "responses",
            },
        )
        self.assertEqual(response.model_runtime["mode"], "custom")
        self.assertEqual(response.model_runtime["provider_label"], "OpenRouter")
        self.assertNotIn("api_key", response.model_runtime)
        metadata = json.loads(Path(response.output_path).with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["model_runtime"]["provider_label"], "OpenRouter")
        self.assertNotIn("api_key", metadata["model_runtime"])
        detail = service.get_generated_document(response.artifact_id)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["model_runtime"]["model"], "gpt-5.4")

    def test_intake_session_plan_and_generation(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        service.analyze_corpus()
        request = GenerationRequest(
            template_type="api_integration",
            industry="ai_ml",
            task_description="Create a browser-based workflow that collects task info, previews PLAN.md, and generates AGENTS.md.",
            environment="local_plus_remote",
            preferred_stack=["python", "fastapi"],
            constraints=["记录所有关键过程并带时间戳", "供应商必须可替换"],
            output_language="zh",
        )
        session = service.start_intake_session(request)
        self.assertTrue(session.session_id)
        self.assertGreater(len(session.questions), 0)
        answered = service.answer_intake_session(
            session.session_id,
            {
                "goal_definition": "产出一个浏览器可访问的服务，先完成问答和 PLAN.md，再生成最终 AGENTS.md。",
                "acceptance_criteria": "- 页面可以补充任务问答\n- 生成前可以看到 PLAN.md\n- AGENTS.md 与当前任务直接相关",
                "current_state": "existing_project",
                "project_root": str(self.root),
                "current_gap": "已有基础生成能力，但还没有基于问答的 intake 和 PLAN.md 预览流程。",
                "local_workdir": str(self.root / "tmp"),
                "output_paths": f"{self.root / 'tmp'}\n{self.root / 'localagent'}",
                "target_platform": "local_and_server",
                "allowed_operations": ["read_only_review", "modify_existing_files", "create_new_files"],
                "private_dependencies": "no_private",
                "test_requirements": "运行 unittest；检查 PLAN.md 和 AGENTS.md 产物；确认 metadata 保存 session 与 plan 信息。",
                "remote_access_mode": "ssh_key_ready",
                "remote_hosts": "agent@example.internal:22",
                "remote_workdir": "/srv/agents/workflow",
                "model_usage": "external_api",
                "vendor_replaceability": "must_replaceable",
                "batching_rules": "默认每批 50 条；在单次请求压力可接受时可增加批量；必须保留样本与结果映射关系。",
            },
        )
        self.assertIsNotNone(answered)
        assert answered is not None
        self.assertTrue(answered.ready_for_plan)
        self.assertEqual(answered.phase, "plan_ready")
        self.assertTrue(answered.plan_markdown.startswith("# PLAN.md"))
        self.assertTrue(answered.plan_output_path)
        self.assertTrue(Path(answered.plan_output_path).exists())
        rebuilt = service.build_generation_request_from_session(session.session_id)
        self.assertIsNotNone(rebuilt)
        assert rebuilt is not None
        self.assertEqual(rebuilt.session_id, session.session_id)
        self.assertTrue(rebuilt.plan_markdown.startswith("# PLAN.md"))
        self.assertEqual(rebuilt.paths["project_root"], str(self.root))
        response = service.generate_agents_document(rebuilt)
        self.assertEqual(response.intake_session_id, session.session_id)
        self.assertTrue(response.plan_markdown.startswith("# PLAN.md"))
        self.assertTrue(response.plan_output_path)
        self.assertTrue(Path(response.plan_output_path).exists())
        metadata_path = Path(response.output_path).with_suffix(".json")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(metadata["intake_session_id"], session.session_id)
        self.assertTrue(str(metadata["plan_output_path"]).endswith(".plan.md"))
        self.assertTrue(str(metadata["plan_markdown"]).startswith("# PLAN.md"))
        detail = service.get_generated_document(response.artifact_id)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["intake_session_id"], session.session_id)
        self.assertTrue(detail["plan_markdown"].startswith("# PLAN.md"))

    def test_intake_allows_deferred_answers(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        request = GenerationRequest(
            template_type="http_service",
            industry="devtools",
            task_description="Create a browser-based workflow.",
            environment="browser_service",
            output_language="zh",
        )
        session = service.start_intake_session(request)
        answered = service.answer_intake_session(
            session.session_id,
            {
                "goal_definition": "Create a browser-based workflow.",
                "acceptance_criteria": "页面可用",
                "current_state": "待确认：后续补充",
                "local_workdir": "待确认：后续补充",
                "output_paths": "待确认：后续补充",
                "target_platform": ["browser_http"],
                "allowed_operations": ["read_only_review"],
                "private_dependencies": "no_private",
                "test_requirements": "待确认：后续补充",
            },
        )
        self.assertIsNotNone(answered)
        assert answered is not None
        self.assertTrue(answered.ready_for_plan)
        self.assertIn("待后续补充", answered.plan_markdown)

    def test_intake_accepts_custom_values_for_required_choice_questions(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        request = GenerationRequest(
            template_type="http_service",
            industry="devtools",
            task_description="Create a browser-based workflow.",
            environment="browser_service",
            output_language="zh",
        )
        session = service.start_intake_session(request)
        answered = service.answer_intake_session(
            session.session_id,
            {
                "goal_definition": "Create a browser-based workflow.",
                "acceptance_criteria": "页面可用且可以生成结果",
                "current_state": "部分新建，部分接入现有系统",
                "output_paths": str(self.root / "tmp"),
                "target_platform": ["browser_http", "桌面客户端壳层"],
                "allowed_operations": ["read_only_review", "调用内部审批系统"],
                "private_dependencies": "no_private",
                "test_requirements": "运行 unittest 并手工检查关键路径",
            },
        )
        self.assertIsNotNone(answered)
        assert answered is not None
        self.assertTrue(answered.ready_for_plan)
        self.assertFalse(answered.validation_errors)

    def test_intake_prefilled_goal_does_not_need_repeat_input_and_docker_path_can_be_empty(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        request = GenerationRequest(
            template_type="api_integration",
            industry="devtools",
            task_description="Create a browser-accessible service and produce AGENTS.md.",
            environment="docker",
            output_language="zh",
        )
        session = service.start_intake_session(request)
        answered = service.answer_intake_session(
            session.session_id,
            {
                "acceptance_criteria": "页面可用；可生成 PLAN.md 和 AGENTS.md",
                "current_state": "new_project",
                "output_paths": str(self.root / "tmp"),
                "target_platform": ["browser_http", "docker_or_container"],
                "allowed_operations": ["create_new_files", "modify_existing_files"],
                "private_dependencies": "no_private",
                "test_requirements": "运行 unittest 并手工验证页面流程",
                "docker_requirement": "preferred",
                "model_usage": "no_model",
            },
        )
        self.assertIsNotNone(answered)
        assert answered is not None
        self.assertTrue(answered.ready_for_plan)
        self.assertFalse(answered.validation_errors)
        self.assertIn("执行目标", answered.plan_markdown)
        self.assertIn("后续按任务生成新的 Dockerfile / compose / 构建上下文", answered.plan_markdown)

    def test_intake_generates_acceptance_suggestions_from_existing_context(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        request = GenerationRequest(
            template_type="http_service",
            industry="devtools",
            task_description="Create a browser workflow that previews PLAN.md and supports one-click copy.",
            environment="browser_service",
            constraints=["记录所有关键过程并带时间戳", "不得跳过验证"],
            output_language="zh",
        )
        session = service.start_intake_session(request)
        acceptance_question = next(item for item in session.questions if item.question_id == "acceptance_criteria")
        self.assertTrue(acceptance_question.suggestions)
        self.assertIn("acceptance_criteria", session.answers)
        self.assertIn("PLAN.md", str(session.answers["acceptance_criteria"]))

    def test_intake_questionnaire_can_be_model_optimized(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        service.semantic_client = StubFinalizationClient()
        request = GenerationRequest(
            template_type="http_service",
            industry="devtools",
            task_description="Create a browser workflow that previews PLAN.md and supports one-click copy.",
            environment="browser_service",
            output_language="zh",
        )
        session = service.start_intake_session(request)
        acceptance_question = next(item for item in session.questions if item.question_id == "acceptance_criteria")
        self.assertEqual(session.question_generation_mode, "rule_plus_model")
        self.assertIn("模型优化", session.question_generation_note)
        self.assertEqual(acceptance_question.title, "验收标准建议")
        self.assertTrue(acceptance_question.suggestions)
        self.assertIn("PLAN.md", str(session.answers.get("acceptance_criteria", "")))

    def test_intake_questionnaire_can_use_request_scoped_model_client(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        request = GenerationRequest(
            template_type="http_service",
            industry="devtools",
            task_description="Create a browser workflow that previews PLAN.md and supports one-click copy.",
            environment="browser_service",
            output_language="zh",
        )
        session = service.start_intake_session(request, semantic_client=StubFinalizationClient())
        self.assertEqual(session.question_generation_mode, "rule_plus_model")
        self.assertIn("模型优化", session.question_generation_note)

    def test_index_html_contains_custom_choice_and_restore_controls(self) -> None:
        html = render_index_html({"library_preview": []})
        self.assertIn("不在选项中，手动输入", html)
        self.assertIn("选项里没有时，在这里补充自定义值", html)
        self.assertIn("恢复此项", html)
        self.assertIn("应用建议", html)
        self.assertIn("当前字段已与模板建议一致", html)
        self.assertIn("模型优化开关与配置", html)
        self.assertIn("模型优化", html)
        self.assertIn("应用当前设置", html)
        self.assertIn("禁用模型增强功能", html)
        self.assertIn("管理员令牌", html)
        self.assertIn("选择仓库示例", html)
        self.assertIn("加载 JSON", html)

    def test_service_lists_form_input_examples_from_source_root(self) -> None:
        examples_root = self.root / "examples" / "form_inputs"
        examples_root.mkdir(parents=True)
        (examples_root / "custom_sample.zh-CN.json").write_text(
            json.dumps(
                {
                    "template_type": "http_service",
                    "industry": "公共服务",
                    "task_description": "生成一个浏览器工作台，用于采集服务办理需求并输出 AGENTS.md。",
                    "target_user": "internal_team",
                    "output_language": "zh",
                    "environment": ["browser_service", "docker"],
                    "preferred_stack": ["python", "fastapi"],
                    "constraints": ["记录所有关键过程并带时间戳"],
                    "creative_notes": "界面优先使用结构化输入。",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        service = WorkflowService(self.root, self.root / "tmp")
        rows = service.list_form_input_examples()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["example_id"], "custom_sample.zh-CN")
        self.assertEqual(rows[0]["title"], "公共服务")
        self.assertEqual(rows[0]["request"]["environment"], ["browser_service", "docker"])
        self.assertEqual(rows[0]["request"]["preferred_stack"], ["python", "fastapi"])
        self.assertEqual(rows[0]["request"]["creative_notes"], "界面优先使用结构化输入。")

    def test_frontend_smoke_renders_sidebar_and_import_controls(self) -> None:
        if importlib_util.find_spec("playwright.sync_api") is None:
            self.skipTest("playwright is not installed")

        browser_path = next(
            (
                path
                for path in (
                    shutil.which("google-chrome"),
                    shutil.which("google-chrome-stable"),
                    shutil.which("chromium"),
                    shutil.which("chromium-browser"),
                )
                if path
            ),
            "",
        )
        if not browser_path:
            self.skipTest("no Chromium-compatible browser is available")

        from playwright.sync_api import sync_playwright

        port = self._pick_free_port()
        repo_root = Path(__file__).resolve().parents[1]
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "agents_corpus_workflow.cli",
                "serve-api",
                "--source-root",
                str(self.root),
                "--output-dir",
                str(self.root / "tmp"),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            deadline = time.time() + 10
            last_error = ""
            while time.time() < deadline:
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                        if response.status == 200:
                            break
                except Exception as exc:  # pragma: no cover - best effort diagnostic path
                    last_error = str(exc)
                    time.sleep(0.2)
            else:
                process.terminate()
                output, _ = process.communicate(timeout=2)
                self.fail(f"frontend smoke server did not become healthy: {last_error}\n{output}")

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    executable_path=browser_path,
                    headless=True,
                    args=["--no-sandbox"],
                )
                page = browser.new_page()
                page_errors: list[str] = []
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                page.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")

                self.assertEqual(page.locator("[data-screen-button]").count(), 3)
                self.assertEqual(page.locator("[data-step-button]").count(), 5)
                self.assertGreaterEqual(page.locator("#example_select option").count(), 2)
                self.assertEqual(page.locator("#load-json-btn").count(), 1)
                self.assertFalse(page_errors, f"unexpected page errors: {page_errors}")
                browser.close()
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)

    def test_service_default_model_settings_persist_and_hide_public_secret(self) -> None:
        service = WorkflowService(self.root, self.root / "tmp")
        candidate = {
            "mode": "custom",
            "provider_label": "OpenAI",
            "base_url": "https://api.openai.com/v1",
            "api_key": "secret-test-key",
            "model": "gpt-5.4",
            "wire_api": "responses",
        }
        with patch(
            "agents_corpus_workflow.service.validate_semantic_config",
            return_value=(
                {
                    "enabled": True,
                    "mode": "custom",
                    "source": "request",
                    "provider": "openai_compatible",
                    "provider_label": "OpenAI",
                    "model": "gpt-5.4",
                    "wire_api": "responses",
                },
                "",
            ),
        ):
            validation_result, validation_error = service.validate_default_model_candidate(candidate)
        self.assertFalse(validation_error)
        saved = service.save_default_model_candidate(candidate, validated_at=str(validation_result["validated_at"]))
        self.assertTrue(saved["effective_default_runtime"]["enabled"])
        self.assertEqual(saved["effective_default_runtime"]["provider_label"], "OpenAI")
        self.assertNotIn("api_key", json.dumps(saved, ensure_ascii=False))
        config_path = self.root / "tmp" / "default_model_config.json"
        self.assertTrue(config_path.exists())
        persisted = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["api_key"], "secret-test-key")

        reloaded = WorkflowService(self.root, self.root / "tmp")
        settings = reloaded.get_model_settings(admin_configured=True)
        self.assertTrue(settings["effective_default_runtime"]["enabled"])
        self.assertEqual(settings["effective_default_runtime"]["provider_label"], "OpenAI")
        self.assertNotIn("api_key", json.dumps(settings, ensure_ascii=False))

        disabled = reloaded.disable_default_model_enhancement()
        self.assertFalse(disabled["effective_default_runtime"]["enabled"])
        self.assertEqual(disabled["saved_default_model"]["mode"], "disabled")
        self.assertTrue(disabled["saved_default_model"]["has_custom_config"])

        re_enabled, re_enable_error = reloaded.enable_default_model_enhancement()
        self.assertFalse(re_enable_error)
        self.assertTrue(re_enabled["effective_default_runtime"]["enabled"])
        self.assertEqual(re_enabled["saved_default_model"]["mode"], "custom")

        disabled_reloaded = WorkflowService(self.root, self.root / "tmp")
        self.assertTrue(disabled_reloaded.get_overview()["default_model_runtime"]["enabled"])

    def test_resolve_custom_model_config_requires_no_codex_binding(self) -> None:
        client, summary, error = resolve_semantic_client(
            {
                "mode": "custom",
                "provider_label": "OpenAI",
                "base_url": "https://api.openai.com/v1",
                "api_key": "test-key",
                "model": "gpt-5.4",
                "wire_api": "responses",
            }
        )
        self.assertFalse(error)
        self.assertTrue(client.is_enabled())
        self.assertEqual(summary["mode"], "custom")
        self.assertEqual(summary["provider_label"], "OpenAI")
        self.assertEqual(summary["wire_api"], "responses")


if __name__ == "__main__":
    unittest.main()
