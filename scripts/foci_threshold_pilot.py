from __future__ import annotations

import argparse
import math
import pickle
import re
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from skimage import filters, measure, morphology


CHANNELS = {
    "DAPI": {
        "image_col": "Image_DAPI_nuc",
        "contour_col": "Nuc_cnt_DAPI_nuc",
        "name_col": "Image_name_DAPI_nuc",
    },
    "gh2AX": {
        "image_col": "Image_gh2AX_nuc",
        "contour_col": "Nuc_cnt_gh2AX_nuc",
        "name_col": "Image_name_gh2AX_nuc",
    },
}

METHODS = (
    "raw_triangle",
    "raw_yen",
    "tophat_p90",
    "tophat_p95",
    "tophat_p97",
    "tophat_p98",
    "tophat_p99",
    "tophat_p995",
    "tophat_p999",
)


def safe_name(value: object) -> str:
    text = str(value).strip()
    text = re.sub(r"[^A-Za-z0-9._+-]+", "_", text)
    return text.strip("_") or "item"


def normalize_to_uint8(image: np.ndarray) -> np.ndarray:
    arr = np.asarray(image)
    if arr.ndim == 3:
        arr = arr[..., 0]
    if arr.dtype == np.uint8:
        return arr
    arr = arr.astype(np.float32)
    finite = np.isfinite(arr)
    if not finite.any():
        return np.zeros(arr.shape, dtype=np.uint8)
    lo = float(np.nanmin(arr[finite]))
    hi = float(np.nanmax(arr[finite]))
    if hi <= lo:
        return np.zeros(arr.shape, dtype=np.uint8)
    return np.clip((arr - lo) * 255.0 / (hi - lo), 0, 255).astype(np.uint8)


def crop_nucleus(image: np.ndarray, contour: np.ndarray, margin: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    img = normalize_to_uint8(image)
    cnt = np.asarray(contour, dtype=np.int32).reshape(-1, 2)
    h, w = img.shape[:2]
    x0 = max(int(cnt[:, 0].min()) - margin, 0)
    y0 = max(int(cnt[:, 1].min()) - margin, 0)
    x1 = min(int(cnt[:, 0].max()) + margin + 1, w)
    y1 = min(int(cnt[:, 1].max()) + margin + 1, h)
    crop = img[y0:y1, x0:x1]
    rel = (cnt - np.array([x0, y0])).astype(np.int32)
    mask = np.zeros(crop.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [rel.reshape(-1, 1, 2)], 1)
    return crop, mask.astype(bool), rel


def threshold_mask(crop: np.ndarray, nucleus_mask: np.ndarray, method: str) -> tuple[np.ndarray, float]:
    working = crop.astype(np.float32)
    pixels = working[nucleus_mask]
    pixels = pixels[np.isfinite(pixels)]
    pixels = pixels[pixels > 0]
    if pixels.size < 8:
        return np.zeros_like(nucleus_mask, dtype=bool), math.nan

    if method == "raw_triangle":
        smooth = filters.gaussian(working, sigma=1.0, preserve_range=True)
        values = smooth[nucleus_mask]
        values = values[values > 0]
        threshold = float(filters.threshold_triangle(values))
        binary = smooth > threshold
    elif method == "raw_otsu":
        smooth = filters.gaussian(working, sigma=1.0, preserve_range=True)
        values = smooth[nucleus_mask]
        values = values[values > 0]
        threshold = float(filters.threshold_otsu(values))
        binary = smooth > threshold
    elif method == "raw_yen":
        smooth = filters.gaussian(working, sigma=1.0, preserve_range=True)
        values = smooth[nucleus_mask]
        values = values[values > 0]
        threshold = float(filters.threshold_yen(values))
        binary = smooth > threshold
    elif method.startswith("tophat_p"):
        enhanced = morphology.white_tophat(working, morphology.disk(6))
        values = enhanced[nucleus_mask]
        values = values[values > 0]
        if values.size < 8:
            return np.zeros_like(nucleus_mask, dtype=bool), math.nan
        percentile_text = method.removeprefix("tophat_p")
        percentile = float(percentile_text) / 10.0 if len(percentile_text) == 3 else float(percentile_text)
        threshold = float(np.percentile(values, percentile))
        binary = enhanced > threshold
    else:
        raise ValueError(f"Unknown method: {method}")

    binary &= nucleus_mask
    binary = morphology.remove_small_objects(binary.astype(bool), min_size=3)
    binary = morphology.remove_small_holes(binary, area_threshold=3)
    return binary, threshold


def measure_foci(crop: np.ndarray, binary: np.ndarray) -> tuple[list[dict], dict]:
    labels = measure.label(binary, connectivity=2)
    rows: list[dict] = []
    for region in measure.regionprops(labels, intensity_image=crop):
        area = int(region.area)
        if area < 3 or area > 500:
            continue
        perimeter = float(region.perimeter)
        circularity = 4.0 * math.pi * area / (perimeter * perimeter) if perimeter > 0 else 0.0
        if circularity < 0.15:
            continue
        rows.append(
            {
                "label": int(region.label),
                "area": area,
                "mean_intensity": float(region.mean_intensity),
                "median_intensity": float(np.median(crop[labels == region.label])),
                "max_intensity": float(region.max_intensity),
                "circularity": circularity,
            }
        )

    if not rows:
        return rows, {
            "count": 0,
            "area_total": 0,
            "mean_intensity": math.nan,
            "median_intensity": math.nan,
        }

    all_pixels = np.concatenate([crop[labels == row["label"]] for row in rows])
    return rows, {
        "count": len(rows),
        "area_total": int(sum(row["area"] for row in rows)),
        "mean_intensity": float(np.mean(all_pixels)),
        "median_intensity": float(np.median(all_pixels)),
    }


def save_overlay(
    out_path: Path,
    crop: np.ndarray,
    nucleus_mask: np.ndarray,
    nucleus_contour: np.ndarray,
    foci_mask: np.ndarray,
    title: str,
) -> None:
    base = normalize_to_uint8(crop)
    rgb = cv2.cvtColor(base, cv2.COLOR_GRAY2BGR)
    outside = ~nucleus_mask
    rgb[outside] = (rgb[outside] * 0.25).astype(np.uint8)
    cv2.polylines(rgb, [nucleus_contour.reshape(-1, 1, 2)], isClosed=True, color=(255, 255, 0), thickness=1)
    contours, _ = cv2.findContours(foci_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(rgb, contours, -1, (0, 0, 255), 1)

    scale = 2 if max(rgb.shape[:2]) < 320 else 1
    if scale > 1:
        rgb = cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    canvas = cv2.copyMakeBorder(rgb, 28, 0, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    cv2.putText(canvas, title[:110], (8, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), canvas)


def choose_pilot_rows(df: pd.DataFrame, n: int) -> list[int]:
    if len(df) <= n:
        return list(df.index)
    area = None
    for contour_col in ("Nuc_cnt_DAPI_nuc", "Nuc_cnt_gh2AX_nuc"):
        if contour_col in df:
            areas = []
            for contour in df[contour_col]:
                cnt = np.asarray(contour, dtype=np.int32).reshape(-1, 2)
                areas.append(abs(cv2.contourArea(cnt.reshape(-1, 1, 2))))
            area = pd.Series(areas, index=df.index)
            break
    if area is None:
        return list(df.head(n).index)
    quantiles = np.linspace(0.1, 0.9, n)
    selected = []
    for q in quantiles:
        target = area.quantile(q)
        idx = (area - target).abs().sort_values().index[0]
        if idx not in selected:
            selected.append(idx)
    for idx in df.index:
        if len(selected) >= n:
            break
        if idx not in selected:
            selected.append(idx)
    return selected[:n]


def first_pkl_per_condition(results_root: Path) -> list[Path]:
    selected = []
    for results_csv in sorted(results_root.glob("*/*/Results.csv")):
        pkl_dir = results_csv.parent / "pkl-data"
        pkls = sorted(pkl_dir.glob("*.pkl"))
        if pkls:
            selected.append(pkls[0])
    return selected


def all_pkls(results_root: Path) -> list[Path]:
    return sorted(results_root.glob("*/*/pkl-data/*.pkl"))


def condition_dir_for_pkl(pkl_path: Path) -> Path:
    return pkl_path.parent.parent


def process_pkl(
    pkl_path: Path,
    out_root: Path,
    cells_per_pkl: int | None,
    margin: int,
    output_folder: str,
) -> pd.DataFrame:
    df = pickle.load(open(pkl_path, "rb"))
    row_indices = list(df.index) if cells_per_pkl is None else choose_pilot_rows(df, cells_per_pkl)
    condition_dir = condition_dir_for_pkl(pkl_path)
    relative_condition = condition_dir.relative_to(out_root)
    qc_dir = condition_dir / output_folder / safe_name(pkl_path.stem)
    rows = []

    for idx in row_indices:
        row = df.loc[idx]
        for channel, cols in CHANNELS.items():
            crop, nucleus_mask, nucleus_contour = crop_nucleus(row[cols["image_col"]], row[cols["contour_col"]], margin)
            for method in METHODS:
                foci_mask, threshold = threshold_mask(crop, nucleus_mask, method)
                foci_rows, summary = measure_foci(crop, foci_mask)
                title = (
                    f"{relative_condition} | cell {row['Cell']} | {channel} | {method} | "
                    f"n={summary['count']} area={summary['area_total']}"
                )
                image_name = (
                    f"cell_{int(row['Cell']):04d}_{channel}_{method}_"
                    f"n{summary['count']}_area{summary['area_total']}.png"
                )
                save_overlay(qc_dir / image_name, crop, nucleus_mask, nucleus_contour, foci_mask, title)
                rows.append(
                    {
                        "results_dir": str(condition_dir),
                        "pkl_path": str(pkl_path),
                        "image_name": row[cols["name_col"]],
                        "Frame": int(row["Frame"]),
                        "Cell": int(row["Cell"]),
                        "channel": channel,
                        "method": method,
                        "threshold": threshold,
                        "foci_count": summary["count"],
                        "foci_area_total": summary["area_total"],
                        "foci_mean_intensity": summary["mean_intensity"],
                        "foci_median_intensity": summary["median_intensity"],
                        "qc_image": str(qc_dir / image_name),
                        "foci_detail_json": str(foci_rows),
                    }
                )
    return pd.DataFrame(rows)


def write_wide_results(condition_dir: Path, measurements: pd.DataFrame, output_csv_name: str) -> None:
    results_path = condition_dir / "Results.csv"
    if not results_path.exists():
        return
    results = pd.read_csv(results_path)
    wide = results.copy()
    metrics = {
        "foci_count": "Foci_count",
        "foci_area_total": "Foci_area_total",
        "foci_mean_intensity": "Foci_mean_intensity",
        "foci_median_intensity": "Foci_median_intensity",
    }
    for channel in CHANNELS:
        for method in METHODS:
            for metric, prefix in metrics.items():
                wide[f"{prefix}_{channel}_{method}"] = np.nan

    for _, row in measurements.iterrows():
        mask = (
            (wide["Frame"].astype(int) == int(row["Frame"]))
            & (wide["Cell"].astype(int) == int(row["Cell"]))
            & (wide[f"Image_name_{row['channel']}_nuc"].astype(str) == str(row["image_name"]))
        )
        for metric, prefix in metrics.items():
            wide.loc[mask, f"{prefix}_{row['channel']}_{row['method']}"] = row[metric]

    out_path = condition_dir / output_csv_name
    wide.to_csv(out_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--cells-per-pkl", type=int, default=6)
    parser.add_argument("--margin", type=int, default=12)
    parser.add_argument("--full", action="store_true", help="Process every pkl and every cell.")
    args = parser.parse_args()

    pkl_paths = all_pkls(args.results_root) if args.full else first_pkl_per_condition(args.results_root)
    cells_per_pkl = None if args.full else args.cells_per_pkl
    output_folder = "foci_threshold_all_nuclei" if args.full else "foci_threshold_pilot_v2"
    per_condition_csv = "Results_with_foci_thresholds_ALL.csv" if args.full else "Results_with_foci_thresholds_PILOT.csv"
    summary_name = "foci_threshold_all_nuclei_summary.csv" if args.full else "foci_threshold_pilot_v2_summary.csv"
    all_measurements = []
    by_condition: dict[Path, list[pd.DataFrame]] = {}
    for pkl_path in pkl_paths:
        pilot = process_pkl(pkl_path, args.results_root, cells_per_pkl, args.margin, output_folder)
        condition_dir = condition_dir_for_pkl(pkl_path)
        pilot_dir = condition_dir / output_folder
        pilot_dir.mkdir(parents=True, exist_ok=True)
        pkl_measurements_path = pilot_dir / f"{safe_name(pkl_path.stem)}_foci_measurements.csv"
        pilot.to_csv(pkl_measurements_path, index=False)
        by_condition.setdefault(condition_dir, []).append(pilot)
        all_measurements.append(pilot)
        print(f"processed {pkl_path} -> {len(pilot)} measurements")

    for condition_dir, frames in by_condition.items():
        condition_measurements = pd.concat(frames, ignore_index=True)
        condition_out_dir = condition_dir / output_folder
        condition_measurements.to_csv(condition_out_dir / "foci_measurements.csv", index=False)
        write_wide_results(condition_dir, condition_measurements, per_condition_csv)

    combined = pd.concat(all_measurements, ignore_index=True) if all_measurements else pd.DataFrame()
    combined_path = args.results_root / summary_name
    combined.to_csv(combined_path, index=False)
    print(f"summary: {combined_path}")


if __name__ == "__main__":
    main()
