# Experiment ledger

Real pretrained inference and development prompt experiments were executed on October 6, 2026.
The four-example fixture also completed real LoRA training. These experiments expose weak model
performance and do not establish usefulness on real repositories.

| Experiment | Inputs | Status |
| --- | --- | --- |
| Static baseline | Controlled development examples | See validation.md |
| Basic instruction baseline | 84 development examples | Completed, review-v3 |
| Few-shot prompt | 84 development examples | Completed; no findings returned |
| Contextual prompt | 84 development examples | Completed; selected by development F1 |
| Selected prompt | 36 reserved test examples | Base and adapter completed |
| Tiny LoRA fixture | Four fixture examples | Completed, four optimizer steps |
| Reviewed-data LoRA | 48 separate author-generated training examples | Completed, six optimizer steps |
| Base vs adapter | Same reserved examples and settings | Completed; both have recall 0 |

## Development results

| Prompt | Precision | Recall | F1 selection score | Failures |
| --- | --- | --- | --- | --- |
| Basic | 0.028986 | 0.047619 | 0.036036 | 4/84 |
| Few-shot | Undefined | 0 | 0 | 0/84 |
| Contextual | 0.06 | 0.071429 | 0.065217 | 6/84 |

The pre-recorded [selection protocol](results/prompt-selection-protocol.md) chose contextual;
[selection.json](results/prompt-selection.json) freezes the choice before reserved testing.
All prompts used review-v3, greedy decoding, the pinned model revision, seed 42, and identical
4,096/512 input/output budgets. The model's inherited repetition penalty was 1.1. Sampling-only
temperature/top-p/top-k defaults were ignored by greedy decoding. New reports preserve the full
model generation defaults in addition to the explicitly overridden settings. Contextual still
has poor precision, low recall, and six failed outputs. The few-shot result is schema-valid
abstention on every example, not evidence of correctness.

Full aggregate, raw per-example responses, and Markdown reports are preserved under
[prompts-v3](results/prompts-v3/comparison.md). Scores match category and accepted source line;
they do not judge explanatory correctness. Inspection found misleading explanations even among
location/category matches. No manual adjudication or independent semantic review was applied.

The selected base model processed all 36 reserved examples with zero matched findings and
24 false positives (precision 0, recall 0, correct-function FPR 13/18). No prompt or training
hyperparameter was changed in response to these reserved results. The four-row fixture completed
four optimizer steps in 15.4805 measured training seconds with mean training loss
0.5936920549720526; fixture loss is not a review quality measure.

## Reserved comparison and training

The 48-example, one-epoch LoRA run completed six optimizer steps in 20.0947 measured training
seconds, with mean training loss 0.9374366104602814. The learning rate was 0.0002, batch size 1,
gradient accumulation 8, rank 8, alpha 16, and seed 42. These settings were fixed before reserved
evaluation; no subsequent tuning or repeated prompt selection used the reserved scores.

| Metric | Selected base | LoRA adapter |
| --- | --- | --- |
| Processed / examples | 36 / 36 | 36 / 36 |
| Matched findings | 0 | 0 |
| False-positive findings | 24 | 1 |
| Precision | 0 | 0 |
| Recall | 0 | 0 |
| Correct-function FPR | 13/18 (72.22%) | 1/18 (5.56%) |
| Valid-output rate | 100% | 100% |
| Mean attempted-review latency | 1.9800 s | 0.8172 s |
| Peak PyTorch GPU allocation | 3,149,723,648 bytes | 3,158,439,936 bytes |

The adapter mostly abstained. It reduced false positives in this controlled run but detected
none of the expected reserved bugs, so no improvement in bug detection or overall usefulness
is demonstrated. Timing includes cold loading and is not a controlled latency benchmark.
Both runs had identical generation settings, data hash, prompt/parsing/matching versions, and
device; the base and adapter ran sequentially, not concurrently. Full results:
[base](results/real-base-test-v3/report.md), [adapter](results/real-adapter-test-v3/report.md),
[comparison](results/real-comparison-v3.md), and [training manifests](results/training/lora/run.json).
The adapters remain local under `checkpoints/`; no model was published.

Initial sample runs using review-v1 and review-v2 were preserved as diagnostic attempts. They
revealed Markdown envelopes, incorrect category spelling, and Windows path separator mismatch.
The implementation now accepts only an exact JSON fence, records raw responses, uses POSIX
file-path separators, and resolves cached model revisions to local directories to avoid an
unwanted tokenizer metadata network request. Review-v3 was frozen before the development sweep.
The first fixture attempt failed because datasets 3.6.0/dill 0.3.8 was incompatible with Python
3.14's pickler; datasets 4.8.5/dill 0.4.1 resolved it. Python 3.14 training dependencies now have
corresponding minimum version constraints. See [runtime versions](results/ml-runtime.json).

Protocol: fix generation settings; run basic, few-shot, and contextual prompts on development
only; inspect precision/recall with coverage; record the chosen prompt and selection rationale
in a new experiment entry; then freeze that choice and evaluate reserved test once. Copy the same
prompt setting into `configs/adapter.yaml` before comparing an adapter. Imports context is absent
from most controlled benchmark examples, so contextual gains here may be small or uninformative.
No results should be inferred from mock tests or static scores.

```sh
python scripts/prompt_experiments.py --allow-download --output reports/prompts
codereviewlab evaluate --dataset data/test.jsonl --config configs/selected.yaml --output reports/base-test
codereviewlab train --config configs/lora-fixture.yaml --allow-download
codereviewlab train --config configs/lora.yaml --allow-download
codereviewlab evaluate --dataset data/test.jsonl --config configs/adapter.yaml --output reports/adapter-test
codereviewlab compare reports/base-test/metrics.json reports/adapter-test/metrics.json --output reports/comparison.md
```

The supplied training collection is separate and author-generated, with 24 buggy and 24 correct
examples and 12 training-only families. Its reference cases passed Docker validation. Its MIT
license, selection, and authoring review procedure are described in the dataset card. No external
source, independent annotation, or sufficiency for real-world quality is claimed.
Training manifests include configuration, dataset and evaluation hashes, immutable model
revision, software versions, and seed. `run.json` means started, not completed;
`completed.json` is written only after successful training and adapter saving. Set
`resume_from_checkpoint` to an existing checkpoint inside the same output directory; the
configuration and all data hashes must match. Other existing outputs are protected.
