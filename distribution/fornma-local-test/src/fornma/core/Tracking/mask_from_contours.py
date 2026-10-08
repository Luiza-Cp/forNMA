"""
Build a labelled segmentation mask (T x H x W, pixel value == track_id) from the
nuclear contours forNMA already stores in its segmentation ``pkl-data`` files.

forNMA's segmentation keeps nuclei as OpenCV contours inside per-image pickles
(``Nuc_cnt_<channel>`` columns), not as a label stack. napari-TRACE, however,
needs a label mask where each pixel equals the cell's ``track_id``. This module
is the one-way bridge: it rasterizes those contours, colouring each nucleus with
the ``track_id`` the tracking step assigned, and writes a single ``.tif`` stack.

Contour handling mirrors ``Segmentation/analyze.py::_drawable_contours`` so the
mask matches exactly what the segmentation overlay draws.
"""
from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd


def _normalize_contour(value) -> np.ndarray | None:
    """Coerce one stored contour value to an int32 (N,1,2) array, or None.

    Accepts the (N,2) and (N,1,2) shapes forNMA stores; anything else is skipped
    (matches Segmentation/analyze.py::_drawable_contours).
    """
    if not isinstance(value, np.ndarray):
        return None
    cnt = np.asarray(value)
    if cnt.ndim == 2 and cnt.shape[1] == 2 and len(cnt) > 0:
        return np.ascontiguousarray(cnt, dtype=np.int32).reshape(-1, 1, 2)
    if cnt.ndim == 3 and cnt.shape[1:] == (1, 2) and len(cnt) > 0:
        return np.ascontiguousarray(cnt, dtype=np.int32)
    return None


def _rasterize_frame(contours_and_ids, height: int, width: int) -> np.ndarray:
    """Paint one frame: each contour filled with its track_id on a uint32 canvas.

    contours_and_ids: iterable of (contour_ndarray, track_id). Later cells
    overwrite earlier ones where they overlap.
    # ponytail: last-writer-wins on overlap; segmentation nuclei rarely overlap,
    # upgrade to area-priority only if double-painting shows up in practice.
    """
    import cv2 as cv  # local import keeps module importable without cv2 for tests that stub it

    canvas = np.zeros((height, width), dtype=np.uint32)
    for cnt, track_id in contours_and_ids:
        norm = _normalize_contour(cnt)
        if norm is None or track_id is None:
            continue
        stamp = np.zeros((height, width), dtype=np.uint8)
        cv.drawContours(stamp, [norm], -1, 255, thickness=-1)
        canvas[stamp > 0] = np.uint32(track_id)
    return canvas


def _image_shape(image_dir: str, image_name: str) -> tuple[int, int]:
    from fornma.core.image_io import imread

    path = image_name if os.path.isabs(image_name) else os.path.join(image_dir, image_name)
    img = imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not read raw image to size the mask: {path}")
    return int(img.shape[0]), int(img.shape[1])


def build_label_mask(tracked_csv: str, pkl_dir: str, image_dir: str, out_path: str) -> str:
    """Write a T x H x W uint32 label mask (pixel == track_id) to *out_path*.

    tracked_csv : forNMA 'Tracked Results.csv' (has Frame, Cell, track_id, Image_name_*).
    pkl_dir     : the segmentation 'pkl-data' folder with the *results.pkl contours.
    image_dir   : folder with the raw images (used only to size the mask).
    """
    tracked = pd.read_csv(tracked_csv)
    img_col = next((c for c in tracked.columns if str(c).startswith("Image_name")), None)
    if img_col is None:
        raise KeyError("No 'Image_name*' column in the tracked table.")
    channel = str(img_col).split("Image_name_")[-1]
    cnt_col = f"Nuc_cnt_{channel}"

    tracked = tracked.dropna(subset=["Frame", "Cell", img_col])
    tracked["Frame"] = tracked["Frame"].astype(int)
    tracked["Cell"] = tracked["Cell"].astype(int)
    # (image, cell) -> track_id, and image -> frame, straight from the tracked table.
    id_lookup: dict[tuple[str, int], int] = {}
    frame_of_image: dict[str, int] = {}
    for _, r in tracked.iterrows():
        image = os.path.basename(str(r[img_col]))
        tid = r.get("track_id")
        if pd.notna(tid):
            id_lookup[(image, int(r["Cell"]))] = int(tid)
        frame_of_image[image] = int(r["Frame"])

    pkls = sorted(glob.glob(os.path.join(pkl_dir, "*.pkl")))
    if not pkls:
        raise FileNotFoundError(f"No .pkl contour files found in {pkl_dir}")

    height, width = _image_shape(image_dir, str(tracked[img_col].iloc[0]))
    frames: dict[int, list] = {}
    for pkl in pkls:
        df = pd.read_pickle(pkl)
        if cnt_col not in df.columns or img_col not in df.columns or "Cell" not in df.columns:
            continue
        for _, row in df.iterrows():
            image = os.path.basename(str(row[img_col]))
            frame = frame_of_image.get(image)
            if frame is None:
                continue
            track_id = id_lookup.get((image, int(row["Cell"])))
            if track_id is None:
                continue
            frames.setdefault(frame, []).append((row[cnt_col], track_id))

    if not frames:
        raise ValueError("No contour matched the tracked table (channel/Cell/Image mismatch).")

    import tifffile

    stack = np.stack(
        [_rasterize_frame(frames.get(f, []), height, width) for f in sorted(frames)],
        axis=0,
    )
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    tifffile.imwrite(out_path, stack)
    return out_path


def _self_check() -> None:
    """Two square nuclei rasterize to their own track_ids; background stays 0."""
    sq_a = np.array([[2, 2], [2, 6], [6, 6], [6, 2]], dtype=np.int32)          # (N,2)
    sq_b = np.array([[10, 10], [10, 14], [14, 14], [14, 10]], dtype=np.int32).reshape(-1, 1, 2)  # (N,1,2)
    frame = _rasterize_frame([(sq_a, 7), (sq_b, 42)], height=20, width=20)
    assert frame[4, 4] == 7, frame[4, 4]
    assert frame[12, 12] == 42, frame[12, 12]
    assert frame[0, 0] == 0
    assert set(np.unique(frame).tolist()) == {0, 7, 42}
    print("mask_from_contours self-check OK")


if __name__ == "__main__":
    _self_check()
