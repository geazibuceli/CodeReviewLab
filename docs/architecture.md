# Architecture

CodeReviewLab is one Python package with a synchronous CLI. No server, frontend, code execution
agent, or external review service is involved.

```text
Python file / verified post-image diff
  -> extraction.FunctionInput
  -> StaticReviewer or lazy LLMReviewer
  -> Pydantic ReviewResult + InferenceMetadata
  -> JSON + Markdown

Validated JSONL examples -> same reviewer -> exact matching -> metrics + per-example report
Separate reviewed training JSONL -> response-token masking -> TRL SFTTrainer + PEFT LoRA
```

`schemas.py` owns contracts; `extraction.py` owns line mapping and diff verification; `static.py`
owns three narrow syntactic rules. `config.py`, `prompts.py`, and `llm.py` configure local inference.
`dataset.py` validates collections without executing them. `evaluation.py` implements matching
and audited overrides. `training.py` prepares response-only loss and checkpoint provenance.
`reports.py` uses exclusive file creation and removes only artifacts it created if a write fails.

Extraction uses AST boundaries including decorators. Original indentation and file lines are
retained; the static reviewer dedents a function before parsing, then offsets its findings.
Nested functions are extracted separately; static checks skip nested scopes in the outer review.
Imports are bounded to 4,000 characters as optional context. Functions longer than 200 lines are
rejected with a report issue; inference additionally checks the complete chat token budget.

Diff review verifies all available post-image context and added lines, including hunk counts,
against files under the resolved repository root. Missing files, unsafe paths, unsupported inputs,
and mismatches produce issues. Pure deletions select the adjacent surviving line. Deleted files
cannot be reviewed. Quoted Git paths, renames without hunks, binary patches, and diff-only
reconstruction are not supported. A diff is not proof of the repository's complete Git history.

Imports of PyTorch, Transformers, PEFT, datasets, and TRL are lazy. Ordinary installation, static
review, dataset validation, CLI help, and training-data validation require no model dependencies.
`doctor` imports installed PyTorch solely to query actual CUDA availability.

Review never executes input code. Source comments and strings are untrusted data. The LLM uses
the tokenizer's chat template, greedy decoding, a pinned revision, and no remote model code.
Strict JSON parsing failures differ from successful empty findings. The prompt is not a guarantee
against hallucination or prompt injection; findings still need human verification.
