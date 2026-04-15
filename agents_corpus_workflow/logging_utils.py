from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import DecisionLogRecord, RunLogRecord, json_ready
from .time_utils import iso_now, timestamp_now


class ArtifactLogger:
    def __init__(self, output_dir: str | Path, run_id: str | None = None) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or timestamp_now()
        self.run_log_path = self.output_dir / f"run_log_{self.run_id}.jsonl"
        self.decision_log_path = self.output_dir / f"decision_log_{self.run_id}.md"
        self.batch_log_path = self.output_dir / f"batch_runs_{self.run_id}.jsonl"
        self.evaluation_path = self.output_dir / f"evaluation_{self.run_id}.md"

    def timestamped_path(self, prefix: str, suffix: str) -> Path:
        return self.output_dir / f"{prefix}_{self.run_id}.{suffix}"

    def write_jsonl(self, path: str | Path, rows: list[Any]) -> Path:
        output = Path(path)
        with output.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(json_ready(row), ensure_ascii=False) + "\n")
        return output

    def append_jsonl(self, path: str | Path, row: Any) -> Path:
        output = Path(path)
        with output.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(json_ready(row), ensure_ascii=False) + "\n")
        return output

    def write_text(self, path: str | Path, text: str) -> Path:
        output = Path(path)
        output.write_text(text, encoding="utf-8")
        return output

    def write_json(self, path: str | Path, payload: Any) -> Path:
        output = Path(path)
        output.write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return output

    def append_markdown(self, path: str | Path, heading: str, body: str) -> Path:
        output = Path(path)
        stamp = iso_now()
        with output.open("a", encoding="utf-8") as handle:
            handle.write(f"## {heading}\n\n")
            handle.write(f"- timestamp: {stamp}\n")
            handle.write(body.rstrip() + "\n\n")
        return output

    def record_run(
        self,
        stage: str,
        action: str,
        input_basis: str,
        output_path: str,
        status: str,
        duration_ms: int,
        notes: str = "",
    ) -> Path:
        record = RunLogRecord(
            timestamp=iso_now(),
            stage=stage,
            action=action,
            input_basis=input_basis,
            output_path=output_path,
            status=status,
            duration_ms=duration_ms,
            notes=notes,
        )
        return self.append_jsonl(self.run_log_path, record)

    def record_decision(self, decision: str, reason: str, impact: str, rollback: str) -> Path:
        record = DecisionLogRecord(
            timestamp=iso_now(),
            decision=decision,
            reason=reason,
            impact=impact,
            rollback=rollback,
        )
        body = "\n".join(
            [
                f"- decision: {record.decision}",
                f"- reason: {record.reason}",
                f"- impact: {record.impact}",
                f"- rollback: {record.rollback}",
            ]
        )
        return self.append_markdown(self.decision_log_path, "Decision", body)
