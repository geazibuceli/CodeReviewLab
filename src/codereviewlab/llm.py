"""Lazy local inference; model fetching requires explicit configuration."""

import hashlib
import re
import time
from pathlib import Path

from .prompts import PROMPT_VERSION, messages
from .schemas import InferenceMetadata, ReviewResult, StructuredResponse


def parse_response(response):
    """Accept JSON or one complete Markdown JSON envelope, without repairing its content."""
    text = response.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*\n(.*?)\n```", text, flags=re.DOTALL)
    return StructuredResponse.model_validate_json(fenced[1] if fenced else text)


def model_source(config):
    """Resolve cached revisions to local directories to prevent tokenizer metadata requests."""
    if config.allow_download:
        return config.model
    from huggingface_hub import snapshot_download

    return snapshot_download(repo_id=config.model, revision=config.revision, local_files_only=True)


def adapter_hash(path):
    digest = hashlib.sha256()
    files = sorted(p for p in Path(path).rglob("*") if p.is_file())
    if not files:
        raise ValueError("Adapter directory is empty or missing")
    for file in files:
        digest.update(str(file.relative_to(path)).encode())
        with file.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


class LLMReviewer:
    def __init__(self, config):
        self.config = config
        self.model = self.tokenizer = None
        self.adapter_digest = adapter_hash(config.adapter) if config.adapter else None

    def load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

        cfg = self.config
        set_seed(cfg.seed)
        device = "cuda" if cfg.device == "auto" and torch.cuda.is_available() else cfg.device
        if device == "auto":
            device = "cpu"
        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable")
        self.device = device
        options = {
            "revision": cfg.revision,
            "local_files_only": not cfg.allow_download,
            "trust_remote_code": False,
        }
        source = model_source(cfg)
        self.tokenizer = AutoTokenizer.from_pretrained(source, **options)
        self.model = AutoModelForCausalLM.from_pretrained(
            source,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            **options,
        ).to(device)
        if cfg.adapter:
            from peft import PeftModel

            self.model = PeftModel.from_pretrained(self.model, cfg.adapter, local_files_only=True)
        self.model.eval()

    def review(self, function):
        started = time.perf_counter()
        cfg = self.config
        metadata = InferenceMetadata(
            backend="llm",
            model=cfg.model,
            revision=cfg.revision,
            prompt_version=f"{PROMPT_VERSION}:{cfg.prompt}",
            adapter=cfg.adapter,
            adapter_hash=self.adapter_digest,
            device=cfg.device,
            generation={
                "do_sample": False,
                "max_new_tokens": cfg.max_new_tokens,
                "max_input_tokens": cfg.max_input_tokens,
                "seed": cfg.seed,
            },
        )
        status, error, findings, response = "ok", None, [], None
        try:
            import torch

            if self.model is None:
                self.load()
            metadata.device = self.device
            generation_config = getattr(self.model, "generation_config", None)
            if generation_config is not None:
                metadata.generation["model_defaults"] = generation_config.to_dict()
            encoded = self.tokenizer.apply_chat_template(
                messages(function, cfg.prompt),
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
                return_dict=True,
            ).to(self.device)
            length = encoded["input_ids"].shape[-1]
            context_limit = getattr(self.model.config, "max_position_embeddings", 32768)
            if length > cfg.max_input_tokens or length + cfg.max_new_tokens > context_limit:
                status = "input_error"
                raise ValueError("Function exceeds token budget; no truncation performed")
            if self.device == "cuda":
                torch.cuda.synchronize()
                torch.cuda.reset_peak_memory_stats()
            with torch.inference_mode():
                output = self.model.generate(
                    **encoded,
                    do_sample=False,
                    max_new_tokens=cfg.max_new_tokens,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            if self.device == "cuda":
                torch.cuda.synchronize()
                metadata.peak_gpu_memory_bytes = torch.cuda.max_memory_allocated()
            response = self.tokenizer.decode(output[0, length:], skip_special_tokens=True)
            status = "parse_error"
            parsed = parse_response(response)
            for finding in parsed.findings:
                if finding.path != function.path or not (
                    function.start_line <= finding.line <= function.end_line
                ):
                    raise ValueError("Model finding is outside the supplied function")
            findings = parsed.findings
            status = "ok"
        except Exception as exc:
            status = status if status != "ok" else "inference_error"
            error = f"{type(exc).__name__}: {exc}"
        metadata.latency_seconds = time.perf_counter() - started
        return ReviewResult(
            function=function,
            status=status,
            error=error,
            findings=findings,
            metadata=metadata,
            raw_response=response,
        )


def make_reviewer(config):
    if config.backend == "static":
        from .static import StaticReviewer

        return StaticReviewer()
    return LLMReviewer(config)
