from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .corpus import extract_headers_and_commands
from .models import AgentProfile, CorpusRecord, LabelRecord


def build_label_schema() -> dict[str, object]:
    return {
        "industry": [
            "finance",
            "healthcare",
            "education",
            "ecommerce",
            "gaming",
            "devtools",
            "cybersecurity",
            "communications",
            "ai_ml",
            "web3_blockchain",
            "media_content",
            "productivity",
            "iot_robotics",
            "government",
            "research",
        ],
        "task_type": [
            "agent_orchestration",
            "backend_api",
            "frontend_ui",
            "fullstack",
            "data_analysis",
            "documentation",
            "testing",
            "deployment",
            "security",
            "mobile",
            "desktop",
            "ml_ai",
            "cli_tooling",
        ],
        "programming_language": [
            "python",
            "typescript",
            "javascript",
            "rust",
            "go",
            "java",
            "cpp",
            "csharp",
            "php",
            "ruby",
            "swift",
            "kotlin",
            "shell",
            "sql",
            "dart",
        ],
        "runtime": [
            "local_cli",
            "api_service",
            "browser_webapp",
            "docker",
            "kubernetes",
            "ssh_remote",
            "mobile_ios",
            "mobile_android",
            "desktop_app",
            "cloud",
        ],
        "tool_dependency": [
            "git",
            "docker",
            "kubectl",
            "pytest",
            "npm",
            "yarn",
            "pnpm",
            "cargo",
            "go",
            "maven",
            "gradle",
            "cmake",
            "make",
            "uvicorn",
        ],
        "collaboration_mode": [
            "single_agent",
            "multi_agent",
            "user_confirmation",
            "review_driven",
            "autonomous",
        ],
        "risk_constraint": [
            "no_destructive_commands",
            "tests_required",
            "approval_required",
            "credentials_sensitive",
            "production_sensitive",
            "heavy_build_warning",
        ],
        "freeform_policy": {
            "allowed": True,
            "description": "Canonical labels may be supplemented by freeform tags for long-tail traits.",
        },
    }


LANGUAGE_PATTERNS = {
    "python": [r"\bpython\b", r"\bpytest\b", r"\bfastapi\b", r"\bpydantic\b", r"\buvicorn\b", r"\.py\b"],
    "typescript": [r"\btypescript\b", r"\btsx\b", r"\btsconfig\b", r"\bvitest\b"],
    "javascript": [r"\bjavascript\b", r"\bnode\b", r"\bnpm run\b", r"\byarn\b", r"\bpnpm\b", r"\.js\b"],
    "rust": [r"\brust\b", r"\bcargo\b", r"\.rs\b"],
    "go": [r"\bgolang\b", r"\bgo test\b", r"\bgo build\b", r"\bgo mod\b"],
    "java": [r"\bjava\b", r"\bmaven\b", r"\bgradle\b", r"\bspring\b"],
    "cpp": [r"\bc\+\+\b", r"\bcmake\b", r"\bvisual studio\b", r"\bqt\b", r"\.cpp\b"],
    "csharp": [r"\bc#\b", r"\bdotnet\b", r"\.csproj\b"],
    "php": [r"\bphp\b", r"\blaravel\b", r"\bcomposer\b"],
    "ruby": [r"\bruby\b", r"\brails\b", r"\bbundler\b", r"\bgemfile\b"],
    "swift": [r"\bswift\b", r"\bxcode\b", r"\bswiftui\b"],
    "kotlin": [r"\bkotlin\b", r"\bandroid\b", r"\bgradle\b"],
    "shell": [r"\bbash\b", r"\bzsh\b", r"\bshell\b", r"```bash", r"```sh"],
    "sql": [r"\bsql\b", r"\bpostgres\b", r"\bmysql\b", r"\bsqlalchemy\b"],
    "dart": [r"\bdart\b", r"\bflutter\b"],
}

TASK_PATTERNS = {
    "agent_orchestration": [r"\bsubagent\b", r"\bmulti-agent\b", r"\borchestrator\b", r"\bprompt file\b", r"\bagent workflow\b"],
    "backend_api": [r"\bapi\b", r"\bbackend\b", r"\bfastapi\b", r"\bendpoint\b", r"\bserver\b"],
    "frontend_ui": [r"\breact\b", r"\bvue\b", r"\bangular\b", r"\bfrontend\b", r"\bui\b", r"\bwebsocket\b"],
    "fullstack": [r"\bfrontend\b", r"\bbackend\b", r"\bfull-stack\b", r"\bfull stack\b"],
    "data_analysis": [r"\bdata analysis\b", r"\bvisualization\b", r"\bdataset\b", r"\breport\b", r"\banalytics\b"],
    "documentation": [r"\bdocumentation\b", r"\bdocs\b", r"\btechnical writer\b", r"\bmarkdown\b"],
    "testing": [r"\btest\b", r"\bpytest\b", r"\bvitest\b", r"\bcoverage\b", r"\blint\b"],
    "deployment": [r"\bdeploy\b", r"\bdocker\b", r"\bkubernetes\b", r"\bterraform\b", r"\bci/cd\b"],
    "security": [r"\bsecurity\b", r"\bpentest\b", r"\bvulnerability\b", r"\bauth\b"],
    "mobile": [r"\bandroid\b", r"\bios\b", r"\bmobile\b", r"\breact native\b", r"\bflutter\b"],
    "desktop": [r"\bdesktop\b", r"\belectron\b", r"\bqt\b", r"\btelegram desktop\b"],
    "ml_ai": [r"\bllm\b", r"\bmodel\b", r"\btraining\b", r"\binference\b", r"\brag\b", r"\bai\b"],
    "cli_tooling": [r"\bcli\b", r"\bcommand line\b", r"\bterminal\b", r"\bshell\b"],
}

INDUSTRY_PATTERNS = {
    "finance": [r"\bstock\b", r"\btrading\b", r"\bmarket\b", r"\bwallet\b", r"\bpayment\b", r"\bcrypto\b", r"\binvoice\b"],
    "healthcare": [r"\bmedical\b", r"\bhealth\b", r"\bclinic\b", r"\bpatient\b"],
    "education": [r"\beducation\b", r"\blearning\b", r"\bcurriculum\b", r"\bquiz\b"],
    "ecommerce": [r"\becommerce\b", r"\bshopping\b", r"\bstore\b", r"\border\b", r"\bwoocommerce\b"],
    "gaming": [r"\bgame\b", r"\bgaming\b", r"\bplayer\b", r"\bunity\b"],
    "devtools": [r"\bdeveloper\b", r"\bdevops\b", r"\btooling\b", r"\bbuild system\b", r"\brepository\b"],
    "cybersecurity": [r"\bsecurity\b", r"\bpentest\b", r"\bmalware\b", r"\bthreat\b"],
    "communications": [r"\btelegram\b", r"\bchat\b", r"\bmessage\b", r"\bemail\b", r"\bnotification\b"],
    "ai_ml": [r"\bllm\b", r"\bmachine learning\b", r"\btraining\b", r"\binference\b", r"\brag\b", r"\bopenai\b", r"\banthropic\b", r"\bclaude\b", r"\bgpt\b", r"\bgenerative ai\b"],
    "web3_blockchain": [r"\bblockchain\b", r"\bweb3\b", r"\bwallet\b", r"\bdefi\b", r"\baave\b"],
    "media_content": [r"\bcontent\b", r"\bcopywriter\b", r"\bvideo\b", r"\bmedia\b"],
    "productivity": [r"\bproductivity\b", r"\btask\b", r"\bworkflow\b", r"\bdashboard\b"],
    "iot_robotics": [r"\brotics\b", r"\biot\b", r"\bdevice\b", r"\bsensor\b"],
    "government": [r"\bgovernment\b", r"\bpublic\b", r"\bcivic\b"],
    "research": [r"\bresearch\b", r"\bexperiment\b", r"\bpaper\b", r"\bsimulation\b"],
}

RUNTIME_PATTERNS = {
    "local_cli": [r"\bcli\b", r"\bterminal\b", r"\bshell\b", r"\bcommand line\b"],
    "api_service": [r"\bapi\b", r"\bserver\b", r"\buvicorn\b", r"\bfastapi\b", r"\brest\b"],
    "browser_webapp": [r"\breact\b", r"\bvue\b", r"\bfrontend\b", r"\bbrowser\b", r"\bvite\b"],
    "docker": [r"\bdocker\b", r"\bdocker-compose\b"],
    "kubernetes": [r"\bkubernetes\b", r"\bkubectl\b", r"\bhelm\b"],
    "ssh_remote": [r"\bssh\b", r"\bremote server\b", r"\bremote host\b"],
    "mobile_ios": [r"\bios\b", r"\bswift\b", r"\bxcode\b"],
    "mobile_android": [r"\bandroid\b", r"\bkotlin\b", r"\bgradle\b"],
    "desktop_app": [r"\bdesktop\b", r"\belectron\b", r"\bqt\b"],
    "cloud": [r"\baws\b", r"\bgcp\b", r"\bazure\b", r"\bcloud\b"],
}

TOOL_PATTERNS = {
    "git": [r"\bgit\b"],
    "docker": [r"\bdocker\b"],
    "kubectl": [r"\bkubectl\b"],
    "pytest": [r"\bpytest\b"],
    "npm": [r"\bnpm\b"],
    "yarn": [r"\byarn\b"],
    "pnpm": [r"\bpnpm\b"],
    "cargo": [r"\bcargo\b"],
    "go": [r"\bgo test\b", r"\bgo build\b"],
    "maven": [r"\bmaven\b", r"\bmvn\b"],
    "gradle": [r"\bgradle\b"],
    "cmake": [r"\bcmake\b"],
    "make": [r"\bmake\b"],
    "uvicorn": [r"\buvicorn\b"],
}

COLLABORATION_PATTERNS = {
    "multi_agent": [r"\bsubagent\b", r"\bdelegate\b", r"\bmulti-agent\b", r"\borchestrator\b"],
    "user_confirmation": [r"\bwait for user\b", r"\buser confirmation\b", r"\bask the user\b", r"\bapproval\b"],
    "review_driven": [r"\breview\b", r"\bcode review\b", r"\brequested changes\b"],
    "autonomous": [r"\bautonomous\b", r"\bautomatically\b", r"\bself-heal\b"],
}

RISK_PATTERNS = {
    "no_destructive_commands": [r"\bdo not\b.*\bdelete\b", r"\bnever\b.*\breset\b", r"\bdestructive\b"],
    "tests_required": [r"\bmust\b.*\btest\b", r"\bcoverage\b", r"\blint\b"],
    "approval_required": [r"\bapproval\b", r"\bconfirm\b", r"\bwait for user\b"],
    "credentials_sensitive": [r"\bsecret\b", r"\bcredential\b", r"\bapi key\b", r"\btoken\b"],
    "production_sensitive": [r"\bproduction\b", r"\bshared service\b", r"\bdo not restart\b"],
    "heavy_build_warning": [r"\bheavy\b", r"\brelease build\b", r"\blong-running\b"],
}

_LITERAL_CACHE: dict[str, str | None] = {}
_REGEX_CACHE: dict[str, re.Pattern[str]] = {}


def _collect_matches(text: str, pattern_map: dict[str, list[str]]) -> dict[str, str]:
    matches: dict[str, str] = {}
    for canonical, patterns in pattern_map.items():
        for pattern in patterns:
            literal = _pattern_to_literal(pattern)
            if literal is not None:
                if _literal_in_text(text, literal):
                    matches[canonical] = literal
                    break
                continue
            compiled = _REGEX_CACHE.get(pattern)
            if compiled is None:
                compiled = re.compile(pattern, re.IGNORECASE)
                _REGEX_CACHE[pattern] = compiled
            found = compiled.search(text)
            if found:
                matches[canonical] = found.group(0)
                break
    return matches


def _pattern_to_literal(pattern: str) -> str | None:
    cached = _LITERAL_CACHE.get(pattern)
    if pattern in _LITERAL_CACHE:
        return cached
    regex_only_tokens = (".*", "(", ")", "[", "]", "{", "}", "|", "^", "$", "?")
    if any(token in pattern for token in regex_only_tokens):
        _LITERAL_CACHE[pattern] = None
        return None
    literal = pattern
    literal = literal.replace(r"\b", "")
    literal = literal.replace(r"\.", ".")
    literal = literal.replace(r"\+", "+")
    literal = literal.replace(r"\-", "-")
    literal = literal.replace(r"\/", "/")
    literal = literal.replace(r"\#", "#")
    literal = literal.replace("\\", "")
    literal = literal.strip().lower()
    if not literal:
        _LITERAL_CACHE[pattern] = None
        return None
    _LITERAL_CACHE[pattern] = literal
    return literal


def _literal_in_text(text: str, literal: str) -> bool:
    if not literal:
        return False
    if literal.isalnum() and len(literal) <= 4:
        pattern = _REGEX_CACHE.get(f"literal::{literal}")
        if pattern is None:
            pattern = re.compile(rf"\b{re.escape(literal)}\b", re.IGNORECASE)
            _REGEX_CACHE[f"literal::{literal}"] = pattern
        return bool(pattern.search(text))
    return literal in text


def _dedupe_labels(labels: list[LabelRecord]) -> list[LabelRecord]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[LabelRecord] = []
    for label in labels:
        key = (label.label_type, label.canonical_value, label.freeform_value)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(label)
    return deduped


def _language_label_from_record(record: CorpusRecord) -> LabelRecord:
    value = "english" if record.source_lang == "en" else "chinese"
    return LabelRecord(
        label_type="content_language",
        canonical_value=value,
        source_method="rule",
        confidence=1.0,
        evidence=f"source_lang={record.source_lang}",
    )


def _translation_label(record: CorpusRecord) -> LabelRecord | None:
    if record.pair_status == "paired":
        value = "paired_translation_candidate"
    elif record.pair_status in {"english_only", "chinese_only"}:
        value = "unpaired_corpus_entry"
    else:
        return None
    return LabelRecord(
        label_type="pairing",
        canonical_value=value,
        source_method="rule",
        confidence=0.9,
        evidence=f"pair_status={record.pair_status}",
    )


class RuleLabeler:
    def __init__(self) -> None:
        self.schema = build_label_schema()

    def label_record(self, record: CorpusRecord) -> AgentProfile:
        headers, commands, text = extract_headers_and_commands(record.source_path)
        lower_text = f"{record.filename}\n{record.title}\n{text}".lower()
        labels: list[LabelRecord] = [_language_label_from_record(record)]
        translation = _translation_label(record)
        if translation:
            labels.append(translation)
        for label_type, pattern_map in (
            ("programming_language", LANGUAGE_PATTERNS),
            ("task_type", TASK_PATTERNS),
            ("industry", INDUSTRY_PATTERNS),
            ("runtime", RUNTIME_PATTERNS),
            ("tool_dependency", TOOL_PATTERNS),
            ("collaboration_mode", COLLABORATION_PATTERNS),
            ("risk_constraint", RISK_PATTERNS),
        ):
            for canonical, evidence in _collect_matches(lower_text, pattern_map).items():
                labels.append(
                    LabelRecord(
                        label_type=label_type,
                        canonical_value=canonical,
                        source_method="rule",
                        confidence=0.72,
                        evidence=evidence,
                    )
                )
        if not any(label.label_type == "collaboration_mode" for label in labels):
            labels.append(
                LabelRecord(
                    label_type="collaboration_mode",
                    canonical_value="single_agent",
                    source_method="rule",
                    confidence=0.6,
                    evidence="fallback_default",
                )
            )
        labels.extend(self._extra_labels(record, lower_text, headers))
        prompt_excerpt = text[:1600]
        return AgentProfile(
            record=record,
            labels=_dedupe_labels(labels),
            section_headers=headers,
            command_examples=commands,
            prompt_excerpt=prompt_excerpt,
            parse_notes=self._build_notes(record, headers),
        )

    def label_request_text(self, text: str, language_hint: str = "en") -> list[LabelRecord]:
        labels: list[LabelRecord] = [
            LabelRecord(
                label_type="content_language",
                canonical_value="chinese" if language_hint.startswith("zh") else "english",
                source_method="input",
                confidence=1.0,
                evidence=f"language_hint={language_hint}",
            )
        ]
        lower_text = text.lower()
        for label_type, pattern_map in (
            ("programming_language", LANGUAGE_PATTERNS),
            ("task_type", TASK_PATTERNS),
            ("industry", INDUSTRY_PATTERNS),
            ("runtime", RUNTIME_PATTERNS),
            ("tool_dependency", TOOL_PATTERNS),
            ("collaboration_mode", COLLABORATION_PATTERNS),
            ("risk_constraint", RISK_PATTERNS),
        ):
            for canonical, evidence in _collect_matches(lower_text, pattern_map).items():
                labels.append(
                    LabelRecord(
                        label_type=label_type,
                        canonical_value=canonical,
                        source_method="input",
                        confidence=0.7,
                        evidence=evidence,
                    )
                )
        if not any(label.label_type == "collaboration_mode" for label in labels):
            labels.append(
                LabelRecord(
                    label_type="collaboration_mode",
                    canonical_value="single_agent",
                    source_method="input",
                    confidence=0.6,
                    evidence="fallback_default",
                )
            )
        return _dedupe_labels(labels)

    def _extra_labels(self, record: CorpusRecord, lower_text: str, headers: list[str]) -> list[LabelRecord]:
        extras: list[LabelRecord] = []
        if record.evaluation_avg_score is not None:
            band = "high_quality" if record.evaluation_avg_score >= 70 else "medium_quality" if record.evaluation_avg_score >= 55 else "low_quality"
            extras.append(
                LabelRecord(
                    label_type="quality_band",
                    canonical_value=band,
                    source_method="rule",
                    confidence=0.95,
                    evidence=f"avg_score={record.evaluation_avg_score}",
                )
            )
        if "codex" in lower_text or "claude" in lower_text or "opencode" in lower_text:
            for tool in ("codex", "claude", "opencode", "openai"):
                if tool in lower_text:
                    extras.append(
                        LabelRecord(
                            label_type="freeform_tag",
                            canonical_value="agent_runtime",
                            freeform_value=tool,
                            source_method="rule",
                            confidence=0.6,
                            evidence=tool,
                        )
                    )
        for header in headers[:6]:
            normalized = re.sub(r"[^a-z0-9]+", "_", header.lower()).strip("_")
            if normalized:
                extras.append(
                    LabelRecord(
                        label_type="freeform_tag",
                        canonical_value="section_header",
                        freeform_value=normalized[:48],
                        source_method="rule",
                        confidence=0.55,
                        evidence=header,
                    )
                )
        return extras

    @staticmethod
    def _build_notes(record: CorpusRecord, headers: list[str]) -> list[str]:
        notes = [f"pair_status={record.pair_status}", f"variant_flags={','.join(record.variant_flags) or 'none'}"]
        if headers:
            notes.append(f"top_header={headers[0]}")
        return notes


def profile_label_map(profile: AgentProfile) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = defaultdict(set)
    for label in profile.labels:
        mapping[label.label_type].add(label.canonical_value)
        if label.freeform_value:
            mapping[f"{label.label_type}:freeform"].add(label.freeform_value)
    return mapping
