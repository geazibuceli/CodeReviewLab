"""Versioned inference and training configuration."""

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, model_validator

from .schemas import StrictModel

MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
REVISION = "2e1fd397ee46e1388853d2af2c993145b0f1098a"


class ReviewConfig(StrictModel):
    backend: Literal["static", "llm"] = "static"
    model: str = MODEL
    revision: str = REVISION
    prompt: Literal["basic", "few-shot", "contextual"] = "basic"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    max_input_tokens: int = Field(default=4096, ge=64)
    max_new_tokens: int = Field(default=512, ge=1)
    seed: int = 42
    adapter: str | None = None
    allow_download: bool = False

    @model_validator(mode="after")
    def pinned_revision(self):
        if not re.fullmatch(r"[0-9a-f]{40}", self.revision):
            raise ValueError("revision must be an immutable 40-character commit SHA")
        return self


class TrainingConfig(StrictModel):
    inference: ReviewConfig = Field(default_factory=lambda: ReviewConfig(backend="llm"))
    dataset: str
    evaluation_datasets: list[str] = Field(min_length=1)
    output_dir: str
    fixture_only: bool = False
    qlora: bool = False
    epochs: float = Field(default=1, gt=0)
    learning_rate: float = Field(default=0.0002, gt=0)
    batch_size: int = Field(default=1, ge=1)
    gradient_accumulation_steps: int = Field(default=8, ge=1)
    lora_r: int = Field(default=8, ge=1)
    lora_alpha: int = Field(default=16, ge=1)
    resume_from_checkpoint: str | None = None


def load_config(path: Path | None, schema=ReviewConfig):
    return (
        schema.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        if (path is not None)
        else schema()
    )
