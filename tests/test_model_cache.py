import sys
import types
from pathlib import Path

from codereviewlab.config import ReviewConfig, TrainingConfig, load_config
from codereviewlab.llm import model_source
from codereviewlab.training import validate_training


def test_offline_model_source_uses_pinned_local_snapshot(monkeypatch):
    calls = []

    def snapshot_download(**kwargs):
        calls.append(kwargs)
        return "/local/snapshot"

    monkeypatch.setitem(
        sys.modules, "huggingface_hub", types.SimpleNamespace(snapshot_download=snapshot_download)
    )
    config = ReviewConfig(backend="llm")
    assert model_source(config) == "/local/snapshot"
    assert calls == [
        {"repo_id": config.model, "revision": config.revision, "local_files_only": True}
    ]
    config.allow_download = True
    assert model_source(config) == config.model
    assert len(calls) == 1


def test_full_training_collection_has_disjoint_reviewed_families(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(root)
    rows = validate_training(load_config(root / "configs/lora.yaml", TrainingConfig))
    assert len(rows) == 48
    assert len({r.family_id for r in rows}) == 12
    assert sum(r.buggy for r in rows) == 24
