#!/bin/sh
# Run the CI checks in a disposable Linux container with /input mounted read-only.
set -eu
mkdir /tmp/codereviewlab
cd /tmp/codereviewlab
cp /input/pyproject.toml /input/MANIFEST.in /input/README.md /input/LICENSE .
cp -r /input/src /input/tests /input/data /input/configs /input/docs /input/examples /input/scripts .
python -m pip install '.[dev]'
ruff check .
pytest
python -m build
python -m pip install --force-reinstall --no-deps dist/*.whl
cd /tmp
codereviewlab --help
codereviewlab doctor
python -c "import codereviewlab; assert 'site-packages' in codereviewlab.__file__"
echo "CPU checks and installed-wheel verification completed successfully."
