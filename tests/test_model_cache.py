import sys
import types
from pathlib import Path

import pytest

from codereviewlab.config import ReviewConfig, TrainingConfig, load_config
from codereviewlab.llm import adapter_hash, model_source
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


def test_adapter_hash_and_training_validation_reject_invalid_contracts(tmp_path):
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(ValueError, match="empty or missing"):
        adapter_hash(tmp_path)

    training_rows = load_config(root / "configs/lora-fixture.yaml", TrainingConfig)
    rows = validate_training(training_rows)
    wrong_split = [row.model_copy(update={"split": "dev"}) for row in rows[:2]]
    train_path = tmp_path / "bad-training.jsonl"
    train_path.write_text(
        "\n".join(row.model_dump_json() for row in wrong_split) + "\n", encoding="utf-8"
    )
    cfg = TrainingConfig(
        dataset=str(train_path),
        evaluation_datasets=[str(root / "data/dev.jsonl")],
        output_dir=str(tmp_path / "out"),
        fixture_only=True,
    )
    with pytest.raises(ValueError, match="Training requires reviewed fixture"):
        validate_training(cfg)

    base = rows[0]
    shared = [
        base.model_copy(
            update={
                "id": "eval-row-1",
                "split": "fixture",
                "buggy": False,
                "expected_findings": [],
                "function": base.function.model_copy(
                    update={
                        "name": "shared_family_one",
                        "start_line": 1,
                        "end_line": 2,
                        "code": "def shared_family_one():\n    return 1",
                    }
                ),
            }
        ),
        base.model_copy(
            update={
                "id": "eval-row-2",
                "split": "dev",
                "buggy": False,
                "expected_findings": [],
                "function": base.function.model_copy(
                    update={
                        "name": "shared_family_two",
                        "start_line": 1,
                        "end_line": 2,
                        "code": "def shared_family_two():\n    return 2",
                    }
                ),
            }
        ),
    ]
    evaluation_path = tmp_path / "overlap-eval.jsonl"
    evaluation_path.write_text(
        "\n".join(row.model_dump_json() for row in shared) + "\n", encoding="utf-8"
    )
    cfg = TrainingConfig(
        dataset=str(root / "data/training-fixture.jsonl"),
        evaluation_datasets=[str(evaluation_path)],
        output_dir=str(tmp_path / "out"),
        fixture_only=True,
    )
    with pytest.raises(
        ValueError, match="Family crosses splits|Training and evaluation families overlap"
    ):
        validate_training(cfg)
