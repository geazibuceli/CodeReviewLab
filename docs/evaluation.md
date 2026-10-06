# Evaluation protocol

Matching version: `category-line-v1`, defined before any model evaluation.

Predictions are deduplicated by `(path, category, line)` in first-occurrence order. The last
explanation for an identical key is retained, without adding another scored prediction. Each
prediction matches at most one expected finding and each expected finding at most one prediction.
An exact match needs the same category and one of the accepted source lines. Finding schemas
first ensure the path and line belong to the input function. Other predictions are false positives.

Metrics:
- Finding precision: matched findings / deduplicated findings on successfully processed examples.
- Bug recall: matched findings / all expected findings, including failed examples in the denominator.
- Correct-function false-positive rate: successful correct examples with any prediction /
  successfully processed correct examples.
- Localization accuracy: exact matches / category-only one-to-one matches, ignoring line for
  the denominator. An audited override can affect this ratio; inspect the adjudication records.
- Valid-output rate and coverage: successfully processed examples / all examples. Extraction or
  schema-invalid datasets fail validation before evaluation; inference, parsing, and token-budget
  failures appear in individual rows.
- Mean latency: all attempted reviews, including failures and first-call loading. No throughput or
  cold/warm distinction is inferred. Peak GPU memory: maximum measured PyTorch allocation; this
  is not total device memory and does not capture all driver allocations.

Zero-denominator metrics are JSON null and Markdown `undefined`. Failures and coverage are
reported beside scores. Always inspect them: a low clean-function FPR with poor coverage is not
evidence of a safe reviewer. Recall here is finding recall; this benchmark has one expected bug
per buggy function, making it equivalent to bug-function recall for this dataset.

All examples use identical source inputs for static and LLM reviewers. Reports include dataset
SHA256, full configuration, matching version, metadata per example, and optional adjudication
SHA256. Raw model output is stored in `raw_response`, including failed generations, for diagnosis.
The initial review-v1 attempt predates that field and retains parsing diagnostics only.
Output parsing accepts strict JSON or one complete Markdown JSON fence; prose surrounding a
fence, invalid schemas, wrong paths, unsupported categories, and wrong lines remain failures.
No semantic values are repaired. The parser version and actual prompt versions are recorded.
Aggregate JSON and
per-example JSON are accompanied by a Markdown metric table and per-example statuses.

Manual adjudication takes an explicitly supplied JSON array:

```json
[
  {"example_id": "some-id", "prediction_index": 0, "expected_index": 0,
   "rationale": "Equivalent location confirmed against the contract", "reviewer": "reviewer-name"}
]
```

Indices refer to deduplicated predictions and expected findings in `examples.json`. Null
`expected_index` rejects a prediction. Overrides cannot fabricate extra expected findings or reuse
a target. Keep the original unadjudicated report and generate a separate output directory with
`--adjudications decisions.json`. Reviewing predictions before assigning labels may introduce bias;
publish both scores and the recorded rationales. No ambiguous finding is silently accepted.

`compare` requires identical data hash, matching version, adjudication hash, model revision,
prompt and parsing versions, token budgets, seed, and device. It compares recorded values,
not statistical significance.
The development prompt comparison script deliberately varies prompts with fixed generation
settings, reuses one loaded baseline, and never reads the reserved dataset.
