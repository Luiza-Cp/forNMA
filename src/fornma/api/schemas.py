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


class NMASettingsUploadResponse(BaseModel):
    name: str
    sd_area: float
    sd_nii: float
    mean_nii: float
    std_nii: float
    mean_area: float
    std_area: float
    graph_limits: List[float]
    thresholds: NMAThresholds


class NMADotPlotConfig(BaseModel):
    column1: Optional[str] = None
    column2: Optional[str] = None
    hue_min: Optional[float] = None
    hue_max: Optional[float] = None
    size_min: Optional[float] = None
    size_max: Optional[float] = None
    sample_size: Optional[int] = None
    palette: Optional[str] = None
    single: bool = False
    overtime: bool = False


class NMAHeatmapPlotConfig(BaseModel):
    single: bool = False
    overtime: bool = False
    jointplot: bool = False
    palette: Optional[str] = None


class NMAPlotRunRequest(BaseModel):
    params: NMAParams
    output_dir: str
    kind: str = "dot"
    dot: NMADotPlotConfig = Field(default_factory=NMADotPlotConfig)
    heatmap: NMAHeatmapPlotConfig = Field(default_factory=NMAHeatmapPlotConfig)


class NMAPlotStartResponse(BaseModel):
    job_id: str
    status: str


class NMAPlotStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    output_dir: str
    files: List[str]
    error: Optional[str] = None


class SegmentationStartRequest(BaseModel):
    images_data: Dict[str, Any]
    seg_data: Dict[str, Any]
    preview: bool = False
    preview_index: Optional[int] = None


class SegmentationStartResponse(BaseModel):
    job_id: str
    status: str


class SegmentationStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    log: str = ""
    preview_path: Optional[str] = None
    preview_paths: List[str] = Field(default_factory=list)
    preview_index: Optional[int] = None
    progress_file: Optional[str] = None
    error: Optional[str] = None
