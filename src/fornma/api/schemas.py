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
    categorical_columns: List[str] = Field(default_factory=list)
    numeric_columns: List[str] = Field(default_factory=list)


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


class RegistrationStartRequest(BaseModel):
    images_data: Dict[str, Any]
    reg_data: Dict[str, Any]


class RegistrationStartResponse(BaseModel):
    job_id: str
    status: str


class RegistrationStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    log: str = ""
    done: int = 0
    total: int = 0
    progress_file: Optional[str] = None
    error: Optional[str] = None


class FociChannelsRequest(BaseModel):
    pkl_path: str


class FociChannelsResponse(BaseModel):
    channels: List[str]


class FociStartRequest(BaseModel):
    pkl_path: str
    save_path: str
    channels: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=lambda: ["overlay"])
    save_images: bool = True


class FociStartResponse(BaseModel):
    job_id: str
    status: str


class FociStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    log: str = ""
    progress_file: Optional[str] = None
    error: Optional[str] = None


class GraphPreviewRequest(BaseModel):
    datasets: List[Dict[str, str]] = Field(default_factory=list)
    paths: List[str] = Field(default_factory=list)
    graph_type: str = "scatter"
    plot_overtime: bool = False
    x: Optional[str] = None
    y: Optional[str] = None
    hue: Optional[str] = None
    size: Optional[str] = None
    violin_box: bool = True
    violin_points: bool = True
    box_outliers: bool = False
    compute_auc: bool = False
    control: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)
    frames: List[int] = Field(default_factory=list)
    dot: bool = False
    n: Optional[int] = None


class GraphPreviewResponse(BaseModel):
    figure: Dict[str, Any]
    columns: List[str] = Field(default_factory=list)
    message: str = ""


class GraphConditionsRequest(BaseModel):
    datasets: List[Dict[str, str]] = Field(default_factory=list)
    paths: List[str] = Field(default_factory=list)


class GraphConditionsResponse(BaseModel):
    conditions: List[str] = Field(default_factory=list)


class UMAPPreviewRequest(BaseModel):
    datasets: List[Dict[str, str]] = Field(default_factory=list)
    paths: List[str] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    n_neighbors: int = 15
    min_dist: float = 0.1
    metric: str = "euclidean"
    method: str = "umap"
    scale: bool = True
    max_points: int = 12000
    color_by: Optional[str] = None
    use_clusters: bool = False
    n_clusters: Optional[int] = None
    k_min: int = 2
    k_max: int = 12


class UMAPPreviewResponse(BaseModel):
    figure: Dict[str, Any]
    columns: List[str] = Field(default_factory=list)
    numeric_columns: List[str] = Field(default_factory=list)
    message: str = ""


class ClusteringElbowResponse(BaseModel):
    figure: Dict[str, Any]
    message: str = ""


class StatsTable(BaseModel):
    name: str
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)


class StatsRunRequest(BaseModel):
    paths: List[str] = Field(default_factory=list)
    method: str = "oneway"  # oneway | twoway | chi2 | chi2-subgroups
    numeric_col: Optional[str] = None
    group_col: Optional[str] = None
    group_col1: Optional[str] = None
    group_col2: Optional[str] = None
    category_col: Optional[str] = None
    condition_col: Optional[str] = None
    alpha: float = 0.05
    expected_min: float = 5.0
    correction_method: str = "auto"
    pairs_of_interest: List[str] = Field(default_factory=list)


class StatsRunResponse(BaseModel):
    method: str
    message: str = ""
    log: str = ""
    tables: List[StatsTable] = Field(default_factory=list)


class GatingBounds(BaseModel):
    x_min: float
    x_max: float
    y_min: float
    y_max: float


class GatingPreviewRequest(BaseModel):
    datasets: List[Dict[str, str]] = Field(default_factory=list)
    paths: List[str] = Field(default_factory=list)
    x_col: str = "Area"
    y_col: str = "NII"
    x_min: Optional[float] = None
    x_max: Optional[float] = None
    y_min: Optional[float] = None
    y_max: Optional[float] = None
    q_low: float = 0.05
    q_high: float = 0.95
    max_points: int = 12000
    color_by_dataset: bool = False


class GatingPreviewResponse(BaseModel):
    figure: Dict[str, Any]
    bounds: GatingBounds
    tables: List[StatsTable] = Field(default_factory=list)
    message: str = ""


class GatingApplyRequest(GatingPreviewRequest):
    output_dir: str


class GatingApplyResponse(BaseModel):
    bounds: GatingBounds
    tables: List[StatsTable] = Field(default_factory=list)
    output_dir: str
    files: List[str] = Field(default_factory=list)
    message: str = ""


class TrackingRunRequest(BaseModel):
    path_to_table: str
    output_dir: str
    image_dir: str
    image_col: str
    max_distance: int = 30
    time_window: int = 5
    max_split_distance: int = 10
    max_gap_closing_distance: int = 30


class TrackingFrameRequest(BaseModel):
    table_path: str
    frame: int = 0
    image_dir: Optional[str] = None
    image_col: Optional[str] = None
    preview_cache_dir: Optional[str] = None
    trail_window: int = 7
    show_complete_trail: bool = False


class TrackingSelection(BaseModel):
    frame: int
    cell: int
    track_id: int


class TrackingDeleteRequest(TrackingFrameRequest):
    selections: List[TrackingSelection] = Field(default_factory=list)


class TrackingLinkRequest(TrackingFrameRequest):
    selections: List[TrackingSelection] = Field(default_factory=list)


class TrackingPreviewResponse(BaseModel):
    table_path: str
    image_col: str
    preview_cache_dir: Optional[str] = None
    preview_image_path: Optional[str] = None
    frame: int
    max_frame: int
    total_rows: int
    total_tracks: int
    figure: Dict[str, Any]
    message: str = ""


class TrackingRunResponse(TrackingPreviewResponse):
    output_dir: str


class TrackingEditResponse(TrackingPreviewResponse):
    edited_rows: int = 0
