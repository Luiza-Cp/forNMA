"""Download the four supported Cellpose weights once, before freezing."""
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
destination = root / "build" / "desktop-models"
destination.mkdir(parents=True, exist_ok=True)
os.environ["CELLPOSE_LOCAL_MODELS_PATH"] = str(destination)
os.environ["NUMBA_CACHE_DIR"] = str(root / "build" / "numba")
from cellpose import models
import torch

if torch.version.cuda is not None:
    raise SystemExit("Refusing to package a CUDA-enabled PyTorch. Install the CPU wheel first.")
for name in ("nuclei", "cyto3", "cyto2", "cyto"):
    model = models.CellposeModel(pretrained_model=name, gpu=False)
    print(f"Prepared {name}: {model.pretrained_model}", flush=True)
