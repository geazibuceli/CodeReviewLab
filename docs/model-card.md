# Baseline model card

Default: `Qwen/Qwen2.5-Coder-1.5B-Instruct`.
Pinned revision: `2e1fd397ee46e1388853d2af2c993145b0f1098a`.
License: Apache 2.0, verified against the publisher's model card. Model provenance belongs to
Qwen; CodeReviewLab makes no claims about its pretraining examples.

Sources:
- [Publisher model card](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct)
- [License at the pinned revision](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct/blob/2e1fd397ee46e1388853d2af2c993145b0f1098a/LICENSE)
- [TRL v0.15.2 trainer implementation](https://github.com/huggingface/trl/blob/v0.15.2/trl/trainer/sft_trainer.py)

The hardware inspection found NVIDIA RTX 5080, 16,303 MiB reported by nvidia-smi, with PyTorch
CUDA available. A 1.54B code instruction model was selected as a modest baseline rather than
assuming that the largest model fitting nominal VRAM is suitable. Memory, latency, quality, and
training capacity must still be measured in actual runs. CPU fallback uses float32; CUDA inference
uses float16. The published context window is 32,768 tokens, while this project defaults to a
4,096-token input cap and 512 new tokens. Token budget overflow is a recorded input failure.

Default generation is greedy (`do_sample=false`) with seed 42. GPU kernels and library versions
can still introduce numerical differences. Generation metadata includes model, immutable
revision, prompt version, settings, device, wall time, adapter hash, and peak CUDA allocation when
available. First-example timing includes cold loading; subsequent timings use the loaded model.

No model download happens during package installation or help. Loading uses local cache unless
explicitly allowed. Remote Python code is disabled. Optional local adapters are hashed, and their
exact training provenance should accompany comparisons. Inference does not guarantee structured
JSON, calibrated confidence, correctness, or resistance to instructions embedded in code.

LoRA trains attention projections via PEFT and TRL SFTTrainer. Pretokenized inputs carry `-100`
labels for every prompt token; the collator also masks padding. Template prefix mismatches and
long examples fail rather than silently masking the wrong tokens or truncating. Optional NF4
QLoRA requires compatible CUDA/bitsandbytes support. Real inference was exercised on Windows
and Python 3.14 using the versions in [ml-runtime.json](results/ml-runtime.json). This validates
that concrete environment rather than every optional dependency combination. QLoRA remains
unverified. Python 3.11/3.12 on Linux remains an alternative for training setup.

Actual model and adapter execution status is in `validation.md`; no improvement is claimed.
