from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DatasetSpec(BaseModel):
    name: Optional[str] = None
    path: str
    area_col: str = "Area"
    nii_col: str = "NII"
    is_control: bool = False


class NMAParams(BaseModel):
    datasets: List[DatasetSpec] = Field(default_factory=list)


class NMAComputeRequest(BaseModel):
    params: NMAParams
    sample_per_ds: int = 2000
    axis_k: float = 3.0
    axis_headroom: float = 0.05
    axis_quantile: Optional[float] = None
    axis_k_neg: float = 2.0


class NMAComputeResponse(BaseModel):
    log: str
    stats: Dict[str, float]
    axis: Optional[Dict[str, Any]]
    sample: Dict[str, List[float]]
    sd_factors: Dict[str, float]
    figure: Dict[str, Any]


class NMAAutoDbscanRequest(BaseModel):
    params: NMAParams
    sample_per_ds: int = 2000
    pctl: int = 90
    eps_percentile: int = 90


class NMAAutoDbscanResponse(BaseModel):
    log: str
    stats: Dict[str, float]
    sd_factors: Dict[str, float]
    ellipse: Dict[str, float]


class NMAThresholds(BaseModel):
    v_up: float
    v_mid: float
    v_down: float
    v_down2: float
    y_high: float
    y_low: float


class NMASaveSettingsRequest(BaseModel):
    name: str
    mean_nii: float
    std_nii: float
    mean_area: float
    std_area: float
    sd_nii: float
    sd_area: float
    graph_limits: List[float]
    thresholds: NMAThresholds


class NMASaveSettingsResponse(BaseModel):
    status: str
    settings_path: str


class NMASettingsResponse(BaseModel):
    name: str
    sd_area: float
    sd_nii: float
    mean_nii: float
    std_nii: float
    mean_area: float
    std_area: float
    graph_limits: List[float]
    thresholds: NMAThresholds


class NMAPreviewResponse(BaseModel):
    stats: Dict[str, float]
    sd_factors: Dict[str, float]
    graph_limits: List[float]
    thresholds: NMAThresholds


class NMAFigureRequest(BaseModel):
    params: NMAParams
    sample_per_ds: int = 2000
    sample_per_ds_all: int = 4000
    axis_k: float = 3.0
    axis_headroom: float = 0.05
    axis_quantile: Optional[float] = None
    axis_k_neg: float = 2.0
    sd_nii: float = 1.0
    sd_area: float = 1.0
    thresholds: Optional[NMAThresholds] = None
    include_sample: bool = True
    include_all_datasets: bool = False


class NMAFigureResponse(BaseModel):
    figure: Dict[str, Any]
    stats: Dict[str, float]
    graph_limits: List[float]


class DatasetColumnsRequest(BaseModel):
    path: str


class DatasetColumnsResponse(BaseModel):
    columns: List[str]
