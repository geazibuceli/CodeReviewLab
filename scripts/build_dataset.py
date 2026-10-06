"""Reproduce 120 original template-authored cases without executing their code."""

import hashlib
import json
import random
from pathlib import Path

from codereviewlab.dataset import validate_collections
from codereviewlab.schemas import Example

# Each template is a distinct contract, with buggy/correct forms and counterexample calls.
BOUNDARY = [
    (
        "age_gate",
        "age, minimum",
        "return age {op} minimum",
        ">",
        ">=",
        [{"age": 18, "minimum": 18}],
        [True],
    ),
    (
        "capacity",
        "used, limit",
        "return used {op} limit",
        "<=",
        "<",
        [{"used": 5, "limit": 5}],
        [False],
    ),
    (
        "index_valid",
        "index, items",
        "return 0 <= index {op} len(items)",
        "<=",
        "<",
        [{"index": 2, "items": [1, 2]}],
        [False],
    ),
    (
        "deadline",
        "now, deadline",
        "return now {op} deadline",
        "<=",
        "<",
        [{"now": 10, "deadline": 10}],
        [False],
    ),
    (
        "free_shipping",
        "total, threshold",
        "return total {op} threshold",
        ">",
        ">=",
        [{"total": 50, "threshold": 50}],
        [True],
    ),
    (
        "retry_budget",
        "attempts, maximum",
        "return attempts {op} maximum",
        "<=",
        "<",
        [{"attempts": 3, "maximum": 3}],
        [False],
    ),
    (
        "temperature_alert",
        "temperature, threshold",
        "return temperature {op} threshold",
        ">=",
        ">",
        [{"temperature": 30, "threshold": 30}],
        [False],
    ),
    (
        "page_count",
        "count, size",
        "return {expr}",
        "count // size + 1",
        "(count + size - 1) // size",
        [{"count": 4, "size": 2}],
        [2],
    ),
    (
        "indexed_sum",
        "items",
        "total = 0\nfor index in range({expr}):\n    total += items[index]\nreturn total",
        "len(items) + 1",
        "len(items)",
        [{"items": [1, 2]}],
        [3],
    ),
    (
        "prefix",
        "items, count",
        "return items[:{expr}]",
        "count + 1",
        "count",
        [{"items": [1, 2, 3], "count": 2}],
        [[1, 2]],
    ),
]
NONE_EMPTY = [
    (
        "first",
        "items",
        "return items[0]",
        "return items[0] if items else None",
        [{"items": []}],
        [None],
    ),
    (
        "last",
        "items",
        "return items[-1]",
        "return items[-1] if items else None",
        [{"items": []}],
        [None],
    ),
    (
        "average",
        "items",
        "return sum(items) / len(items)",
        "return sum(items) / len(items) if items else 0",
        [{"items": []}],
        [0],
    ),
    (
        "maximum",
        "items",
        "return max(items)",
        "return max(items) if items else None",
        [{"items": []}],
        [None],
    ),
    (
        "optional_length",
        "items",
        "return len(items)",
        "return len(items) if items is not None else 0",
        [{"items": None}],
        [0],
    ),
    (
        "optional_strip",
        "text",
        "return text.strip()",
        "return text.strip() if text is not None else ''",
        [{"text": None}],
        [""],
    ),
    ("empty_check", "items", "return items is []", "return items == []", [{"items": []}], [True]),
    (
        "optional_lookup",
        "mapping",
        "return mapping.get('key')",
        "return mapping.get('key') if mapping is not None else None",
        [{"mapping": None}],
        [None],
    ),
    (
        "zero_preserved",
        "value",
        "return value or 10",
        "return 10 if value is None else value",
        [{"value": 0}],
        [0],
    ),
    (
        "optional_sort",
        "items",
        "return sorted(items)",
        "return sorted(items) if items is not None else []",
        [{"items": None}],
        [[]],
    ),
]
MUTABLE = [
    (
        "append",
        "value",
        "items",
        "[]",
        "items.append(value)\nreturn items",
        [{"value": 1}, {"value": 2}],
        [[1], [2]],
    ),
    (
        "cache",
        "key, value",
        "items",
        "{}",
        "items[key] = value\nreturn items",
        [{"key": "a", "value": 1}, {"key": "b", "value": 2}],
        [{"a": 1}, {"b": 2}],
    ),
    (
        "unique",
        "value",
        "items",
        "set()",
        "items.add(value)\nreturn sorted(items)",
        [{"value": 1}, {"value": 2}],
        [[1], [2]],
    ),
    (
        "prepend",
        "value",
        "items",
        "list()",
        "items.insert(0, value)\nreturn items",
        [{"value": 1}, {"value": 2}],
        [[1], [2]],
    ),
    (
        "history",
        "value",
        "history",
        "[]",
        "history.extend([value, value])\nreturn history",
        [{"value": 1}, {"value": 2}],
        [[1, 1], [2, 2]],
    ),
    (
        "counter",
        "key",
        "counts",
        "dict()",
        "counts[key] = counts.get(key, 0) + 1\nreturn counts[key]",
        [{"key": "a"}, {"key": "a"}],
        [1, 1],
    ),
    (
        "bucket",
        "value",
        "bucket",
        "{'values': []}",
        "bucket['values'].append(value)\nreturn bucket",
        [{"value": 1}, {"value": 2}],
        [{"values": [1]}, {"values": [2]}],
    ),
    (
        "seen_count",
        "value",
        "seen",
        "set()",
        "seen.add(value)\nreturn len(seen)",
        [{"value": 1}, {"value": 2}],
        [1, 1],
    ),
    (
        "queue",
        "value",
        "queue",
        "[]",
        "queue += [value]\nreturn queue",
        [{"value": 1}, {"value": 2}],
        [[1], [2]],
    ),
    (
        "nested",
        "value",
        "state",
        "[[]]",
        "state[0].append(value)\nreturn state",
        [{"value": 1}, {"value": 2}],
        [[[1]], [[2]]],
    ),
]


def generate():
    rows = []
    for category, templates in [
        ("boundary_condition", BOUNDARY),
        ("none_or_empty", NONE_EMPTY),
        ("mutable_default", MUTABLE),
    ]:
        families = list(range(10))
        random.Random(42).shuffle(families)
        test_families = set(families[:3])
        for index, template in enumerate(templates):
            family = f"{category}-{index:02}"
            for variant in range(2):
                for buggy in (True, False):
                    if category == "boundary_condition":
                        name, args, body, bad, good, calls, expected = template
                        body = body.format(op=bad if buggy else good, expr=bad if buggy else good)
                        fix = f"Use {good} to satisfy the documented boundary contract."
                        contract = (
                            "Inputs follow the documented valid domain; "
                            "threshold semantics are explicit."
                        )
                        contracts = [
                            "Allow age equal to minimum.",
                            "Only allow used strictly below limit.",
                            "Valid indices are from zero through len(items)-1.",
                            "Deadline is exclusive.",
                            "Shipping is free at the threshold.",
                            "Attempts equal to maximum exhaust the budget.",
                            "Alert only strictly above threshold.",
                            "Count nonnegative items in positive-size pages without an extra page.",
                            "Sum all items exactly once.",
                            "Return exactly the first count items.",
                        ]
                        contract += " " + contracts[index]
                    elif category == "none_or_empty":
                        name, args, bad, good, calls, expected = template
                        body = bad if buggy else good
                        fix = good
                        contract = "Handle the empty or None input shown in the contract."
                        contract += " Expected result: " + json.dumps(expected[0]) + "."
                    else:
                        name, args, collection, default, body, calls, expected = template
                        fix = f"Default {collection} to None and initialize {default} per call."
                        args += f", {collection}={default if buggy else 'None'}"
                        if not buggy:
                            body = (
                                f"if {collection} is None:\n    {collection} = {default}\n" + body
                            )
                        contract = "Omitted collection creates fresh state for each call."
                    suffix = hashlib.sha256(f"{family}:{variant}:{buggy}".encode()).hexdigest()[:8]
                    function_name = f"{name}_{suffix}"
                    # Two context variants remain in one family and one split.
                    doc = contract + (" This is a service helper." if variant else "")
                    code = f'def {function_name}({args}):\n    """{doc}"""\n' + "\n".join(
                        "    " + line for line in body.splitlines()
                    )
                    location = (
                        1
                        if category == "mutable_default"
                        else (4 if category == "boundary_condition" and index == 8 else 3)
                    )
                    rows.append(
                        Example.model_validate(
                            {
                                "id": f"{family}-{variant}-{'bug' if buggy else 'correct'}",
                                "family_id": family,
                                "provenance": (
                                    "Original CodeReviewLab author-generated template; "
                                    "no external source or independent annotation."
                                ),
                                "review_status": "author_reviewed",
                                "split": "test" if index in test_families else "dev",
                                "function": {
                                    "path": f"benchmark/{name}.py",
                                    "name": function_name,
                                    "start_line": 1,
                                    "end_line": len(code.splitlines()),
                                    "code": code,
                                },
                                "buggy": buggy,
                                "expected_findings": [
                                    {
                                        "category": category,
                                        "accepted_lines": [location],
                                        "explanation": contract,
                                        "suggested_fix": fix,
                                    }
                                ]
                                if buggy
                                else [],
                                "reference_cases": [{"calls": calls, "expected": expected}],
                            }
                        )
                    )
    validate_collections(rows)
    return rows


def main():
    root = Path("data")
    root.mkdir(exist_ok=True)
    rows = generate()
    for name, selected in [
        ("benchmark", rows),
        ("dev", [e for e in rows if e.split == "dev"]),
        ("test", [e for e in rows if e.split == "test"]),
    ]:
        text = "\n".join(e.model_dump_json() for e in selected) + "\n"
        path = root / f"{name}.jsonl"
        if path.exists() and path.read_text(encoding="utf-8") != text:
            raise FileExistsError(f"Refusing to replace different dataset: {path}")
        path.write_text(text, encoding="utf-8")
    print("Reproduced 120 examples: 84 development, 36 reserved test; 30 families.")


if __name__ == "__main__":
    main()
