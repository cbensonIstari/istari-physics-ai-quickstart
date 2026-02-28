#!/usr/bin/env python3
"""Istari function runner for @istari:train_nemo_surrogate (scaffold).

This scaffold is intentionally beginner-friendly:
- It can run a small baseline surrogate fit on macOS/CPU.
- It produces Istari artifacts so end-to-end integration can be validated.
- It is not a full PhysicsNeMo implementation yet.

Contract:
    python3 train_nemo_surrogate.py <input.json> <output.json> <temp_dir>
"""

from __future__ import annotations

import csv
import json
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


DEFAULT_CONFIG = {
    "backend": "baseline_mlp",
    "target_column": "target",
    "val_split": 0.2,
    "random_seed": 42,
    "ridge_lambda": 1e-6,
}


@dataclass
class Dataset:
    features: np.ndarray
    targets: np.ndarray
    feature_names: list[str]
    source: str


def unwrap(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


def read_input(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {k: unwrap(v) for k, v in payload.items()}


def parse_training_config(raw: Any) -> dict[str, Any]:
    if raw is None:
        cfg = {}
    elif isinstance(raw, dict):
        cfg = raw
    elif isinstance(raw, str):
        text = raw.strip()
        cfg = {} if not text else json.loads(text)
    else:
        raise ValueError("training_config must be an object or JSON string")
    merged = dict(DEFAULT_CONFIG)
    merged.update(cfg)
    return merged


def resolve_model_path(raw_path: str, input_file: Path) -> Path:
    candidate = Path(str(raw_path))
    if candidate.is_absolute():
        return candidate
    input_relative = (input_file.parent / candidate).resolve()
    if input_relative.exists():
        return input_relative
    return (Path.cwd() / candidate).resolve()


def load_csv_dataset(path: Path, config: dict[str, Any]) -> Dataset:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError(f"CSV missing header row: {path}")

        target_column = str(config.get("target_column", "target"))
        if target_column not in fieldnames:
            target_column = fieldnames[-1]

        configured_features = config.get("feature_columns")
        if isinstance(configured_features, list) and configured_features:
            feature_columns = [str(c) for c in configured_features if str(c) in fieldnames and str(c) != target_column]
        else:
            feature_columns = [c for c in fieldnames if c != target_column]

        if not feature_columns:
            raise ValueError("No feature columns found in CSV")

        x_rows: list[list[float]] = []
        y_vals: list[float] = []
        for row in reader:
            try:
                x_rows.append([float(row[c]) for c in feature_columns])
                y_vals.append(float(row[target_column]))
            except (TypeError, ValueError):
                # Skip malformed rows in scaffold mode.
                continue

    if not x_rows:
        raise ValueError(f"No valid numeric rows found in CSV: {path}")

    return Dataset(
        features=np.asarray(x_rows, dtype=np.float64),
        targets=np.asarray(y_vals, dtype=np.float64),
        feature_names=feature_columns,
        source=f"csv:{path}",
    )


def load_json_dataset(path: Path, config: dict[str, Any]) -> Dataset:
    payload = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(payload, dict) and "features" in payload and "targets" in payload:
        x = np.asarray(payload["features"], dtype=np.float64)
        y = np.asarray(payload["targets"], dtype=np.float64)
        feature_names = [f"x{i}" for i in range(x.shape[1])]
        return Dataset(features=x, targets=y, feature_names=feature_names, source=f"json:{path}")

    records: list[dict[str, Any]]
    if isinstance(payload, list):
        records = [r for r in payload if isinstance(r, dict)]
    elif isinstance(payload, dict) and isinstance(payload.get("records"), list):
        records = [r for r in payload["records"] if isinstance(r, dict)]
    else:
        raise ValueError(
            "JSON dataset must be either {'features': [...], 'targets': [...]} "
            "or a list of record objects"
        )

    if not records:
        raise ValueError(f"No record objects found in JSON: {path}")

    target_column = str(config.get("target_column", "target"))
    keys = sorted({k for r in records for k in r.keys()})
    if target_column not in keys:
        target_column = keys[-1]
    feature_columns = [k for k in keys if k != target_column]

    x_rows: list[list[float]] = []
    y_vals: list[float] = []
    for row in records:
        try:
            x_rows.append([float(row[k]) for k in feature_columns])
            y_vals.append(float(row[target_column]))
        except (KeyError, TypeError, ValueError):
            continue

    if not x_rows:
        raise ValueError(f"No valid numeric rows found in JSON records: {path}")

    return Dataset(
        features=np.asarray(x_rows, dtype=np.float64),
        targets=np.asarray(y_vals, dtype=np.float64),
        feature_names=feature_columns,
        source=f"json-records:{path}",
    )


def synthetic_dataset() -> Dataset:
    rng = np.random.default_rng(42)
    n = 512
    d = 8
    x = rng.normal(size=(n, d))
    w = np.linspace(0.5, 2.0, d)
    noise = rng.normal(scale=0.05, size=n)
    y = x @ w + noise
    return Dataset(
        features=x.astype(np.float64),
        targets=y.astype(np.float64),
        feature_names=[f"x{i}" for i in range(d)],
        source="synthetic:fallback",
    )


def load_dataset(model_path: Path, config: dict[str, Any]) -> Dataset:
    if model_path.exists():
        suffix = model_path.suffix.lower()
        if suffix == ".csv":
            return load_csv_dataset(model_path, config)
        if suffix == ".json":
            return load_json_dataset(model_path, config)
    return synthetic_dataset()


def split_dataset(x: np.ndarray, y: np.ndarray, val_split: float, seed: int) -> tuple[np.ndarray, ...]:
    n = x.shape[0]
    if n < 5:
        raise ValueError("Need at least 5 samples for scaffold training")

    val_split = min(max(float(val_split), 0.05), 0.5)
    n_val = max(1, int(round(n * val_split)))

    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    rng.shuffle(idx)
    val_idx = idx[:n_val]
    train_idx = idx[n_val:]
    if len(train_idx) == 0:
        train_idx = val_idx
    return x[train_idx], y[train_idx], x[val_idx], y[val_idx]


def fit_ridge_regression(x_train: np.ndarray, y_train: np.ndarray, ridge_lambda: float) -> np.ndarray:
    x_aug = np.hstack([x_train, np.ones((x_train.shape[0], 1), dtype=np.float64)])
    eye = np.eye(x_aug.shape[1], dtype=np.float64)
    eye[-1, -1] = 0.0  # do not regularize bias term
    a = x_aug.T @ x_aug + float(ridge_lambda) * eye
    b = x_aug.T @ y_train
    return np.linalg.pinv(a) @ b


def predict(x: np.ndarray, weights: np.ndarray) -> np.ndarray:
    x_aug = np.hstack([x, np.ones((x.shape[0], 1), dtype=np.float64)])
    return x_aug @ weights


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    err = y_true - y_pred
    mse = float(np.mean(err ** 2))
    mae = float(np.mean(np.abs(err)))
    denom = float(np.sum((y_true - np.mean(y_true)) ** 2))
    if denom == 0.0:
        r2 = 1.0 if mse == 0.0 else 0.0
    else:
        r2 = float(1.0 - np.sum(err ** 2) / denom)
    return {"mse": mse, "mae": mae, "r2": r2}


def has_nvidia_gpu() -> bool:
    try:
        result = subprocess.run(
            ["nvidia-smi", "-L"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except FileNotFoundError:
        return False


def detect_hardware() -> dict[str, Any]:
    mps = False
    try:
        import torch  # type: ignore

        mps = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    except Exception:
        mps = False
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "nvidia_gpu_available": has_nvidia_gpu(),
        "apple_mps_available": mps,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# NeMo Surrogate Training Report (Scaffold)",
        "",
        "## Summary",
        "",
        f"- Backend: `{payload['backend']}`",
        f"- Dataset source: `{payload['dataset_source']}`",
        f"- Samples: `{payload['samples']}`",
        f"- Features: `{payload['features']}`",
        f"- Dataset job id: `{payload.get('dataset_job_id', '')}`",
        "",
        "## Validation Metrics",
        "",
        f"- MSE: `{payload['val_metrics']['mse']:.6f}`",
        f"- MAE: `{payload['val_metrics']['mae']:.6f}`",
        f"- R2: `{payload['val_metrics']['r2']:.6f}`",
        "",
        "## Hardware Notes",
        "",
        "- This scaffold backend can run on macOS CPU for first-time integration testing.",
        "- For production PhysicsNeMo training, use Linux + NVIDIA CUDA GPU.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_output_manifest(path: Path, outputs: list[dict[str, str]]) -> None:
    path.write_text(json.dumps(outputs, indent=2), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: train_nemo_surrogate.py <input.json> <output.json> <temp_dir>", file=sys.stderr)
        return 2

    input_file = Path(sys.argv[1]).resolve()
    output_file = Path(sys.argv[2]).resolve()
    temp_dir = Path(sys.argv[3]).resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    payload = read_input(input_file)

    model_raw = str(payload.get("campaign_root_model", "")).strip()
    if not model_raw:
        raise ValueError("Missing required input: campaign_root_model")
    model_path = resolve_model_path(model_raw, input_file)

    dataset_job_id = str(payload.get("dataset_job_id", "")).strip()
    config = parse_training_config(payload.get("training_config", {}))
    backend = str(config.get("backend", "baseline_mlp")).strip().lower()

    if backend == "physicsnemo":
        raise RuntimeError(
            "Scaffold backend does not execute full PhysicsNeMo yet. "
            "Use backend='baseline_mlp' for smoke tests, then replace src/train_nemo_surrogate.py "
            "with your production GPU training implementation."
        )

    dataset = load_dataset(model_path, config)
    x_train, y_train, x_val, y_val = split_dataset(
        dataset.features,
        dataset.targets,
        float(config.get("val_split", 0.2)),
        int(config.get("random_seed", 42)),
    )

    weights = fit_ridge_regression(
        x_train=x_train,
        y_train=y_train,
        ridge_lambda=float(config.get("ridge_lambda", 1e-6)),
    )
    train_pred = predict(x_train, weights)
    val_pred = predict(x_val, weights)

    metrics_payload = {
        "backend": backend,
        "dataset_job_id": dataset_job_id,
        "dataset_source": dataset.source,
        "samples": int(dataset.features.shape[0]),
        "features": int(dataset.features.shape[1]),
        "feature_names": dataset.feature_names,
        "train_metrics": metrics(y_train, train_pred),
        "val_metrics": metrics(y_val, val_pred),
        "training_config": config,
        "hardware": detect_hardware(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - started, 3),
    }

    metrics_path = temp_dir / "metrics.json"
    checkpoint_path = temp_dir / "model_checkpoint.npz"
    report_path = temp_dir / "training_report.md"

    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")
    np.savez(
        checkpoint_path,
        weights=weights,
        feature_names=np.asarray(dataset.feature_names, dtype=object),
        dataset_source=np.asarray([dataset.source], dtype=object),
    )
    write_report(report_path, metrics_payload)

    outputs = [
        {"name": "metrics_json", "path": str(metrics_path)},
        {"name": "model_checkpoint_npz", "path": str(checkpoint_path)},
        {"name": "training_report_md", "path": str(report_path)},
    ]
    write_output_manifest(output_file, outputs)

    print(f"[train_nemo_surrogate] wrote: {metrics_path}")
    print(f"[train_nemo_surrogate] wrote: {checkpoint_path}")
    print(f"[train_nemo_surrogate] wrote: {report_path}")
    print(f"[train_nemo_surrogate] output manifest: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
