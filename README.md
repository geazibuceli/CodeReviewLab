# CodeReviewLab

Local Python code review suggestions using deterministic AST rules and a configurable
instruction model. Every finding requires human verification. This project does not certify
code correctness. See `docs/` for architecture, dataset, model, evaluation, and experiments.

## Installation

Python 3.11+ is required. Python 3.11 or 3.12 is recommended for the pinned training stack.

```sh
python -m pip install -e ".[dev]"
codereviewlab --help
codereviewlab doctor
```

Installation and help do not download model weights. Inference and training are optional:

```sh
python -m pip install -e ".[inference]"
python -m pip install -e ".[training]"
```

## Quick start

```sh
codereviewlab review examples/sample.py --output reports/review.json
codereviewlab validate-dataset data/benchmark.jsonl
codereviewlab evaluate --dataset data/dev.jsonl --config configs/static.yaml --output reports/static-dev
git diff > changes.diff
codereviewlab review-diff changes.diff --repo . --output reports/diff.json
```

Diff review requires complete post-image files in the repository and verifies hunk context.
Outputs are JSON plus Markdown. Existing artifacts are protected; choose a new output path.
Exit codes: 0 success (including findings), 1 incomplete processing, 2 invalid operation/configuration.

## Supported scope

- Boundary conditions: static detection of indexed `range(len(items) + 1)` loops.
- None/empty handling: static detection of identity comparison with a fresh collection literal.
- Mutable default arguments: literals and empty built-in collection constructors.

The LLM can suggest other instances within those categories. AST checks are syntactic and can
produce false positives when names are shadowed, execution is unreachable, or contracts differ.
Methods, async functions, and nested functions preserve source locations. Oversized functions and
syntax errors are reported explicitly. No reviewed code is executed during review or evaluation.

## Real model and training runs

```sh
codereviewlab review examples/sample.py --config configs/baseline.yaml --allow-download --output reports/llm-review.json
codereviewlab evaluate --dataset data/dev.jsonl --config configs/baseline.yaml --allow-download --output reports/base-dev
python scripts/prompt_experiments.py --allow-download --output reports/prompts
codereviewlab evaluate --dataset data/test.jsonl --config configs/selected.yaml --output reports/base-test
codereviewlab train --config configs/lora-fixture.yaml --validate-only
codereviewlab train --config configs/lora-fixture.yaml --allow-download
codereviewlab train --config configs/lora.yaml --validate-only
codereviewlab train --config configs/lora.yaml --allow-download
codereviewlab evaluate --dataset data/test.jsonl --config configs/adapter.yaml --output reports/adapter-test
codereviewlab compare reports/base-test/metrics.json reports/adapter-test/metrics.json --output reports/comparison.md
```

`configs/lora.yaml` uses the separate author-generated `data/training.jsonl`: 48 examples in
12 training-only families, with reference cases verified in Docker. This small synthetic collection
is an experiment dataset, not evidence of general reviewing quality. The tiny fixture only verifies
the pipeline. The model cache is used offline unless `--allow-download` is explicitly given.
Select prompts only on development results before opening reserved test results.

To reproduce the training collection: `python scripts/build_training_data.py`.

## Validation status

See `docs/validation.md` for actually executed checks and exact environment. No real model
inference, fine-tuning, or improvement claims are included unless explicitly recorded there.
Mocked model tests validate contracts, not model quality. The controlled author-generated
benchmark does not establish performance on real repositories.

Real Qwen inference, three development prompt comparisons, fixture training, and 48-example LoRA
training have now completed. Both base and adapter processed all 36 reserved test examples, but
neither matched an expected bug (recall 0). LoRA reduced false-positive findings from 24 to 1.
That mostly reflects abstention, not demonstrated bug-detection effectiveness. The static
development baseline achieved precision 1.0 and recall 0.4286 on the controlled benchmark.
The final 28 tests passed on Windows and in Linux Python 3.11/3.12 CPU containers. GitHub-hosted
Actions has not run on GitHub; the equivalent checks were verified locally.

Actual [experiment results](docs/experiments.md) and
[base/adapter comparison](docs/results/real-comparison-v3.md) are included. Adapters are stored
locally in `checkpoints/fixture/adapter` and `checkpoints/lora/adapter`; weights/cache/checkpoints
are ignored by Git. `configs/selected.yaml` preserves the development-selected contextual prompt.

```sh
python -m pytest
python -m ruff check .
python -m build
```
