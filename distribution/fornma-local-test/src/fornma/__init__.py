from __future__ import annotations

import importlib
import sys
from pathlib import Path


# Keep historical imports such as `fornma.Segmentation` working while the
# active package layout lives under `fornma.core`.
_CORE_PATH = Path(__file__).resolve().parent / "core"
if _CORE_PATH.exists():
    __path__.append(str(_CORE_PATH))


def _alias_module(old_name: str, new_name: str) -> None:
    if old_name not in sys.modules:
        sys.modules[old_name] = importlib.import_module(new_name)


_alias_module(
    "fornma.Statistics.Scheirer_ray_hare",
    "fornma.core.Statistics.ScheirerRayHare",
)
