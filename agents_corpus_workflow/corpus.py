from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path

from .models import CorpusRecord

EVAL_BLOCK_RE = re.compile(r"<!-- AGENTS\.md EVALUATION METADATA(?P<body>.*?)-->", re.DOTALL)
HEADER_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
COMMAND_BLOCK_RE = re.compile(r"```(?:bash|sh|shell|zsh)?\n(.*?)```", re.DOTALL | re.IGNORECASE)
ANALYSIS_WINDOW_CHARS = 20000


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _sha1_for_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def _sample_id(path: Path, source_lang: str) -> str:
    digest = hashlib.sha1(f"{source_lang}:{path.name}:{path.as_posix()}".encode("utf-8")).hexdigest()
    return digest[:16]


def _detect_variant_flags(filename: str) -> list[str]:
    flags: list[str] = []
    if re.search(r"__\d+\.md$", filename):
        flags.append("numeric_suffix_variant")
    if filename.count(".md") > 1 or filename.count(".MD") > 1:
        flags.append("double_md_extension")
    if filename.endswith(".MD.md") or filename.endswith(".MD.MD"):
        flags.append("mixed_case_extension")
    if not filename.lower().endswith((".md", ".json")):
        flags.append("non_markdown")
    if "__" not in filename:
        flags.append("nonstandard_pair_key")
    return flags


def _extract_eval_value(block: str, field: str) -> str:
    match = re.search(rf"^{field}:\s*(.+)$", block, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_title(text: str) -> str:
    match = HEADER_RE.search(text)
    return match.group(1).strip() if match else ""


def _extract_preview(text: str, limit: int = 800) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized[:limit]


class CorpusScanner:
    def __init__(self, source_root: str | Path) -> None:
        self.source_root = Path(source_root)
        self.contents_dirs = [
            ("en", self.source_root / "agents_process" / "contents"),
            ("zh", self.source_root / "agents_process" / "contents_zh"),
        ]

    def scan(self, max_files: int | None = None) -> list[CorpusRecord]:
        started = time.perf_counter()
        records: list[CorpusRecord] = []
        pair_map: dict[str, set[str]] = {}
        visited = 0
        for source_lang, base_dir in self.contents_dirs:
            if not base_dir.exists():
                continue
            for path in sorted(base_dir.iterdir()):
                if max_files is not None and visited >= max_files:
                    break
                if not path.is_file():
                    continue
                visited += 1
                text = _read_text(path)
                eval_match = EVAL_BLOCK_RE.search(text)
                eval_block = eval_match.group("body") if eval_match else ""
                filename = path.name
                pair_key = filename
                pair_map.setdefault(pair_key, set()).add(source_lang)
                repo_owner, repo_name = "", ""
                if "__" in filename:
                    owner_name = filename.split("__", 1)
                    repo_owner = owner_name[0]
                    repo_name = owner_name[1].rsplit(".", 1)[0]
                record = CorpusRecord(
                    sample_id=_sample_id(path, source_lang),
                    filename=filename,
                    source_path=str(path.resolve()),
                    source_lang=source_lang,
                    file_kind=path.suffix.lower().lstrip(".") or "unknown",
                    file_size=path.stat().st_size,
                    sha1=_sha1_for_text(text),
                    char_count=len(text),
                    line_count=text.count("\n") + (1 if text else 0),
                    pair_key=pair_key,
                    pair_status="unknown",
                    missing_language="",
                    variant_flags=_detect_variant_flags(filename),
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                    title=_extract_title(text),
                    evaluation_repo=_extract_eval_value(eval_block, "REPO"),
                    evaluation_file=_extract_eval_value(eval_block, "FILE"),
                    evaluation_avg_score=_safe_float(_extract_eval_value(eval_block, "AVG_SCORE")),
                    content_preview=_extract_preview(text),
                )
                records.append(record)
        statuses = self._pair_statuses(pair_map)
        for record in records:
            pair_status, missing_language = statuses.get(record.pair_key, ("unmatched", ""))
            record.pair_status = pair_status
            record.missing_language = missing_language
        _ = started
        return records

    @staticmethod
    def _pair_statuses(pair_map: dict[str, set[str]]) -> dict[str, tuple[str, str]]:
        statuses: dict[str, tuple[str, str]] = {}
        for pair_key, langs in pair_map.items():
            if {"en", "zh"}.issubset(langs):
                statuses[pair_key] = ("paired", "")
            elif langs == {"en"}:
                statuses[pair_key] = ("english_only", "zh")
            elif langs == {"zh"}:
                statuses[pair_key] = ("chinese_only", "en")
            else:
                statuses[pair_key] = ("unmatched", "")
        return statuses


def _safe_float(value: str) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def extract_headers_and_commands(path: str | Path) -> tuple[list[str], list[str], str]:
    text = _read_text(Path(path))
    window_text = text[:ANALYSIS_WINDOW_CHARS]
    headers = [item.strip() for item in HEADER_RE.findall(window_text)]
    commands: list[str] = []
    for match in COMMAND_BLOCK_RE.findall(window_text):
        snippet = "\n".join(line.rstrip() for line in match.strip().splitlines()[:6]).strip()
        if snippet:
            commands.append(snippet)
    return headers[:20], commands[:10], window_text
