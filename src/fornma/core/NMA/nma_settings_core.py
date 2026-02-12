from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np

@dataclass
class DatasetSpec:
    name: str
    path: Path
    area_col: str
    nii_col: str
    is_control: bool = False

class NMASettingsCore:
    """Somente lógica de dados — sem Matplotlib/Dash/Plotly."""
    def __init__(self, spec: DatasetSpec):
        self.spec = spec
        self.df: pd.DataFrame | None = None

    def load(self, nrows: int | None = None) -> pd.DataFrame:
        self.df = pd.read_csv(self.spec.path, nrows=nrows)
        # saneamento básico
        self.df = self.df.dropna(subset=[self.spec.area_col, self.spec.nii_col])
        return self.df

    def percentiles(self, col: str, qs=(0.05, 0.95)) -> tuple[float, float]:
        s = self.df[col].astype(float)
        lo, hi = np.quantile(s, qs)
        return float(lo), float(hi)

    def suggest_thresholds(self) -> dict:
        """Exemplo: thresholds ‘iniciais’ para sliders."""
        a_lo, a_hi = self.percentiles(self.spec.area_col, (0.05, 0.95))
        n_lo, n_hi = self.percentiles(self.spec.nii_col, (0.05, 0.95))
        return {
            "area_min": a_lo, "area_max": a_hi,
            "nii_min": n_lo,  "nii_max": n_hi,
        }

    def filtered(self, area_min: float, area_max: float, nii_min: float, nii_max: float) -> pd.DataFrame:
        df = self.df
        a, n = self.spec.area_col, self.spec.nii_col
        return df[(df[a] >= area_min) & (df[a] <= area_max) & (df[n] >= nii_min) & (df[n] <= nii_max)].copy()
