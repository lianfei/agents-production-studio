from __future__ import annotations

import json
import os
import re
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .models import AgentProfile, BatchRequestRecord, BatchResponseRecord, BatchTuningRecord, LabelRecord
from .time_utils import iso_now


@dataclass(slots=True)
class ModelConfig:
    provider: str = "noop"
    provider_label: str = ""
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    wire_api: str = "chat_completions"
    source: str = "none"
    mode: str = "default"


class BaseSemanticClient:
    def classify_batch(self, batch_id: str, profiles: list[AgentProfile]) -> list[BatchResponseRecord]:
        raise NotImplementedError

    def generate_agents(self, prompt: str) -> str:
        raise NotImplementedError

    def is_enabled(self) -> bool:
        return False


class NoopSemanticClient(BaseSemanticClient):
    def __init__(
        self,
        *,
        reason: str = "semantic labeling disabled",
        source: str = "none",
        mode: str = "default",
        provider_label: str = "",
    ) -> None:
        self.reason = reason
        self.source = source
        self.mode = mode
        self.provider_label = provider_label

    def classify_batch(self, batch_id: str, profiles: list[AgentProfile]) -> list[BatchResponseRecord]:
        responses: list[BatchResponseRecord] = []
        for profile in profiles:
            responses.append(
                BatchResponseRecord(
                    batch_id=batch_id,
                    sample_id=profile.record.sample_id,
                    raw_response=self.reason,
                    parsed_labels=[],
                    parse_status="skipped",
                )
            )
        return responses

    def generate_agents(self, prompt: str) -> str:
        return ""


class OpenAICompatibleClient(BaseSemanticClient):
    def __init__(self, config: ModelConfig) -> None:
        self.config = config

    def classify_batch(self, batch_id: str, profiles: list[AgentProfile]) -> list[BatchResponseRecord]:
        prompt = self._classification_prompt(profiles)
        raw = self._post_chat(prompt)
        parsed = self._parse_label_response(raw, profiles, batch_id)
        return parsed

    def generate_agents(self, prompt: str) -> str:
        return self._post_chat(prompt)

    def is_enabled(self) -> bool:
        return True

    def validate_connection(self) -> tuple[bool, str]:
        prompt = "Reply with exactly OK."
        text, error = self._post_chat_with_error(prompt, timeout=45)
        if error:
            return False, error
        if not text.strip():
            return False, "模型接口返回成功状态，但没有返回可用文本内容。"
        return True, ""

    def _post_chat(self, prompt: str) -> str:
        text, _ = self._post_chat_with_error(prompt)
        return text

    def _post_responses(self, prompt: str) -> str:
        text, _ = self._post_responses_with_error(prompt)
        return text

    def _post_chat_with_error(self, prompt: str, timeout: int = 120) -> tuple[str, str]:
        if not self.config.base_url or not self.config.api_key or not self.config.model:
            return "", "模型配置缺少 Base URL、API Key 或模型名。"
        if self.config.wire_api == "responses":
            return self._post_responses_with_error(prompt, timeout=timeout)
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }
        body, error = self._post_json(url, payload, timeout=timeout)
        if error:
            return "", error
        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return "", "模型接口返回格式异常，未找到 chat completion 文本内容。"
        return str(text or ""), ""

    def _post_responses_with_error(self, prompt: str, timeout: int = 180) -> tuple[str, str]:
        if not self.config.base_url or not self.config.api_key or not self.config.model:
            return "", "模型配置缺少 Base URL、API Key 或模型名。"
        url = self.config.base_url.rstrip("/") + "/responses"
        payload = {
            "model": self.config.model,
            "input": prompt,
            "text": {"format": {"type": "text"}, "verbosity": "low"},
            "reasoning": {"effort": "low"},
        }
        body, error = self._post_json(url, payload, timeout=timeout)
        if error:
            return "", error
        if isinstance(body.get("output_text"), str) and body["output_text"].strip():
            return body["output_text"], ""
        outputs = body.get("output", [])
        collected: list[str] = []
        for item in outputs:
            for content in item.get("content", []):
                text = content.get("text")
                if text:
                    collected.append(text)
        if collected:
            return "\n".join(collected), ""
        return "", "模型接口返回格式异常，未找到 responses 文本内容。"

    def _post_json(self, url: str, payload: dict[str, object], timeout: int) -> tuple[dict[str, object], str]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return {}, _http_error_message(exc)
        except urllib.error.URLError as exc:
            return {}, _url_error_message(exc)
        except socket.timeout:
            return {}, "连接模型接口超时。"
        except TimeoutError:
            return {}, "连接模型接口超时。"
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            return {}, "模型接口返回了无法解析的 JSON。"
        return body if isinstance(body, dict) else {}, ""

    @staticmethod
    def _classification_prompt(profiles: list[AgentProfile]) -> str:
        items = []
        for profile in profiles:
            full_text = _read_full_text(profile.record.source_path)
            items.append(
                {
                    "sample_id": profile.record.sample_id,
                    "filename": profile.record.filename,
                    "source_lang": profile.record.source_lang,
                    "content": full_text,
                    "existing_labels": [
                        {
                            "label_type": label.label_type,
                            "canonical_value": label.canonical_value,
                            "freeform_value": label.freeform_value,
                        }
                        for label in profile.labels
                        if label.label_type != "freeform_tag"
                    ],
                }
            )
        instructions = {
            "task": "Review each sample and return semantic labels for core label families plus optional freeform tags.",
            "core_label_types": [
                "industry",
                "task_type",
                "programming_language",
                "runtime",
                "tool_dependency",
                "collaboration_mode",
                "risk_constraint",
            ],
            "required_format": [
                {
                    "sample_id": "string",
                    "labels": [
                        {
                            "label_type": "industry|task_type|programming_language|runtime|tool_dependency|collaboration_mode|risk_constraint|freeform_tag",
                            "canonical_value": "string",
                            "freeform_value": "string",
                            "confidence": 0.0,
                            "evidence": "string",
                        }
                    ],
                }
            ],
        }
        return json.dumps({"instructions": instructions, "items": items}, ensure_ascii=False)

    @staticmethod
    def _parse_label_response(raw: str, profiles: list[AgentProfile], batch_id: str) -> list[BatchResponseRecord]:
        profile_ids = {profile.record.sample_id for profile in profiles}
        try:
            payload = json.loads(raw) if raw else []
        except json.JSONDecodeError:
            payload = []
        by_id = {item.get("sample_id"): item for item in payload if isinstance(item, dict)}
        responses: list[BatchResponseRecord] = []
        for sample_id in profile_ids:
            item = by_id.get(sample_id, {})
            labels: list[LabelRecord] = []
            for label_data in item.get("labels", []):
                if not isinstance(label_data, dict):
                    continue
                labels.append(
                    LabelRecord(
                        label_type=str(label_data.get("label_type", "freeform_tag")),
                        canonical_value=str(label_data.get("canonical_value", "semantic")),
                        freeform_value=str(label_data.get("freeform_value", "")),
                        source_method="model",
                        confidence=float(label_data.get("confidence", 0.5)),
                        evidence=str(label_data.get("evidence", "")),
                    )
                )
            responses.append(
                BatchResponseRecord(
                    batch_id=batch_id,
                    sample_id=sample_id,
                    raw_response=json.dumps(item, ensure_ascii=False),
                    parsed_labels=labels,
                    parse_status="ok" if labels else "empty",
                )
            )
        return responses


def build_semantic_client_from_env() -> BaseSemanticClient:
    if os.environ.get("AGENTS_WORKFLOW_DISABLE_CODEX_CONFIG", "").strip() in {"1", "true", "TRUE"}:
        return NoopSemanticClient(
            reason="semantic labeling disabled by AGENTS_WORKFLOW_DISABLE_CODEX_CONFIG",
            source="flag",
            mode="default",
            provider_label="默认模型已禁用",
        )
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_MODEL", "").strip()
    if base_url and api_key and model:
        return OpenAICompatibleClient(
            ModelConfig(
                provider="openai_compatible",
                provider_label="默认 OpenAI 兼容接口",
                base_url=_normalize_base_url(base_url),
                api_key=api_key,
                model=model,
                wire_api="chat_completions",
                source="env",
                mode="default",
            )
        )
    codex_config = _load_codex_config()
    if codex_config is not None:
        return OpenAICompatibleClient(codex_config)
    return NoopSemanticClient(
        reason="no semantic model client configured",
        source="none",
        mode="default",
        provider_label="未配置默认模型",
    )


def resolve_semantic_client(
    raw_config: object,
    *,
    fallback_client: BaseSemanticClient | None = None,
) -> tuple[BaseSemanticClient, dict[str, object], str]:
    config = raw_config if isinstance(raw_config, dict) else {}
    mode = _normalize_mode(config.get("mode", "default"))
    if mode == "disabled":
        client = NoopSemanticClient(
            reason="semantic labeling disabled for this request",
            source="request",
            mode="disabled",
            provider_label="当前请求已禁用模型",
        )
        return client, semantic_client_summary(client), ""
    if mode == "custom":
        provider_label = str(config.get("provider_label", "") or config.get("provider", "") or "自定义 OpenAI 兼容接口").strip()
        base_url = _normalize_base_url(str(config.get("base_url", "")).strip())
        api_key = str(config.get("api_key", "")).strip()
        model = str(config.get("model", "")).strip()
        wire_api = str(config.get("wire_api", "chat_completions") or "chat_completions").strip()
        missing: list[str] = []
        if not base_url:
            missing.append("base_url")
        if not api_key:
            missing.append("api_key")
        if not model:
            missing.append("model")
        if wire_api not in {"chat_completions", "responses"}:
            return (
                NoopSemanticClient(
                    reason="invalid custom model config",
                    source="request_invalid",
                    mode="custom",
                    provider_label=provider_label,
                ),
                {
                    "enabled": False,
                    "mode": "custom",
                    "source": "request_invalid",
                    "provider": "openai_compatible",
                    "provider_label": provider_label,
                    "model": model,
                    "wire_api": wire_api or "chat_completions",
                },
                "Custom model config has unsupported wire_api; expected chat_completions or responses.",
            )
        if missing:
            return (
                NoopSemanticClient(
                    reason="incomplete custom model config",
                    source="request_invalid",
                    mode="custom",
                    provider_label=provider_label,
                ),
                {
                    "enabled": False,
                    "mode": "custom",
                    "source": "request_invalid",
                    "provider": "openai_compatible",
                    "provider_label": provider_label,
                    "model": model,
                    "wire_api": wire_api,
                },
                f"Custom model config missing required fields: {', '.join(missing)}.",
            )
        client = OpenAICompatibleClient(
            ModelConfig(
                provider="openai_compatible",
                provider_label=provider_label,
                base_url=base_url,
                api_key=api_key,
                model=model,
                wire_api=wire_api,
                source="request",
                mode="custom",
            )
        )
        return client, semantic_client_summary(client), ""
    client = fallback_client or build_semantic_client_from_env()
    summary = semantic_client_summary(client)
    summary["mode"] = "default"
    return client, summary, ""


def validate_semantic_config(raw_config: object) -> tuple[dict[str, object], str]:
    client, summary, error = resolve_semantic_client(raw_config, fallback_client=None)
    if error:
        return summary, error
    if isinstance(client, NoopSemanticClient):
        return summary, "当前配置未启用模型。"
    if isinstance(client, OpenAICompatibleClient):
        ok, message = client.validate_connection()
        if not ok:
            return summary, message
        return summary, ""
    return summary, "当前模型客户端不支持验证。"


def persisted_default_client(raw_config: object) -> tuple[BaseSemanticClient | None, dict[str, object], str]:
    data = raw_config if isinstance(raw_config, dict) else {}
    if not data:
        return None, {}, ""
    enabled = bool(data.get("enabled", False))
    mode = _normalize_mode(data.get("mode", "default"))
    if not enabled or mode == "disabled":
        client = NoopSemanticClient(
            reason="semantic labeling disabled by persisted default config",
            source="persisted",
            mode="disabled",
            provider_label="禁用模型增强功能",
        )
        summary = semantic_client_summary(client)
        summary["enabled"] = False
        summary["mode"] = "disabled"
        summary["source"] = "persisted"
        return client, summary, ""
    if mode == "default":
        return None, {"enabled": True, "mode": "default", "source": "persisted"}, ""
    provider_label = str(data.get("provider_label", "") or "服务端默认模型").strip()
    base_url = _normalize_base_url(str(data.get("base_url", "")).strip())
    api_key = str(data.get("api_key", "")).strip()
    model = str(data.get("model", "")).strip()
    wire_api = str(data.get("wire_api", "chat_completions") or "chat_completions").strip()
    if not base_url or not api_key or not model:
        return None, {}, "持久化默认模型配置缺少 Base URL、API Key 或模型名。"
    if wire_api not in {"chat_completions", "responses"}:
        return None, {}, "持久化默认模型配置的接口协议无效。"
    client = OpenAICompatibleClient(
        ModelConfig(
            provider="openai_compatible",
            provider_label=provider_label,
            base_url=base_url,
            api_key=api_key,
            model=model,
            wire_api=wire_api,
            source="persisted",
            mode="default",
        )
    )
    return client, semantic_client_summary(client), ""


def semantic_client_summary(client: BaseSemanticClient) -> dict[str, object]:
    if isinstance(client, OpenAICompatibleClient):
        return {
            "enabled": True,
            "mode": client.config.mode or "default",
            "source": client.config.source or "unknown",
            "provider": client.config.provider or "openai_compatible",
            "provider_label": client.config.provider_label or "OpenAI 兼容接口",
            "model": client.config.model,
            "wire_api": client.config.wire_api or "chat_completions",
        }
    if isinstance(client, NoopSemanticClient):
        return {
            "enabled": False,
            "mode": client.mode or "default",
            "source": client.source or "none",
            "provider": "noop",
            "provider_label": client.provider_label or "未启用模型",
            "model": "",
            "wire_api": "",
        }
    return {
        "enabled": bool(client.is_enabled()),
        "mode": "default",
        "source": "unknown",
        "provider": "unknown",
        "provider_label": "未知模型客户端",
        "model": "",
        "wire_api": "",
    }


class AdaptiveBatchPlanner:
    def __init__(self, initial_batch_size: int = 50, max_batch_size: int = 200, target_chars: int = 120000) -> None:
        self.initial_batch_size = initial_batch_size
        self.max_batch_size = max_batch_size
        self.target_chars = target_chars

    def plan(self, profiles: list[AgentProfile], use_full_text: bool = False) -> tuple[list[list[AgentProfile]], list[BatchTuningRecord]]:
        batches: list[list[AgentProfile]] = []
        records: list[BatchTuningRecord] = []
        cursor = 0
        current_size = self.initial_batch_size
        while cursor < len(profiles):
            estimated = 0
            batch: list[AgentProfile] = []
            while cursor < len(profiles) and len(batch) < current_size:
                profile = profiles[cursor]
                addition = _estimate_profile_chars(profile, use_full_text=use_full_text)
                if batch and estimated + addition > self.target_chars:
                    break
                batch.append(profile)
                estimated += addition
                cursor += 1
            if not batch:
                batch.append(profiles[cursor])
                estimated = _estimate_profile_chars(profiles[cursor], use_full_text=use_full_text)
                cursor += 1
            next_size = current_size
            if estimated < self.target_chars * 0.55 and current_size < self.max_batch_size:
                next_size = min(self.max_batch_size, current_size + 25)
            elif estimated > self.target_chars * 0.95 and current_size > 10:
                next_size = max(10, current_size - 10)
            if next_size != current_size:
                records.append(
                    BatchTuningRecord(
                        timestamp=iso_now(),
                        old_batch_size=current_size,
                        new_batch_size=next_size,
                        trigger_reason="char_budget_adjustment",
                        estimated_chars=estimated,
                        status="applied",
                    )
                )
            current_size = next_size
            batches.append(batch)
        return batches, records


def _read_full_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _estimate_profile_chars(profile: AgentProfile, use_full_text: bool = False) -> int:
    if use_full_text:
        return max(len(_read_full_text(profile.record.source_path)), 1)
    return max(len(profile.prompt_excerpt) or len(profile.record.content_preview), 1)


def _load_codex_config() -> ModelConfig | None:
    config_path = Path.home() / ".codex" / "config.toml"
    auth_path = Path.home() / ".codex" / "auth.json"
    if not config_path.exists() or not auth_path.exists():
        return None
    config_text = config_path.read_text(encoding="utf-8", errors="ignore")
    model = _extract_toml_string(config_text, "model")
    provider = _extract_toml_string(config_text, "model_provider")
    base_url = _extract_provider_value(config_text, provider or "custom", "base_url")
    wire_api = _extract_provider_value(config_text, provider or "custom", "wire_api") or "chat_completions"
    try:
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
        api_key = str(auth.get("OPENAI_API_KEY", "")).strip()
    except json.JSONDecodeError:
        api_key = ""
    if not model or not base_url or not api_key:
        return None
    normalized_base = base_url.rstrip("/")
    if not normalized_base.endswith("/v1"):
        normalized_base = normalized_base + "/v1"
    return ModelConfig(
        provider=provider or "custom",
        provider_label="Codex 默认模型配置",
        base_url=normalized_base,
        api_key=api_key,
        model=model,
        wire_api=wire_api,
        source="codex",
        mode="default",
    )


def _normalize_mode(value: object) -> str:
    text = str(value or "default").strip().lower()
    if text in {"off", "disable", "disabled", "none", "no_model"}:
        return "disabled"
    if text in {"custom", "custom_api", "custom_model"}:
        return "custom"
    return "default"


def _normalize_base_url(value: str) -> str:
    normalized = str(value or "").strip().rstrip("/")
    if not normalized:
        return ""
    for suffix in ("/chat/completions", "/responses"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break
    if not normalized.endswith("/v1"):
        normalized = normalized + "/v1"
    return normalized


def _http_error_message(exc: urllib.error.HTTPError) -> str:
    status = int(getattr(exc, "code", 0) or 0)
    detail = ""
    try:
        body = exc.read().decode("utf-8", errors="ignore")
        if body:
            try:
                payload = json.loads(body)
                if isinstance(payload, dict):
                    error_obj = payload.get("error", payload)
                    if isinstance(error_obj, dict):
                        detail = str(error_obj.get("message", "") or error_obj.get("error", "") or "").strip()
                    else:
                        detail = str(error_obj).strip()
                else:
                    detail = str(payload).strip()
            except json.JSONDecodeError:
                detail = body.strip()
    except OSError:
        detail = ""
    if status in {401, 403}:
        prefix = "模型接口认证失败，请检查 API Key 或访问权限。"
    elif status == 404:
        prefix = "模型接口地址或模型名不存在，请检查 Base URL、接口协议或模型名。"
    elif status == 429:
        prefix = "模型接口触发限流，请稍后重试。"
    elif 500 <= status < 600:
        prefix = f"模型服务端返回 {status}，请稍后重试。"
    else:
        prefix = f"模型接口返回 HTTP {status}。"
    return f"{prefix}{(' 详情：' + detail) if detail else ''}"


def _url_error_message(exc: urllib.error.URLError) -> str:
    reason = getattr(exc, "reason", None)
    if isinstance(reason, socket.timeout):
        return "连接模型接口超时。"
    if isinstance(reason, ConnectionRefusedError):
        return "模型接口拒绝连接，请检查 Base URL 和服务是否可达。"
    text = str(reason or exc).strip()
    if "Name or service not known" in text or "Temporary failure in name resolution" in text:
        return "模型接口域名无法解析，请检查 Base URL。"
    if "CERTIFICATE_VERIFY_FAILED" in text:
        return "模型接口 TLS 证书校验失败。"
    return f"无法连接模型接口：{text or '未知网络错误'}。"


def _extract_toml_string(text: str, key: str) -> str:
    match = re.search(rf'^{re.escape(key)}\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_provider_value(text: str, provider: str, key: str) -> str:
    section = re.search(rf'^\[model_providers\.{re.escape(provider)}\]\s*(.*?)(?=^\[|\Z)', text, re.MULTILINE | re.DOTALL)
    if not section:
        return ""
    match = re.search(rf'^{re.escape(key)}\s*=\s*"([^"]+)"', section.group(1), re.MULTILINE)
    return match.group(1).strip() if match else ""
