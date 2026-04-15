from __future__ import annotations

import hashlib
from collections import Counter, defaultdict

from .labels import profile_label_map
from .models import AgentProfile, CapabilityCard, CapabilityCatalog
from .time_utils import timestamp_now

SIGNATURE_LIMITS = {
    "industry": 1,
    "task_type": 1,
    "runtime": 1,
    "programming_language": 1,
}

SUMMARY_LABEL_TYPES = (
    "industry",
    "task_type",
    "programming_language",
    "runtime",
    "tool_dependency",
    "collaboration_mode",
    "risk_constraint",
)


def build_capability_catalog(profiles: list[AgentProfile], source_run_id: str = "") -> CapabilityCatalog:
    buckets: dict[str, dict[str, object]] = {}
    taxonomy_totals: dict[str, Counter[str]] = defaultdict(Counter)
    for profile in profiles:
        label_map = profile_label_map(profile)
        signature_labels: dict[str, list[str]] = {}
        for label_type, limit in SIGNATURE_LIMITS.items():
            values = sorted(label_map.get(label_type, set()))[:limit]
            if values:
                signature_labels[label_type] = values
        signature = _capability_signature(signature_labels)
        bucket = buckets.setdefault(
            signature,
            {
                "signature_labels": signature_labels,
                "profile_count": 0,
                "score_total": 0.0,
                "score_count": 0,
                "source_languages": Counter(),
                "pair_statuses": Counter(),
                "label_counts": defaultdict(Counter),
                "exemplars": [],
            },
        )
        bucket["profile_count"] = int(bucket["profile_count"]) + 1
        bucket["source_languages"][profile.record.source_lang] += 1
        bucket["pair_statuses"][profile.record.pair_status] += 1
        if profile.record.evaluation_avg_score is not None:
            bucket["score_total"] = float(bucket["score_total"]) + float(profile.record.evaluation_avg_score)
            bucket["score_count"] = int(bucket["score_count"]) + 1
        label_counts = bucket["label_counts"]
        for label_type in SUMMARY_LABEL_TYPES:
            for value in label_map.get(label_type, set()):
                label_counts[label_type][value] += 1
                taxonomy_totals[label_type][value] += 1
        exemplars = bucket["exemplars"]
        exemplars.append(
            (
                float(profile.record.evaluation_avg_score or 0.0),
                profile.record.filename,
                profile.record.source_path,
            )
        )

    cards: list[CapabilityCard] = []
    for signature, bucket in buckets.items():
        label_counts = {
            label_type: dict(counter.most_common(10))
            for label_type, counter in dict(bucket["label_counts"]).items()
            if counter
        }
        top_labels = {label_type: list(counts.keys())[:5] for label_type, counts in label_counts.items()}
        exemplars = sorted(bucket["exemplars"], key=lambda item: (item[0], item[1]), reverse=True)[:6]
        card = CapabilityCard(
            capability_id=_capability_id(signature),
            title=_build_card_title(top_labels),
            summary=_build_card_summary(top_labels, int(bucket["profile_count"]), dict(bucket["source_languages"])),
            profile_count=int(bucket["profile_count"]),
            average_quality_score=round(
                float(bucket["score_total"]) / int(bucket["score_count"]),
                1,
            )
            if int(bucket["score_count"])
            else 0.0,
            source_languages={str(key): int(value) for key, value in dict(bucket["source_languages"]).items()},
            pair_statuses={str(key): int(value) for key, value in dict(bucket["pair_statuses"]).items()},
            top_labels=top_labels,
            label_counts=label_counts,
            exemplar_filenames=[item[1] for item in exemplars],
            exemplar_paths=[item[2] for item in exemplars],
        )
        cards.append(card)

    cards.sort(key=lambda card: (card.profile_count, card.average_quality_score, card.title), reverse=True)
    snapshot = {
        label_type: [{"value": value, "count": count} for value, count in counter.most_common(8)]
        for label_type, counter in taxonomy_totals.items()
        if counter
    }
    return CapabilityCatalog(
        created_at=timestamp_now(),
        source_run_id=source_run_id,
        profile_count=len(profiles),
        card_count=len(cards),
        taxonomy_snapshot=snapshot,
        cards=cards,
    )


def _capability_signature(signature_labels: dict[str, list[str]]) -> str:
    if not signature_labels:
        return "general"
    parts = []
    for label_type in SIGNATURE_LIMITS:
        values = signature_labels.get(label_type)
        if values:
            parts.append(f"{label_type}={','.join(values)}")
    return "|".join(parts) or "general"


def _capability_id(signature: str) -> str:
    return hashlib.sha1(signature.encode("utf-8")).hexdigest()[:12]


def _build_card_title(top_labels: dict[str, list[str]]) -> str:
    industries = top_labels.get("industry", [])[:2]
    task_types = top_labels.get("task_type", [])[:2]
    runtimes = top_labels.get("runtime", [])[:1]
    stacks = top_labels.get("programming_language", [])[:1]
    parts = []
    if industries:
        parts.append(" / ".join(_humanize(value) for value in industries))
    if task_types:
        parts.append(" + ".join(_humanize(value) for value in task_types))
    if runtimes:
        parts.append(_humanize(runtimes[0]))
    if stacks:
        parts.append(_humanize(stacks[0]))
    return " · ".join(parts) if parts else "General Capability Pattern"


def _build_card_summary(top_labels: dict[str, list[str]], profile_count: int, source_languages: dict[str, int]) -> str:
    stacks = ", ".join(_humanize(value) for value in top_labels.get("programming_language", [])[:3]) or "mixed stacks"
    tools = ", ".join(_humanize(value) for value in top_labels.get("tool_dependency", [])[:3]) or "common tooling"
    runtimes = ", ".join(_humanize(value) for value in top_labels.get("runtime", [])[:2]) or "mixed runtimes"
    languages = ", ".join(f"{lang}:{count}" for lang, count in sorted(source_languages.items())) or "unknown"
    return (
        f"{profile_count} profiles. Dominant stack: {stacks}. "
        f"Typical runtimes: {runtimes}. "
        f"Frequent tools: {tools}. "
        f"Corpus languages: {languages}."
    )


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip().title()
