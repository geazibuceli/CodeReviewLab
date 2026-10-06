"""Explicitly execute reference cases in a resource-limited offline Docker container."""

import argparse
import json
import subprocess
import sys
import textwrap
import uuid
from pathlib import Path


def inside(dataset):
    # This branch is reached only inside the explicitly invoked container.
    for raw in Path(dataset).read_text(encoding="utf-8").splitlines():
        example = json.loads(raw)
        namespace = {}
        exec(compile(textwrap.dedent(example["function"]["code"]), "case.py", "exec"), namespace)
        function = namespace[example["function"]["name"]]
        exposes_bug = False
        for case in example["reference_cases"]:
            for arguments, expected in zip(case["calls"], case["expected"], strict=True):
                try:
                    # Serialize immediately so later mutation cannot change earlier observations.
                    actual = json.loads(json.dumps(function(**arguments)))
                    exposes_bug |= actual != expected
                except Exception:
                    exposes_bug = True
        if exposes_bug != example["buggy"]:
            raise RuntimeError(f"Reference disagrees with label: {example['id']}")
    print("All reference cases agree with labels")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--inside-container", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--image", default="python:3.11-slim")
    args = parser.parse_args()
    if args.inside_container:
        if not Path("/.dockerenv").is_file() or Path(__file__).resolve() != Path("/runner.py"):
            parser.error("Internal execution mode is allowed only in the isolated container")
        inside(args.dataset)
        return
    path = args.dataset.resolve()
    script = Path(__file__).resolve()
    container_name = f"codereviewlab-reference-{uuid.uuid4().hex}"
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "--pull=never",
        "--network=none",
        "--memory=256m",
        "--cpus=1",
        "--pids-limit=32",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--user=65534:65534",
        "--mount",
        f"type=bind,source={path},target=/dataset.jsonl,readonly",
        "--mount",
        f"type=bind,source={script},target=/runner.py,readonly",
        args.image,
        "python",
        "-I",
        "/runner.py",
        "/dataset.jsonl",
        "--inside-container",
    ]
    try:
        subprocess.run(command, check=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Isolated execution failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    finally:
        try:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                check=False,
                timeout=10,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.SubprocessError):
            pass


if __name__ == "__main__":
    main()
