"""CLI remains usable without any inference dependencies or model weights."""

import importlib.util
import json
import platform
from pathlib import Path
from typing import Annotated

import typer

from .config import TrainingConfig, load_config
from .dataset import load_dataset, validate_collections
from .evaluation import evaluate as run_evaluation
from .extraction import changed_functions, extract_file
from .llm import make_reviewer
from .reports import ensure_new, review_report, write_artifacts

app = typer.Typer(
    help="Python review suggestions requiring human verification.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


def fail(exc):
    typer.echo(f"Error: {exc}", err=True)
    raise typer.Exit(2) from exc


@app.command()
def doctor():
    """Inspect software and hardware without downloading weights."""
    typer.echo(f"Python: {platform.python_version()} | OS: {platform.platform()}")
    for name in ["torch", "transformers", "peft", "trl"]:
        typer.echo(f"{name}: {'available' if importlib.util.find_spec(name) else 'missing'}")
    if importlib.util.find_spec("torch"):
        import torch

        typer.echo(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            typer.echo(f"GPU: {torch.cuda.get_device_name(0)}")
            typer.echo(f"GPU memory bytes: {torch.cuda.get_device_properties(0).total_memory}")


def review_inputs(functions, issues, config, output):
    ensure_new([output, output.with_suffix(".md")])
    reviewer = make_reviewer(config)
    results = [reviewer.review(function) for function in functions]
    review_report(results, issues, output)
    failed = sum(r.status != "ok" for r in results)
    typer.echo(f"Processed {len(results)} functions; {failed} failed; report: {output}")
    for issue in issues:
        typer.echo(f"Input issue: {issue}", err=True)
    for result in results:
        if result.error:
            typer.echo(
                f"{result.function.path}:{result.function.start_line}: {result.error}", err=True
            )
    if issues or any(r.status != "ok" for r in results):
        raise typer.Exit(1)


@app.command()
def review(
    path: Path,
    output: Path = Path("reports/review.json"),
    config: Path | None = None,
    allow_download: bool = False,
):
    """Review a Python file using the static baseline by default."""
    try:
        cfg = load_config(config)
        cfg.allow_download = cfg.allow_download or allow_download
        functions, issues = extract_file(path)
        review_inputs(functions, issues, cfg, output)
    except typer.Exit:
        raise
    except Exception as exc:
        fail(exc)


@app.command()
def review_diff(
    diff: Path,
    repo: Path = Path("."),
    output: Path = Path("reports/diff-review.json"),
    config: Path | None = None,
    allow_download: bool = False,
):
    """Review changed functions in verified repository post-image files."""
    try:
        cfg = load_config(config)
        cfg.allow_download = cfg.allow_download or allow_download
        functions, issues = changed_functions(diff.read_text(encoding="utf-8"), repo)
        review_inputs(functions, issues, cfg, output)
    except typer.Exit:
        raise
    except Exception as exc:
        fail(exc)


@app.command()
def validate_dataset(path: Path):
    """Validate schemas, labels, syntax, duplicates, and family splits."""
    try:
        typer.echo(json.dumps(validate_collections(load_dataset(path)), indent=2))
    except Exception as exc:
        fail(exc)


@app.command()
def evaluate(
    dataset: Annotated[Path, typer.Option()],
    config: Annotated[Path, typer.Option()],
    output: Annotated[Path, typer.Option()],
    adjudications: Path | None = None,
    allow_download: bool = False,
):
    """Evaluate every row, recording failures and undefined metrics explicitly."""
    try:
        cfg = load_config(config)
        cfg.allow_download = cfg.allow_download or allow_download
        metrics = run_evaluation(dataset, make_reviewer(cfg), cfg, output, adjudications)
        typer.echo(metrics.model_dump_json(indent=2))
        if metrics.failures:
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as exc:
        fail(exc)


@app.command()
def train(
    config: Annotated[Path, typer.Option()],
    validate_only: bool = False,
    allow_download: bool = False,
):
    """Validate or explicitly run response-only LoRA/QLoRA training."""
    try:
        from .training import train as run_training
        from .training import validate_training

        cfg = load_config(config, TrainingConfig)
        cfg.inference.allow_download = cfg.inference.allow_download or allow_download
        if validate_only:
            typer.echo(f"Validated {len(validate_training(cfg))} training examples")
        else:
            run_training(cfg)
    except Exception as exc:
        fail(exc)


@app.command()
def compare(base: Path, adapter: Path, output: Annotated[Path, typer.Option()]):
    """Compare compatible recorded evaluations without claiming significance."""
    try:
        left, right = [json.loads(p.read_text(encoding="utf-8")) for p in (base, adapter)]
        keys = ["dataset_sha256", "matching_version", "adjudication_sha256"]
        if any(left[k] != right[k] for k in keys):
            raise ValueError("Evaluation data or matching/adjudication differs")
        if any(left.get(k) != right.get(k) for k in ["prompt_versions", "output_parsing_version"]):
            raise ValueError("Prompt version or output parsing differs")
        settings = [
            "model",
            "revision",
            "prompt",
            "device",
            "max_new_tokens",
            "max_input_tokens",
            "seed",
        ]
        if any(left["config"][k] != right["config"][k] for k in settings):
            raise ValueError("Model, prompt, device, or generation settings differ")
        lines = [
            "# Recorded comparison",
            "",
            "No statistical significance is implied.",
            "",
            "| Metric | Base | Candidate | Delta |",
            "| --- | --- | --- | --- |",
        ]
        for key, value in left["metrics"].items():
            other = right["metrics"][key]
            delta = other - value if value is not None and other is not None else "undefined"
            lines.append(f"| {key} | {value} | {other} | {delta} |")
        write_artifacts({output: "\n".join(lines) + "\n"})
    except Exception as exc:
        fail(exc)


if __name__ == "__main__":
    app()
