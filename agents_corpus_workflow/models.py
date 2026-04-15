from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any


def json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {key: json_ready(item) for key, item in asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_ready(item) for item in value]
    return value


@dataclass(slots=True)
class CorpusRecord:
    sample_id: str
    filename: str
    source_path: str
    source_lang: str
    file_kind: str
    file_size: int
    sha1: str
    char_count: int
    line_count: int
    pair_key: str
    pair_status: str
    missing_language: str
    variant_flags: list[str] = field(default_factory=list)
    repo_owner: str = ""
    repo_name: str = ""
    title: str = ""
    evaluation_repo: str = ""
    evaluation_file: str = ""
    evaluation_avg_score: float | None = None
    content_preview: str = ""


@dataclass(slots=True)
class LabelRecord:
    label_type: str
    canonical_value: str
    freeform_value: str = ""
    source_method: str = "rule"
    confidence: float = 0.0
    evidence: str = ""


@dataclass(slots=True)
class AgentProfile:
    record: CorpusRecord
    labels: list[LabelRecord] = field(default_factory=list)
    section_headers: list[str] = field(default_factory=list)
    command_examples: list[str] = field(default_factory=list)
    prompt_excerpt: str = ""
    parse_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BatchRequestRecord:
    batch_id: str
    sample_id: str
    source_path: str
    prompt_fragment: str
    batch_size: int


@dataclass(slots=True)
class BatchResponseRecord:
    batch_id: str
    sample_id: str
    raw_response: str
    parsed_labels: list[LabelRecord] = field(default_factory=list)
    parse_status: str = "ok"


@dataclass(slots=True)
class BatchTuningRecord:
    timestamp: str
    old_batch_size: int
    new_batch_size: int
    trigger_reason: str
    estimated_chars: int
    status: str


@dataclass(slots=True)
class RunLogRecord:
    timestamp: str
    stage: str
    action: str
    input_basis: str
    output_path: str
    status: str
    duration_ms: int
    notes: str = ""


@dataclass(slots=True)
class DecisionLogRecord:
    timestamp: str
    decision: str
    reason: str
    impact: str
    rollback: str


@dataclass(slots=True)
class GenerationRequest:
    template_type: str
    industry: str
    task_description: str
    target_user: str = "general"
    output_language: str = "zh"
    environment: str = ""
    constraints: list[str] = field(default_factory=list)
    preferred_stack: list[str] = field(default_factory=list)
    risk_tolerance: str = "medium"
    session_id: str = ""
    current_state: str = ""
    goal_definition: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    paths: dict[str, str] = field(default_factory=dict)
    environment_detail: str = ""
    permissions: dict[str, object] = field(default_factory=dict)
    resource_constraints: dict[str, object] = field(default_factory=dict)
    question_answers: dict[str, object] = field(default_factory=dict)
    plan_markdown: str = ""


@dataclass(slots=True)
class QuestionOption:
    value: str
    label: str
    description: str = ""


@dataclass(slots=True)
class QuestionItem:
    question_id: str
    title: str
    prompt: str
    kind: str = "free_text"
    required: bool = False
    source_rule: str = ""
    options: list[QuestionOption] = field(default_factory=list)
    depends_on: dict[str, list[str]] = field(default_factory=dict)
    placeholder: str = ""
    help_text: str = ""
    suggestions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class IntakeSession:
    session_id: str
    created_at: str
    updated_at: str
    phase: str = "collecting"
    base_request: dict[str, object] = field(default_factory=dict)
    questions: list[QuestionItem] = field(default_factory=list)
    answers: dict[str, object] = field(default_factory=dict)
    question_generation_mode: str = "rule"
    question_generation_note: str = ""
    active_question_ids: list[str] = field(default_factory=list)
    missing_required_ids: list[str] = field(default_factory=list)
    validation_errors: dict[str, str] = field(default_factory=dict)
    completion_percent: int = 0
    ready_for_plan: bool = False
    next_action: str = ""
    plan_markdown: str = ""
    plan_summary: list[str] = field(default_factory=list)
    plan_output_path: str = ""


@dataclass(slots=True)
class ReferenceFile:
    path: str
    title: str = ""
    reason: str = ""
    source_type: str = "capability_exemplar"


@dataclass(slots=True)
class CapabilityMatch:
    capability_id: str
    title: str
    summary: str
    score: float = 0.0
    profile_count: int = 0
    matched_dimensions: list[str] = field(default_factory=list)
    exemplar_paths: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GenerationResponse:
    agents_markdown: str
    references: list[str]
    matched_labels: dict[str, list[str]]
    open_questions: list[str]
    reference_files: list[ReferenceFile] = field(default_factory=list)
    capability_matches: list[CapabilityMatch] = field(default_factory=list)
    draft_markdown: str = ""
    final_markdown: str = ""
    display_markdown: str = ""
    finalization_status: str = "draft_only"
    finalization_error: str = ""
    used_model_optimization: bool = False
    model_runtime: dict[str, object] = field(default_factory=dict)
    output_path: str = ""
    display_output_path: str = ""
    draft_output_path: str = ""
    final_output_path: str = ""
    artifact_id: str = ""
    created_at: str = ""
    title: str = ""
    summary: str = ""
    template_type: str = ""
    task_excerpt: str = ""
    plan_markdown: str = ""
    plan_output_path: str = ""
    intake_session_id: str = ""


@dataclass(slots=True)
class CapabilityCard:
    capability_id: str
    title: str
    summary: str
    profile_count: int
    average_quality_score: float = 0.0
    source_languages: dict[str, int] = field(default_factory=dict)
    pair_statuses: dict[str, int] = field(default_factory=dict)
    top_labels: dict[str, list[str]] = field(default_factory=dict)
    label_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    exemplar_filenames: list[str] = field(default_factory=list)
    exemplar_paths: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CapabilityCatalog:
    created_at: str
    source_run_id: str
    profile_count: int
    card_count: int
    taxonomy_snapshot: dict[str, list[dict[str, int | str]]] = field(default_factory=dict)
    cards: list[CapabilityCard] = field(default_factory=list)


def corpus_record_from_dict(data: dict[str, Any]) -> CorpusRecord:
    return CorpusRecord(**data)


def label_record_from_dict(data: dict[str, Any]) -> LabelRecord:
    return LabelRecord(**data)


def agent_profile_from_dict(data: dict[str, Any]) -> AgentProfile:
    return AgentProfile(
        record=corpus_record_from_dict(data["record"]),
        labels=[label_record_from_dict(item) for item in data.get("labels", [])],
        section_headers=list(data.get("section_headers", [])),
        command_examples=list(data.get("command_examples", [])),
        prompt_excerpt=str(data.get("prompt_excerpt", "")),
        parse_notes=list(data.get("parse_notes", [])),
    )


def capability_card_from_dict(data: dict[str, Any]) -> CapabilityCard:
    return CapabilityCard(
        capability_id=str(data.get("capability_id", "")),
        title=str(data.get("title", "")),
        summary=str(data.get("summary", "")),
        profile_count=int(data.get("profile_count", 0)),
        average_quality_score=float(data.get("average_quality_score", 0.0) or 0.0),
        source_languages={str(key): int(value) for key, value in dict(data.get("source_languages", {})).items()},
        pair_statuses={str(key): int(value) for key, value in dict(data.get("pair_statuses", {})).items()},
        top_labels={str(key): [str(item) for item in value] for key, value in dict(data.get("top_labels", {})).items()},
        label_counts={
            str(key): {str(inner_key): int(inner_value) for inner_key, inner_value in dict(value).items()}
            for key, value in dict(data.get("label_counts", {})).items()
        },
        exemplar_filenames=[str(item) for item in data.get("exemplar_filenames", [])],
        exemplar_paths=[str(item) for item in data.get("exemplar_paths", [])],
    )


def capability_catalog_from_dict(data: dict[str, Any]) -> CapabilityCatalog:
    return CapabilityCatalog(
        created_at=str(data.get("created_at", "")),
        source_run_id=str(data.get("source_run_id", "")),
        profile_count=int(data.get("profile_count", 0)),
        card_count=int(data.get("card_count", 0)),
        taxonomy_snapshot={
            str(key): [{"value": str(item.get("value", "")), "count": int(item.get("count", 0))} for item in value]
            for key, value in dict(data.get("taxonomy_snapshot", {})).items()
        },
        cards=[capability_card_from_dict(item) for item in data.get("cards", [])],
    )
