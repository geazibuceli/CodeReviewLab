# Operations and release readiness

This document captures the operational expectations for shipping and maintaining CodeReviewLab as a
local research and review tool. It complements the architecture and validation notes and should be
used as the operational baseline for ongoing maintenance.

## Production readiness checklist

The project is in a good maintenance baseline when all of the following are true:

- Python environment is reproducible and documented.
- Core CLI commands run without model downloads.
- Static review and dataset validation work without optional ML dependencies.
- All benchmark and training contracts are checked before metrics are reported.
- Output artifacts are written to new paths and documented in the report.
- CI and local validation pass with the same commands used in development.
- User-facing copy remains in English.
- Any model-quality claim is explicitly tied to recorded benchmark evidence.

## Local environment expectations

Use a dedicated virtual environment for development work:

```sh
python -m venv .venv
. .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

Additional optional dependencies are intentionally separated so that ordinary review and validation
still work without a full ML stack:

```sh
python -m pip install -e ".[inference]"
python -m pip install -e ".[training]"
```

## Standard validation commands

These are the commands expected before merging or releasing:

```sh
ruff check .
pytest --cov=src/codereviewlab --cov-report=term-missing --cov-fail-under=75
python -m build
python -m pre_commit run --all-files
```

For CLI-level verification, use the project entry point directly:

```sh
codereviewlab --help
codereviewlab doctor
codereviewlab review examples/sample.py --output reports/review.json
```

## GitHub and release workflow expectations

- CI should validate lint, tests, coverage, and build steps.
- Release tags should be created only after the validation checklist passes.
- Release notes should include the exact benchmark status and any known limitations.
- Generated artifacts should be kept in clearly named report directories and not silently overwritten.

The release workflow should be considered an enforcement layer, not a guarantee of real-world quality.

## Artifact and data governance

- `reports/` contains generated output and should be treated as ephemeral evidence.
- `checkpoints/` stores local model and adapter states; it is intentionally not tracked by Git.
- `data/` holds benchmark and training collections; any change should be reviewed with validation rules.
- Benchmark results should always be tied to their corresponding config and data hash in the report metadata.

## Incident and rollback expectations

If an evaluation or training command fails:

1. Check whether the issue is configuration-related, dataset-related, or dependency-related.
2. Re-run the smallest relevant validation command.
3. Confirm that the model was not implicitly downloaded without explicit opt-in.
4. Preserve the report artifacts and recorded config for debugging.
5. Do not claim performance gains unless the exact run and dataset are documented.

## Safe usage policy

CodeReviewLab is a review aid, not an autonomous repair or enforcement agent. It is appropriate for:

- local code inspection
- benchmark-driven experiments
- human-led review workflows
- explicit research and documentation work

It is not appropriate for:

- unsupervised production execution
- automatic patching of arbitrary repositories
- representative claims of general-purpose code review quality across all software

## Documentation maintenance

When the project changes, update the relevant docs in the same patch:

- README for usage and scope
- docs/architecture.md for design changes
- docs/limitations.md for newly discovered constraints
- docs/validation.md for validation results and exact environment details
- release notes for benchmark changes or policy changes

This keeps the project honest, auditable, and maintainable as it grows.
