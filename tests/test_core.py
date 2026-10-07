import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from codereviewlab.cli import app
from codereviewlab.config import ReviewConfig, TrainingConfig, load_config
from codereviewlab.dataset import load_dataset, validate_collections
from codereviewlab.evaluation import Decision, evaluate, match_findings
from codereviewlab.extraction import changed_functions, extract_source
from codereviewlab.prompts import messages
from codereviewlab.reports import review_report
from codereviewlab.schemas import ExpectedFinding, Finding, InferenceMetadata, ReviewResult
from codereviewlab.static import StaticReviewer
from codereviewlab.training import response_tokens, validate_training

ROOT = Path(__file__).resolve().parents[1]


def function(code="def f(items=[]):\n    return items", path="example.py"):
    return extract_source(code, path)[0][0]


def finding(line=1):
    return Finding(
        path="example.py",
        line=line,
        category="mutable_default",
        explanation="Shared state",
        suggested_fix="Use None",
    )


def label():
    return ExpectedFinding(
        category="mutable_default",
        accepted_lines=[1],
        explanation="Shared state",
        suggested_fix="Use None",
    )


def test_nested_async_methods_and_decorated_lines():
    source = (
        "import os\nclass C:\n    @decorator\n    async def f(self, items=[]):\n"
        "        def inner():\n            return 1\n        return items\n"
    )
    inputs, errors = extract_source(source, "original.py")
    assert not errors
    assert [(f.name, f.start_line, f.end_line) for f in inputs] == [
        ("C.f", 3, 7),
        ("C.f.inner", 5, 6),
    ]
    assert inputs[0].context == "import os"
    assert StaticReviewer().review(inputs[0]).findings[0].line == 4


def test_syntax_and_size_failures():
    assert "syntax error" in extract_source("def f(:", "bad.py")[1][0]
    inputs, errors = extract_source("def f():\n    return 1", "large.py", max_lines=1)
    assert inputs == [] and "oversized" in errors[0]


@pytest.mark.parametrize(
    "code,category,line",
    [
        ("def f(*, a={}):\n    return a", "mutable_default", 1),
        ("def f(items):\n    return items is []", "none_or_empty", 2),
        (
            "def f(items):\n    for i in range(len(items) + 1):\n        print(items[i])",
            "boundary_condition",
            2,
        ),
    ],
)
def test_static_patterns(code, category, line):
    result = StaticReviewer().review(function(code))
    assert [(f.category, f.line) for f in result.findings] == [(category, line)]


def test_static_correct_counterexamples_and_nested_ownership():
    code = (
        "def outer(items=None):\n    def inner(a=[]):\n        return a\n"
        "    return items if items is not None else []"
    )
    assert not StaticReviewer().review(function(code)).findings
    assert (
        not StaticReviewer()
        .review(function("def f(items):\n    for i in range(len(items)):\n        print(items[i])"))
        .findings
    )


def test_schema_rejects_unknown_and_out_of_range():
    with pytest.raises(ValidationError):
        Finding(**finding().model_dump(), unknown=True)
    with pytest.raises(ValidationError):
        ReviewResult(
            function=function(),
            status="ok",
            findings=[finding(3)],
            metadata=InferenceMetadata(backend="test"),
        )
    with pytest.raises(ValidationError):
        ReviewResult(
            function=function(),
            status="inference_error",
            metadata=InferenceMetadata(backend="test"),
        )


def test_diff_context_verification_and_deleted_lines(tmp_path):
    (tmp_path / "example.py").write_text("def f(a=[]):\n    return a\n", encoding="utf-8")
    diff = (
        "--- a/example.py\n+++ b/example.py\n@@ -1,2 +1,2 @@\n"
        "-def f(a=None):\n+def f(a=[]):\n     return a\n"
    )
    inputs, issues = changed_functions(diff, tmp_path)
    assert len(inputs) == 1 and not issues
    assert inputs[0].path == "example.py"
    assert changed_functions(diff.replace("return a", "return b"), tmp_path)[1]
    assert changed_functions(diff.replace("example.py", "../outside.py"), tmp_path)[1]
    assert changed_functions(diff.replace("example.py", "missing.py"), tmp_path)[1]
    assert changed_functions(diff.replace("+1,2", "+1,4"), tmp_path)[1]


def test_matching_duplicates_and_manual_decision():
    matched = match_findings([label()], [finding(), finding(), finding(2)])
    assert matched["true_positives"] == 1 and matched["false_positives"] == 1
    assert match_findings([label()], [finding(2)])["true_positives"] == 0
    decision = Decision(
        example_id="a",
        prediction_index=0,
        expected_index=0,
        rationale="Equivalent location",
        reviewer="tester",
    )
    assert match_findings([label()], [finding(2)], [decision])["true_positives"] == 1


def test_dataset_balance_family_splits_and_reproducibility():
    rows = load_dataset(ROOT / "data/benchmark.jsonl")
    assert validate_collections(rows) == {
        "examples": 120,
        "families": 30,
        "buggy": 60,
        "correct": 60,
    }
    assert len(load_dataset(ROOT / "data/dev.jsonl")) == 84
    assert len(load_dataset(ROOT / "data/test.jsonl")) == 36
    for category in {f.category for e in rows for f in e.expected_findings}:
        assert sum(e.buggy and e.expected_findings[0].category == category for e in rows) == 20
    with pytest.raises(ValueError, match="Duplicate"):
        validate_collections([rows[0], rows[0]])
    modified = rows[1].model_copy(update={"split": "train"})
    with pytest.raises(ValueError, match="Family"):
        validate_collections([rows[0], modified])


def test_benchmark_edge_cases_cover_all_categories_and_expected_bounds():
    rows = load_dataset(ROOT / "data/benchmark.jsonl")
    expected = {
        "boundary_condition": 20,
        "none_or_empty": 20,
        "mutable_default": 20,
    }
    actual = {
        category: sum(
            1 for row in rows for finding in row.expected_findings if finding.category == category
        )
        for category in expected
    }
    assert actual == expected
    assert {row.buggy for row in rows} == {True, False}
    assert all(
        (row.buggy and row.expected_findings) or ((not row.buggy) and not row.expected_findings)
        for row in rows
    )
    assert all(all(finding.accepted_lines for finding in row.expected_findings) for row in rows)


def test_prompts_have_only_unlabeled_input():
    example = load_dataset(ROOT / "data/dev.jsonl")[0]
    payload = json.loads(messages(example.function)[-1]["content"])
    assert set(payload) == {"path", "name", "code"}
    assert "1: def" in payload["code"]
    for example in load_dataset(ROOT / "data/benchmark.jsonl"):
        assert "correct" not in example.function.name and "bug" not in example.function.name
        assert example.expected_findings == [] or (
            example.expected_findings[0].category not in example.function.path
        )


def test_evaluation_failure_denominators_and_artifacts(tmp_path):
    class FailedReviewer:
        def review(self, input_function):
            return ReviewResult(
                function=input_function,
                status="parse_error",
                error="bad JSON",
                metadata=InferenceMetadata(backend="mock"),
            )

    cfg = ReviewConfig()
    metrics = evaluate(ROOT / "data/dev.jsonl", FailedReviewer(), cfg, tmp_path / "failed")
    assert metrics.failures == 84 and metrics.processed == 0
    assert metrics.bug_recall == 0
    assert metrics.finding_precision is None
    assert metrics.correct_function_false_positive_rate is None
    assert (tmp_path / "failed/report.md").exists()
    with pytest.raises(FileExistsError):
        evaluate(ROOT / "data/dev.jsonl", StaticReviewer(), cfg, tmp_path / "failed")


def test_report_overwrite_protection(tmp_path):
    output = tmp_path / "review.json"
    result = StaticReviewer().review(function())
    review_report([result], [], output)
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        review_report([], [], output)
    assert output.read_bytes() == original


def test_cli_help_review_errors_and_training_validation(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    runner = CliRunner()
    for command in [[], ["review"], ["evaluate"], ["train"], ["review-diff"], ["compare"]]:
        assert runner.invoke(app, [*command, "--help"]).exit_code == 0
    output = tmp_path / "review.json"
    result = runner.invoke(app, ["review", "examples/sample.py", "--output", str(output)])
    assert result.exit_code == 0, result.output
    assert runner.invoke(app, ["review", "missing.py"]).exit_code == 2
    assert (
        runner.invoke(app, ["review", "examples/sample.py", "--output", str(output)]).exit_code == 2
    )
    assert (
        runner.invoke(
            app, ["train", "--config", "configs/lora-fixture.yaml", "--validate-only"]
        ).exit_code
        == 0
    )


def test_cli_doctor_and_review_diff_smoke(tmp_path):
    runner = CliRunner()
    repo = tmp_path / "repo"
    repo.mkdir()
    source = repo / "sample.py"
    source.write_text("def f(items=[]):\n    return items\n", encoding="utf-8")
    diff = repo / "changes.diff"
    diff.write_text(
        "diff --git a/sample.py b/sample.py\n"
        "--- a/sample.py\n"
        "+++ b/sample.py\n"
        "@@ -1,2 +1,2 @@\n"
        "-def f(items=None):\n"
        "+def f(items=[]):\n"
        "     return items\n",
        encoding="utf-8",
    )
    assert runner.invoke(app, ["doctor"]).exit_code == 0
    output = tmp_path / "diff-report.json"
    result = runner.invoke(
        app,
        ["review-diff", str(diff), "--repo", str(repo), "--output", str(output)],
    )
    assert result.exit_code == 0, result.output
    assert output.exists()


def test_cli_compare_accepts_matching_payloads_and_rejects_mismatch(tmp_path):
    runner = CliRunner()
    base = tmp_path / "base.json"
    candidate = tmp_path / "candidate.json"
    output = tmp_path / "comparison.md"
    payload = {
        "dataset_sha256": "abc",
        "matching_version": "v1",
        "adjudication_sha256": "def",
        "prompt_versions": {"static": "p1"},
        "output_parsing_version": "v1",
        "config": {
            "model": "test-model",
            "revision": "main",
            "prompt": "baseline",
            "device": "cpu",
            "max_new_tokens": 32,
            "max_input_tokens": 256,
            "seed": 7,
        },
        "metrics": {"precision": 1.0, "recall": 0.5},
    }
    base.write_text(json.dumps(payload), encoding="utf-8")
    candidate.write_text(json.dumps(payload), encoding="utf-8")
    result = runner.invoke(app, ["compare", str(base), str(candidate), "--output", str(output)])
    assert result.exit_code == 0, result.output
    assert output.exists()

    changed = json.loads(candidate.read_text(encoding="utf-8"))
    changed["dataset_sha256"] = "xyz"
    candidate.write_text(json.dumps(changed), encoding="utf-8")
    result = runner.invoke(app, ["compare", str(base), str(candidate), "--output", str(output)])
    assert result.exit_code == 2
    assert "differs" in result.output


def test_training_mask_and_template_mismatch():
    class Tokenizer:
        def apply_chat_template(self, chat, **kwargs):
            return [1, 2, 3, 4] if chat[-1]["role"] == "assistant" else [1, 2]

    example = load_dataset(ROOT / "data/dev.jsonl")[0]
    tokens = response_tokens(Tokenizer(), example, ReviewConfig())
    assert tokens["labels"] == [-100, -100, 3, 4]
    cfg = load_config(
        ROOT / "configs/lora-fixture.yaml",
        TrainingConfig,
    )
    assert len(validate_training(cfg)) == 4
    cfg.dataset = str(ROOT / "data/dev.jsonl")
    with pytest.raises(ValueError):
        validate_training(cfg)
