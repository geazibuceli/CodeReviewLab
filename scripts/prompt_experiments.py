"""Run fixed-generation development comparisons; reserved test is never opened."""

import argparse
from pathlib import Path

from codereviewlab.config import ReviewConfig
from codereviewlab.evaluation import evaluate
from codereviewlab.llm import make_reviewer
from codereviewlab.reports import write_artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-download", action="store_true")
    args = parser.parse_args()
    rows = []
    reviewer = make_reviewer(ReviewConfig(backend="llm", allow_download=args.allow_download))
    for variant in ["basic", "few-shot", "contextual"]:
        print(f"Evaluating development prompt: {variant}", flush=True)
        reviewer.config.prompt = variant
        metrics = evaluate(Path("data/dev.jsonl"), reviewer, reviewer.config, args.output / variant)
        rows.append((variant, metrics))
        print(metrics.model_dump_json(), flush=True)
    lines = [
        "# Development prompt comparison",
        "",
        "Select a prompt before reserved testing.",
        "",
        "| Prompt | Precision | Recall | Failures |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {name} | {m.finding_precision} | {m.bug_recall} | {m.failures} |" for name, m in rows
    )
    write_artifacts({args.output / "comparison.md": "\n".join(lines) + "\n"})


if __name__ == "__main__":
    main()
