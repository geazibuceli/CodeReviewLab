"""Reproduce four tiny, author-reviewed training cases, not a quality dataset."""

from pathlib import Path

from codereviewlab.extraction import extract_source
from codereviewlab.schemas import Example


def main():
    rows = []
    for family, bad, good, line, category, explanation, fix in [
        (
            "fixture-window",
            "return start <= position <= stop",
            "return start <= position < stop",
            3,
            "boundary_condition",
            "Exclusive stop incorrectly included.",
            "Use position < stop.",
        ),
        (
            "fixture-tags",
            "tags.add(tag)",
            "tags = {tag} if tags is None else tags | {tag}",
            1,
            "mutable_default",
            "Set default shared across requests.",
            "Use None and create a fresh set when omitted.",
        ),
    ]:
        for buggy in [True, False]:
            name = f"{family.replace('-', '_')}_{'bug' if buggy else 'correct'}"
            args = (
                "start, stop, position"
                if category == "boundary_condition"
                else ("tag, tags=set()" if buggy else "tag, tags=None")
            )
            contract = (
                "Stop is exclusive."
                if category == "boundary_condition"
                else ("Each omitted tags argument gets a fresh set.")
            )
            body = bad if buggy else good
            code = f'def {name}({args}):\n    """{contract}"""\n    {body}'
            if category == "mutable_default":
                code += "\n    return sorted(tags)"
            function = extract_source(code, f"fixtures/{family}.py")[0][0]
            rows.append(
                Example(
                    id=name,
                    family_id=family,
                    provenance="Original author-generated pipeline fixture.",
                    review_status="author_reviewed",
                    split="fixture",
                    function=function,
                    buggy=buggy,
                    expected_findings=[
                        {
                            "category": category,
                            "accepted_lines": [line],
                            "explanation": explanation,
                            "suggested_fix": fix,
                        }
                    ]
                    if buggy
                    else [],
                )
            )
    path = Path("data/training-fixture.jsonl")
    content = "\n".join(e.model_dump_json() for e in rows) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != content:
        raise FileExistsError("Fixture already exists with different content")
    path.write_text(content, encoding="utf-8")
    print("Reproduced four fixture examples; insufficient for quality claims.")


if __name__ == "__main__":
    main()
