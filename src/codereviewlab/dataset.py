"""Dataset validation without execution, leakage, or silent exclusions."""

import ast
import hashlib
import json
import textwrap
from pathlib import Path

from .extraction import extract_source
from .schemas import Example


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_fingerprint(example):
    return ast.dump(ast.parse(textwrap.dedent(example.function.code)), include_attributes=False)


def load_dataset(path):
    examples = []
    for line, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            raise ValueError(f"{path}:{line}: blank dataset row")
        try:
            example = Example.model_validate(json.loads(raw))
            functions, issues = extract_source(
                textwrap.dedent(example.function.code), example.function.path
            )
            if issues or len(functions) != 1:
                raise ValueError("Dataset row must contain exactly one complete function")
            if functions[0].name != example.function.name:
                raise ValueError("Function name does not match source")
            for case in example.reference_cases:
                if len(case.calls) != len(case.expected):
                    raise ValueError("Reference call and expected result counts disagree")
            examples.append(example)
        except Exception as exc:
            raise ValueError(f"{path}:{line}: {exc}") from exc
    if not examples:
        raise ValueError("Dataset is empty")
    validate_collections(examples)
    return examples


def validate_collections(examples):
    ids, codes, families = set(), set(), {}
    for example in examples:
        if example.id in ids:
            raise ValueError(f"Duplicate ID: {example.id}")
        code = code_fingerprint(example)
        if code in codes:
            raise ValueError(f"Duplicate source: {example.id}")
        if example.family_id in families and families[example.family_id] != example.split:
            raise ValueError(f"Family crosses splits: {example.family_id}")
        ids.add(example.id)
        codes.add(code)
        families[example.family_id] = example.split
    return {
        "examples": len(examples),
        "families": len(families),
        "buggy": sum(e.buggy for e in examples),
        "correct": sum(not e.buggy for e in examples),
    }
