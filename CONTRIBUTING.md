# Contributing

Contributions are welcome. Please keep all user-facing text in English and follow the existing
project conventions.

## Local setup

```sh
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Quality checks

Before opening a pull request, run:

```sh
ruff check .
pytest --cov=src/codereviewlab --cov-report=term-missing --cov-fail-under=75
python -m build
python -m pre_commit run --all-files
```

## Pull request expectations

- Keep the scope narrow and focused.
- Prefer small, reviewable changes.
- Ensure the command output is clean and the tests still pass.
- Update documentation when behavior or setup changes.

## Release flow

- Create a tag such as `v0.1.1`.
- Push the tag to GitHub.
- The release workflow builds the package and uploads the artifacts to the corresponding GitHub
  release.
