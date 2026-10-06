"""Response-only LoRA training on a separate reviewed collection."""

import importlib.metadata
import json
from pathlib import Path

from .dataset import load_dataset, sha256, validate_collections
from .llm import model_source
from .prompts import messages
from .reports import json_text, write_artifacts


def training_target(example):
    return json.dumps(
        {
            "findings": [
                {
                    "path": example.function.path,
                    "line": finding.accepted_lines[0],
                    "category": finding.category.value,
                    "explanation": finding.explanation,
                    "suggested_fix": finding.suggested_fix,
                }
                for finding in example.expected_findings
            ]
        }
    )


def validate_training(config):
    training = load_dataset(config.dataset)
    evaluation = [example for path in config.evaluation_datasets for example in load_dataset(path)]
    validate_collections([*training, *evaluation])
    allowed = "fixture" if config.fixture_only else "train"
    if any(e.split != allowed or e.review_status != "author_reviewed" for e in training):
        raise ValueError(f"Training requires reviewed {allowed} examples")
    if {e.buggy for e in training} != {True, False}:
        raise ValueError("Training requires both buggy and correct examples")
    if any(e.split not in {"dev", "test"} for e in evaluation):
        raise ValueError("Evaluation collections must contain dev/test examples")
    train_families = {e.family_id for e in training}
    if train_families & {e.family_id for e in evaluation}:
        raise ValueError("Training and evaluation families overlap")
    # Catch renamed exact clones as well as labeled family overlap.
    import ast
    import textwrap

    def normalized(e):
        tree = ast.parse(textwrap.dedent(e.function.code))
        tree.body[0].name = "function"
        return ast.dump(tree, include_attributes=False)

    if {normalized(e) for e in training} & {normalized(e) for e in evaluation}:
        raise ValueError("Training and evaluation source overlaps")
    return training


def response_tokens(tokenizer, example, config):
    prompt_messages = messages(example.function, config.prompt)
    prompt_ids = tokenizer.apply_chat_template(
        prompt_messages, tokenize=True, add_generation_prompt=True
    )
    full_ids = tokenizer.apply_chat_template(
        [*prompt_messages, {"role": "assistant", "content": training_target(example)}],
        tokenize=True,
        add_generation_prompt=False,
    )
    if full_ids[: len(prompt_ids)] != prompt_ids:
        raise ValueError("Chat template prefix mismatch; cannot safely mask prompt tokens")
    if len(full_ids) > config.max_input_tokens:
        raise ValueError(f"Training example {example.id} exceeds token budget")
    return {
        "input_ids": full_ids,
        "attention_mask": [1] * len(full_ids),
        "labels": [-100] * len(prompt_ids) + full_ids[len(prompt_ids) :],
    }


class ResponseCollator:
    def __init__(self, pad_token_id):
        self.pad_token_id = pad_token_id

    def __call__(self, features):
        import torch

        length = max(len(f["input_ids"]) for f in features)
        return {
            key: torch.tensor([f[key] + [padding] * (length - len(f[key])) for f in features])
            for key, padding in (
                ("input_ids", self.pad_token_id),
                ("attention_mask", 0),
                ("labels", -100),
            )
        }


def train(config):
    examples = validate_training(config)
    output = Path(config.output_dir)
    if (output / "adapter").exists() or (output / "completed.json").exists():
        raise FileExistsError("Training already completed; choose a new output directory")
    if output.exists() and not config.resume_from_checkpoint:
        raise FileExistsError("Training output exists; use explicit checkpoint resume")
    if config.resume_from_checkpoint:
        checkpoint = Path(config.resume_from_checkpoint).resolve()
        if not checkpoint.is_dir() or not checkpoint.is_relative_to(output.resolve()):
            raise ValueError("Resume checkpoint must exist within the training output directory")
        previous = json.loads((output / "run.json").read_text(encoding="utf-8"))
        current = config.model_dump()
        current["resume_from_checkpoint"] = None
        if (
            previous["config"] != current
            or previous["dataset_sha256"] != sha256(config.dataset)
            or previous["evaluation_hashes"] != {p: sha256(p) for p in config.evaluation_datasets}
        ):
            raise ValueError("Resume configuration or dataset differs from original run")
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
    from trl import SFTConfig, SFTTrainer

    cfg = config.inference
    if cfg.adapter:
        raise ValueError("Training starts from the pinned baseline; use checkpoint resume")
    set_seed(cfg.seed)
    cuda = torch.cuda.is_available() and cfg.device != "cpu"
    if (config.qlora or cfg.device == "cuda") and not cuda:
        raise ValueError("Requested training mode requires CUDA")
    options = {
        "revision": cfg.revision,
        "local_files_only": not cfg.allow_download,
        "trust_remote_code": False,
    }
    source = model_source(cfg)
    tokenizer = AutoTokenizer.from_pretrained(source, **options)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    dataset = Dataset.from_list([response_tokens(tokenizer, e, cfg) for e in examples])
    quantization = (
        BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16
        )
        if config.qlora
        else None
    )
    model = AutoModelForCausalLM.from_pretrained(
        source,
        torch_dtype=torch.float16 if cuda else torch.float32,
        quantization_config=quantization,
        device_map="auto" if config.qlora else None,
        **options,
    )
    if not config.qlora:
        model.to("cuda" if cuda else "cpu")
    model.config.use_cache = False
    args = SFTConfig(
        output_dir=str(output),
        num_train_epochs=config.epochs,
        learning_rate=config.learning_rate,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        seed=cfg.seed,
        data_seed=cfg.seed,
        fp16=cuda,
        use_cpu=not cuda,
        save_strategy="steps",
        save_steps=10,
        logging_steps=1,
        report_to="none",
        max_seq_length=cfg.max_input_tokens,
        packing=False,
        dataset_kwargs={"skip_prepare_dataset": True},
        remove_unused_columns=False,
    )
    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=dataset,
        processing_class=tokenizer,
        data_collator=ResponseCollator(tokenizer.pad_token_id),
        peft_config=LoraConfig(
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        ),
    )
    output.mkdir(parents=True, exist_ok=True)
    if not config.resume_from_checkpoint:
        write_artifacts(
            {
                output / "run.json": json_text(
                    {
                        "config": config.model_dump(),
                        "dataset_sha256": sha256(config.dataset),
                        "evaluation_hashes": {p: sha256(p) for p in config.evaluation_datasets},
                        "fixture_only": config.fixture_only,
                        "status": "started",
                        "versions": {
                            name: importlib.metadata.version(name)
                            for name in ["torch", "transformers", "peft", "trl", "datasets"]
                        },
                    }
                )
            }
        )
    result = trainer.train(resume_from_checkpoint=config.resume_from_checkpoint)
    adapter = output / "adapter"
    if adapter.exists():
        raise FileExistsError("Final adapter already exists")
    trainer.save_model(str(adapter))
    tokenizer.save_pretrained(str(adapter))
    write_artifacts({output / "completed.json": json_text(result.metrics)})
