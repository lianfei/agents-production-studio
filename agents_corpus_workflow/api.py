from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from mimetypes import guess_type
from pathlib import Path
from urllib.parse import unquote, urlparse

from .llm import resolve_semantic_client
from .models import CapabilityCatalog
from .models import GenerationRequest, json_ready
from .service import WorkflowService
from .time_utils import iso_now
from .web_ui import render_index_html


def serve(
    source_root: str,
    output_dir: str,
    host: str = "127.0.0.1",
    port: int = 8765,
    initial_batch_size: int = 50,
    enable_admin_endpoints: bool = False,
) -> None:
    service = WorkflowService(source_root=source_root, output_dir=output_dir, initial_batch_size=initial_batch_size)
    cached_profiles: list | None = None
    cached_catalog: CapabilityCatalog | None = None
    max_request_bytes = 256 * 1024
    admin_token = os.environ.get("AGENTS_ADMIN_TOKEN", "").strip()
    progress_entries: dict[str, dict[str, object]] = {}
    progress_lock = threading.Lock()
    validation_entries: dict[str, dict[str, object]] = {}
    validation_lock = threading.Lock()
    validation_ttl_seconds = 15 * 60

    def update_progress(
        request_id: str,
        stage: str,
        message: str,
        percent: int,
        *,
        status: str = "running",
        done: bool = False,
        error: str = "",
    ) -> dict[str, object]:
        payload = {
            "request_id": request_id,
            "stage": stage,
            "message": message,
            "percent": max(0, min(int(percent), 100)),
            "status": status,
            "done": done,
            "error": error,
            "updated_at": iso_now(),
        }
        with progress_lock:
            progress_entries[request_id] = payload
        return payload

    def read_progress(request_id: str) -> dict[str, object] | None:
        with progress_lock:
            return progress_entries.get(request_id)

    def config_fingerprint(raw_config: object) -> str:
        data = raw_config if isinstance(raw_config, dict) else {}
        normalized = {
            "mode": str(data.get("mode", "custom") or "custom").strip(),
            "provider_label": str(data.get("provider_label", "") or "").strip(),
            "base_url": str(data.get("base_url", "") or "").strip(),
            "model": str(data.get("model", "") or "").strip(),
            "api_key": str(data.get("api_key", "") or "").strip(),
            "wire_api": str(data.get("wire_api", "chat_completions") or "chat_completions").strip(),
        }
        payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def prune_validation_entries() -> None:
        now = time.time()
        with validation_lock:
            expired = [
                token
                for token, item in validation_entries.items()
                if float(item.get("expires_at", 0) or 0) <= now
            ]
            for token in expired:
                validation_entries.pop(token, None)

    def create_validation_entry(raw_config: object, result: dict[str, object]) -> dict[str, object]:
        fingerprint = config_fingerprint(raw_config)
        validated_at = str(result.get("validated_at", "") or iso_now())
        created_at = time.time()
        token = f"val_{fingerprint[:12]}_{int(created_at)}"
        entry = {
            "fingerprint": fingerprint,
            "validated_at": validated_at,
            "created_at": created_at,
            "expires_at": created_at + validation_ttl_seconds,
        }
        with validation_lock:
            validation_entries[token] = entry
        return {
            "validation_token": token,
            "validated_at": validated_at,
            "expires_in_seconds": validation_ttl_seconds,
        }

    def consume_validation_entry(validation_token: str, raw_config: object) -> tuple[dict[str, object] | None, str]:
        prune_validation_entries()
        token = str(validation_token or "").strip()
        if not token:
            return None, "请先完成模型配置验证。"
        with validation_lock:
            entry = validation_entries.get(token)
        if entry is None:
            return None, "当前验证结果不存在或已过期，请重新验证配置。"
        if str(entry.get("fingerprint", "")) != config_fingerprint(raw_config):
            return None, "模型配置已变化，请重新验证后再保存。"
        with validation_lock:
            validation_entries.pop(token, None)
        return entry, ""

    def resolve_request_client(body: dict) -> tuple[object, dict[str, object]]:
        client, summary, error = resolve_semantic_client(body.get("model_config", {}), fallback_client=service.semantic_client)
        if error:
            raise ValueError(error)
        return client, summary

    def public_generation_payload(result: object) -> dict[str, object]:
        payload = json_ready(result)
        if not isinstance(payload, dict):
            return {}
        for key in ("output_path", "display_output_path", "draft_output_path", "final_output_path", "plan_output_path"):
            payload[key] = service._public_artifact_name(str(payload.get(key, "") or ""))
        references = payload.get("references", [])
        if isinstance(references, list):
            payload["references"] = [service._safe_reference_label(str(item or "")) for item in references if str(item or "").strip()]
        reference_files = payload.get("reference_files", [])
        if isinstance(reference_files, list):
            payload["reference_files"] = service._sanitize_reference_files(reference_files)
        for key in ("agents_markdown", "display_markdown", "draft_markdown", "final_markdown"):
            payload[key] = service._sanitize_markdown_reference_section(str(payload.get(key, "") or ""))
        return payload

    def public_intake_payload(result: object) -> dict[str, object]:
        payload = json_ready(result)
        if not isinstance(payload, dict):
            return {}
        payload["plan_output_path"] = service._public_artifact_name(str(payload.get("plan_output_path", "") or ""))
        active_ids = {str(item) for item in payload.get("active_question_ids", [])}
        questions = payload.get("questions", [])
        if isinstance(questions, list):
            payload["active_questions"] = [item for item in questions if str(item.get("question_id", "")) in active_ids]
        else:
            payload["active_questions"] = []
        return payload

    class Handler(BaseHTTPRequestHandler):
        def _send_text(self, status: int, content: str, content_type: str = "text/plain; charset=utf-8") -> None:
            data = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(data)

        def _send(self, status: int, payload: dict) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(data)

        def _body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length > max_request_bytes:
                raise ValueError("request body too large")
            raw = self.rfile.read(length) if length else b"{}"
            try:
                return json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                return {}

        def _admin_token_from_request(self, body: dict) -> str:
            header_token = self.headers.get("X-Admin-Token", "")
            if header_token and header_token.strip():
                return header_token.strip()
            return str(body.get("admin_token", "") or "").strip()

        def _require_admin_token(self, body: dict) -> str:
            if not admin_token:
                return "服务端未配置 AGENTS_ADMIN_TOKEN，当前模型配置页为只读模式。"
            provided = self._admin_token_from_request(body)
            if not provided:
                return "请输入管理员令牌后再执行该操作。"
            if provided != admin_token:
                return "管理员令牌无效。"
            return ""

        def do_POST(self) -> None:  # noqa: N802
            nonlocal cached_profiles, cached_catalog
            try:
                body = self._body()
            except ValueError as exc:
                self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"status": "error", "message": str(exc)})
                return
            if self.path == "/analyze":
                if not enable_admin_endpoints:
                    self._send(HTTPStatus.FORBIDDEN, {"status": "error", "message": "admin endpoint disabled"})
                    return
                result = service.analyze_corpus(max_files=body.get("max_files"))
                cached_profiles = None
                cached_catalog = None
                self._send(HTTPStatus.OK, {"status": "ok", "result": result})
                return
            if self.path == "/label":
                if not enable_admin_endpoints:
                    self._send(HTTPStatus.FORBIDDEN, {"status": "error", "message": "admin endpoint disabled"})
                    return
                semantic_client, _ = resolve_request_client(body)
                records, _ = service.scan_corpus(max_files=body.get("max_files"))
                cached_profiles, labeled_path = service.label_corpus(records, semantic_client=semantic_client)
                cached_catalog = service.load_latest_capability_catalog()
                self._send(
                    HTTPStatus.OK,
                    {"status": "ok", "result": {"count": len(cached_profiles), "labeled_path": str(labeled_path)}},
                )
                return
            if self.path == "/model-config/validate":
                admin_error = self._require_admin_token(body)
                if admin_error:
                    self._send(HTTPStatus.FORBIDDEN, {"status": "error", "message": admin_error})
                    return
                result, error = service.validate_default_model_candidate(body.get("model_config", {}))
                if error:
                    self._send(HTTPStatus.BAD_REQUEST, {"status": "error", "message": error, "result": result})
                    return
                token_payload = create_validation_entry(body.get("model_config", {}), result)
                self._send(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "result": {
                            **result,
                            **token_payload,
                        },
                    },
                )
                return
            if self.path == "/model-config/save":
                admin_error = self._require_admin_token(body)
                if admin_error:
                    self._send(HTTPStatus.FORBIDDEN, {"status": "error", "message": admin_error})
                    return
                entry, error = consume_validation_entry(str(body.get("validation_token", "") or ""), body.get("model_config", {}))
                if error:
                    self._send(HTTPStatus.BAD_REQUEST, {"status": "error", "message": error})
                    return
                result = service.save_default_model_candidate(
                    body.get("model_config", {}),
                    validated_at=str((entry or {}).get("validated_at", "") or ""),
                )
                result["admin_configured"] = bool(admin_token)
                self._send(HTTPStatus.OK, {"status": "ok", "result": result})
                return
            if self.path == "/model-config/enable":
                admin_error = self._require_admin_token(body)
                if admin_error:
                    self._send(HTTPStatus.FORBIDDEN, {"status": "error", "message": admin_error})
                    return
                result, error = service.enable_default_model_enhancement()
                if error:
                    self._send(HTTPStatus.BAD_REQUEST, {"status": "error", "message": error, "result": result})
                    return
                result["admin_configured"] = bool(admin_token)
                self._send(HTTPStatus.OK, {"status": "ok", "result": result})
                return
            if self.path == "/model-config/disable":
                admin_error = self._require_admin_token(body)
                if admin_error:
                    self._send(HTTPStatus.FORBIDDEN, {"status": "error", "message": admin_error})
                    return
                result = service.disable_default_model_enhancement()
                result["admin_configured"] = bool(admin_token)
                self._send(HTTPStatus.OK, {"status": "ok", "result": result})
                return
            if self.path == "/generate":
                request_id = str(body.get("request_id", "") or "").strip() or f"req_{len(progress_entries) + 1}"
                session_id = str(body.get("session_id", "") or "").strip()
                update_progress(request_id, "queued", "请求已提交，正在准备处理阶段…", 4)
                try:
                    semantic_client, model_runtime = resolve_request_client(body)
                    if session_id:
                        update_progress(request_id, "prepare_session", "正在载入问答结果与计划稿…", 10)
                        request = service.build_generation_request_from_session(session_id)
                        if request is None:
                            raise ValueError("intake session not ready for generation")
                        update_progress(request_id, "plan_ready", "问答与计划稿已就绪，准备生成草稿…", 24)
                    else:
                        request = GenerationRequest(
                            template_type=body.get("template_type", ""),
                            industry=body.get("industry", ""),
                            task_description=body.get("task_description", ""),
                            target_user=body.get("target_user", "general"),
                            output_language=body.get("output_language", "zh"),
                            environment=body.get("environment", ""),
                            constraints=body.get("constraints", []),
                            preferred_stack=body.get("preferred_stack", []),
                            risk_tolerance=body.get("risk_tolerance", "medium"),
                        )
                    if cached_catalog is None:
                        update_progress(request_id, "prepare_catalog", "正在加载能力目录…", 12)
                        cached_catalog = service.load_or_build_capability_catalog(
                            max_files=body.get("max_files"),
                            prefer_existing=body.get("max_files") in (None, ""),
                        )
                    else:
                        update_progress(request_id, "prepare_catalog", "能力目录已就绪，准备生成草稿…", 20)
                    response = service.generate_agents_document(
                        request,
                        catalog=cached_catalog,
                        progress_callback=lambda stage, message, percent: update_progress(request_id, stage, message, percent),
                        semantic_client=semantic_client,
                        model_runtime=model_runtime,
                    )
                except Exception as exc:
                    update_progress(
                        request_id,
                        "error",
                        str(exc) or "生成失败",
                        100,
                        status="error",
                        done=True,
                        error=str(exc),
                    )
                    self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"status": "error", "message": str(exc), "request_id": request_id})
                    return
                update_progress(request_id, "completed", "生成完成，结果已写入案例库。", 100, status="ok", done=True)
                self._send(HTTPStatus.OK, {"status": "ok", "request_id": request_id, "result": public_generation_payload(response)})
                return
            if self.path == "/intake/start":
                semantic_client, _ = resolve_request_client(body)
                request = GenerationRequest(
                    template_type=body.get("template_type", ""),
                    industry=body.get("industry", ""),
                    task_description=body.get("task_description", ""),
                    target_user=body.get("target_user", "general"),
                    output_language=body.get("output_language", "zh"),
                    environment=body.get("environment", ""),
                    constraints=body.get("constraints", []),
                    preferred_stack=body.get("preferred_stack", []),
                    risk_tolerance=body.get("risk_tolerance", "medium"),
                )
                result = service.start_intake_session(request, semantic_client=semantic_client)
                self._send(HTTPStatus.OK, {"status": "ok", "result": public_intake_payload(result)})
                return
            if self.path == "/intake/answer":
                session_id = str(body.get("session_id", "") or "").strip()
                result = service.answer_intake_session(session_id, dict(body.get("answers", {})))
                if result is None:
                    self._send(HTTPStatus.NOT_FOUND, {"status": "error", "message": "intake session not found"})
                    return
                self._send(HTTPStatus.OK, {"status": "ok", "result": public_intake_payload(result)})
                return
            self._send(HTTPStatus.NOT_FOUND, {"status": "error", "message": "unknown endpoint"})

        def do_GET(self) -> None:  # noqa: N802
            nonlocal cached_profiles, cached_catalog
            parsed = urlparse(self.path)
            if parsed.path == "/":
                html = render_index_html(service.get_overview(), enable_admin_actions=enable_admin_endpoints)
                self._send_text(HTTPStatus.OK, html, "text/html; charset=utf-8")
                return
            if parsed.path == "/overview":
                self._send(HTTPStatus.OK, {"status": "ok", "result": service.get_overview()})
                return
            if parsed.path == "/model-config":
                self._send(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "result": service.get_model_settings(admin_configured=bool(admin_token)),
                    },
                )
                return
            if parsed.path == "/form-examples":
                self._send(HTTPStatus.OK, {"status": "ok", "result": service.list_form_input_examples()})
                return
            if parsed.path == "/library":
                self._send(HTTPStatus.OK, {"status": "ok", "result": service.list_generated_documents(limit=None)})
                return
            if parsed.path.startswith("/intake/"):
                session_id = parsed.path.rsplit("/", 1)[-1]
                result = service.get_intake_session(session_id)
                if result is None:
                    self._send(HTTPStatus.NOT_FOUND, {"status": "error", "message": "intake session not found"})
                    return
                self._send(HTTPStatus.OK, {"status": "ok", "result": public_intake_payload(result)})
                return
            if parsed.path.startswith("/progress/"):
                request_id = parsed.path.rsplit("/", 1)[-1]
                result = read_progress(request_id)
                if result is None:
                    self._send(HTTPStatus.NOT_FOUND, {"status": "error", "message": "progress not found"})
                    return
                self._send(HTTPStatus.OK, {"status": "ok", "result": result})
                return
            if parsed.path.startswith("/library/"):
                artifact_id = parsed.path.rsplit("/", 1)[-1]
                result = service.get_generated_document(artifact_id)
                if result is None:
                    self._send(HTTPStatus.NOT_FOUND, {"status": "error", "message": "artifact not found"})
                    return
                self._send(HTTPStatus.OK, {"status": "ok", "result": json_ready(result)})
                return
            if parsed.path.startswith("/files/"):
                filename = unquote(parsed.path.rsplit("/", 1)[-1])
                if "/" in filename or "\\" in filename:
                    self._send(HTTPStatus.BAD_REQUEST, {"status": "error", "message": "invalid filename"})
                    return
                target = Path(output_dir) / filename
                if not target.exists() or not target.is_file():
                    self._send(HTTPStatus.NOT_FOUND, {"status": "error", "message": "file not found"})
                    return
                content_type = guess_type(target.name)[0] or "text/plain"
                if content_type.startswith("text/"):
                    content_type += "; charset=utf-8"
                self._send_text(HTTPStatus.OK, target.read_text(encoding="utf-8", errors="ignore"), content_type)
                return
            if parsed.path.startswith("/samples/"):
                sample_id = parsed.path.rsplit("/", 1)[-1]
                if cached_profiles is None:
                    cached_profiles = service.load_or_build_profiles(prefer_existing=True)
                for profile in cached_profiles:
                    if profile.record.sample_id == sample_id:
                        self._send(HTTPStatus.OK, {"status": "ok", "result": json_ready(profile)})
                        return
                self._send(HTTPStatus.NOT_FOUND, {"status": "error", "message": "sample not found"})
                return
            if parsed.path == "/health":
                self._send(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "source_root_name": Path(source_root).name,
                        "output_dir_name": Path(output_dir).name,
                        "generation_mode": "capability_catalog",
                        "admin_endpoints_enabled": enable_admin_endpoints,
                        "admin_token_configured": bool(admin_token),
                        "default_model_runtime": service.get_overview().get("default_model_runtime", {}),
                    },
                )
                return
            self._send(HTTPStatus.NOT_FOUND, {"status": "error", "message": "unknown endpoint"})

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
