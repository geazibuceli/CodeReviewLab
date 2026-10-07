# Architecture

CodeReviewLab is a synchronous Python CLI and evaluation toolkit. It has no web service, no
remote review backend, and no code execution environment for user-provided source. The project is
built around a controlled and auditable pipeline: extract code, validate contracts, run a narrow
static review or optional local model review, and report results as structured artifacts.

## Design principles

1. Explicit scope
   - The static reviewer covers a few rule-based patterns and no broader semantic reasoning.
   - The LLM path is optional and resolves to local execution only.

2. Human validation remains mandatory
   - Findings are suggestions, not proof of a defect.
   - Output is intended to support review, not replace it.

3. Reproducibility over novelty
   - Configs are versioned and validated.
   - Dataset and benchmark contracts are explicit.
   - Artifacts are recorded for later comparison and auditing.

4. Safety over convenience
   - No model downloads unless explicitly requested.
   - Unsafe or unsupported diff inputs fail with an error instead of guessing.
   - Output files are protected from accidental overwrite.

## System boundaries

```text
Source file / patch
        |
        v
Extraction layer
  - AST boundary detection
  - source line mapping
  - diff verification against repository files
        |
        v
Validation layer
  - strict Pydantic schemas
  - dataset family/split checks
  - config validation
        |
        +----> Static review
        |          - mutable defaults
        |          - empty/identity comparisons
        |          - range(len(items)+1) loops
        |
        +----> Optional LLM review
                   - local model prompt + JSON parsing
                   - no remote inference
```

## Component map

### `src/codereviewlab/cli.py`
The CLI is the public entry point and owns exit semantics. It validates command arguments, loads the
selected config, invokes extraction or evaluation logic, and reports the result to stdout/stderr.

### `src/codereviewlab/extraction.py`
This layer owns source extraction, function boundaries, and post-image diff verification. It keeps
source line numbers, preserves original indentation, and rejects unsupported cases such as binary or
rename-only diffs.

### `src/codereviewlab/static.py`
The static review engine keeps a deliberately narrow rule set. It parses Python source with the AST,
finds candidate patterns, and emits review results with source locations. It does not resolve full
execution semantics or prove reachability.

### `src/codereviewlab/llm.py`
This is the local inference layer. It builds prompts, configures the model path, parses JSON output,
and returns structured review results. It remains lazy-imported so ordinary static and dataset checks
work without installing weights.

### `src/codereviewlab/config.py`
All config is validated through Pydantic models. Model revision hashes are enforced, and config files
must remain explicit about model selection, token limits, and download permissions.

### `src/codereviewlab/dataset.py`
Dataset validation is intentionally strict. It checks schema validity, duplication, family/split
consistency, and benchmark integrity without executing any example data.

### `src/codereviewlab/evaluation.py`
This module runs benchmark scoring, compares predicted findings to expected ones, and records explicit
metrics and failures. It does not assume the benchmark is representative of real-world repositories.

### `src/codereviewlab/training.py`
Training logic is limited to response-only supervision and LoRA/QLoRA setup. The implementation is
configuration-driven and records provenance, but does not claim general-quality gains from a tiny
synthetic dataset.

### `src/codereviewlab/reports.py`
Artifact writing is centralized so output paths are protected from accidental overwrite and rollback
happens cleanly on write failure.

### `src/codereviewlab/schemas.py`
This is the contract boundary. All major result, dataset, and config objects pass through strict Pydantic
models to keep serialization predictable and the validation story explicit.

## Data flow

### Normal review flow

```text
source file
  -> extraction.extract_file
  -> static review or local LLM review
  -> ReviewResult objects
  -> JSON/Markdown report written to output path
```

### Diff review flow

```text
git diff
  -> changed_functions
  -> verify hunk context, repo-root paths, and available files
  -> extraction of changed functions only
  -> static or LLM review
  -> report with issue summary and function-level results
```

### Benchmark flow

```text
JSONL dataset
  -> load_dataset + validate_collections
  -> run reviewer per example
  -> match predictions to expected findings
  -> metrics + failures + per-example report
```

## Key invariants

- The project does not execute user code.
- Review results are always untrusted until a human checks them.
- Static rules are intentionally narrow and explainable.
- All model and training operations are explicit opt-in.
- All benchmark and evaluation artifacts are recorded with their relevant config metadata.
- The config contract requires pinned commit hashes for model revisions.

## Failure modes and guardrails

- Unsupported or malformed diffs fail clearly instead of silently producing misleading output.
- Overlong functions are rejected rather than being partially evaluated.
- Broken or mismatched dataset records fail validation before metrics are computed.
- Invalid JSON from the model is treated as a structured failure, not as a plausible review result.
- Optional dependencies are lazy-loaded so ordinary operations remain usable without heavyweight ML stacks.

## Extension points

The code is structured to support clean extension without expanding the support contract too far:

- add new static rules in `static.py`
- add new dataset validation rules in `dataset.py`
- add new config fields in `config.py`
- add new report formats in `reports.py`
- add new evaluation metrics in `evaluation.py`
- add new prompt variants in `prompts.py` or the config model

The project remains intentionally conservative: new features should preserve the current safety and
auditability guarantees, even when model capability increases.
