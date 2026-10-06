import json
import types

import pytest
from typer.testing import CliRunner

from codereviewlab.cli import app
from codereviewlab.config import ReviewConfig
from codereviewlab.extraction import changed_functions, extract_file, extract_source
from codereviewlab.llm import LLMReviewer
from codereviewlab.training import response_tokens


def test_diff_deletion_only_and_multiple_hunks(tmp_path):
    (tmp_path / "a.py").write_text(
        "def first():\n    return 1\n\ndef second():\n    return 2\n", encoding="utf-8"
    )
    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n"
        "@@ -1,3 +1,2 @@\n def first():\n-    unused = 3\n     return 1\n"
        "@@ -5,2 +4,2 @@\n def second():\n-    return 1\n+    return 2\n"
    )
    functions, errors = changed_functions(diff, tmp_path)
    assert not errors and [f.name for f in functions] == ["first", "second"]
    assert changed_functions("nonsense", tmp_path)[1]


def test_unsupported_input_and_syntax_exit(tmp_path):
    assert extract_file(tmp_path / "a.txt")[1]
    source = tmp_path / "bad.py"
    source.write_text("def broken(:", encoding="utf-8")
    output = tmp_path / "report.json"
    result = CliRunner().invoke(app, ["review", str(source), "--output", str(output)])
    assert result.exit_code == 1
    assert "syntax error" in json.loads(output.read_text())["issues"][0]


def test_template_prefix_and_training_token_overflow():
    example = types.SimpleNamespace(
        function=extract_source("def f():\n    return 1", "a.py")[0][0],
        expected_findings=[],
        id="mock",
    )

    class Mismatch:
        def apply_chat_template(self, chat, **kwargs):
            return [2] if chat[-1]["role"] == "assistant" else [1]

    with pytest.raises(ValueError, match="prefix mismatch"):
        response_tokens(Mismatch(), example, ReviewConfig())

    class Long:
        def apply_chat_template(self, chat, **kwargs):
            return [1] * (100 if chat[-1]["role"] == "assistant" else 10)

    with pytest.raises(ValueError, match="token budget"):
        response_tokens(Long(), example, ReviewConfig(max_input_tokens=64))


def test_inference_overflow_never_generates(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "torch", types.SimpleNamespace())

    class Encoded(dict):
        def to(self, device):
            return self

    class Tokenizer:
        def apply_chat_template(self, *args, **kwargs):
            return Encoded(input_ids=types.SimpleNamespace(shape=(1, 65)))

    reviewer = LLMReviewer(ReviewConfig(backend="llm", max_input_tokens=64))
    reviewer.device = "cpu"
    reviewer.model = types.SimpleNamespace(
        config=types.SimpleNamespace(max_position_embeddings=999)
    )
    reviewer.tokenizer = Tokenizer()
    result = reviewer.review(extract_source("def f():\n    return 1", "a.py")[0][0])
    assert result.status == "input_error" and "no truncation" in result.error
