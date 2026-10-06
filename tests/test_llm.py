"""Mocked inference checks: no model weights and no claims about model quality."""

import sys
import types

import pytest

from codereviewlab.config import ReviewConfig
from codereviewlab.extraction import extract_source
from codereviewlab.llm import LLMReviewer


class Tensor:
    shape = (1, 8)


class Encoded(dict):
    def to(self, device):
        return self


class Output:
    def __getitem__(self, item):
        return [99]


class FakeTokenizer:
    eos_token_id = 0

    def __init__(self, response):
        self.response = response

    def apply_chat_template(self, chat, **kwargs):
        assert kwargs["add_generation_prompt"]
        return Encoded(input_ids=Tensor())

    def decode(self, output, **kwargs):
        return self.response


class FakeModel:
    config = types.SimpleNamespace(max_position_embeddings=1000)

    def generate(self, **kwargs):
        assert kwargs["do_sample"] is False
        return Output()


@pytest.mark.parametrize(
    "response,status",
    [
        ('{"findings": []}', "ok"),
        ('```json\n{"findings": []}\n```', "ok"),
        ('Here is the result:\n```json\n{"findings": []}\n```', "parse_error"),
        ('```json\n{"findings": [}\n```', "parse_error"),
        ('{"findings": [], "extra": 1}', "parse_error"),
        (
            '{"findings": [{"path": "wrong.py", "line": 1, "category": "mutable_default", '
            '"explanation": "shared", "suggested_fix": "None"}]}',
            "parse_error",
        ),
    ],
)
def test_output_contract(monkeypatch, response, status):
    class Context:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace(inference_mode=Context))
    reviewer = LLMReviewer(ReviewConfig(backend="llm"))
    reviewer.device = "cpu"
    reviewer.model, reviewer.tokenizer = FakeModel(), FakeTokenizer(response)
    function = extract_source("def f():\n    return 1", "sample.py")[0][0]
    result = reviewer.review(function)
    assert result.status == status
    assert bool(result.error) == (status != "ok")


def test_model_load_failure_is_not_empty_success(monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace())
    reviewer = LLMReviewer(ReviewConfig(backend="llm"))

    def failure():
        raise RuntimeError("weights unavailable offline")

    monkeypatch.setattr(reviewer, "load", failure)
    result = reviewer.review(extract_source("def f():\n    return 1", "x.py")[0][0])
    assert result.status == "inference_error" and "offline" in result.error
