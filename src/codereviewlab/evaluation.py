"""Frozen exact matching with optional auditable human adjudication."""

import json
from pathlib import Path

from .dataset import load_dataset, sha256
from .reports import ensure_new, json_text, write_artifacts
from .schemas import EvaluationMetrics, StrictModel


class Decision(StrictModel):
    example_id: str
    prediction_index: int
    expected_index: int | None
    rationale: str
    reviewer: str


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def match_findings(expected, predictions, decisions=()):
    # Category + accepted line; predictions deduplicated before matching.
    unique = list({(f.path, f.category, f.line): f for f in predictions}.values())
    overrides = {d.prediction_index: d.expected_index for d in decisions}
    if len(overrides) != len(decisions):
        raise ValueError("Duplicate adjudication for one prediction")
    claimed, matched, category_matched = set(), 0, 0
    remaining_categories = [f.category for f in expected]
    for i, prediction in enumerate(unique):
        if prediction.category in remaining_categories:
            category_matched += 1
            remaining_categories.remove(prediction.category)
        if i in overrides:
            j = overrides[i]
            if j is not None and (j < 0 or j >= len(expected) or j in claimed):
                raise ValueError("Invalid or reused adjudication target")
        else:
            j = next(
                (
                    j
                    for j, label in enumerate(expected)
                    if j not in claimed
                    and prediction.category == label.category
                    and prediction.line in label.accepted_lines
                ),
                None,
            )
        if j is not None:
            claimed.add(j)
            matched += 1
    if any(i < 0 or i >= len(unique) for i in overrides):
        raise ValueError("Adjudication prediction index is out of range")
    return {
        "true_positives": matched,
        "false_positives": len(unique) - matched,
        "category_matches": category_matched,
        "deduplicated_predictions": [f.model_dump(mode="json") for f in unique],
    }


def evaluate(dataset, reviewer, config, output, adjudications=None):
    output = Path(output)
    ensure_new([output / "metrics.json", output / "examples.json", output / "report.md"])
    examples = load_dataset(dataset)
    decisions = (
        []
        if not adjudications
        else [
            Decision.model_validate(d)
            for d in json.loads(Path(adjudications).read_text(encoding="utf-8"))
        ]
    )
    if any(
        d.example_id not in {e.id for e in examples} or not d.rationale or not d.reviewer
        for d in decisions
    ):
        raise ValueError("Adjudication requires an existing example, reviewer, and rationale")
    rows, processed, tp, fp, category_matches, clean_fp, clean_processed = [], 0, 0, 0, 0, 0, 0
    latencies, gpu = [], []
    for example in examples:
        result = reviewer.review(example.function)
        matching = match_findings(
            example.expected_findings,
            result.findings,
            [d for d in decisions if d.example_id == example.id],
        )
        if result.status == "ok":
            processed += 1
            tp += matching["true_positives"]
            fp += matching["false_positives"]
            category_matches += matching["category_matches"]
            if not example.buggy:
                clean_processed += 1
                clean_fp += bool(result.findings)
        latencies.append(result.metadata.latency_seconds)
        if result.metadata.peak_gpu_memory_bytes is not None:
            gpu.append(result.metadata.peak_gpu_memory_bytes)
        rows.append(
            {
                "id": example.id,
                "buggy": example.buggy,
                "expected_findings": [f.model_dump(mode="json") for f in example.expected_findings],
                "result": result.model_dump(mode="json"),
                "matching": matching,
            }
        )
    expected = sum(len(e.expected_findings) for e in examples)
    metrics = EvaluationMetrics(
        examples=len(examples),
        processed=processed,
        failures=len(examples) - processed,
        coverage=ratio(processed, len(examples)),
        true_positives=tp,
        false_positives=fp,
        expected_bugs=expected,
        finding_precision=ratio(tp, tp + fp),
        bug_recall=ratio(tp, expected),
        correct_function_false_positive_rate=ratio(clean_fp, clean_processed),
        localization_accuracy=ratio(tp, category_matches),
        valid_output_rate=ratio(processed, len(examples)),
        mean_latency_seconds=ratio(sum(latencies), len(latencies)),
        peak_gpu_memory_bytes=max(gpu) if gpu else None,
    )
    report = {
        "metrics": metrics.model_dump(),
        "dataset_sha256": sha256(dataset),
        "config": config.model_dump(),
        "matching_version": "category-line-v1",
        "prompt_versions": sorted({r["result"]["metadata"]["prompt_version"] for r in rows}),
        "output_parsing_version": "json-envelope-v1",
        "adjudication_sha256": sha256(adjudications) if adjudications else None,
        "adjudications": [d.model_dump() for d in decisions],
        "notice": "Controlled synthetic benchmark; not real-repository performance.",
    }
    markdown = [
        "# Evaluation",
        "",
        report["notice"],
        "",
        f"Dataset SHA256: {report['dataset_sha256']}",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    markdown.extend(
        f"| {key} | {value if value is not None else 'undefined'} |"
        for key, value in metrics.model_dump().items()
    )
    markdown.extend(["", "| Example | Status | TP | FP |", "| --- | --- | --- | --- |"])
    markdown.extend(
        f"| {r['id']} | {r['result']['status']} | "
        f"{r['matching']['true_positives']} | {r['matching']['false_positives']} |"
        for r in rows
    )
    output = Path(output)
    write_artifacts(
        {
            output / "metrics.json": json_text(report),
            output / "examples.json": json_text(rows),
            output / "report.md": "\n".join(markdown) + "\n",
        }
    )
    return metrics
