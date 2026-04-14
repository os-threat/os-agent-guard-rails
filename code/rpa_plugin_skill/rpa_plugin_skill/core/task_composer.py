from __future__ import annotations

import re
from dataclasses import dataclass

from .config import AppConfig
from .database_lifecycle import layer_a_db_name
from .typedb_bootstrap import connect_with_retry

PROCESS_KEYWORDS = (
    "extract",
    "load",
    "validate",
    "transform",
    "sync",
    "approve",
    "deny",
    "review",
    "notify",
    "schedule",
)


@dataclass(frozen=True)
class HighlightTerm:
    label: str
    kind: str


@dataclass(frozen=True)
class FlowStep:
    step_id: str
    title: str
    detail: str


@dataclass(frozen=True)
class TaskComposerPreview:
    registration_id: str
    description: str
    layer_a_db: str
    highlighted_objects: list[HighlightTerm]
    highlighted_process_terms: list[str]
    flow_steps: list[FlowStep]
    diagram_mermaid: str


def compose_task_preview(
    config: AppConfig,
    registration_id: str,
    description: str,
    schema_text: str | None = None,
) -> TaskComposerPreview:
    schema = (
        schema_text
        if schema_text is not None
        else _load_layer_a_schema(config, registration_id)
    )
    labels = _extract_schema_labels(schema)
    object_highlights = _find_object_highlights(description, labels)
    process_highlights = _find_process_highlights(description)
    steps = _build_flow_steps(object_highlights, process_highlights)
    diagram = _build_diagram(description, object_highlights, process_highlights)
    return TaskComposerPreview(
        registration_id=registration_id,
        description=description,
        layer_a_db=layer_a_db_name(config, registration_id),
        highlighted_objects=object_highlights,
        highlighted_process_terms=process_highlights,
        flow_steps=steps,
        diagram_mermaid=diagram,
    )


def _load_layer_a_schema(config: AppConfig, registration_id: str) -> str:
    db_name = layer_a_db_name(config, registration_id)
    driver = connect_with_retry(config)
    try:
        if not driver.databases.contains(db_name):
            return ""
        return driver.databases.get(db_name).schema()
    finally:
        driver.close()


def _extract_schema_labels(schema_text: str) -> list[HighlightTerm]:
    labels: list[HighlightTerm] = []
    for kind, label in re.findall(
        r"\b(entity|relation|attribute)\s+(\w+)",
        schema_text,
    ):
        if label.startswith("gr_") or label.startswith("grb_"):
            continue
        labels.append(HighlightTerm(label=label, kind=kind))
    dedup: dict[tuple[str, str], HighlightTerm] = {}
    for item in labels:
        dedup[(item.kind, item.label)] = item
    return sorted(dedup.values(), key=lambda item: (item.kind, item.label))


def _find_object_highlights(
    description: str,
    labels: list[HighlightTerm],
) -> list[HighlightTerm]:
    tokens = set(re.findall(r"\w+", description.lower()))
    hits = [
        label
        for label in labels
        if any(alias in tokens for alias in _label_aliases(label.label))
    ]
    return sorted(hits, key=lambda item: (item.kind, item.label))


def _find_process_highlights(description: str) -> list[str]:
    lower = description.lower()
    return [term for term in PROCESS_KEYWORDS if term in lower]


def _label_aliases(label: str) -> set[str]:
    raw = label.lower()
    aliases = {raw}
    if raw.startswith("gra_") or raw.startswith("grb_") or raw.startswith("gr_"):
        aliases.add(raw.split("_", 1)[1])
    parts = raw.split("_")
    aliases.add(parts[-1])
    aliases.add(parts[-1].rstrip("s"))
    if not parts[-1].endswith("s"):
        aliases.add(f"{parts[-1]}s")
    return {alias for alias in aliases if alias}


def _build_flow_steps(
    object_highlights: list[HighlightTerm],
    process_highlights: list[str],
) -> list[FlowStep]:
    object_summary = ", ".join(item.label for item in object_highlights[:5]) or "schema context"
    process_summary = ", ".join(process_highlights[:5]) or "task operations"
    return [
        FlowStep("describe", "Describe task intent", process_summary),
        FlowStep("map", "Map to schema objects", object_summary),
        FlowStep("extract", "Build extract plan", "Generate SQL/API extraction scope"),
        FlowStep("execute", "Run guarded task", "Execute with Promise/Guard checks"),
        FlowStep("assess", "Record outcomes", "Persist assessments for review/appeal"),
    ]


def _build_diagram(
    description: str,
    object_highlights: list[HighlightTerm],
    process_highlights: list[str],
) -> str:
    safe_description = description.replace('"', "'")
    object_text = ", ".join(item.label for item in object_highlights[:4]) or "no-schema-match"
    process_text = ", ".join(process_highlights[:4]) or "manual-review"
    return (
        "flowchart LR\n"
        f"  D[\"Task Description: {safe_description}\"] --> O[\"Schema Objects: {object_text}\"]\n"
        f"  O --> P[\"Process Logic: {process_text}\"]\n"
        "  P --> X[\"Extract + Sync Layer A\"]\n"
        "  X --> G[\"Guard + Promise Assessment\"]\n"
    )
