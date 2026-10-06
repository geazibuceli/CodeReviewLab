# Executed validation

Date: October 6, 2026. Host: Windows 11, Python 3.14.0. Development environment: project-local
`.venv`. Core dependency versions: Pydantic 2.13.5, Typer 0.27.2, PyYAML 6.0.3, pytest 9.1.1,
Ruff 0.16.10, build 1.6.1. Isolated builds used setuptools 84.0.0 and wheel 0.48.0.

## Initial core checks

- 24 pytest cases passed, covering extraction, decorators, methods/async/nested scopes, original
  line mapping, syntax/size errors, AST rules and counterexamples, verified/mismatched/missing
  diff context, multiple hunks, deletion-only hunks, unsafe paths, schemas, matching, deduplication,
  adjudication, split integrity, input label separation, failure denominators, CLI exit codes/help,
  overwrite protection, training validation, template-prefix masking, and token overflow.
- Ruff lint passed; all 20 Python source/test/script/example files passed format checking.
- Both sdist and wheel built successfully, including a wheel built from the sdist.
- Installed the non-editable wheel into `.venv`, changed to a newly created temporary directory
  outside the checkout, confirmed imports came from `site-packages`, and ran the installed
  `codereviewlab --help`, `doctor`, and `review sample.py`. Review produced JSON and Markdown.
  Optional torch, transformers, peft, and trl were absent in that environment; help and static
  review worked without them and without any model download.
- Dataset validation passed: 120 rows, 30 families, 60 buggy and 60 correct. Dataset/fixture
  reproduction accepted identical existing content. Training fixture validation passed: four rows.
- Static development evaluation processed 84/84 rows, with 18 matched findings, zero false
  positives, 42 expected bugs: precision 1.0, recall 0.42857142857142855, correct-function FPR 0,
  localization 1.0, valid-output rate 1.0. These are narrow controlled-benchmark results, not
  real-repository claims. The measured mean wall time was about 0.00002339 seconds per function;
  this is one small run without a latency benchmark protocol.
- A CLI LLM review attempted without optional dependencies recorded three `inference_error`
  results with missing PyTorch diagnostics, not successful empty findings. No model ran.
- `git diff --check` reported no issues. The initial project snapshot was uncommitted.

Recorded static aggregate: [metrics.json](results/static-dev/metrics.json) and
[Markdown report](results/static-dev/report.md). Full local per-example results are in
`reports/static-dev/examples.json`. Dataset SHA256:
`f4007402ebb2aaa5c552d1996c44f18b7e3446eaf5e4e67d4e9a94a7f8f00494`.

Sandbox restrictions initially prevented pytest temporary-directory setup. The complete suite
was rerun outside that sandbox and passed. These permission failures were not ignored as passes.
GitHub Actions is configured for Python 3.11/3.12 CPU checks; it has not been executed on GitHub.

## Model and execution status

During the initial core checks, no model weights were downloaded and no inference or training
completed. Subsequent real runs are recorded below.
The model's Apache 2.0 license was checked in its publisher card and its immutable revision was
retrieved from Hugging Face metadata. Global host PyTorch 2.14.0+cu130 recognized the RTX 5080;
the isolated core environment deliberately contains no inference stack. Hardware discovery is
not inference validation. Mocked model tests verify contracts only.

The initial reference execution attempt was blocked by the unavailable Docker Linux daemon.
On October 6, 2026, Docker Desktop was started and the reference workflow completed successfully:
all 120 benchmark examples agreed with their labels. Correct examples satisfied their reference
expectations, and buggy examples exposed a discrepancy or exception. This validates the supplied
reference cases, not every possible input or real-repository performance.

This reference run checked 120 reference cases containing 160 calls. The executed benchmark
SHA256 was `e8a563543d74530692b771504e166d93aa412f6a734d9d2e1336b46a7acdf26e`;
this identifies the current file separately from the earlier static evaluation dataset hash.

The run used the immutable image
`python@sha256:0dd364ba7e10242f07755449e3a3d0e35f9efd987952737b90def6709ab0c5ce`,
with network disabled, a read-only filesystem and mounts, 256 MB memory, one CPU, a PID limit,
dropped capabilities, a non-root user, and a 60-second timeout. The command exited with code 0
and printed `All reference cases agree with labels`.

```sh
python scripts/run_references.py data/benchmark.jsonl --image python@sha256:0dd364ba7e10242f07755449e3a3d0e35f9efd987952737b90def6709ab0c5ce
```

No reference code was executed directly on the host. The separate 48-example training collection
also passed isolated Docker reference checks before training.

## Subsequent real ML and CPU runs

- Final pytest suite: 28 passed on Windows Python 3.14, Linux Python 3.11.17, and Linux Python
  3.12.15. Linux runs used disposable Docker containers with the checkout mounted read-only.
  Both Linux jobs also passed Ruff, built wheel/sdist, installed the wheel, and verified help,
  doctor, and `site-packages` imports outside the checkout. The GitHub-hosted workflow itself
  remains unexecuted; equivalent checks were verified locally without publishing the repository.
- A project `.venv-ml` with system-site access reused the existing CUDA-enabled PyTorch. The
  pinned Qwen weights were explicitly downloaded into `.cache/huggingface`. Runtime versions
  are preserved in [ml-runtime.json](results/ml-runtime.json).
- Actual sample review attempts exposed fenced JSON, unsupported category spelling, path
  mismatch, and an unwanted offline tokenizer metadata request. The implementation now handles
  an exact JSON fence without repairing content, stores raw responses, emits POSIX source paths,
  and resolves cached revisions to local directories. Diagnostic attempts remain archived.
- Three development prompt experiments processed the same 84 examples. Contextual was selected
  by the pre-recorded F1 protocol. Results and the selection rationale are in `experiments.md`.
- The initial fixture attempt failed with datasets 3.6.0/dill 0.3.8 on Python 3.14. Updating to
  datasets 4.8.5/dill 0.4.1 resolved it; corresponding Python 3.14 minimum dependency constraints
  are now included. The four-row fixture completed four real optimizer steps and saved an adapter.
- Separate training data: 48 author-generated/reviewed rows, 24 buggy/24 correct, 12 families;
  family and exact/renamed-source overlap checks against dev/test passed. Docker verified the
  reference cases. Data hash: `b18c429e71e6b2d139c27639a223c1e304ab4ebc6600c26f95900a4a615553de`.
  The full LoRA run completed one epoch and six optimizer steps and saved its adapter.
- Base and adapter evaluations each processed all 36 reserved examples with no processing
  failures. Both had zero matched findings and recall zero. False-positive findings decreased
  from 24 to 1; correct-function FPR decreased from 72.22% to 5.56%. This largely reflects
  abstention and does not demonstrate useful bug detection. Comparison settings were identical.

Actual model results, raw responses, manifests, hashes, and comparison artifacts are preserved
under `docs/results/`. Base peak GPU allocation was 3,149,723,648 bytes; adapter peak allocation
was 3,158,439,936 bytes. Training runtime/loss are recorded in the completed manifests, not
presented as review quality metrics. QLoRA, checkpoint resume execution, external-data training,
and independent semantic adjudication remain unverified. No quality claim is inferred from mocks.

## Reproduction commands

Use a Python 3.11/3.12 environment compatible with the optional training stack. From the checkout:

```sh
python -m pip install -e ".[training]"
codereviewlab doctor
codereviewlab review examples/sample.py --config configs/baseline.yaml --allow-download --output reports/real-llm-review.json
codereviewlab evaluate --dataset data/dev.jsonl --config configs/baseline.yaml --allow-download --output reports/real-base-dev
python scripts/prompt_experiments.py --output reports/real-prompts
codereviewlab train --config configs/lora-fixture.yaml --validate-only
codereviewlab train --config configs/lora-fixture.yaml --allow-download
```

The fixture command checks the real pipeline only. The supplied separate training collection
allows reproducing the completed LoRA experiment. To repeat it, choose a fresh output directory
in a copied configuration; completed checkpoints are protected from overwrite. Then run:

```sh
codereviewlab train --config configs/lora.yaml --validate-only
codereviewlab train --config configs/lora.yaml --allow-download
codereviewlab evaluate --dataset data/test.jsonl --config configs/selected.yaml --output reports/real-base-test
codereviewlab evaluate --dataset data/test.jsonl --config configs/adapter.yaml --output reports/real-adapter-test
codereviewlab compare reports/real-base-test/metrics.json reports/real-adapter-test/metrics.json --output reports/real-comparison.md
```

The contextual development choice is frozen in selected and adapter configs. Reserved data
has now been evaluated; further tuning needs a fresh held-out set. Include failures, coverage,
versions, hashes, and actual measurements in the experiment
ledger. Optional QLoRA requires installing `.[qlora]` and setting `qlora: true` in a new training
configuration. It remains unverified on this host.
