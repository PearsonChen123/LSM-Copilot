#!/usr/bin/env python3
"""
Thin Spotiflow adapter for 2D fluorescence spot-detection benchmarks.

The adapter does not train or modify Spotiflow. It loads approved pretrained
Spotiflow models, predicts y/x spot coordinates from TIFF images, and compares
them against CSV point annotations using one-to-one distance matching.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment
from tifffile import imread


MODEL_AUTO_MAP = {
    "hybiss": "hybiss",
    "synthetic_complex": "synth_complex",
    "synthetic_simple": "synth_complex",
}


@dataclass
class ImageMetrics:
    dataset: str
    split: str
    image_id: str
    image_path: str
    gt_path: str
    model_name: str
    height_px: int
    width_px: int
    n_gt: int
    n_pred: int
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float
    mean_distance_px: float
    median_distance_px: float
    match_radius_px: float


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, allow_nan=True)


def read_coords(path: Path) -> np.ndarray:
    df = pd.read_csv(path)
    if df.empty:
        return np.zeros((0, 2), dtype=np.float32)

    lower = {str(c).strip().lower(): c for c in df.columns}
    y_col = next((lower[k] for k in ("y", "axis-0", "row") if k in lower), None)
    x_col = next((lower[k] for k in ("x", "axis-1", "col") if k in lower), None)

    if y_col is None or x_col is None:
        numeric = [
            c for c in df.columns
            if not str(c).lower().startswith("unnamed") and pd.api.types.is_numeric_dtype(df[c])
        ]
        if len(numeric) < 2:
            raise ValueError(f"Could not infer y/x columns from {path}")
        y_col, x_col = numeric[:2]

    coords = df[[y_col, x_col]].to_numpy(dtype=np.float32, copy=True)
    return coords[np.isfinite(coords).all(axis=1)]


def paired_files(dataset_dir: Path, split: str) -> list[tuple[Path, Path]]:
    split_dir = dataset_dir / split
    pairs = []
    for tif in sorted(split_dir.glob("*.tif")):
        gt = tif.with_suffix(".csv")
        if gt.exists():
            pairs.append((tif, gt))
    return pairs


def model_for_dataset(dataset: str, strategy: str) -> str:
    if strategy != "auto":
        return strategy
    return MODEL_AUTO_MAP.get(dataset, "general")


def load_models(model_names: Iterable[str], cache_dir: Path, device: str):
    from spotiflow.model import Spotiflow

    models = {}
    for name in sorted(set(model_names)):
        models[name] = Spotiflow.from_pretrained(
            name,
            cache_dir=cache_dir,
            map_location=device,
            verbose=True,
        )
    return models


def match_points(gt: np.ndarray, pred: np.ndarray, radius_px: float) -> tuple[list[tuple[int, int, float]], int, int, int]:
    if len(gt) == 0 and len(pred) == 0:
        return [], 0, 0, 0
    if len(gt) == 0:
        return [], 0, len(pred), 0
    if len(pred) == 0:
        return [], 0, 0, len(gt)

    distances = cdist(gt, pred, metric="euclidean")
    costs = distances.copy()
    costs[costs > radius_px] = 1e9
    gt_idx, pred_idx = linear_sum_assignment(costs)

    matches = []
    for gi, pi in zip(gt_idx, pred_idx):
        dist = float(distances[gi, pi])
        if dist <= radius_px:
            matches.append((int(gi), int(pi), dist))

    tp = len(matches)
    fp = len(pred) - tp
    fn = len(gt) - tp
    return matches, tp, fp, fn


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def summarize(rows: list[ImageMetrics]) -> dict[str, float | int]:
    tp = sum(r.tp for r in rows)
    fp = sum(r.fp for r in rows)
    fn = sum(r.fn for r in rows)
    precision, recall, f1 = prf(tp, fp, fn)
    dists = [r.mean_distance_px for r in rows if np.isfinite(r.mean_distance_px)]
    return {
        "n_images": len(rows),
        "n_gt": int(sum(r.n_gt for r in rows)),
        "n_pred": int(sum(r.n_pred for r in rows)),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "macro_f1": float(np.mean([r.f1 for r in rows])) if rows else 0.0,
        "mean_localization_error_px": float(np.mean(dists)) if dists else math.nan,
    }


def save_qc_overlay(image_path: Path, gt: np.ndarray, pred: np.ndarray, matches: list[tuple[int, int, float]], metrics: ImageMetrics, out_path: Path) -> None:
    img = imread(image_path).astype(np.float32)
    lo, hi = np.percentile(img, (1, 99.8))
    norm = np.clip((img - lo) / max(hi - lo, 1e-6), 0, 1)
    matched_gt = {m[0] for m in matches}
    matched_pred = {m[1] for m in matches}

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(norm, cmap="gray")
    if len(gt):
        miss = np.array([p for i, p in enumerate(gt) if i not in matched_gt], dtype=np.float32)
        hit = np.array([p for i, p in enumerate(gt) if i in matched_gt], dtype=np.float32)
        if len(hit):
            ax.scatter(hit[:, 1], hit[:, 0], s=12, facecolors="none", edgecolors="cyan", linewidths=0.7, label="GT matched")
        if len(miss):
            ax.scatter(miss[:, 1], miss[:, 0], s=16, c="lime", marker="x", linewidths=0.8, label="GT missed")
    if len(pred):
        false = np.array([p for i, p in enumerate(pred) if i not in matched_pred], dtype=np.float32)
        hit_pred = np.array([p for i, p in enumerate(pred) if i in matched_pred], dtype=np.float32)
        if len(hit_pred):
            ax.scatter(hit_pred[:, 1], hit_pred[:, 0], s=8, c="yellow", marker=".", label="Pred matched")
        if len(false):
            ax.scatter(false[:, 1], false[:, 0], s=14, c="magenta", marker="+", linewidths=0.8, label="Pred FP")
    ax.set_title(
        f"{metrics.dataset}/{metrics.image_id} {metrics.model_name}: "
        f"F1={metrics.f1:.3f} TP={metrics.tp} FP={metrics.fp} FN={metrics.fn}"
    )
    ax.axis("off")
    ax.legend(loc="upper right", fontsize=7, framealpha=0.7)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_score_plots(dataset_df: pd.DataFrame, out_dir: Path) -> None:
    if dataset_df.empty:
        return
    x = np.arange(len(dataset_df))
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(x - 0.25, dataset_df["precision"], width=0.25, label="Precision")
    ax.bar(x, dataset_df["recall"], width=0.25, label="Recall")
    ax.bar(x + 0.25, dataset_df["f1"], width=0.25, label="F1")
    ax.set_xticks(x)
    ax.set_xticklabels(dataset_df["dataset"], rotation=35, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Score")
    ax.set_title("Spotiflow test benchmark by dataset")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "07_final_dataset_scores.png", dpi=220)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run approved Spotiflow 2D spot benchmark.")
    parser.add_argument("datasets_root", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("output/spotiflow_test_benchmark"))
    parser.add_argument("--datasets", nargs="*", default=None, help="Optional dataset names to include.")
    parser.add_argument("--split", default="test")
    parser.add_argument("--model-strategy", default="auto", choices=["auto", "general", "hybiss", "synth_complex", "fluo_live"])
    parser.add_argument("--cache-dir", type=Path, default=Path("output/spotiflow_model_cache"))
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda", "mps", "auto"])
    parser.add_argument("--match-radius-px", type=float, default=3.0)
    parser.add_argument("--probability-threshold", type=float, default=None)
    parser.add_argument("--min-distance", type=int, default=1)
    parser.add_argument("--exclude-border", type=int, default=1)
    parser.add_argument("--subpix-radius", type=int, default=0)
    parser.add_argument("--max-images-per-dataset", type=int, default=0)
    parser.add_argument("--qc-images-per-dataset", type=int, default=1)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("SPOTIFLOW_CACHE_DIR", str(args.cache_dir.resolve()))

    dataset_dirs = sorted(p for p in args.datasets_root.iterdir() if p.is_dir())
    if args.datasets:
        wanted = set(args.datasets)
        dataset_dirs = [p for p in dataset_dirs if p.name in wanted]
        missing = sorted(wanted.difference({p.name for p in dataset_dirs}))
        if missing:
            raise ValueError(f"Requested dataset(s) not found: {', '.join(missing)}")
    planned_models = [model_for_dataset(d.name, args.model_strategy) for d in dataset_dirs]

    write_json(out_dir / "00_intake.json", {
        "input_path": str(args.datasets_root),
        "output_dir": str(out_dir),
        "approved_method": "spotiflow",
        "environment": ".venv_spotiflow",
        "split": args.split,
        "model_strategy": args.model_strategy,
        "planned_models": sorted(set(planned_models)),
    })
    write_json(out_dir / "05_extension_provenance.json", {
        "name": "spotiflow",
        "source_url": "https://github.com/weigertlab/spotiflow",
        "docs_url": "https://weigertlab.org/spotiflow/",
        "license": "BSD-3-Clause",
        "installed_package": "spotiflow==0.6.4",
        "torch": "CPU-only torch expected in .venv_spotiflow",
        "adapter_path": "skills/lsm-copilot/tools/extensions/spotiflow_adapter.py",
        "model_cache_dir": str(args.cache_dir),
        "user_approved": True,
    })

    models = load_models(planned_models, args.cache_dir, args.device)

    image_rows: list[ImageMetrics] = []
    prediction_rows: list[dict[str, object]] = []
    inventory_rows: list[dict[str, object]] = []

    for dataset_dir in dataset_dirs:
        dataset = dataset_dir.name
        pairs = paired_files(dataset_dir, args.split)
        if args.max_images_per_dataset > 0:
            pairs = pairs[:args.max_images_per_dataset]
        model_name = model_for_dataset(dataset, args.model_strategy)
        model = models[model_name]
        qc_remaining = args.qc_images_per_dataset

        for tif_path, gt_path in pairs:
            image = imread(tif_path)
            if image.ndim != 2:
                raise ValueError(f"Expected 2D image, got {image.shape}: {tif_path}")
            gt = read_coords(gt_path)
            spots, details = model.predict(
                image,
                prob_thresh=args.probability_threshold,
                min_distance=args.min_distance,
                exclude_border=args.exclude_border,
                subpix=args.subpix_radius,
                device=args.device,
                verbose=args.verbose,
            )
            pred = np.asarray(spots, dtype=np.float32)
            matches, tp, fp, fn = match_points(gt, pred, args.match_radius_px)
            precision, recall, f1 = prf(tp, fp, fn)
            dists = [m[2] for m in matches]
            metrics = ImageMetrics(
                dataset=dataset,
                split=args.split,
                image_id=tif_path.stem,
                image_path=str(tif_path),
                gt_path=str(gt_path),
                model_name=model_name,
                height_px=int(image.shape[0]),
                width_px=int(image.shape[1]),
                n_gt=int(len(gt)),
                n_pred=int(len(pred)),
                tp=int(tp),
                fp=int(fp),
                fn=int(fn),
                precision=float(precision),
                recall=float(recall),
                f1=float(f1),
                mean_distance_px=float(np.mean(dists)) if dists else math.nan,
                median_distance_px=float(np.median(dists)) if dists else math.nan,
                match_radius_px=float(args.match_radius_px),
            )
            image_rows.append(metrics)
            inventory_rows.append({
                "dataset": dataset,
                "split": args.split,
                "image_id": tif_path.stem,
                "image_path": str(tif_path),
                "gt_path": str(gt_path),
                "shape": "x".join(str(s) for s in image.shape),
                "dtype": str(image.dtype),
                "gt_count": int(len(gt)),
                "model_name": model_name,
            })
            probs = np.asarray(getattr(details, "prob", np.full(len(pred), np.nan))).reshape(-1)
            intens_raw = np.asarray(getattr(details, "intens", np.full(len(pred), np.nan)))
            if intens_raw.size == 0:
                intens = np.full(len(pred), np.nan)
            else:
                intens = intens_raw.reshape(len(pred), -1)[:, 0] if len(pred) else np.asarray([])
            for i, p in enumerate(pred):
                prediction_rows.append({
                    "dataset": dataset,
                    "split": args.split,
                    "image_id": tif_path.stem,
                    "prediction_id": i,
                    "y_px": float(p[0]),
                    "x_px": float(p[1]),
                    "probability": float(probs[i]) if i < len(probs) else math.nan,
                    "intensity": float(intens[i]) if i < len(intens) else math.nan,
                    "model_name": model_name,
                })
            if qc_remaining > 0:
                save_qc_overlay(
                    tif_path,
                    gt,
                    pred,
                    matches,
                    metrics,
                    out_dir / f"07_final_qc_{dataset}_{tif_path.stem}.png",
                )
                qc_remaining -= 1

    pd.DataFrame.from_records(inventory_rows).to_csv(out_dir / "01_file_inventory.csv", index=False)
    write_json(out_dir / "02_layout_detection.json", {
        "task": "2d_spot_detection_benchmark",
        "image_layout": "YX",
        "coordinate_units": "pixels",
        "routing": "approved_spotiflow_extension",
    })
    pd.DataFrame.from_records([asdict(r) for r in image_rows]).to_csv(out_dir / "07_final_image_metrics.csv", index=False)
    pd.DataFrame.from_records(prediction_rows).to_csv(out_dir / "07_final_predictions.csv", index=False)

    dataset_records = []
    for dataset, group in pd.DataFrame.from_records([asdict(r) for r in image_rows]).groupby("dataset", sort=True):
        rows = [ImageMetrics(**row) for row in group.to_dict(orient="records")]
        dataset_records.append({"dataset": dataset, **summarize(rows)})
    dataset_df = pd.DataFrame.from_records(dataset_records)
    dataset_df.to_csv(out_dir / "07_final_dataset_metrics.csv", index=False)
    save_score_plots(dataset_df, out_dir)

    overall = summarize(image_rows)
    write_json(out_dir / "08_summary.json", {
        "run_id": out_dir.name,
        "skill": "lsm-copilot",
        "method": "spotiflow_pretrained",
        "model_strategy": args.model_strategy,
        "models_used": sorted(set(planned_models)),
        "match_radius_px": args.match_radius_px,
        "overall_test_metrics": overall,
        "extension": {
            "name": "spotiflow",
            "status": "used",
            "license": "BSD-3-Clause",
            "adapter_path": "skills/lsm-copilot/tools/extensions/spotiflow_adapter.py",
            "model_cache_dir": str(args.cache_dir),
        },
        "artifacts": [
            str(out_dir / "01_file_inventory.csv"),
            str(out_dir / "07_final_image_metrics.csv"),
            str(out_dir / "07_final_dataset_metrics.csv"),
            str(out_dir / "07_final_predictions.csv"),
            str(out_dir / "07_final_dataset_scores.png"),
        ],
        "caveats": [
            "CSV coordinates are interpreted as y/x pixel units.",
            "Model selection is based on dataset name and registered pretrained models, not on test GT performance.",
            "CPU-only inference may be slow.",
        ],
    })
    print(json.dumps({"output_dir": str(out_dir), "overall": overall, "datasets": dataset_records}, indent=2, allow_nan=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
