"""Author-reviewed synthetic training collection, separate from benchmark families."""

import hashlib
from pathlib import Path

from codereviewlab.dataset import validate_collections
from codereviewlab.extraction import extract_source
from codereviewlab.schemas import Example

# Reviewed contracts, counterexamples, and targeted corrections. No external source is claimed.
CASES = [
    (
        "clamp",
        "boundary_condition",
        "value, ceiling",
        "Clamp to ceiling even above the ceiling.",
        "return min(value, ceiling - 1)",
        "return min(value, ceiling)",
        3,
        "Subtracting one incorrectly lowers the inclusive ceiling.",
        "Use min(value, ceiling).",
        [{"value": 10, "ceiling": 10}],
        [10],
    ),
    (
        "closed_interval",
        "boundary_condition",
        "start, stop",
        "Return all integers including stop.",
        "return list(range(start, stop))",
        "return list(range(start, stop + 1))",
        3,
        "range excludes stop, contrary to the inclusive contract.",
        "Use stop + 1 as the range end.",
        [{"start": 2, "stop": 4}],
        [[2, 3, 4]],
    ),
    (
        "tail",
        "boundary_condition",
        "values, offset",
        "Return the suffix starting at offset.",
        "return values[offset + 1:]",
        "return values[offset:]",
        3,
        "Offset plus one drops the first requested suffix element.",
        "Slice from offset directly.",
        [{"values": [5, 6, 7], "offset": 1}],
        [[6, 7]],
    ),
    (
        "pair_count",
        "boundary_condition",
        "values",
        "Count adjacent pairs, including zero for empty input.",
        "return len(values) - 1",
        "return max(0, len(values) - 1)",
        3,
        "Empty input produces a negative pair count.",
        "Clamp the result to zero.",
        [{"values": []}],
        [0],
    ),
    (
        "optional_sum",
        "none_or_empty",
        "values",
        "A missing collection has total zero.",
        "return sum(value for value in values)",
        "return sum(value for value in (values if values is not None else []))",
        3,
        "Iterating None raises TypeError.",
        "Substitute an empty iterable only when values is None.",
        [{"values": None}],
        [0],
    ),
    (
        "join_names",
        "none_or_empty",
        "names",
        "None means no names and produces an empty string.",
        "return ','.join(names)",
        "return ','.join(names if names is not None else [])",
        3,
        "Joining None fails instead of returning the empty string.",
        "Use an empty iterable for None.",
        [{"names": None}],
        [""],
    ),
    (
        "minimum_label",
        "none_or_empty",
        "values",
        "Return the smallest value or None when empty.",
        "return min(values)",
        "return min(values, default=None)",
        3,
        "min raises ValueError on empty input.",
        "Specify default=None when calling min.",
        [{"values": []}],
        [None],
    ),
    (
        "optional_scale",
        "none_or_empty",
        "value, multiplier",
        "None stays None; numeric values are scaled.",
        "return value * multiplier",
        "return None if value is None else value * multiplier",
        3,
        "Multiplying None raises TypeError.",
        "Return None before multiplying missing values.",
        [{"value": None, "multiplier": 2}],
        [None],
    ),
    (
        "events",
        "mutable_default",
        "event, log=[]",
        "Omitted log is fresh for every call.",
        "log.append({'event': event})\nreturn log",
        "if log is None:\n    log = []\nlog.append({'event': event})\nreturn log",
        1,
        "List default retains earlier events.",
        "Default log to None and initialize a list per call.",
        [{"event": "a"}, {"event": "b"}],
        [[{"event": "a"}], [{"event": "b"}]],
    ),
    (
        "weights",
        "mutable_default",
        "label, weight, totals={}",
        "Omitted totals is fresh for every call.",
        "totals[label] = totals.get(label, 0) + weight\nreturn totals[label]",
        "if totals is None:\n    totals = {}\n"
        "totals[label] = totals.get(label, 0) + weight\nreturn totals[label]",
        1,
        "Dictionary default accumulates weights from earlier calls.",
        "Default totals to None and initialize a dictionary per call.",
        [{"label": "a", "weight": 2}, {"label": "a", "weight": 3}],
        [2, 3],
    ),
    (
        "members",
        "mutable_default",
        "name, group={'names': set()}",
        "Omitted group is fresh for every call.",
        "group['names'].add(name)\nreturn sorted(group['names'])",
        "if group is None:\n    group = {'names': set()}\n"
        "group['names'].add(name)\nreturn sorted(group['names'])",
        1,
        "Default dictionary's nested set retains earlier members.",
        "Default group to None and create a new dictionary and set.",
        [{"name": "a"}, {"name": "b"}],
        [["a"], ["b"]],
    ),
    (
        "positions",
        "mutable_default",
        "position, occupied=set()",
        "Omitted occupied is fresh for every call.",
        "duplicate = position in occupied\noccupied.add(position)\nreturn duplicate",
        "if occupied is None:\n    occupied = set()\nduplicate = position in occupied\n"
        "occupied.add(position)\nreturn duplicate",
        1,
        "Set default makes a later independent call appear duplicated.",
        "Default occupied to None and initialize a set per call.",
        [{"position": 1}, {"position": 1}],
        [False, False],
    ),
]


def main():
    rows = []
    for (
        name,
        category,
        args,
        contract,
        bad,
        good,
        location,
        explanation,
        fix,
        calls,
        expected,
    ) in CASES:
        for variant in range(2):
            for buggy in (True, False):
                example_id = f"train-{name}-{variant}-{'bug' if buggy else 'correct'}"
                suffix = hashlib.sha256(example_id.encode()).hexdigest()[:8]
                parameters = args
                if category == "mutable_default" and not buggy:
                    parameters = args[: args.index("=")] + "=None"
                documentation = contract + (" Used by a local batch processor." if variant else "")
                code = f'def {name}_{suffix}({parameters}):\n    """{documentation}"""\n'
                code += "\n".join("    " + line for line in (bad if buggy else good).splitlines())
                function = extract_source(code, f"training/{name}.py")[0][0]
                rows.append(
                    Example(
                        id=example_id,
                        family_id=f"training-{name}",
                        split="train",
                        provenance=(
                            "Original CodeReviewLab author-generated training templates; "
                            "no external source or independent annotation."
                        ),
                        review_status="author_reviewed",
                        function=function,
                        buggy=buggy,
                        expected_findings=[
                            {
                                "category": category,
                                "accepted_lines": [location],
                                "explanation": explanation,
                                "suggested_fix": fix,
                            }
                        ]
                        if buggy
                        else [],
                        reference_cases=[{"calls": calls, "expected": expected}],
                    )
                )
    validate_collections(rows)
    content = "\n".join(e.model_dump_json() for e in rows) + "\n"
    path = Path("data/training.jsonl")
    if path.exists() and path.read_text(encoding="utf-8") != content:
        raise FileExistsError("Refusing to replace different training data")
    path.write_text(content, encoding="utf-8")
    print("Reproduced 48 synthetic training examples in 12 disjoint families; no quality claim.")


if __name__ == "__main__":
    main()
