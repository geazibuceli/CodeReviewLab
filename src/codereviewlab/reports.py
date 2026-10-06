"""Exclusive artifact creation and human-readable companion reports."""

import json
from pathlib import Path


def ensure_new(paths):
    if any(path.exists() for path in paths):
        raise FileExistsError("Output artifact already exists; choose a new output path")


def write_artifacts(artifacts: dict[Path, str]):
    ensure_new(artifacts)
    created = []
    try:
        for path, content in artifacts.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as stream:
                created.append(path)
                stream.write(content)
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise


def json_text(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def review_report(results, issues, output: Path):
    data = {
        "notice": "Review suggestions require human verification.",
        "issues": issues,
        "results": [r.model_dump(mode="json") for r in results],
    }
    lines = ["# CodeReviewLab review", "", data["notice"], ""]
    lines.extend(f"- Input issue: {issue}" for issue in issues)
    for result in results:
        lines.extend(
            [f"\n## {result.function.path}: {result.function.name}", "", f"Status: {result.status}"]
        )
        if result.error:
            lines.append(f"Error: {result.error}")
        for finding in result.findings:
            lines.extend(
                [
                    f"\n- Line {finding.line}: **{finding.category}**",
                    f"  {finding.explanation}",
                    f"  Suggested fix: {finding.suggested_fix}",
                ]
            )
        if result.status == "ok" and not result.findings:
            lines.append("No suggestions returned. This does not establish correctness.")
    companion = output.with_suffix(".md")
    if companion == output:
        raise ValueError("Review output must use a JSON extension")
    write_artifacts({output: json_text(data), companion: "\n".join(lines) + "\n"})
