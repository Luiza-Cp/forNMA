import React, { useEffect, useMemo, useState } from "react";
import Plotly from "plotly.js-dist-min";
import { Button, Card, FieldTitle } from "./design-system/index.js";

const API_BASE = "http://127.0.0.1:8000";
const round2 = (n) => Math.round(Number(n) * 100) / 100;
const makeRowId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
const csvCell = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
const FORNMA_STAGES = [
  "Home",
  "Image Registration",
  "Segmentation",
  "Gating",
  "Foci Overlay",
  "NMA",
  "Plot Data",
  "Clustering",
  "Statistics",
  "Tracking",
];
const HOME_SECTIONS = [
  { id: "about", title: "About" },
  { id: "article", title: "Article" },
  { id: "tutorial-registration", title: "Image Registration" },
  { id: "tutorial-segmentation", title: "Segmentation" },
  { id: "tutorial-gating", title: "Gating" },
  { id: "tutorial-foci", title: "Foci Overlay" },
  { id: "tutorial-nma", title: "NMA" },
  { id: "tutorial-plot", title: "Plot Data" },
  { id: "tutorial-clustering", title: "Clustering" },
  { id: "tutorial-statistics", title: "Statistics" },
  { id: "tutorial-tracking", title: "Tracking" },
  { id: "resources", title: "Resources" },
];
const MODULE_TUTORIAL_SECTION = {
  "Image Registration": "tutorial-registration",
  Segmentation: "tutorial-segmentation",
  Gating: "tutorial-gating",
  "Foci Overlay": "tutorial-foci",
  NMA: "tutorial-nma",
  "Plot Data": "tutorial-plot",
  Clustering: "tutorial-clustering",
  Statistics: "tutorial-statistics",
  Tracking: "tutorial-tracking",
};
const PALETTE_OPTIONS = ["viridis", "plasma", "magma", "inferno", "cividis", "coolwarm", "Spectral", "RdBu"];
const sameArray = (a = [], b = []) => a.length === b.length && a.every((v, i) => v === b[i]);
const makeStatsFilterRow = () => ({ id: makeRowId(), column: "", values: [] });
const normalizeFilterOption = (value) => String(value ?? "").trim();
const copyText = async (text) => {
  const normalized = String(text ?? "");
  if (!normalized) return false;
  try {
    await navigator.clipboard.writeText(normalized);
    return true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = normalized;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return !!ok;
  }
};
const scrollToTopSmooth = () => {
  if (typeof window === "undefined") return;
  window.scrollTo({ top: 0, behavior: "smooth" });
};
const STORAGE_KEYS = {
  activeModule: "fornma.activeModule",
  plotJob: "fornma.plotJob",
  segJob: "fornma.segJob",
  regJob: "fornma.regJob",
  fociJob: "fornma.fociJob",
};
const DEFAULT_PLOT_JOB = {
  job_id: null,
  status: "idle",
  progress: 0,
  message: "",
  files: [],
  output_dir: "",
  error: "",
};
const DEFAULT_SEG_JOB = {
  job_id: null,
  status: "idle",
  progress: 0,
  message: "",
  log: "",
  preview_path: "",
  preview_paths: [],
  preview_index: null,
  error: "",
};
const DEFAULT_REG_JOB = {
  job_id: null,
  status: "idle",
  progress: 0,
  done: 0,
  total: 0,
  message: "",
  log: "",
  error: "",
};
const DEFAULT_FOCI_JOB = {
  job_id: null,
  status: "idle",
  progress: 0,
  message: "",
  log: "",
  error: "",
};
const PLOT_TYPES_REQUIRE_XY = new Set(["scatter"]);
const PLOT_TYPES_REQUIRE_Y = new Set(["scatter", "violin", "box", "dot", "bar", "line", "rolling-average"]);
const PLOT_TYPES_SUPPORT_DOT = new Set(["box"]);
const PLOT_TYPES_SUPPORT_SIZE = new Set(["scatter", "dot"]);
const PLOT_TYPES_SUPPORT_X = new Set(["scatter", "violin", "box", "dot", "bar", "line"]);
const initialPlotConfig = () => ({
  kind: "dot",
  dot: {
    column1: "",
    column2: "",
    hue_min: "",
    hue_max: "",
    size_min: "",
    size_max: "",
    sample_size: "",
    palette: "",
    single: false,
    overtime: false,
  },
  heatmap: {
    single: false,
    overtime: false,
    jointplot: false,
    palette: "",
  },
});
const initialPlotDataState = () => ({
  datasets: [{ id: makeRowId(), name: "Dataset 1", path: "", columns: null, enabled: true }],
  graph_type: "scatter",
  x: "",
  y: "",
  hue: "",
  size: "",
  violin_box: true,
  violin_points: true,
  box_outliers: false,
  line_rolling: false,
  compute_auc: false,
  control: "",
  controlOptions: [],
  conditionsText: "",
  framesText: "",
  dot: false,
  n: "",
  columns: [],
  categoricalColumns: [],
  columnsWarning: "",
  figure: null,
  message: "",
});
const initialClusteringState = () => ({
  datasets: [{ id: makeRowId(), name: "Dataset 1", path: "", enabled: true }],
  columnsAll: [],
  numericColumns: [],
  columns: [],
  n_neighbors: 15,
  min_dist: 0.1,
  metric: "euclidean",
  method: "umap",
  scale: true,
  max_points: 12000,
  use_clusters: false,
  n_clusters: 8,
  k_min: 2,
  k_max: 12,
  color_by: "",
  figure: null,
  elbowFigure: null,
  message: "",
});
const initialStatsState = () => ({
  datasets: [{ id: makeRowId(), name: "Dataset 1", path: "", enabled: true }],
  method: "oneway",
  columns: [],
  categoricalColumns: [],
  numeric_col: "",
  group_col: "",
  group_col1: "",
  group_col2: "",
  category_col: "",
  condition_col: "",
  alpha: 0.05,
  expected_min: 5.0,
  correction_method: "auto",
  pairs_text: "",
  filters: [makeStatsFilterRow()],
  filterValueOptions: {},
  tables: [],
  log: "",
  message: "",
});
const initialGatingState = () => ({
  datasets: [{ id: makeRowId(), name: "Dataset 1", path: "", enabled: true }],
  columns: [],
  numericColumns: [],
  x_col: "",
  y_col: "",
  x_min: "",
  x_max: "",
  y_min: "",
  y_max: "",
  q_low: 0.05,
  q_high: 0.95,
  max_points: 12000,
  color_by_dataset: false,
  output_dir: "",
  figure: null,
  tables: [],
  files: [],
  message: "",
});
const initialTrackingState = () => ({
  path_to_table: "",
  image_dir: "",
  image_col: "",
  columns: [],
  preview_cache_dir: "",
  preview_image_path: "",
  preview_nonce: 0,
  viewer_w: 0,
  viewer_h: 0,
  max_distance: 30,
  time_window: 5,
  max_split_distance: 10,
  max_gap_closing_distance: 30,
  table_path: "",
  frame: 0,
  max_frame: 0,
  trail_window: 7,
  show_complete_trail: false,
  figure: null,
  selected: [],
  selected_markers: [],
  undo_checkpoint_path: "",
  saved_progress_path: "",
  finish_open: false,
  message: "",
  total_rows: 0,
  total_tracks: 0,
  workflow_stage: "step1",
  save_results_dir: "",
});

function readStorage(key, fallback) {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function Tip({ text }) {
  return (
    <span className="tip-badge" title={text} aria-label={text}>
      i
    </span>
  );
}

function HomeLeftPanel({ activeSection, onSelectSection }) {
  return (
    <Card as="aside" className="panel seg-panel home-panel" variant="panel">
      <div className="seg-header">
        <h3>Home Settings</h3>
        <p className="hint">Use this sidebar as an index for the software overview, tutorials, and useful links.</p>
      </div>
      <div className="seg-scroll">
        <div className="home-index">
          {HOME_SECTIONS.map((section) => (
            <button
              key={section.id}
              type="button"
              className={`home-index-item ${activeSection === section.id ? "active" : ""}`}
              onClick={() => onSelectSection(section.id)}
            >
              {section.title}
            </button>
          ))}
        </div>
      </div>
    </Card>
  );
}

function previewMeta(path) {
  const parts = String(path || "").split("/").filter(Boolean);
  const channel = parts.length >= 2 ? parts[parts.length - 2] : "";
  const condition = parts.length >= 3 ? parts[parts.length - 3] : "";
  return { channel, condition };
}

function SegmentationLeftPanel({ onPickDirectory, onStartSegmentation, onStopSegmentation, onResetSegmentation, segJob }) {
  const resetSegForm = () => {
    const ok = window.confirm("Reset all segmentation settings to defaults?");
    if (!ok) return;
    onResetSegmentation?.();
  };

  const [savePath, setSavePath] = useState("");
  const [imagesData, setImagesData] = useState({
    channels: [{ id: "ch1", name: "Channel 1" }],
    rows: [{ condition: "Control", ch1: "" }],
  });
  const [modalOpen, setModalOpen] = useState(false);
  const [modalError, setModalError] = useState("");
  const [summaryText, setSummaryText] = useState("No images loaded yet.");
  const [nuclearChannel, setNuclearChannel] = useState("ch1");
  const [fociEnabled, setFociEnabled] = useState(false);
  const [fociChannels, setFociChannels] = useState([]);
  const [cytoEnabled, setCytoEnabled] = useState(false);
  const [cytoChannels, setCytoChannels] = useState([]);
  const [segMethod, setSegMethod] = useState("fornma");
  const [overtime, setOvertime] = useState(false);
  const [magnification, setMagnification] = useState(20);
  const [pixelSize, setPixelSize] = useState(0.6);
  const [rescaleIntensity, setRescaleIntensity] = useState(false);
  const [removeBackground, setRemoveBackground] = useState(false);
  const [rollingRadius, setRollingRadius] = useState(50);
  const [fornmaThreshold, setFornmaThreshold] = useState("triangle");
  const [fornmaOffset, setFornmaOffset] = useState(5);
  const [fornmaSmooth, setFornmaSmooth] = useState(12);
  const [fornmaAdjustSize, setFornmaAdjustSize] = useState(0);
  const [fornmaCutEdges, setFornmaCutEdges] = useState(0.7);
  const [fornmaFindLow, setFornmaFindLow] = useState(false);
  const [fornmaWeakly, setFornmaWeakly] = useState(false);
  const [cellposeDiameter, setCellposeDiameter] = useState(25);
  const [cellposeFlow, setCellposeFlow] = useState(0.4);
  const [cellposeMask, setCellposeMask] = useState(0);
  const [cellposeCellprob, setCellposeCellprob] = useState(-3);
  const [cellposeUseGpu, setCellposeUseGpu] = useState(true);
  const [cellposeInvert, setCellposeInvert] = useState(true);
  const [advEnable, setAdvEnable] = useState({
    shape: true,
    eccentricity: false,
    min_size: false,
    max_size: false,
    min_radius: false,
    max_radius: false,
  });
  const [advValues, setAdvValues] = useState({
    shape: 0.88,
    eccentricity: 0.8,
    min_size: 100,
    max_size: 10000,
    min_radius: 4,
    max_radius: 120,
  });
  const [channelCfg, setChannelCfg] = useState({});
  const channels = imagesData.channels || [];
  const channelIds = new Set(channels.map((c) => c.id));

  useEffect(() => {
    if (channels.length === 0) return;
    if (!channelIds.has(nuclearChannel)) {
      setNuclearChannel(channels[0].id);
    }
    setFociChannels((prev) => prev.filter((id) => channelIds.has(id)));
    setCytoChannels((prev) => prev.filter((id) => channelIds.has(id)));
  }, [imagesData.channels]);

  useEffect(() => {
    setChannelCfg((prev) => {
      const next = { ...prev };
      channels.forEach((ch) => {
        if (next[ch.id]) return;
        next[ch.id] = {
          rescale_intensity: true,
          remove_background: true,
          rolling_ball_radius: 40,
          match_histograms: false,
          ring_size: 3,
          use_ellipse: true,
          foci_min_size: 7,
          foci_max_size_enable: false,
          foci_max_size: 20,
          foci_min_int_enable: false,
          foci_min_int: 0,
          foci_max_int_enable: false,
          foci_max_int: 1,
          foci_prominence: 1.2,
        };
      });
      Object.keys(next).forEach((k) => {
        if (!channelIds.has(k)) delete next[k];
      });
      return next;
    });
  }, [imagesData.channels]);

  const setAdvToggle = (key, value) => setAdvEnable((prev) => ({ ...prev, [key]: value }));
  const setAdvValue = (key, value) => setAdvValues((prev) => ({ ...prev, [key]: value }));
  const setChCfg = (chId, patch) => {
    setChannelCfg((prev) => ({ ...prev, [chId]: { ...(prev[chId] || {}), ...patch } }));
  };

  const addCondition = () => {
    setImagesData((prev) => {
      const row = { condition: "" };
      (prev.channels || []).forEach((ch) => { row[ch.id] = ""; });
      return { ...prev, rows: [...(prev.rows || []), row] };
    });
  };

  const addChannel = () => {
    setImagesData((prev) => {
      const maxIdx = Math.max(0, ...(prev.channels || []).map((ch) => Number((ch.id || "").replace("ch", "")) || 0));
      const newId = `ch${maxIdx + 1}`;
      const nextChannels = [...(prev.channels || []), { id: newId, name: `Channel ${maxIdx + 1}` }];
      const nextRows = (prev.rows || []).map((r) => ({ ...r, [newId]: "" }));
      return { ...prev, channels: nextChannels, rows: nextRows };
    });
  };

  const removeCondition = (rowIdx) => {
    setImagesData((prev) => ({
      ...prev,
      rows: (prev.rows || []).filter((_, i) => i !== rowIdx),
    }));
  };

  const removeChannel = (chId) => {
    setImagesData((prev) => {
      const nextChannels = (prev.channels || []).filter((ch) => ch.id !== chId);
      const nextRows = (prev.rows || []).map((r) => {
        const copy = { ...r };
        delete copy[chId];
        return copy;
      });
      return { ...prev, channels: nextChannels, rows: nextRows };
    });
    setFociChannels((prev) => prev.filter((id) => id !== chId));
    setCytoChannels((prev) => prev.filter((id) => id !== chId));
  };

  const updateChannelName = (chId, name) => {
    setImagesData((prev) => ({
      ...prev,
      channels: (prev.channels || []).map((ch) => (ch.id === chId ? { ...ch, name } : ch)),
    }));
  };

  const updateCondition = (rowIdx, condition) => {
    setImagesData((prev) => ({
      ...prev,
      rows: (prev.rows || []).map((r, i) => (i === rowIdx ? { ...r, condition } : r)),
    }));
  };

  const updatePathCell = (rowIdx, chId, path) => {
    setImagesData((prev) => ({
      ...prev,
      rows: (prev.rows || []).map((r, i) => (i === rowIdx ? { ...r, [chId]: path } : r)),
    }));
  };

  const browsePathCell = async (rowIdx, chId) => {
    const picked = await onPickDirectory();
    if (!picked) return;
    updatePathCell(rowIdx, chId, picked);
  };

  const saveImagesTable = () => {
    const errors = [];
    const chs = imagesData.channels || [];
    const rows = imagesData.rows || [];

    const chNames = chs.map((c) => (c.name || "").trim());
    if (chNames.some((n) => !n)) errors.push("There are channels without a name.");
    if (new Set(chNames).size !== chNames.length) errors.push("Channel names must be unique.");

    const conds = rows.map((r) => (r.condition || "").trim());
    if (conds.some((c) => !c)) errors.push("There are conditions without a name.");
    if (new Set(conds).size !== conds.length) errors.push("Condition names must be unique.");

    rows.forEach((r, idx) => {
      chs.forEach((ch) => {
        const p = (r[ch.id] || "").trim();
        if (!p) errors.push(`Row ${idx + 1} — ${ch.name}: empty path.`);
      });
    });

    if (errors.length) {
      setModalError(errors.join("\n"));
      return;
    }

    const lines = [`Image selection OK:`, `Conditions: ${rows.length} | Channels: ${chs.length}`, ""];
    rows.forEach((r) => {
      lines.push(`- ${r.condition}:`);
      chs.forEach((ch) => lines.push(`    ${ch.name}: ${r[ch.id] || ""}`));
    });
    setSummaryText(lines.join("\n"));
    setModalError("");
    setModalOpen(false);
  };

  const counterText = `Channels: ${channels.length} | Conditions: ${(imagesData.rows || []).length}`;

  const buildSegDataPayload = () => {
    const channelsMap = {};
    channels.forEach((ch) => {
      const cfg = channelCfg[ch.id] || {};
      channelsMap[ch.id] = {
        rescale_intensity: !!cfg.rescale_intensity,
        remove_background: !!cfg.remove_background,
        rolling_ball_radius: Number(cfg.rolling_ball_radius ?? 40),
        match_histograms: !!cfg.match_histograms,
        ring_size: showNumber(cfg.ring_size, 3),
        use_ellipse: !!cfg.use_ellipse,
        wants_foci: fociEnabled && fociChannels.includes(ch.id),
        foci_min_size: showNumber(cfg.foci_min_size, 7),
        foci_max_size: cfg.foci_max_size_enable ? showNumber(cfg.foci_max_size, 20) : false,
        foci_min_int: cfg.foci_min_int_enable ? showNumber(cfg.foci_min_int, 0) : false,
        foci_max_int: cfg.foci_max_int_enable ? showNumber(cfg.foci_max_int, 1) : false,
        foci_prominence: showNumber(cfg.foci_prominence, 1.2),
      };
    });

    return {
      general: {
        path_to_save: savePath,
        channel_with_nuclei: nuclearChannel || null,
        overtime: !!overtime,
      },
      segmentation: {
        magnification: showNumber(magnification, 20),
        "pixel-size": showNumber(pixelSize, 0.6),
        "rescale-intensity": !!rescaleIntensity,
        "remove-bg": !!removeBackground,
        "rolling-radius": showNumber(rollingRadius, 50),
        seg_method: segMethod,
      },
      fornma: {
        threshold: fornmaThreshold,
        offset: showNumber(fornmaOffset, 5),
        smooth: showNumber(fornmaSmooth, 12),
        adjust_size: showNumber(fornmaAdjustSize, 0),
        cut_edges: showNumber(fornmaCutEdges, 0.7),
        find_low_intensity_nucleus: !!fornmaFindLow,
        weakly_labeled: !!fornmaWeakly,
      },
      cellpose: {
        diameter: showNumber(cellposeDiameter, 25),
        flow_threshold: showNumber(cellposeFlow, 0.4),
        mask_threshold: showNumber(cellposeMask, 0),
        cellprob_threshold: showNumber(cellposeCellprob, -3),
        use_gpu: !!cellposeUseGpu,
        invert: !!cellposeInvert,
      },
      filters: {
        shape: advEnable.shape ? showNumber(advValues.shape, 0.88) : null,
        eccentricity: advEnable.eccentricity ? showNumber(advValues.eccentricity, 0.8) : null,
        minimum_size: advEnable.min_size ? showNumber(advValues.min_size, 100) : null,
        maximum_size: advEnable.max_size ? showNumber(advValues.max_size, 10000) : null,
        minimum_radius: advEnable.min_radius ? showNumber(advValues.min_radius, 4) : null,
        maximum_radius: advEnable.max_radius ? showNumber(advValues.max_radius, 120) : null,
      },
      channels: channelsMap,
    };
  };

  const showNumber = (v, fallback) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : fallback;
  };

  const startSeg = async (preview) => {
    const payload = {
      images_data: imagesData,
      seg_data: buildSegDataPayload(),
      preview: !!preview,
      preview_index: preview ? 0 : null,
    };
    await onStartSegmentation(payload);
  };

  const segRunning =
    segJob?.status === "starting" ||
    segJob?.status === "running" ||
    segJob?.status === "queued" ||
    segJob?.status === "canceling";

  return (
    <>
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Segmentation Settings</h3>
        <p className="hint">Configure image inputs, nucleus detection, and per-channel measurement options.</p>
        <div className="row">
          <button className="secondary" onClick={() => { setModalError(""); setModalOpen(true); }}>Load images</button>
          <button className="ghost" onClick={resetSegForm} disabled={segRunning}>Reset settings</button>
        </div>
        <div className="field-head">Saving path <Tip text="Where outputs (tables, images, logs) will be written." /></div>
        <div className="row path-row">
          <input
            className="input"
            value={savePath}
            onChange={(e) => setSavePath(e.target.value)}
            placeholder="Folder to save results..."
          />
          <button
            className="ghost"
            onClick={async () => {
              const p = await onPickDirectory();
              if (p) setSavePath(p);
            }}
          >
            Browse
          </button>
        </div>
        <details className="seg-summary">
          <summary>Image selection summary</summary>
          <pre>{summaryText}</pre>
        </details>
      </div>

      <div className="seg-scroll">
        <details open className="seg-section">
          <summary>General Settings</summary>
          <div className="seg-body">
            <div className="field-head">Nuclear Detection <Tip text="Pick the channel that contains nuclei for detection." /></div>
            <select className="input" value={nuclearChannel} onChange={(e) => setNuclearChannel(e.target.value)}>
              <option value="">Select one channel...</option>
              {channels.map((ch) => <option key={ch.id} value={ch.id}>{ch.name}</option>)}
            </select>
            <label className="checkbox">
              <input type="checkbox" checked={overtime} onChange={(e) => setOvertime(e.target.checked)} />
              Overtime <Tip text="Check this if images represent time sequence." />
            </label>
            <label className="checkbox">
              <input type="checkbox" checked={fociEnabled} onChange={(e) => setFociEnabled(e.target.checked)} />
              Foci <Tip text="Enable spot (foci) detection and extra foci parameters for selected channels." />
            </label>
            {fociEnabled && (
              <>
                <div className="field-head">Channels for Foci</div>
                <div className="multi-picker">
                  {channels.map((ch) => (
                    <label className="checkbox" key={`f-${ch.id}`}>
                      <input
                        type="checkbox"
                        checked={fociChannels.includes(ch.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFociChannels((prev) => Array.from(new Set([...prev, ch.id])));
                          } else {
                            setFociChannels((prev) => prev.filter((id) => id !== ch.id));
                          }
                        }}
                      />
                      {ch.name}
                    </label>
                  ))}
                </div>
                <p className="hint">You can select multiple channels.</p>
              </>
            )}
            <label className="checkbox">
              <input type="checkbox" checked={cytoEnabled} onChange={(e) => setCytoEnabled(e.target.checked)} />
              Cytoplasmatic Ring <Tip text="Enable translocation (cytoplasmatic ring) parameters for selected channels." />
            </label>
            {cytoEnabled && (
              <>
                <div className="field-head">Channels for Cytoplasmatic Ring</div>
                <div className="multi-picker">
                  {channels.map((ch) => (
                    <label className="checkbox" key={`c-${ch.id}`}>
                      <input
                        type="checkbox"
                        checked={cytoChannels.includes(ch.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setCytoChannels((prev) => Array.from(new Set([...prev, ch.id])));
                          } else {
                            setCytoChannels((prev) => prev.filter((id) => id !== ch.id));
                          }
                        }}
                      />
                      {ch.name}
                    </label>
                  ))}
                </div>
                <p className="hint">You can select multiple channels.</p>
              </>
            )}
          </div>
        </details>

        <details open className="seg-section">
          <summary>Segmentation Settings</summary>
          <div className="seg-body">
            <div className="row">
              <div className="metric">
                <label>Magnification <Tip text="Numeric objective magnification used for acquisition (e.g. 20x)." /></label>
                <input type="number" className="input" value={magnification} onChange={(e) => setMagnification(e.target.value)} />
              </div>
            </div>
            <div className="row">
              <div className="metric">
                <label>Pixel Size <Tip text="Real sample distance represented by each pixel." /></label>
                <input type="number" className="input" value={pixelSize} onChange={(e) => setPixelSize(e.target.value)} step="0.1" />
              </div>
            </div>
            <label className="checkbox">
              <input type="checkbox" checked={rescaleIntensity} onChange={(e) => setRescaleIntensity(e.target.checked)} />
              Rescale Intensity <Tip text="Normalize intensity values to improve contrast for segmentation." />
            </label>
            <label className="checkbox">
              <input type="checkbox" checked={removeBackground} onChange={(e) => setRemoveBackground(e.target.checked)} />
              Remove Background <Tip text="Subtract smooth background before segmentation." />
            </label>
            <div className="field-head">Segmentation Method <Tip text="Choose forNMA (faster) or Cellpose (more robust) pipeline." /></div>
            <div className="row">
              <label className="radio"><input type="radio" checked={segMethod === "fornma"} onChange={() => setSegMethod("fornma")} /> forNMA</label>
              <label className="radio"><input type="radio" checked={segMethod === "cellpose"} onChange={() => setSegMethod("cellpose")} /> Cellpose</label>
            </div>
            {segMethod === "fornma" ? (
              <>
                <h4 className="seg-subtitle">forNMA Parameters</h4>
                <div className="field-head">Threshold <Tip text="Threshold strategy used to separate nuclei from background." /></div>
                <div className="seg-threshold-wrap">
                <select className="input seg-threshold-input" value={fornmaThreshold} onChange={(e) => setFornmaThreshold(e.target.value)}>
                  <option value="isodata">Isodata</option>
                  <option value="li">Li</option>
                  <option value="mean">Mean</option>
                  <option value="minimum">Minimum</option>
                  <option value="median">Median</option>
                  <option value="multi_otsu">Multi-Otsu</option>
                  <option value="otsu">Otsu</option>
                  <option value="triangle">Triangle</option>
                  <option value="yen">Yen</option>
                  <option value="local_mean">Local Mean</option>
                  <option value="local_gaussian">Local Gaussian</option>
                </select>
                </div>
                <label className="checkbox">
                  <input type="checkbox" checked={fornmaFindLow} onChange={(e) => setFornmaFindLow(e.target.checked)} />
                  Find low-intensity nuclei <Tip text="Extra pass to recover missed nuclei in low-intensity regions." />
                </label>
                <label className="checkbox">
                  <input type="checkbox" checked={fornmaWeakly} onChange={(e) => setFornmaWeakly(e.target.checked)} />
                  Weakly labeled images <Tip text="Enable additional handling for weak staining/unclear contours." />
                </label>
              </>
            ) : (
              <>
                <h4 className="seg-subtitle">Cellpose Parameters</h4>
                <div className="field-head">Diameter (px) <Tip text="Typical cell diameter in pixels for Cellpose scale normalization." /></div>
                <input className="input" type="number" value={cellposeDiameter} onChange={(e) => setCellposeDiameter(e.target.value)} />
                <div className="field-head">Flow Threshold <Tip text="Maximum flow error allowed; lower values are stricter." /></div>
                <input className="input" type="number" value={cellposeFlow} onChange={(e) => setCellposeFlow(e.target.value)} step="0.05" />
                <div className="field-head">Mask Threshold <Tip text="Threshold for mask inclusion from probability maps." /></div>
                <input className="input" type="number" value={cellposeMask} onChange={(e) => setCellposeMask(e.target.value)} step="0.5" />
                <div className="field-head">Cellprob Threshold <Tip text="Cell probability threshold; lower values include more cells." /></div>
                <input className="input" type="number" value={cellposeCellprob} onChange={(e) => setCellposeCellprob(e.target.value)} step="0.5" />
                <label className="checkbox">
                  <input type="checkbox" checked={cellposeUseGpu} onChange={(e) => setCellposeUseGpu(e.target.checked)} />
                  Use GPU <Tip text="Enable GPU acceleration if available." />
                </label>
                <label className="checkbox">
                  <input type="checkbox" checked={cellposeInvert} onChange={(e) => setCellposeInvert(e.target.checked)} />
                  Invert Intensities <Tip text="Invert image values before segmentation when needed." />
                </label>
              </>
            )}
          </div>
        </details>

        <details open className="seg-section">
          <summary>Advanced Settings</summary>
          <div className="seg-body">
            <label className="checkbox">
              <input type="checkbox" checked={advEnable.shape} onChange={(e) => setAdvToggle("shape", e.target.checked)} />
              Shape <Tip text="Filter by irregularity/shape metric. Enable to set a threshold." />
            </label>
            {advEnable.shape && <input className="input" type="number" step="0.01" value={advValues.shape} onChange={(e) => setAdvValue("shape", e.target.value)} />}

            <label className="checkbox">
              <input type="checkbox" checked={advEnable.eccentricity} onChange={(e) => setAdvToggle("eccentricity", e.target.checked)} />
              Eccentricity <Tip text="0 = circle, closer to 1 = elongated nuclei." />
            </label>
            {advEnable.eccentricity && <input className="input" type="number" step="0.01" value={advValues.eccentricity} onChange={(e) => setAdvValue("eccentricity", e.target.value)} />}

            <label className="checkbox">
              <input type="checkbox" checked={advEnable.min_size} onChange={(e) => setAdvToggle("min_size", e.target.checked)} />
              Min Size <Tip text="Minimum nucleus area (px²)." />
            </label>
            {advEnable.min_size && <input className="input" type="number" step="1" value={advValues.min_size} onChange={(e) => setAdvValue("min_size", e.target.value)} />}

            <label className="checkbox">
              <input type="checkbox" checked={advEnable.max_size} onChange={(e) => setAdvToggle("max_size", e.target.checked)} />
              Max Size <Tip text="Maximum nucleus area (px²)." />
            </label>
            {advEnable.max_size && <input className="input" type="number" step="1" value={advValues.max_size} onChange={(e) => setAdvValue("max_size", e.target.value)} />}

            <label className="checkbox">
              <input type="checkbox" checked={advEnable.min_radius} onChange={(e) => setAdvToggle("min_radius", e.target.checked)} />
              Min Radius <Tip text="Minimum nucleus radius (px)." />
            </label>
            {advEnable.min_radius && <input className="input" type="number" step="1" value={advValues.min_radius} onChange={(e) => setAdvValue("min_radius", e.target.value)} />}

            <label className="checkbox">
              <input type="checkbox" checked={advEnable.max_radius} onChange={(e) => setAdvToggle("max_radius", e.target.checked)} />
              Max Radius <Tip text="Maximum nucleus radius (px)." />
            </label>
            {advEnable.max_radius && <input className="input" type="number" step="1" value={advValues.max_radius} onChange={(e) => setAdvValue("max_radius", e.target.value)} />}
          </div>
        </details>

        <details open className="seg-section">
          <summary>Channel Settings</summary>
          <div className="seg-body">
            {channels.length === 0 ? (
              <p className="hint">No channels loaded yet. Use Load images and save the table.</p>
            ) : (
              channels.map((ch) => {
                const cfg = channelCfg[ch.id] || {};
                const showRing = cytoEnabled && cytoChannels.includes(ch.id);
                const showFoci = fociEnabled && fociChannels.includes(ch.id);
                return (
                  <details key={`ch-settings-${ch.id}`} className="seg-section">
                    <summary>{ch.name}</summary>
                    <div className="seg-body">
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={!!cfg.rescale_intensity}
                          onChange={(e) => setChCfg(ch.id, { rescale_intensity: e.target.checked })}
                        />
                        Rescale intensity <Tip text="Re-distributes channel intensity values to improve contrast." />
                      </label>

                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={!!cfg.remove_background}
                          onChange={(e) => setChCfg(ch.id, { remove_background: e.target.checked })}
                        />
                        Remove background <Tip text="Apply rolling-ball background subtraction in this channel." />
                      </label>
                      {cfg.remove_background && (
                        <input
                          className="input"
                          type="number"
                          min="1"
                          step="1"
                          value={cfg.rolling_ball_radius ?? 40}
                          onChange={(e) => setChCfg(ch.id, { rolling_ball_radius: e.target.value })}
                          placeholder="Rolling-ball radius (px)"
                        />
                      )}

                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={!!cfg.match_histograms}
                          onChange={(e) => setChCfg(ch.id, { match_histograms: e.target.checked })}
                        />
                        Match histograms <Tip text="Normalize histogram across images for this channel." />
                      </label>

                      {showRing && (
                        <>
                          <h4 className="seg-subtitle">Cytoplasmatic Ring</h4>
                          <div className="field-head">Ring size (px) <Tip text="Width of cytoplasmatic ring for translocation measurement." /></div>
                          <input
                            className="input"
                            type="number"
                            min="1"
                            step="1"
                            value={cfg.ring_size ?? 3}
                            onChange={(e) => setChCfg(ch.id, { ring_size: e.target.value })}
                          />
                          <label className="checkbox">
                            <input
                              type="checkbox"
                              checked={!!cfg.use_ellipse}
                              onChange={(e) => setChCfg(ch.id, { use_ellipse: e.target.checked })}
                            />
                            Use ellipse <Tip text="Use ellipse approximation for ring calculation." />
                          </label>
                        </>
                      )}

                      {showFoci && (
                        <>
                          <h4 className="seg-subtitle">Foci Detection</h4>
                          <div className="field-head">Min foci size (px²) <Tip text="Minimum foci area to keep." /></div>
                          <input
                            className="input"
                            type="number"
                            min="1"
                            step="1"
                            value={cfg.foci_min_size ?? 7}
                            onChange={(e) => setChCfg(ch.id, { foci_min_size: e.target.value })}
                          />

                          <label className="checkbox">
                            <input
                              type="checkbox"
                              checked={!!cfg.foci_max_size_enable}
                              onChange={(e) => setChCfg(ch.id, { foci_max_size_enable: e.target.checked })}
                            />
                            Max foci size <Tip text="Enable to cap foci maximum area." />
                          </label>
                          {cfg.foci_max_size_enable && (
                            <input
                              className="input"
                              type="number"
                              min="1"
                              step="1"
                              value={cfg.foci_max_size ?? 20}
                              onChange={(e) => setChCfg(ch.id, { foci_max_size: e.target.value })}
                            />
                          )}

                          <label className="checkbox">
                            <input
                              type="checkbox"
                              checked={!!cfg.foci_min_int_enable}
                              onChange={(e) => setChCfg(ch.id, { foci_min_int_enable: e.target.checked })}
                            />
                            Min foci intensity <Tip text="Enable to enforce minimum spot intensity." />
                          </label>
                          {cfg.foci_min_int_enable && (
                            <input
                              className="input"
                              type="number"
                              step="0.1"
                              value={cfg.foci_min_int ?? 0}
                              onChange={(e) => setChCfg(ch.id, { foci_min_int: e.target.value })}
                            />
                          )}

                          <label className="checkbox">
                            <input
                              type="checkbox"
                              checked={!!cfg.foci_max_int_enable}
                              onChange={(e) => setChCfg(ch.id, { foci_max_int_enable: e.target.checked })}
                            />
                            Max foci intensity <Tip text="Enable to cap spot intensity." />
                          </label>
                          {cfg.foci_max_int_enable && (
                            <input
                              className="input"
                              type="number"
                              step="0.1"
                              value={cfg.foci_max_int ?? 1}
                              onChange={(e) => setChCfg(ch.id, { foci_max_int: e.target.value })}
                            />
                          )}

                          <div className="field-head">Foci prominence <Tip text="How much a spot must stand out from background." /></div>
                          <input
                            className="input"
                            type="number"
                            step="0.1"
                            min="0"
                            value={cfg.foci_prominence ?? 1.2}
                            onChange={(e) => setChCfg(ch.id, { foci_prominence: e.target.value })}
                          />
                        </>
                      )}
                    </div>
                  </details>
                );
              })
            )}
          </div>
        </details>
      </div>

      <div className="seg-footer">
        <button className="secondary" onClick={() => startSeg(true)} disabled={segRunning}>Preview</button>
        <button className="primary" onClick={() => startSeg(false)} disabled={segRunning}>Run</button>
        <button className="ghost" onClick={() => onStopSegmentation()} disabled={!segRunning}>Stop</button>
      </div>
    </Card>
    {modalOpen && (
      <div className="seg-modal-backdrop" onClick={() => setModalOpen(false)}>
        <div className="seg-modal" onClick={(e) => e.stopPropagation()}>
          <div className="seg-modal-header">
            <h4>Load images — conditions × channels</h4>
          </div>
          <div className="seg-modal-body">
            {modalError && <div className="seg-modal-error">{modalError}</div>}
            <div className="seg-load-table-wrap">
              <table className="seg-load-table">
                <thead>
                  <tr>
                    <th>Condition</th>
                    {channels.map((ch) => (
                      <th key={`h-${ch.id}`}>
                        <div className="row row-between">
                          <input
                            className="input"
                            value={ch.name}
                            onChange={(e) => updateChannelName(ch.id, e.target.value)}
                            placeholder="Channel name"
                          />
                          <button
                            className="ghost btn-small"
                            onClick={() => removeChannel(ch.id)}
                            disabled={channels.length <= 1}
                            title="Remove channel"
                          >
                            Remove
                          </button>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(imagesData.rows || []).map((row, rIdx) => (
                    <tr key={`r-${rIdx}`}>
                      <td>
                        <div className="row row-between">
                          <input
                            className="input"
                            value={row.condition || ""}
                            onChange={(e) => updateCondition(rIdx, e.target.value)}
                            placeholder="Condition name"
                          />
                          <button
                            className="ghost btn-small"
                            onClick={() => removeCondition(rIdx)}
                            disabled={(imagesData.rows || []).length <= 1}
                            title="Remove condition"
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                      {channels.map((ch) => (
                        <td key={`c-${rIdx}-${ch.id}`}>
                          <div className="row path-row">
                            <input
                              className="input"
                              value={row[ch.id] || ""}
                              onChange={(e) => updatePathCell(rIdx, ch.id, e.target.value)}
                              placeholder={`Path to ${ch.name}`}
                            />
                            <button className="ghost btn-small" onClick={() => browsePathCell(rIdx, ch.id)}>Browse</button>
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="seg-modal-footer">
            <span className="hint">{counterText}</span>
            <button className="ghost" onClick={addCondition}>+ Add condition</button>
            <button className="ghost" onClick={addChannel}>+ Add channel</button>
            <button className="primary" onClick={saveImagesTable}>Save</button>
            <button className="secondary" onClick={() => setModalOpen(false)}>Close</button>
          </div>
        </div>
      </div>
    )}
    </>
  );
}

function RegistrationLeftPanel({ onPickDirectory, onStartRegistration, onStopRegistration, regJob }) {
  const [savePath, setSavePath] = useState("");
  const [imagesData, setImagesData] = useState({
    channels: [{ id: "ch1", name: "Channel 1" }],
    rows: [{ condition: "Control", ch1: "" }],
  });
  const [modalOpen, setModalOpen] = useState(false);
  const [modalError, setModalError] = useState("");
  const [summaryText, setSummaryText] = useState("No images loaded yet.");
  const [referenceChannel, setReferenceChannel] = useState("");
  const [movingChannels, setMovingChannels] = useState([]);
  const [cropOutput, setCropOutput] = useState(true);

  const channels = imagesData.channels || [];
  const channelIds = new Set(channels.map((c) => c.id));
  const regRunning = ["starting", "queued", "running", "canceling"].includes(regJob?.status || "idle");

  useEffect(() => {
    if (channels.length === 0) return;
    if (!channelIds.has(referenceChannel)) {
      setReferenceChannel(channels[0].id);
    }
    setMovingChannels((prev) => prev.filter((id) => channelIds.has(id) && id !== referenceChannel));
  }, [imagesData.channels, referenceChannel]);

  const addCondition = () => {
    setImagesData((prev) => {
      const row = { condition: "" };
      (prev.channels || []).forEach((ch) => { row[ch.id] = ""; });
      return { ...prev, rows: [...(prev.rows || []), row] };
    });
  };

  const addChannel = () => {
    setImagesData((prev) => {
      const maxIdx = Math.max(0, ...(prev.channels || []).map((ch) => Number((ch.id || "").replace("ch", "")) || 0));
      const newId = `ch${maxIdx + 1}`;
      const nextChannels = [...(prev.channels || []), { id: newId, name: `Channel ${maxIdx + 1}` }];
      const nextRows = (prev.rows || []).map((r) => ({ ...r, [newId]: "" }));
      return { ...prev, channels: nextChannels, rows: nextRows };
    });
  };

  const removeCondition = (rowIdx) => {
    setImagesData((prev) => ({ ...prev, rows: (prev.rows || []).filter((_, i) => i !== rowIdx) }));
  };

  const removeChannel = (chId) => {
    setImagesData((prev) => {
      const nextChannels = (prev.channels || []).filter((ch) => ch.id !== chId);
      const nextRows = (prev.rows || []).map((r) => {
        const copy = { ...r };
        delete copy[chId];
        return copy;
      });
      return { ...prev, channels: nextChannels, rows: nextRows };
    });
    if (referenceChannel === chId) setReferenceChannel("");
    setMovingChannels((prev) => prev.filter((id) => id !== chId));
  };

  const updateChannelName = (chId, name) => {
    setImagesData((prev) => ({
      ...prev,
      channels: (prev.channels || []).map((ch) => (ch.id === chId ? { ...ch, name } : ch)),
    }));
  };

  const updateCondition = (rowIdx, condition) => {
    setImagesData((prev) => ({
      ...prev,
      rows: (prev.rows || []).map((r, i) => (i === rowIdx ? { ...r, condition } : r)),
    }));
  };

  const updatePathCell = (rowIdx, chId, path) => {
    setImagesData((prev) => ({
      ...prev,
      rows: (prev.rows || []).map((r, i) => (i === rowIdx ? { ...r, [chId]: path } : r)),
    }));
  };

  const browsePathCell = async (rowIdx, chId) => {
    const picked = await onPickDirectory();
    if (!picked) return;
    updatePathCell(rowIdx, chId, picked);
  };

  const saveImagesTable = () => {
    const errors = [];
    const chs = imagesData.channels || [];
    const rows = imagesData.rows || [];

    const chNames = chs.map((c) => (c.name || "").trim());
    if (chNames.some((n) => !n)) errors.push("There are channels without a name.");
    if (new Set(chNames).size !== chNames.length) errors.push("Channel names must be unique.");

    const conds = rows.map((r) => (r.condition || "").trim());
    if (conds.some((c) => !c)) errors.push("There are conditions without a name.");
    if (new Set(conds).size !== conds.length) errors.push("Condition names must be unique.");

    rows.forEach((r, idx) => {
      chs.forEach((ch) => {
        const p = (r[ch.id] || "").trim();
        if (!p) errors.push(`Row ${idx + 1} — ${ch.name}: empty path.`);
      });
    });

    if (errors.length) {
      setModalError(errors.join("\n"));
      return;
    }

    const lines = [`Image selection OK:`, `Conditions: ${rows.length} | Channels: ${chs.length}`, ""];
    rows.forEach((r) => {
      lines.push(`- ${r.condition}:`);
      chs.forEach((ch) => lines.push(`    ${ch.name}: ${r[ch.id] || ""}`));
    });
    setSummaryText(lines.join("\n"));
    setModalError("");
    setModalOpen(false);
  };

  const startRegistration = async () => {
    await onStartRegistration({
      images_data: imagesData,
      reg_data: {
        save_path: savePath,
        reference: referenceChannel,
        moving: movingChannels,
        crop: !!cropOutput,
      },
    });
  };

  const counterText = `Channels: ${channels.length} | Conditions: ${(imagesData.rows || []).length}`;

  return (
    <>
      <Card as="aside" className="panel seg-panel" variant="panel">
        <div className="seg-header">
          <h3>Image Registration Settings</h3>
          <p className="hint">Set the reference channel, moving channels, and output options for registration.</p>
          <button className="secondary" title="Open the condition-by-channel table used to define the registration inputs." onClick={() => { setModalError(""); setModalOpen(true); }}>Load images</button>
          <div className="field-head">Saving path <Tip text="Directory where registered outputs will be saved." /></div>
          <div className="row path-row">
            <input className="input" value={savePath} onChange={(e) => setSavePath(e.target.value)} placeholder="Folder to save results..." />
            <button className="ghost" title="Choose where registration outputs should be written." onClick={async () => {
              const p = await onPickDirectory();
              if (p) setSavePath(p);
            }}>Browse</button>
          </div>
          <details className="seg-summary">
            <summary>Image selection summary</summary>
            <pre>{summaryText}</pre>
          </details>
        </div>

        <div className="seg-scroll">
          <details open className="seg-section">
            <summary>Channel mapping</summary>
            <div className="seg-body">
              <div className="field-head">Reference channel <Tip text="Fixed channel used as the alignment target for all corrected channels." /></div>
              <select className="input" value={referenceChannel} onChange={(e) => setReferenceChannel(e.target.value)}>
                <option value="">Select reference...</option>
                {channels.map((ch) => <option key={`reg-ref-${ch.id}`} value={ch.id}>{ch.name}</option>)}
              </select>
              <div className="field-head">Other channels to correct <Tip text="Channels that will be transformed to match the reference channel." /></div>
              <div className="multi-picker">
                {channels.filter((ch) => ch.id !== referenceChannel).map((ch) => (
                  <label className="checkbox" key={`reg-m-${ch.id}`}>
                    <input
                      type="checkbox"
                      checked={movingChannels.includes(ch.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setMovingChannels((prev) => Array.from(new Set([...prev, ch.id])));
                        } else {
                          setMovingChannels((prev) => prev.filter((id) => id !== ch.id));
                        }
                      }}
                    />
                    {ch.name}
                  </label>
                ))}
              </div>
            </div>
          </details>

          <details open className="seg-section">
            <summary>Options</summary>
            <div className="seg-body">
              <label className="checkbox">
                <input type="checkbox" checked={cropOutput} onChange={(e) => setCropOutput(e.target.checked)} />
                Crop output (keep common FOV) <Tip text="Trim the output to the common overlapping field of view after registration." />
              </label>
            </div>
          </details>

        </div>

        <div className="seg-footer">
          <button className="primary" title="Run image registration with the current mapping and options." onClick={startRegistration} disabled={regRunning}>Run Registration</button>
          <button className="ghost" title="Request cancellation of the current registration job." onClick={() => onStopRegistration()} disabled={!regRunning}>Stop</button>
        </div>
      </Card>

      {modalOpen && (
        <div className="seg-modal-backdrop" onClick={() => setModalOpen(false)}>
          <div className="seg-modal" onClick={(e) => e.stopPropagation()}>
            <div className="seg-modal-header"><h4>Load images — conditions × channels</h4></div>
            <div className="seg-modal-body">
              {modalError && <div className="seg-modal-error">{modalError}</div>}
              <div className="seg-load-table-wrap">
                <table className="seg-load-table">
                  <thead>
                    <tr>
                      <th>Condition</th>
                      {channels.map((ch) => (
                        <th key={`h-reg-${ch.id}`}>
                          <div className="row row-between">
                            <input className="input" value={ch.name} onChange={(e) => updateChannelName(ch.id, e.target.value)} placeholder="Channel name" />
                            <button className="ghost btn-small" onClick={() => removeChannel(ch.id)} disabled={channels.length <= 1}>Remove</button>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(imagesData.rows || []).map((row, rIdx) => (
                      <tr key={`reg-r-${rIdx}`}>
                        <td>
                          <div className="row row-between">
                            <input className="input" value={row.condition || ""} onChange={(e) => updateCondition(rIdx, e.target.value)} placeholder="Condition name" />
                            <button className="ghost btn-small" onClick={() => removeCondition(rIdx)} disabled={(imagesData.rows || []).length <= 1}>Remove</button>
                          </div>
                        </td>
                        {channels.map((ch) => (
                          <td key={`reg-c-${rIdx}-${ch.id}`}>
                            <div className="row path-row">
                              <input className="input" value={row[ch.id] || ""} onChange={(e) => updatePathCell(rIdx, ch.id, e.target.value)} placeholder={`Path to ${ch.name}`} />
                              <button className="ghost btn-small" onClick={() => browsePathCell(rIdx, ch.id)}>Browse</button>
                            </div>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="seg-modal-footer">
              <span className="hint">{counterText}</span>
              <button className="ghost" onClick={addCondition}>+ Add condition</button>
              <button className="ghost" onClick={addChannel}>+ Add channel</button>
              <button className="primary" onClick={saveImagesTable}>Save</button>
              <button className="secondary" onClick={() => setModalOpen(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function FociOverlayLeftPanel({ onPickDirectory, onStartFoci, onStopFoci, onLoadFociChannels, fociJob }) {
  const [pklPath, setPklPath] = useState("");
  const [savePath, setSavePath] = useState("");
  const [channelsOptions, setChannelsOptions] = useState([]);
  const [channels, setChannels] = useState([]);
  const [actions, setActions] = useState(["overlay"]);
  const [saveImages, setSaveImages] = useState(true);
  const running = ["starting", "queued", "running", "canceling"].includes(fociJob?.status || "idle");

  const loadChannels = async (path) => {
    if (!path?.trim()) {
      setChannelsOptions([]);
      setChannels([]);
      return;
    }
    try {
      const opts = await onLoadFociChannels(path.trim());
      setChannelsOptions(opts);
      setChannels(opts.map((o) => o.value));
    } catch {
      setChannelsOptions([]);
      setChannels([]);
    }
  };

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Foci Overlay Settings</h3>
        <p className="hint">Generate overlay views and profile outputs from previously processed `.pkl` files.</p>
        <div className="field-head">Pickle (.pkl) folder <Tip text="Folder containing the `.pkl` files used to generate the selected foci outputs." /></div>
        <div className="row path-row">
          <input className="input" value={pklPath} onChange={(e) => setPklPath(e.target.value)} placeholder="Folder with .pkl result files..." />
          <button className="ghost" title="Choose the folder containing the `.pkl` files." onClick={async () => {
            const p = await onPickDirectory();
            if (p) {
              setPklPath(p);
              await loadChannels(p);
            }
          }}>Browse</button>
        </div>
        <div className="field-head">Saving path <Tip text="Directory where the overlay outputs and optional rendered images will be saved." /></div>
        <div className="row path-row">
          <input className="input" value={savePath} onChange={(e) => setSavePath(e.target.value)} placeholder="Folder to save overlay outputs..." />
          <button className="ghost" title="Choose where the foci overlay outputs should be written." onClick={async () => {
            const p = await onPickDirectory();
            if (p) setSavePath(p);
          }}>Browse</button>
        </div>
      </div>

      <div className="seg-scroll">
        <details open className="seg-section">
          <summary>Channels</summary>
          <div className="seg-body">
            {channelsOptions.length === 0 ? (
              <p className="hint">Point to a .pkl folder to load channels automatically.</p>
            ) : (
              <div className="multi-picker">
                {channelsOptions.map((opt) => (
                  <label className="checkbox" key={`foci-ch-${opt.value}`}>
                    <input
                      type="checkbox"
                      checked={channels.includes(opt.value)}
                      onChange={(e) => {
                        if (e.target.checked) setChannels((prev) => Array.from(new Set([...prev, opt.value])));
                        else setChannels((prev) => prev.filter((v) => v !== opt.value));
                      }}
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            )}
          </div>
        </details>

        <details open className="seg-section">
          <summary>Actions</summary>
          <div className="seg-body">
            <label className="checkbox">
              <input
                type="checkbox"
                checked={actions.includes("overlay")}
                onChange={(e) => {
                  if (e.target.checked) setActions((prev) => Array.from(new Set([...prev, "overlay"])));
                  else setActions((prev) => prev.filter((a) => a !== "overlay"));
                }}
              />
              Overlay <Tip text="Generate overlay views showing the detected foci over the original image context." />
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={actions.includes("profiles")}
                onChange={(e) => {
                  if (e.target.checked) setActions((prev) => Array.from(new Set([...prev, "profiles"])));
                  else setActions((prev) => prev.filter((a) => a !== "profiles"));
                }}
              />
              Plot profiles <Tip text="Generate profile-style output plots from the loaded foci measurements." />
            </label>
            <label className="checkbox">
              <input type="checkbox" checked={saveImages} onChange={(e) => setSaveImages(e.target.checked)} />
              Save overlay images <Tip text="Export the rendered overlay images in addition to the other selected outputs." />
            </label>
          </div>
        </details>

      </div>

      <div className="seg-footer">
        <button
          className="primary"
          title="Run the selected foci overlay/profile outputs with the chosen channels and save options."
          onClick={() => onStartFoci({
            pkl_path: pklPath.trim(),
            save_path: (savePath.trim() || pklPath.trim()),
            channels,
            actions,
            save_images: !!saveImages,
          })}
          disabled={running}
        >
          Run Overlay
        </button>
        <button className="ghost" title="Request cancellation of the current foci overlay job." onClick={() => onStopFoci()} disabled={!running}>Stop</button>
      </div>
    </Card>
  );
}

function PlotDataLeftPanel({ onPickCsv, onPreview, status, setStatusExternal, graphState, setGraphState, loading }) {
  const graphTypes = ["scatter", "violin", "box", "dot", "bar", "line", "cpd"];

  const setField = (k, v) => setGraphState((prev) => ({ ...prev, [k]: v }));
  const addDataset = () => setField("datasets", [...(graphState.datasets || []), { id: makeRowId(), name: `Dataset ${(graphState.datasets || []).length + 1}`, path: "", columns: null, enabled: true }]);
  const removeDataset = (id) => setField("datasets", (graphState.datasets || []).filter((d) => d.id !== id));
  const updateDataset = (id, patch) => setField("datasets", (graphState.datasets || []).map((d) => (d.id === id ? { ...d, ...patch } : d)));

  const cols = graphState.columns || [];
  const categoricalCols = graphState.categoricalColumns || [];
  const canPreview = (graphState.datasets || []).some((d) => d.enabled !== false && String(d.path || "").trim()) && !graphState.columnsWarning;
  const graphType = graphState.graph_type || "scatter";
  const requiresXY = PLOT_TYPES_REQUIRE_XY.has(graphType);
  const requiresY = PLOT_TYPES_REQUIRE_Y.has(graphType);
  const supportsDot = PLOT_TYPES_SUPPORT_DOT.has(graphType);
  const supportsSize = PLOT_TYPES_SUPPORT_SIZE.has(graphType);
  const supportsX = PLOT_TYPES_SUPPORT_X.has(graphType);
  const xOptions = (graphType === "violin" || graphType === "box" || graphType === "dot" || graphType === "bar") ? categoricalCols : cols;
  const lineRolling = graphType === "line" && !!graphState.line_rolling;
  const isCpd = graphType === "cpd";
  const shouldShowFrames = isCpd || (graphType === "line" && (!graphState.x || graphState.x === "Frame"));

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Plot Data Settings</h3>
        <p className="hint">Use CSV outputs to build interactive plots.</p>
      </div>
      <div className="seg-scroll">
        <details open className="seg-section">
          <summary>Data</summary>
          <div className="seg-body">
            {(graphState.datasets || []).map((d, idx) => (
              <div className="dataset" key={d.id}>
                <div className="row">
                  <label className="checkbox" style={{ minWidth: 62 }}>
                    <input
                      type="checkbox"
                      checked={d.enabled !== false}
                      onChange={(e) => updateDataset(d.id, { enabled: e.target.checked })}
                    />
                    plot
                  </label>
                  <div style={{ flex: 1 }}>
                    <div className="field-head">Dataset name <Tip text="Friendly label used in legends and plot summaries." /></div>
                    <input
                      className="input"
                      value={d.name || ""}
                      onChange={(e) => updateDataset(d.id, { name: e.target.value })}
                      placeholder={`Dataset ${idx + 1} name`}
                    />
                  </div>
                  {(graphState.datasets || []).length > 1 && (
                    <button className="ghost btn-small" title="Remove this dataset from the plotting configuration." onClick={() => removeDataset(d.id)}>Remove</button>
                  )}
                </div>
                <div className="row path-row">
                  <div style={{ flex: 1 }}>
                    <div className="field-head">CSV path <Tip text="Local CSV file containing the measurements to plot." /></div>
                    <input className="input" value={d.path || ""} onChange={(e) => updateDataset(d.id, { path: e.target.value })} placeholder="/path/Results.csv" />
                  </div>
                  <button
                    className="ghost"
                    title="Choose a CSV file for this plot dataset."
                    onClick={async () => {
                      try {
                        const picked = await onPickCsv();
                        if (picked) updateDataset(d.id, { path: picked, name: (d.name || "").trim() ? d.name : String(picked).split("/").pop() || d.name });
                      } catch (err) {
                        setStatusExternal(err.message || "Failed to pick CSV.", "error");
                      }
                    }}
                  >
                    Browse CSV
                  </button>
                </div>
              </div>
            ))}
            <button className="secondary" title="Add another CSV dataset to the plot configuration." onClick={addDataset}>Add CSV</button>
            {graphState.columnsWarning && (
              <Status level="error" text={graphState.columnsWarning} />
            )}
          </div>
        </details>

        <details open className="seg-section">
          <summary>Plot options</summary>
          <div className="seg-body">
            <div className="field-head">Graph type <Tip text="Select the plot style to generate from the loaded datasets." /></div>
            <select
              className="input"
              value={graphState.graph_type}
              onChange={(e) => {
                const nextType = e.target.value;
                setGraphState((prev) => ({
                  ...prev,
                  graph_type: nextType,
                  x: PLOT_TYPES_SUPPORT_X.has(nextType) ? prev.x : "",
                  size: PLOT_TYPES_SUPPORT_SIZE.has(nextType) ? prev.size : "",
                  line_rolling: nextType === "line" ? prev.line_rolling : false,
                }));
              }}
            >
              {graphTypes.map((g) => <option key={`gt-${g}`} value={g}>{g}</option>)}
            </select>
            {!isCpd && supportsX && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">X axis <Tip text="Column used on the horizontal axis of the selected plot type." /></div>
                  <select className="input" value={graphState.x} onChange={(e) => setField("x", e.target.value)}>
                  <option value="">
                    {(graphType === "violin" || graphType === "box" || graphType === "dot" || graphType === "bar")
                      ? "Category axis (optional)"
                      : (graphType === "line"
                        ? "X axis (default: Frame)"
                        : (requiresXY ? "Select X axis (required)" : "Select X axis"))}
                  </option>
                  {xOptions.map((c) => <option key={`x-${c}`} value={c}>{c}</option>)}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <div className="field-head">Y axis <Tip text="Column used on the vertical axis of the selected plot type." /></div>
                  <select className="input" value={graphState.y} onChange={(e) => setField("y", e.target.value)}>
                  <option value="">{requiresY ? "Select Y axis (required)" : "Select Y axis"}</option>
                  {cols.map((c) => <option key={`y-${c}`} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>
            )}
            {!isCpd && !supportsX && (
              <div>
                <div className="field-head">Y axis <Tip text="Column used on the vertical axis of the selected plot type." /></div>
                <select className="input" value={graphState.y} onChange={(e) => setField("y", e.target.value)}>
                  <option value="">{requiresY ? "Select Y axis (required)" : "Select Y axis"}</option>
                  {cols.map((c) => <option key={`y-${c}`} value={c}>{c}</option>)}
                </select>
              </div>
            )}
            {!isCpd && (
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Hue <Tip text="Optional column used to color points or groups in the plot." /></div>
                <select
                className="input"
                value={graphState.hue}
                onChange={(e) => setField("hue", e.target.value)}
              >
                <option value="">Hue (optional)</option>
                {cols.map((c) => <option key={`h-${c}`} value={c}>{c}</option>)}
              </select>
              </div>
              {supportsSize && (
                <div style={{ flex: 1 }}>
                  <div className="field-head">Size <Tip text="Optional numeric column used to scale marker size when supported." /></div>
                  <select className="input" value={graphState.size} onChange={(e) => setField("size", e.target.value)}>
                  <option value="">Size (optional)</option>
                  {cols.map((c) => <option key={`s-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              )}
            </div>
            )}
            {graphType === "violin" && (
              <>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={!!graphState.violin_box}
                    onChange={(e) => setField("violin_box", e.target.checked)}
                  />
                  Show box inside violin <Tip text="Overlay a boxplot summary inside each violin distribution." />
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={!!graphState.violin_points}
                    onChange={(e) => setField("violin_points", e.target.checked)}
                  />
                  Show dots <Tip text="Overlay the individual observations on top of the violin plot." />
                </label>
              </>
            )}
            {isCpd && (
              <div className="hint">
                CPD (Cumulative Population Doubling) estimates cumulative growth by summing doublings between consecutive frames:
                CPD = sum(log2(Nt+1 / Nt)). Use frames from different days/timepoints.
              </div>
            )}
            {shouldShowFrames && (
              <div>
                <div className="field-head">Frames <Tip text="Comma-separated list of frames/timepoints to include in the plot." /></div>
                <input
                  className="input"
                  value={graphState.framesText || ""}
                  onChange={(e) => setField("framesText", e.target.value)}
                  placeholder={isCpd ? "Frames (required, e.g. 0,1,2,3)" : "Frames (optional, empty = all)"}
                />
              </div>
            )}
            {isCpd && (
              <div>
                <div className="field-head">Control condition <Tip text="Optional control group used as a reference in CPD interpretation." /></div>
                <select
                  className="input"
                  value={graphState.control || ""}
                  onChange={(e) => setField("control", e.target.value)}
                >
                  <option value="">Control condition (optional)</option>
                  {(graphState.controlOptions || []).map((c) => (
                    <option key={`ctrl-${c}`} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            )}
            {graphType === "line" && (
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={!!graphState.line_rolling}
                  onChange={(e) => setField("line_rolling", e.target.checked)}
                />
                Rolling average <Tip text="Smooth the line using a moving average window." />
              </label>
            )}
            {lineRolling && (
              <div>
                <div className="field-head">Rolling window <Tip text="Number of points used in the moving average for line plots." /></div>
                <input
                  className="input"
                  type="number"
                  min="1"
                  value={graphState.n ?? ""}
                  onChange={(e) => setField("n", e.target.value)}
                  placeholder="Rolling window n"
                />
              </div>
            )}
            {supportsDot && (
              <>
                <label className="checkbox">
                  <input type="checkbox" checked={!!graphState.dot} onChange={(e) => setField("dot", e.target.checked)} />
                  Dot (box) <Tip text="Overlay individual observations on the box plot." />
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={!!graphState.box_outliers}
                    onChange={(e) => setField("box_outliers", e.target.checked)}
                  />
                  Show outliers <Tip text="Display points considered outliers by the box plot rule." />
                </label>
              </>
            )}
            {graphType === "line" && (
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={!!graphState.compute_auc}
                  onChange={(e) => setField("compute_auc", e.target.checked)}
                />
                Compute AUC <Tip text="Calculate the area under the line curve when supported by the data." />
              </label>
            )}
          </div>
        </details>
      </div>
      <div className="seg-footer">
        <button
          className="primary"
          title="Generate the selected plot using the current datasets and plot options."
          onClick={onPreview}
          disabled={!canPreview || loading}
        >
          {loading ? "Generating..." : "Plot"}
        </button>
      </div>
      <Status level={status.level} text={status.text} />
    </Card>
  );
}

function ClusteringLeftPanel({ onPickCsv, onPreview, onElbow, status, loading, elbowLoading, state, setState }) {
  const setField = (k, v) => setState((prev) => ({ ...prev, [k]: v }));
  const addDataset = () => setField("datasets", [...(state.datasets || []), { id: makeRowId(), name: `Dataset ${(state.datasets || []).length + 1}`, path: "", enabled: true }]);
  const removeDataset = (id) => setField("datasets", (state.datasets || []).filter((d) => d.id !== id));
  const updateDataset = (id, patch) => setField("datasets", (state.datasets || []).map((d) => (d.id === id ? { ...d, ...patch } : d)));

  const numeric = state.numericColumns || [];
  const selectedSet = new Set(state.columns || []);
  const canRun = (state.datasets || []).some((d) => d.enabled !== false && String(d.path || "").trim()) && (state.columns || []).length > 0 && !loading;

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Clustering Settings</h3>
        <p className="hint">Interactive embedding preview with optional KMeans coloring.</p>
      </div>
      <div className="seg-scroll">
        <details open className="seg-section">
          <summary>Data</summary>
          <div className="seg-body">
            {(state.datasets || []).map((d, idx) => (
              <div className="dataset" key={d.id}>
                <div className="row">
                  <label className="checkbox" style={{ minWidth: 62 }}>
                    <input
                      type="checkbox"
                      checked={d.enabled !== false}
                      onChange={(e) => updateDataset(d.id, { enabled: e.target.checked })}
                    />
                    use
                  </label>
                  <div style={{ flex: 1 }}>
                    <div className="field-head">Dataset name <Tip text="Friendly label used to identify this dataset in the embedding preview." /></div>
                    <input
                      className="input"
                      value={d.name || ""}
                      onChange={(e) => updateDataset(d.id, { name: e.target.value })}
                      placeholder={`Dataset ${idx + 1} name`}
                    />
                  </div>
                  {(state.datasets || []).length > 1 && (
                    <button className="ghost btn-small" title="Remove this dataset from the clustering configuration." onClick={() => removeDataset(d.id)}>Remove</button>
                  )}
                </div>
                <div className="row path-row">
                  <div style={{ flex: 1 }}>
                    <div className="field-head">CSV path <Tip text="Local CSV file used to compute the embedding." /></div>
                    <input className="input" value={d.path || ""} onChange={(e) => updateDataset(d.id, { path: e.target.value })} placeholder="/path/Results.csv" />
                  </div>
                  <button
                    className="ghost"
                    title="Choose a CSV file for this clustering dataset."
                    onClick={async () => {
                      try {
                        const picked = await onPickCsv();
                        if (picked) updateDataset(d.id, { path: picked, name: (d.name || "").trim() ? d.name : String(picked).split("/").pop() || d.name });
                      } catch {
                        // no-op
                      }
                    }}
                  >
                    Browse CSV
                  </button>
                </div>
              </div>
            ))}
            <button className="secondary" title="Add another CSV dataset to the clustering configuration." onClick={addDataset}>Add CSV</button>
          </div>
        </details>

        <details open className="seg-section">
          <summary>Features</summary>
          <div className="seg-body">
            <div className="field-head">Numeric features <Tip text="Numeric columns used as input features for UMAP or PCA." /></div>
            <select
              className="input"
              multiple
              size={Math.min(10, Math.max(4, numeric.length || 4))}
              value={state.columns || []}
              onChange={(e) => {
                const vals = Array.from(e.target.selectedOptions).map((o) => o.value);
                setField("columns", vals);
              }}
            >
              {numeric.map((c) => <option key={`umap-col-${c}`} value={c}>{c}</option>)}
            </select>
            <div className="row row-right">
              <button className="ghost btn-small" title="Select all numeric columns as embedding features." onClick={() => setField("columns", numeric.slice())}>Select all</button>
              <button className="ghost btn-small" title="Clear the selected embedding features." onClick={() => setField("columns", [])}>Clear</button>
            </div>
          </div>
        </details>

        <details open className="seg-section">
          <summary>Embedding options</summary>
          <div className="seg-body">
            <div className="field-head">Embedding method <Tip text="Choose whether to compute a UMAP embedding or a PCA projection." /></div>
            <select className="input" value={state.method || "umap"} onChange={(e) => setField("method", e.target.value)}>
              <option value="umap">UMAP</option>
              <option value="pca">PCA</option>
            </select>
            {state.method !== "pca" && (
              <>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Neighbors <Tip text="Number of nearest neighbors used by UMAP to preserve local structure." /></div>
                <input className="input" type="number" min="2" value={state.n_neighbors ?? 15} onChange={(e) => setField("n_neighbors", Number(e.target.value || 15))} placeholder="n_neighbors" />
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">Minimum distance <Tip text="How tightly UMAP is allowed to pack points in the embedding." /></div>
                <input className="input" type="number" min="0" max="0.99" step="0.01" value={state.min_dist ?? 0.1} onChange={(e) => setField("min_dist", Number(e.target.value || 0.1))} placeholder="min_dist" />
              </div>
            </div>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Metric <Tip text="Distance metric used to compare rows before embedding." /></div>
                <select className="input" value={state.metric || "euclidean"} onChange={(e) => setField("metric", e.target.value)}>
                {["euclidean", "manhattan", "cosine", "chebyshev", "canberra", "correlation"].map((m) => (
                  <option key={`metric-${m}`} value={m}>{m}</option>
                ))}
                </select>
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">Max points <Tip text="Maximum number of rows sampled into the preview to keep interaction responsive." /></div>
                <input className="input" type="number" min="500" step="500" value={state.max_points ?? 12000} onChange={(e) => setField("max_points", Number(e.target.value || 12000))} placeholder="max points" />
              </div>
            </div>
              </>
            )}
            {state.method === "pca" && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Max points <Tip text="Maximum number of rows sampled into the PCA preview." /></div>
                  <input className="input" type="number" min="500" step="500" value={state.max_points ?? 12000} onChange={(e) => setField("max_points", Number(e.target.value || 12000))} placeholder="max points" />
                </div>
              </div>
            )}
            <label className="checkbox">
              <input type="checkbox" checked={!!state.scale} onChange={(e) => setField("scale", e.target.checked)} />
              Standardize features (z-score) <Tip text="Normalize features before embedding so large-scale variables do not dominate." />
            </label>
          </div>
        </details>

        <details open className="seg-section">
          <summary>Coloring</summary>
          <div className="seg-body">
            <label className="checkbox">
              <input type="checkbox" checked={!!state.use_clusters} onChange={(e) => setField("use_clusters", e.target.checked)} />
              Use KMeans clusters <Tip text="Color the embedding by KMeans cluster assignment instead of a metadata column." />
            </label>
            {state.use_clusters ? (
              <>
                <div className="field-head">Number of clusters (k)</div>
                <input className="input" type="number" min="2" value={state.n_clusters ?? 8} onChange={(e) => setField("n_clusters", Number(e.target.value || 8))} placeholder="k for KMeans coloring" />
                <div className="field-head">Elbow range</div>
                <div className="row">
                  <input className="input" type="number" min="2" value={state.k_min ?? 2} onChange={(e) => setField("k_min", Number(e.target.value || 2))} placeholder="Minimum k" />
                  <input className="input" type="number" min="3" value={state.k_max ?? 12} onChange={(e) => setField("k_max", Number(e.target.value || 12))} placeholder="Maximum k" />
                </div>
                <button className="ghost" title="Generate an elbow plot across the selected k range to help choose the number of clusters." onClick={onElbow} disabled={loading || elbowLoading}>
                  {elbowLoading ? "Generating elbow..." : "Generate elbow plot"}
                </button>
              </>
            ) : (
              <>
              <div className="field-head">Color by <Tip text="Column used to color the embedding when KMeans coloring is disabled." /></div>
              <select className="input" value={state.color_by || ""} onChange={(e) => setField("color_by", e.target.value)}>
                <option value="">Color by default (Condition)</option>
                {(state.columnsAll || []).map((c) => <option key={`color-${c}`} value={c}>{c}</option>)}
              </select>
              </>
            )}
          </div>
        </details>
      </div>

      <div className="seg-footer">
        <button className="primary" title="Compute the embedding preview with the selected datasets, features, and coloring options." onClick={onPreview} disabled={!canRun}>
          {loading ? "Running..." : "Run"}
        </button>
      </div>
      <Status level={status.level} text={status.text} />
    </Card>
  );
}

function StatsLeftPanel({ onPickCsv, onRun, status, loading, state, setState }) {
  const setField = (k, v) => setState((prev) => ({ ...prev, [k]: v }));
  const addDataset = () => setField("datasets", [...(state.datasets || []), { id: makeRowId(), name: `Dataset ${(state.datasets || []).length + 1}`, path: "", enabled: true }]);
  const removeDataset = (id) => setField("datasets", (state.datasets || []).filter((d) => d.id !== id));
  const updateDataset = (id, patch) => setField("datasets", (state.datasets || []).map((d) => (d.id === id ? { ...d, ...patch } : d)));
  const addFilter = () => setField("filters", [...(state.filters || []), makeStatsFilterRow()]);
  const removeFilter = (id) => setField("filters", (state.filters || []).filter((f) => f.id !== id));
  const updateFilter = (id, patch) => setField("filters", (state.filters || []).map((f) => (f.id === id ? { ...f, ...patch } : f)));
  const cols = state.columns || [];
  const categoricalCols = state.categoricalColumns || [];
  const method = state.method || "oneway";
  const canRun = (state.datasets || []).some((d) => d.enabled !== false && String(d.path || "").trim()) && !loading;
  const methodHelp = {
    oneway: "Compares one numeric variable across multiple groups (e.g., Control vs Treatments).",
    twoway: "Evaluates two factors simultaneously and their possible interaction effect.",
    chi2: "Tests association between two categorical variables using a contingency table.",
    "chi2-subgroups": "Compares conditions within each categorical subgroup (2x2 tests per subgroup).",
  };

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Statistics Settings</h3>
        <p className="hint">Run statistical tests and inspect result tables.</p>
      </div>
      <div className="seg-scroll">
        <details open className="seg-section">
          <summary>Data</summary>
          <div className="seg-body">
            {(state.datasets || []).map((d, idx) => (
              <div className="dataset" key={d.id}>
                <div className="row">
                  <label className="checkbox" style={{ minWidth: 62 }}>
                    <input
                      type="checkbox"
                      checked={d.enabled !== false}
                      onChange={(e) => updateDataset(d.id, { enabled: e.target.checked })}
                    />
                    use
                  </label>
                  <div style={{ flex: 1 }}>
                    <div className="field-head">Dataset name <Tip text="Friendly name used to identify this file in the analysis." /></div>
                    <input
                      className="input"
                      value={d.name || ""}
                      onChange={(e) => updateDataset(d.id, { name: e.target.value })}
                      placeholder={`Dataset ${idx + 1} name`}
                    />
                  </div>
                  {(state.datasets || []).length > 1 && (
                    <button className="ghost btn-small" onClick={() => removeDataset(d.id)}>Remove</button>
                  )}
                </div>
                <div className="row path-row">
                  <div style={{ flex: 1 }}>
                    <div className="field-head">CSV path <Tip text="Local path to the CSV file containing your data." /></div>
                    <input className="input" value={d.path || ""} onChange={(e) => updateDataset(d.id, { path: e.target.value })} placeholder="/path/Results.csv" />
                  </div>
                  <button
                    className="ghost"
                    onClick={async () => {
                      try {
                        const picked = await onPickCsv();
                        if (picked) updateDataset(d.id, { path: picked, name: (d.name || "").trim() ? d.name : String(picked).split("/").pop() || d.name });
                      } catch {
                        // noop
                      }
                    }}
                  >
                    Browse CSV
                  </button>
                </div>
              </div>
            ))}
            <button className="secondary" onClick={addDataset}>Add CSV</button>
          </div>
        </details>

        <details open className="seg-section">
          <summary>Test</summary>
          <div className="seg-body">
            <div className="field-head">Test method <Tip text="Choose the statistical test you want to run." /></div>
            <select className="input" value={method} onChange={(e) => setField("method", e.target.value)}>
              <option value="oneway">One-way</option>
              <option value="twoway">Two-way</option>
              <option value="chi2">Chi-square</option>
              <option value="chi2-subgroups">Chi-square subgroups</option>
            </select>
            <div className="hint">{methodHelp[method]}</div>

            {(method === "oneway" || method === "twoway") && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Numeric column <Tip text="Numeric variable to compare across groups." /></div>
                <select className="input" value={state.numeric_col || ""} onChange={(e) => setField("numeric_col", e.target.value)}>
                  <option value="">Numeric column</option>
                  {cols.map((c) => <option key={`sn-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              </div>
            )}

            {method === "oneway" && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Group column <Tip text="Categorical column that defines the groups to compare." /></div>
                <select className="input" value={state.group_col || ""} onChange={(e) => setField("group_col", e.target.value)}>
                  <option value="">Group column</option>
                  {cols.map((c) => <option key={`sg-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              </div>
            )}

            {method === "twoway" && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Factor A <Tip text="First categorical factor in the two-way analysis." /></div>
                <select className="input" value={state.group_col1 || ""} onChange={(e) => setField("group_col1", e.target.value)}>
                  <option value="">Factor A</option>
                  {cols.map((c) => <option key={`sga-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
                <div style={{ flex: 1 }}>
                  <div className="field-head">Factor B <Tip text="Second categorical factor in the two-way analysis." /></div>
                <select className="input" value={state.group_col2 || ""} onChange={(e) => setField("group_col2", e.target.value)}>
                  <option value="">Factor B</option>
                  {cols.map((c) => <option key={`sgb-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              </div>
            )}

            {method === "chi2" && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Group column <Tip text="Row groups in the contingency table." /></div>
                <select className="input" value={state.group_col || ""} onChange={(e) => setField("group_col", e.target.value)}>
                  <option value="">Group column</option>
                  {cols.map((c) => <option key={`scg-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
                <div style={{ flex: 1 }}>
                  <div className="field-head">Category column <Tip text="Category levels represented as columns in the contingency table." /></div>
                <select className="input" value={state.category_col || ""} onChange={(e) => setField("category_col", e.target.value)}>
                  <option value="">Category column</option>
                  {cols.map((c) => <option key={`scc-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              </div>
            )}

            {method === "chi2-subgroups" && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Subgroup column <Tip text="Base category used to split subgroup comparisons." /></div>
                <select className="input" value={state.group_col || ""} onChange={(e) => setField("group_col", e.target.value)}>
                  <option value="">Group column</option>
                  {cols.map((c) => <option key={`ssg-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
                <div style={{ flex: 1 }}>
                  <div className="field-head">Condition column <Tip text="Conditions that will be compared within each subgroup." /></div>
                <select className="input" value={state.condition_col || ""} onChange={(e) => setField("condition_col", e.target.value)}>
                  <option value="">Condition column</option>
                  {cols.map((c) => <option key={`ssc-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              </div>
            )}

            {(method === "oneway" || method === "twoway") && (
              <div>
                <div className="field-head">Alpha <Tip text="Significance threshold. Default: 0.05." /></div>
                <input className="input" type="number" step="0.001" min="0" max="1" value={state.alpha ?? 0.05} onChange={(e) => setField("alpha", Number(e.target.value || 0.05))} placeholder="alpha" />
              </div>
            )}

            {(method === "chi2" || method === "chi2-subgroups") && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Expected minimum <Tip text="Minimum expected count threshold used to trigger fallback methods (e.g., Fisher/Monte Carlo)." /></div>
                  <input className="input" type="number" step="0.1" min="0" value={state.expected_min ?? 5.0} onChange={(e) => setField("expected_min", Number(e.target.value || 5.0))} placeholder="expected min" />
                </div>
                <div style={{ flex: 1 }}>
                  <div className="field-head">Correction method <Tip text="Multiple-comparison correction used in post-hoc results." /></div>
                <select className="input" value={state.correction_method || "auto"} onChange={(e) => setField("correction_method", e.target.value)}>
                  <option value="auto">Correction: auto</option>
                  <option value="bonferroni">Correction: bonferroni</option>
                  <option value="fdr_bh">Correction: fdr_bh</option>
                </select>
                </div>
              </div>
            )}

            {(method === "oneway" || method === "twoway") && (
              <div>
                <div className="field-head">Pairs of interest (optional) <Tip text="Specific pairs for post-hoc testing. Example: A|B; A|C." /></div>
                <input className="input" value={state.pairs_text || ""} onChange={(e) => setField("pairs_text", e.target.value)} placeholder="Pairs (optional): A|B; A|C" />
              </div>
            )}
          </div>
        </details>

        <details open className="seg-section">
          <summary>Subset data</summary>
          <div className="seg-body">
            <div className="hint">Optional exact-match filters applied before the test. Example: `Condition = control` and `Frame = 1`.</div>
            {(state.filters || []).map((filter, idx) => {
              const valueOptions = state.filterValueOptions?.[filter.column] || [];
              return (
                <div className="dataset" key={filter.id}>
                  <div className="row">
                    <div style={{ flex: 1 }}>
                      <div className="field-head">Filter column <Tip text="Column used to subset rows before running the analysis." /></div>
                      <select
                        className="input"
                        value={filter.column || ""}
                        onChange={(e) => updateFilter(filter.id, { column: e.target.value, values: [] })}
                      >
                        <option value="">No filter</option>
                        {cols.map((c) => <option key={`sf-col-${filter.id}-${c}`} value={c}>{c}</option>)}
                      </select>
                    </div>
                    {(state.filters || []).length > 1 && (
                      <button className="ghost btn-small" onClick={() => removeFilter(filter.id)}>Remove</button>
                    )}
                  </div>
                  {filter.column ? (
                    <div>
                      <div className="field-head">Accepted values <Tip text="Only rows matching one of the selected values will be kept." /></div>
                      <select
                        className="input"
                        multiple
                        size={Math.min(6, Math.max(3, valueOptions.length || 3))}
                        value={filter.values || []}
                        onChange={(e) => updateFilter(filter.id, {
                          values: Array.from(e.target.selectedOptions || []).map((opt) => opt.value),
                        })}
                      >
                        {valueOptions.map((value) => <option key={`sf-val-${filter.id}-${value}`} value={value}>{value}</option>)}
                      </select>
                      <div className="hint">
                        {valueOptions.length
                          ? "Use Ctrl/Cmd-click to select more than one value."
                          : "No values loaded yet for this column."}
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
            <button className="secondary" onClick={addFilter}>Add filter</button>
            {categoricalCols.length > 0 && (
              <div className="hint">Suggested categorical columns: {categoricalCols.join(", ")}</div>
            )}
          </div>
        </details>
      </div>
      <div className="seg-footer">
        <button className="primary" onClick={onRun} disabled={!canRun}>
          {loading ? "Running..." : "Run"}
        </button>
      </div>
      <Status level={status.level} text={status.text} />
    </Card>
  );
}

function GatingLeftPanel({ onPickCsv, onPickDirectory, onPreview, onApply, status, loading, applying, state, setState }) {
  const setField = (k, v) => setState((prev) => ({ ...prev, [k]: v }));
  const addDataset = () => setField("datasets", [...(state.datasets || []), { id: makeRowId(), name: `Dataset ${(state.datasets || []).length + 1}`, path: "", enabled: true }]);
  const removeDataset = (id) => setField("datasets", (state.datasets || []).filter((d) => d.id !== id));
  const updateDataset = (id, patch) => setField("datasets", (state.datasets || []).map((d) => (d.id === id ? { ...d, ...patch } : d)));
  const numeric = state.numericColumns || [];
  const busy = !!loading || !!applying;
  const hasDatasets = (state.datasets || []).some((d) => d.enabled !== false && String(d.path || "").trim());
  const canPreview = hasDatasets && !!state.x_col && !!state.y_col && !busy;
  const canApply = canPreview && !!String(state.output_dir || "").trim();

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Gating Settings</h3>
        <p className="hint">Filter populations by rectangular gates on two numeric columns, including cleanup of segmentation errors/debris.</p>
      </div>
      <div className="seg-scroll">
        <details open className="seg-section">
          <summary>Data</summary>
          <div className="seg-body">
            {(state.datasets || []).map((d, idx) => (
              <div className="dataset" key={d.id}>
                <div className="row">
                  <label className="checkbox" style={{ minWidth: 62 }}>
                    <input type="checkbox" checked={d.enabled !== false} onChange={(e) => updateDataset(d.id, { enabled: e.target.checked })} />
                    use
                  </label>
                  <div style={{ flex: 1 }}>
                    <div className="field-head">Dataset name <Tip text="Friendly label shown in the gating preview and saved outputs." /></div>
                    <input className="input" value={d.name || ""} onChange={(e) => updateDataset(d.id, { name: e.target.value })} placeholder={`Dataset ${idx + 1} name`} />
                  </div>
                  {(state.datasets || []).length > 1 && (
                    <button className="ghost btn-small" title="Remove this dataset from the gating analysis." onClick={() => removeDataset(d.id)}>Remove</button>
                  )}
                </div>
                <div className="row path-row">
                  <div style={{ flex: 1 }}>
                    <div className="field-head">CSV path <Tip text="Local CSV file that will be filtered by the gate." /></div>
                    <input className="input" value={d.path || ""} onChange={(e) => updateDataset(d.id, { path: e.target.value })} placeholder="/path/Results.csv" />
                  </div>
                  <button
                    className="ghost"
                    title="Choose a CSV file for this gating dataset."
                    onClick={async () => {
                      try {
                        const picked = await onPickCsv();
                        if (picked) updateDataset(d.id, { path: picked, name: (d.name || "").trim() ? d.name : String(picked).split("/").pop() || d.name });
                      } catch {
                        // no-op
                      }
                    }}
                  >
                    Browse CSV
                  </button>
                </div>
              </div>
            ))}
            <button className="secondary" title="Add another CSV dataset to the gating analysis." onClick={addDataset}>Add CSV</button>
          </div>
        </details>

        <details open className="seg-section">
          <summary>Gate setup</summary>
          <div className="seg-body">
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">X column <Tip text="Numeric column plotted on the horizontal axis of the gate." /></div>
                <select className="input" value={state.x_col || ""} onChange={(e) => setField("x_col", e.target.value)}>
                <option value="">X column</option>
                {numeric.map((c) => <option key={`gx-${c}`} value={c}>{c}</option>)}
                </select>
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">Y column <Tip text="Numeric column plotted on the vertical axis of the gate." /></div>
                <select className="input" value={state.y_col || ""} onChange={(e) => setField("y_col", e.target.value)}>
                <option value="">Y column</option>
                {numeric.map((c) => <option key={`gy-${c}`} value={c}>{c}</option>)}
                </select>
              </div>
            </div>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">X minimum <Tip text="Optional lower horizontal bound for the gate." /></div>
                <input className="input" type="number" value={state.x_min} onChange={(e) => setField("x_min", e.target.value)} placeholder="X minimum (optional)" />
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">X maximum <Tip text="Optional upper horizontal bound for the gate." /></div>
                <input className="input" type="number" value={state.x_max} onChange={(e) => setField("x_max", e.target.value)} placeholder="X maximum (optional)" />
              </div>
            </div>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Y minimum <Tip text="Optional lower vertical bound for the gate." /></div>
                <input className="input" type="number" value={state.y_min} onChange={(e) => setField("y_min", e.target.value)} placeholder="Y minimum (optional)" />
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">Y maximum <Tip text="Optional upper vertical bound for the gate." /></div>
                <input className="input" type="number" value={state.y_max} onChange={(e) => setField("y_max", e.target.value)} placeholder="Y maximum (optional)" />
              </div>
            </div>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Low quantile <Tip text="Lower quantile used to estimate automatic bounds when explicit limits are empty." /></div>
                <input className="input" type="number" min="0" max="0.49" step="0.01" value={state.q_low ?? 0.05} onChange={(e) => setField("q_low", Number(e.target.value || 0.05))} placeholder="Low quantile" />
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">High quantile <Tip text="Upper quantile used to estimate automatic bounds when explicit limits are empty." /></div>
                <input className="input" type="number" min="0.51" max="1" step="0.01" value={state.q_high ?? 0.95} onChange={(e) => setField("q_high", Number(e.target.value || 0.95))} placeholder="High quantile" />
              </div>
            </div>
            <label className="checkbox">
              <input type="checkbox" checked={!!state.color_by_dataset} onChange={(e) => setField("color_by_dataset", e.target.checked)} />
              Color by dataset <Tip text="Color each dataset differently in the gating preview." />
            </label>
            <div className="hint">If bounds are empty, they are estimated from quantiles (legacy filters behavior).</div>
          </div>
        </details>

        <details open className="seg-section">
          <summary>Output</summary>
          <div className="seg-body">
            <div className="field-head">Saving path <Tip text="Directory where the gated CSV files will be written." /></div>
            <div className="row path-row">
              <input className="input" value={state.output_dir || ""} onChange={(e) => setField("output_dir", e.target.value)} placeholder="Folder to save gated CSV files" />
              <button
                className="ghost"
                title="Choose where gated CSV files should be saved."
                onClick={async () => {
                  try {
                    const picked = await onPickDirectory();
                    if (picked) setField("output_dir", picked);
                  } catch {
                    // no-op
                  }
                }}
              >
                Browse
              </button>
            </div>
          </div>
        </details>
      </div>
      <div className="seg-footer">
        <button className="secondary" title="Preview the gate on the selected X/Y columns without saving files yet." onClick={onPreview} disabled={!canPreview}>
          {loading ? "Previewing..." : "Preview gate"}
        </button>
        <button className="primary" title="Apply the gate and save the filtered CSV files to the selected output folder." onClick={onApply} disabled={!canApply}>
          {applying ? "Applying..." : "Apply and save"}
        </button>
      </div>
      <Status level={status.level} text={status.text} />
    </Card>
  );
}

function TrackingLeftPanel({
  onPickCsv,
  onPickDirectory,
  onRunAutomatic,
  onGoToCorrection,
  onOpenCorrection,
  onSaveResults,
  onRefreshFrame,
  onPrevFrame,
  onNextFrame,
  onDeleteTracks,
  onLinkTracks,
  status,
  state,
  setState,
  running,
  loadingFrame,
  editing,
}) {
  const setField = (k, v) => setState((prev) => ({ ...prev, [k]: v }));
  const busy = running || loadingFrame || editing;
  const hasTracked = !!String(state.table_path || "").trim();
  const imageNameColumns = (state.columns || []).filter((c) => String(c || "").toLowerCase().includes("image_name"));
  const workflowStage = String(state.workflow_stage || "step1");
  const hasSelection = (state.selected || []).length > 0;
  const canRun = !!String(state.path_to_table || "").trim()
    && !!String(state.image_dir || "").trim()
    && !!String(state.image_col || "").trim()
    && !busy;
  const canGoToCorrection = hasTracked && !busy;
  const canSaveResults = hasTracked && !!String(state.save_results_dir || "").trim() && !busy;
  const canPreview = hasTracked && !busy;
  const canDelete = hasTracked && hasSelection && !busy;
  const canLink = hasTracked && (state.selected || []).length >= 2 && !busy;

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Tracking Settings</h3>
        <p className="hint">
          Automatic tracking is simple and may produce errors. Step 2 is manual correction and becomes available only
          after running automatic tracking.
        </p>
      </div>
      <div className="seg-scroll">
        {workflowStage === "step1" && (
          <details open className="seg-section">
          <summary>Step 1 - Automatic tracking</summary>
          <div className="seg-body">
            <div className="field-head">Tracking table</div>
            <div className="row path-row">
              <input className="input" value={state.path_to_table || ""} onChange={(e) => setField("path_to_table", e.target.value)} placeholder="/path/Results.csv" />
              <button
                className="ghost"
                title="Open a file picker to choose the tracking Results.csv input table."
                onClick={async () => {
                  try {
                    const p = await onPickCsv();
                    if (p) setField("path_to_table", p);
                  } catch {
                    // no-op
                  }
                }}
              >
                Browse CSV
              </button>
            </div>
            <div className="field-head">Image folder</div>
            <div className="row path-row">
              <input className="input" value={state.image_dir || ""} onChange={(e) => setField("image_dir", e.target.value)} placeholder="Image folder (required)" />
              <button
                className="ghost"
                title="Choose the folder containing the source images used by the tracking viewer."
                onClick={async () => {
                  try {
                    const p = await onPickDirectory();
                    if (p) setField("image_dir", p);
                  } catch {
                    // no-op
                  }
                }}
              >
                Browse
              </button>
            </div>
            <div className="hint">This folder is used to render the tracking viewer images.</div>
            <div className="field-head">
              Image name column <Tip text="Required. Choose the CSV column that stores image file names. These names must exactly match files inside the selected image folder." />
            </div>
            <select
              className="input"
              value={state.image_col || ""}
              onChange={(e) => setField("image_col", e.target.value)}
            >
              <option value="">Select image column</option>
              {imageNameColumns.map((col) => (
                <option key={`tracking-img-col-${col}`} value={col}>{col}</option>
              ))}
            </select>
            <div className="hint">The values in this column must match the image filenames in the folder above.</div>
            <div className="field-head">Tracking parameters</div>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Max distance <Tip text="Maximum distance allowed to link a cell to a candidate in the next frame." /></div>
                <input className="input" type="number" min="1" value={state.max_distance ?? 30} onChange={(e) => setField("max_distance", Number(e.target.value || 30))} placeholder="max distance" />
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">Time window <Tip text="How many frames the tracker can remember when reconnecting interrupted trajectories." /></div>
                <input className="input" type="number" min="1" value={state.time_window ?? 5} onChange={(e) => setField("time_window", Number(e.target.value || 5))} placeholder="time window" />
              </div>
            </div>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Max split distance <Tip text="Maximum distance used to detect possible split events between nearby trajectory segments." /></div>
                <input className="input" type="number" min="1" value={state.max_split_distance ?? 10} onChange={(e) => setField("max_split_distance", Number(e.target.value || 10))} placeholder="max split distance" />
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">Gap closing distance <Tip text="Maximum distance allowed when reconnecting a trajectory after a temporary gap." /></div>
                <input className="input" type="number" min="1" value={state.max_gap_closing_distance ?? 30} onChange={(e) => setField("max_gap_closing_distance", Number(e.target.value || 30))} placeholder="max gap closing distance" />
              </div>
            </div>
            <div className="row">
              <button className="primary" title="Run automatic tracking with the parameters above and generate the first tracked table." onClick={onRunAutomatic} disabled={!canRun}>
                {running ? "Running..." : "Run tracking"}
              </button>
              <button className="secondary" title="Move to step 2 after a tracked table has been generated." onClick={onGoToCorrection} disabled={!canGoToCorrection}>
                Next
              </button>
            </div>
            <Status level={status.level} text={status.text} />
          </div>
          </details>
        )}

        {workflowStage === "menu" && (
          <details open className="seg-section">
            <summary>Step 2 - Choose action</summary>
            <div className="seg-body">
              <div className="field-head">1. Save results</div>
              <div className="row path-row">
                <input className="input" value={state.save_results_dir || ""} onChange={(e) => setField("save_results_dir", e.target.value)} placeholder="Folder to save table and tracking images" />
                <button
                  className="ghost"
                  title="Choose where the final table and rendered tracking images should be exported."
                  onClick={async () => {
                    try {
                      const p = await onPickDirectory();
                      if (p) setField("save_results_dir", p);
                    } catch {
                      // no-op
                    }
                  }}
                >
                  Browse
                </button>
              </div>
              <button className="secondary" title="Export the current tracked table and the cached tracking images to the selected folder." onClick={onSaveResults} disabled={!canSaveResults}>
                Save results
              </button>
              <div className="field-head" style={{ marginTop: 10 }}>2. Correct tracks</div>
              <button className="primary" title="Open the manual correction viewer to inspect and edit tracks." onClick={onOpenCorrection} disabled={!hasTracked || busy}>
                Correct tracks
              </button>
              <Status level={status.level} text={status.text} />
            </div>
          </details>
        )}

        {workflowStage === "correction" && (
          <details open className="seg-section">
            <summary>Step 2 - Manual correction</summary>
            <div className="seg-body">
              <div className="row row-right">
                <button className="ghost btn-small" title="Return to the step 2 menu without losing the current tracked table." onClick={onGoToCorrection} disabled={busy}>Back to options</button>
              </div>
              <div className="row path-row">
                <input className="input" value={state.image_dir || ""} onChange={(e) => setField("image_dir", e.target.value)} placeholder="Image folder for viewer" />
                <button
                  className="ghost"
                  title="Choose the image folder used by the correction viewer."
                  onClick={async () => {
                    try {
                      const p = await onPickDirectory();
                      if (p) setField("image_dir", p);
                    } catch {
                      // no-op
                    }
                  }}
                >
                  Browse
                </button>
              </div>
              <div className="hint">{state.preview_cache_dir ? "Viewer cache ready." : "Viewer cache will be generated automatically."}</div>
              <label className="checkbox">
                <input type="checkbox" checked={!!state.show_complete_trail} onChange={(e) => setField("show_complete_trail", e.target.checked)} />
                Show complete trail
              </label>
              <button className="secondary" title="Redraw the current frame using the latest table state and viewer settings." onClick={onRefreshFrame} disabled={!canPreview}>
                {loadingFrame ? "Updating..." : "Refresh preview"}
              </button>
              <button className="primary" title="Finish correction and open the final export options for the tracked table and images." onClick={() => setField("finish_open", !state.finish_open)} disabled={!hasTracked || busy}>
                {state.finish_open ? "Hide finish options" : "Finish"}
              </button>
              {state.finish_open && (
                <>
                  <div className="field-head">Finish output folder</div>
                  <div className="row path-row">
                    <input className="input" value={state.save_results_dir || ""} onChange={(e) => setField("save_results_dir", e.target.value)} placeholder="Folder to save final tracking outputs" />
                    <button
                      className="ghost"
                      title="Choose the folder where the final tracking outputs will be exported."
                      onClick={async () => {
                        try {
                          const p = await onPickDirectory();
                          if (p) setField("save_results_dir", p);
                        } catch {
                          // no-op
                        }
                      }}
                    >
                      Browse
                    </button>
                  </div>
                  <div className="row">
                    <button className="secondary" title="Export only the final tracked table to the selected folder." onClick={() => onSaveResults(false)} disabled={!canSaveResults}>
                      Save table only
                    </button>
                    <button className="primary" title="Export the final tracked table together with the rendered tracking images." onClick={() => onSaveResults(true)} disabled={!canSaveResults}>
                      Save table + images
                    </button>
                  </div>
                </>
              )}
              <Status level={status.level} text={status.text} />
            </div>
          </details>
        )}
      </div>
    </Card>
  );
}

function StatsTableView({ table, onDownload }) {
  const cols = table?.columns || [];
  const rows = table?.rows || [];
  const group1Key = cols.find((c) => ["group1", "grupo1"].includes(String(c).toLowerCase()));
  const group2Key = cols.find((c) => ["group2", "grupo2"].includes(String(c).toLowerCase()));
  const valueKey = cols.find((c) => ["p_tukey", "p_adjusted", "p_ajustado", "p_raw"].includes(String(c).toLowerCase()));
  const rejectKey = cols.find((c) => ["reject_h0", "significativo"].includes(String(c).toLowerCase()));
  const isPairwiseLongTable = !!group1Key && !!group2Key && !!valueKey && rows.length > 0;

  let displayCols = cols;
  let displayRows = rows;

  if (isPairwiseLongTable) {
    const labels = Array.from(
      new Set(
        rows.flatMap((row) => [String(row?.[group1Key] ?? ""), String(row?.[group2Key] ?? "")]).filter(Boolean)
      )
    );
    const pairMap = new Map();
    rows.forEach((row) => {
      const a = String(row?.[group1Key] ?? "");
      const b = String(row?.[group2Key] ?? "");
      const p = row?.[valueKey];
      const reject = rejectKey ? row?.[rejectKey] : null;
      const base = p == null || p === "" ? "" : String(p);
      const text = reject == null || reject === "" ? base : `${base}${String(reject) === "true" ? " *" : ""}`;
      if (!a || !b) return;
      pairMap.set(`${a}||${b}`, text);
      pairMap.set(`${b}||${a}`, text);
    });
    displayCols = ["group", ...labels];
    displayRows = labels.map((label) => {
      const out = { group: label };
      labels.forEach((other) => {
        out[other] = label === other ? "-" : (pairMap.get(`${label}||${other}`) || "");
      });
      return out;
    });
  }
  const rowHeaderKey = isPairwiseLongTable
    ? "group"
    : ((displayCols[0] === "" || String(displayCols[0] || "").toLowerCase() === "group") ? displayCols[0] : null);

  const handleCopy = async () => {
    if (!displayRows.length || !displayCols.length) return;
    const lines = [displayCols.map((c) => String(c ?? "")).join("\t")];
    displayRows.forEach((row) => {
      const vals = displayCols.map((c) => String(row?.[c] ?? ""));
      lines.push(vals.join("\t"));
    });
    await copyText(`${lines.join("\n")}\n`);
  };
  return (
    <div className="section">
      <div className="row row-between">
        <h3>{table?.name || "Table"}</h3>
        <div className="row">
          <button className="ghost btn-small" onClick={handleCopy} disabled={!displayRows.length}>
            Copy table
          </button>
          <button className="ghost btn-small" onClick={() => onDownload?.(table)} disabled={!rows.length}>
            Download CSV
          </button>
        </div>
      </div>
      {!displayRows.length ? (
        <p className="hint">No rows.</p>
      ) : (
        <div className="table-wrap">
          <table className="results-table">
            <thead>
              <tr>{displayCols.map((c) => <th key={`th-${table.name}-${c}`}>{c}</th>)}</tr>
            </thead>
            <tbody>
              {displayRows.slice(0, 2000).map((r, i) => (
                <tr key={`tr-${table.name}-${i}`}>
                  {displayCols.map((c) => (
                    c === rowHeaderKey
                      ? <th key={`td-${table.name}-${i}-${c}`} scope="row" className="results-table-rowhead">{r[c] == null ? "" : String(r[c])}</th>
                      : <td key={`td-${table.name}-${i}-${c}`}>{r[c] == null ? "" : String(r[c])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const emptyRow = () => ({
  id: makeRowId(),
  name: "",
  path: "",
  area_col: "Area",
  nii_col: "NII",
  is_control: false,
  columns: null,
});
const initialNmaRows = () => ([{
  ...emptyRow(),
  name: "Control",
  is_control: true,
}]);

function buildDatasets(rows) {
  return rows
    .filter((r) => r.path.trim())
    .map((r) => ({
      name: r.name?.trim() || r.path.split("/").pop(),
      path: r.path.trim(),
      area_col: r.area_col?.trim() || "Area",
      nii_col: r.nii_col?.trim() || "NII",
      is_control: !!r.is_control,
    }));
}

function Status({ level = "info", text }) {
  if (!text) return null;
  return <div className={`status ${level}`}>{text}</div>;
}

function PlotPanel({ figure, config, onRelayout, onClick }) {
  const ref = React.useRef(null);
  const requestedWidth = Number(figure?.layout?.width);
  const panelWidth = Number.isFinite(requestedWidth) && requestedWidth > 0 ? Math.round(requestedWidth) : 640;
  const effectiveWidth = Math.min(panelWidth, Math.max(640, (typeof window !== "undefined" ? window.innerWidth - 500 : panelWidth)));
  const defaultConfig = {
    displayModeBar: true,
    displaylogo: false,
    responsive: true,
    scrollZoom: true,
    toImageButtonOptions: {
      format: "png",
      filename: "fornma-plot",
      scale: 2,
    },
  };

  React.useEffect(() => {
    if (!ref.current || !figure) return;
    Plotly.react(ref.current, figure.data, figure.layout, config || defaultConfig);
    if (ref.current?.on) {
      if (ref.current.removeAllListeners) {
        ref.current.removeAllListeners("plotly_relayout");
        ref.current.removeAllListeners("plotly_click");
      }
      if (onRelayout) {
        ref.current.on("plotly_relayout", onRelayout);
      }
      if (onClick) {
        ref.current.on("plotly_click", onClick);
      }
    }
  }, [figure, config, onRelayout, onClick]);

  return (
    <div className="plot-host">
      <div className="plot" style={{ "--plot-width": `${effectiveWidth}px` }} ref={ref} />
    </div>
  );
}

function ellipseTrace(xc, yc, rx, ry, n = 256) {
  const x = [];
  const y = [];
  for (let i = 0; i < n; i += 1) {
    const t = (i / n) * Math.PI * 2;
    x.push(xc + rx * Math.cos(t));
    y.push(yc + ry * Math.sin(t));
  }
  return {
    x,
    y,
    mode: "lines",
    line: { width: 2, color: "black" },
    name: "threshold",
    hoverinfo: "skip",
  };
}

function buildStep1Figure(sample, stats, graphLimits, sdNii, sdArea) {
  const data = [];
  if (sample?.x?.length && sample?.y?.length) {
    data.push({
      x: sample.x,
      y: sample.y,
      mode: "markers",
      type: "scattergl",
      marker: { size: 6, opacity: 0.65, color: "#2563eb" },
      name: "Controls (sample)",
    });
  }
  const rx = sdNii * (stats?.sd_x || 1);
  const ry = sdArea * (stats?.sd_y || 1);
  data.push(ellipseTrace(stats?.mu_x || 0, stats?.mu_y || 0, rx, ry));
  const layout = {
    autosize: false,
    width: 640,
    height: 640,
    margin: { l: 60, r: 10, t: 50, b: 60 },
    title: { text: "NMA · Elipse de controle", x: 0.5, xanchor: "center" },
    xaxis: { title: "NII", range: [graphLimits?.[2] ?? 0, graphLimits?.[3] ?? 1], fixedrange: true },
    yaxis: { title: "Area", range: [graphLimits?.[0] ?? 0, graphLimits?.[1] ?? 1], fixedrange: true },
  };
  return { data, layout };
}

function computeThresholds(stats, sdNii, sdArea) {
  if (!stats) {
    return {
      v_up: 0,
      v_mid: 0,
      v_down: 0,
      v_down2: 0,
      y_high: 0,
      y_low: 0,
    };
  }
  const v = stats.mu_x + 1.5 * (sdNii || 1) * (stats.sd_x || 1);
  const y_high = stats.mu_y + (sdArea || 1) * (stats.sd_y || 1);
  const y_low = stats.mu_y - (sdArea || 1) * (stats.sd_y || 1);
  return {
    v_up: v,
    v_mid: v,
    v_down: stats.mu_x,
    v_down2: v,
    y_high,
    y_low,
  };
}

function buildQuadrantAnnotations(graphLimits, thresholds, stats, sdArea, percentages) {
  const xMin = graphLimits[2];
  const xMax = graphLimits[3];
  const yMin = graphLimits[0];
  const yMax = graphLimits[1];
  const yHigh = stats.mu_y + (sdArea || 1) * (stats.sd_y || 1);
  const yLow = stats.mu_y - (sdArea || 1) * (stats.sd_y || 1);
  const mid = (a, b) => (a + b) / 2;
  const makeText = (label) => {
    const pct = percentages?.[label];
    if (!pct) return label;
    const lines = Object.entries(pct)
      .sort((a, b) => b[1] - a[1])
      .map(([name, value]) => `${name}: ${value.toFixed(1)}%`);
    return [label, ...lines].join("<br>");
  };
  return [
    { label: "SR", x: mid(xMin, thresholds.v_down), y: mid(yMin, yLow) },
    { label: "S", x: mid(thresholds.v_down, thresholds.v_down2), y: mid(yMin, yLow) },
    { label: "SI", x: mid(thresholds.v_down2, xMax), y: mid(yMin, yLow) },
    { label: "N", x: mid(xMin, thresholds.v_mid), y: mid(yLow, yHigh) },
    { label: "I", x: mid(thresholds.v_mid, xMax), y: mid(yLow, yHigh) },
    { label: "LR", x: mid(xMin, thresholds.v_up), y: mid(yHigh, yMax) },
    { label: "LI", x: mid(thresholds.v_up, xMax), y: mid(yHigh, yMax) },
  ].map((a) => ({
    text: makeText(a.label),
    x: a.x,
    y: a.y,
    showarrow: false,
    font: { size: 12, color: "#1b2a3a" },
    bgcolor: "rgba(245, 248, 251, 0.9)",
    bordercolor: "rgba(27, 42, 58, 0.15)",
    borderwidth: 1,
    borderpad: 4,
  }));
}

function computeQuadrantPercentages(traces, thresholds, stats, sdArea) {
  if (!traces || !stats) return null;
  const yHigh = stats.mu_y + (sdArea || 1) * (stats.sd_y || 1);
  const yLow = stats.mu_y - (sdArea || 1) * (stats.sd_y || 1);
  const out = { LR: {}, LI: {}, N: {}, I: {}, SR: {}, S: {}, SI: {} };
  const toNum = (v) => {
    if (v == null) return NaN;
    if (typeof v === "string") return Number(v.replace(",", "."));
    return Number(v);
  };
  const toArray = (v) => {
    if (!v) return [];
    if (Array.isArray(v)) return v;
    if (ArrayBuffer.isView(v)) return Array.from(v);
    if (typeof v === "object") {
      if (v.bdata && v.dtype && typeof window !== "undefined") {
        try {
          const bin = atob(v.bdata);
          const buf = new ArrayBuffer(bin.length);
          const bytes = new Uint8Array(buf);
          for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i);
          let arr = null;
          if (v.dtype === "f4") arr = new Float32Array(buf);
          if (v.dtype === "f8") arr = new Float64Array(buf);
          if (v.dtype === "i4") arr = new Int32Array(buf);
          if (v.dtype === "i2") arr = new Int16Array(buf);
          if (arr) return Array.from(arr);
        } catch (_) {
          return [];
        }
      }
      if (Array.isArray(v.data)) return v.data;
      if (Array.isArray(v.values)) return v.values;
      if (Array.isArray(v.array)) return v.array;
    }
    return [];
  };
  traces.forEach((t) => {
    const name = t.name || "dataset";
    const xs = toArray(t.x);
    const ys = toArray(t.y);
    let total = 0;
    const counts = { LR: 0, LI: 0, N: 0, I: 0, SR: 0, S: 0, SI: 0 };
    for (let i = 0; i < xs.length; i += 1) {
      const x = toNum(xs[i]);
      const y = toNum(ys[i]);
      if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
      total += 1;
      if (y >= yHigh) {
        if (x < thresholds.v_up) counts.LR += 1;
        else counts.LI += 1;
      } else if (y >= yLow) {
        if (x < thresholds.v_mid) counts.N += 1;
        else counts.I += 1;
      } else {
        if (x < thresholds.v_down) counts.SR += 1;
        else if (x < thresholds.v_down2) counts.S += 1;
        else counts.SI += 1;
      }
    }
    Object.keys(counts).forEach((k) => {
      out[k][name] = total === 0 ? 0 : (counts[k] / total) * 100;
    });
  });
  return out;
}

function buildStep2Figure(
  traces,
  stats,
  graphLimits,
  thresholds,
  sdNii,
  sdArea,
  withLabels = false,
  verticalColor = "#12c7e5",
  horizontalColor = "black"
) {
  const data = [...(traces || [])];
  const rx = (sdNii || 1) * (stats.sd_x || 1);
  const ry = (sdArea || 1) * (stats.sd_y || 1);
  data.push(ellipseTrace(stats.mu_x, stats.mu_y, rx, ry));

  const y_high = stats.mu_y + (sdArea || 1) * (stats.sd_y || 1);
  const y_low = stats.mu_y - (sdArea || 1) * (stats.sd_y || 1);
  const v_up_top = stats.mu_y + (2 + (sdArea || 1)) * (stats.sd_y || 1);
  const v_down_bottom = stats.mu_y - (1 + (sdArea || 1)) * (stats.sd_y || 1);
  const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
  const y_top = clamp(v_up_top, graphLimits[0], graphLimits[1]);
  const y_bottom = clamp(v_down_bottom, graphLimits[0], graphLimits[1]);

  const shapes = [
    {
      type: "line",
      x0: graphLimits[2],
      x1: graphLimits[3],
      y0: y_high,
      y1: y_high,
      line: { color: horizontalColor, width: 2 },
      editable: false,
    },
    {
      type: "line",
      x0: graphLimits[2],
      x1: graphLimits[3],
      y0: y_low,
      y1: y_low,
      line: { color: horizontalColor, width: 2 },
      editable: false,
    },
    {
      type: "line",
      x0: thresholds.v_down,
      x1: thresholds.v_down,
      y0: y_bottom,
      y1: y_low,
      line: { color: verticalColor, width: 3 },
      editable: true,
    },
    {
      type: "line",
      x0: thresholds.v_down2,
      x1: thresholds.v_down2,
      y0: y_bottom,
      y1: y_low,
      line: { color: verticalColor, width: 3 },
      editable: true,
    },
    {
      type: "line",
      x0: thresholds.v_mid,
      x1: thresholds.v_mid,
      y0: y_low,
      y1: y_high,
      line: { color: verticalColor, width: 3 },
      editable: true,
    },
    {
      type: "line",
      x0: thresholds.v_up,
      x1: thresholds.v_up,
      y0: y_high,
      y1: y_top,
      line: { color: verticalColor, width: 3 },
      editable: true,
    },
  ];

  const layout = {
    autosize: false,
    width: 640,
    height: 640,
    margin: { l: 60, r: 10, t: 50, b: 60 },
    title: { text: "NMA · Thresholds", x: 0.5, xanchor: "center" },
    xaxis: { title: "NII", range: [graphLimits[2], graphLimits[3]], fixedrange: true },
    yaxis: { title: "Area", range: [graphLimits[0], graphLimits[1]], fixedrange: true },
    shapes,
    annotations: withLabels
      ? buildQuadrantAnnotations(
          graphLimits,
          thresholds,
          stats,
          sdArea,
          computeQuadrantPercentages(traces, thresholds, stats, sdArea)
        )
      : [],
  };

  return { data, layout };
}

export default function App() {
  const [activeModule, setActiveModule] = useState(() => readStorage(STORAGE_KEYS.activeModule, "Home"));
  const [homeSection, setHomeSection] = useState("about");
  const [rows, setRows] = useState(initialNmaRows());
  const [collapsedById, setCollapsedById] = useState({});

  const [step, setStep] = useState(1);
  const [step1Ready, setStep1Ready] = useState(false);
  const [status, setStatus] = useState("");
  const [statusLevel, setStatusLevel] = useState("info");

  const [step1Figure, setStep1Figure] = useState(null);
  const [step1Stats, setStep1Stats] = useState(null);
  const [step1GraphLimits, setStep1GraphLimits] = useState(null);
  const [step1Sample, setStep1Sample] = useState(null);

  const [sdArea, setSdArea] = useState(1.0);
  const [sdNii, setSdNii] = useState(1.0);

  const [thresholds, setThresholds] = useState({
    v_up: 0,
    v_mid: 0,
    v_down: 0,
    v_down2: 0,
    y_high: 0,
    y_low: 0,
  });

  const [step2Figure, setStep2Figure] = useState(null);
  const [step2Traces, setStep2Traces] = useState(null);
  const [step2Stats, setStep2Stats] = useState(null);
  const [step2GraphLimits, setStep2GraphLimits] = useState(null);
  const [finalMode, setFinalMode] = useState(false);
  const [downloadReady, setDownloadReady] = useState(false);
  const [step2Percentages, setStep2Percentages] = useState(null);
  const [showPlotConfig, setShowPlotConfig] = useState(false);
  const [plotConfig, setPlotConfig] = useState({
    ...initialPlotConfig(),
  });
  const [plotSavePath, setPlotSavePath] = useState("");
  const [plotJob, setPlotJob] = useState(() => ({ ...DEFAULT_PLOT_JOB, ...readStorage(STORAGE_KEYS.plotJob, {}) }));
  const [currentPlotIndex, setCurrentPlotIndex] = useState(0);
  const [showNmaPreviewWhilePlotting, setShowNmaPreviewWhilePlotting] = useState(false);
  const [segJob, setSegJob] = useState(() => ({ ...DEFAULT_SEG_JOB, ...readStorage(STORAGE_KEYS.segJob, {}) }));
  const [regJob, setRegJob] = useState(() => ({ ...DEFAULT_REG_JOB, ...readStorage(STORAGE_KEYS.regJob, {}) }));
  const [fociJob, setFociJob] = useState(() => ({ ...DEFAULT_FOCI_JOB, ...readStorage(STORAGE_KEYS.fociJob, {}) }));
  const [segPreviewNonce, setSegPreviewNonce] = useState(0);
  const [segPreviewPage, setSegPreviewPage] = useState(0);
  const [lastSegPreviewPayload, setLastSegPreviewPayload] = useState(null);
  const [segPanelResetKey, setSegPanelResetKey] = useState(0);
  const [regPanelResetKey, setRegPanelResetKey] = useState(0);
  const [fociPanelResetKey, setFociPanelResetKey] = useState(0);
  const [plotData, setPlotData] = useState(initialPlotDataState);
  const [plotDataStatus, setPlotDataStatus] = useState({ level: "info", text: "" });
  const [plotDataLoading, setPlotDataLoading] = useState(false);
  const [clustering, setClustering] = useState(initialClusteringState);
  const [clusteringStatus, setClusteringStatus] = useState({ level: "info", text: "" });
  const [clusteringLoading, setClusteringLoading] = useState(false);
  const [clusteringElbowLoading, setClusteringElbowLoading] = useState(false);
  const [statsState, setStatsState] = useState(initialStatsState);
  const [statsStatus, setStatsStatus] = useState({ level: "info", text: "" });
  const [statsLoading, setStatsLoading] = useState(false);
  const [gatingState, setGatingState] = useState(initialGatingState);
  const [gatingStatus, setGatingStatus] = useState({ level: "info", text: "" });
  const [gatingLoading, setGatingLoading] = useState(false);
  const [gatingApplying, setGatingApplying] = useState(false);
  const [trackingState, setTrackingState] = useState(initialTrackingState);
  const [trackingStatus, setTrackingStatus] = useState({ level: "info", text: "" });
  const [trackingRunning, setTrackingRunning] = useState(false);
  const [trackingLoadingFrame, setTrackingLoadingFrame] = useState(false);
  const [trackingEditing, setTrackingEditing] = useState(false);
  const fileInputRef = React.useRef(null);
  const attemptedColumnsRef = React.useRef(new Set());
  const plotDataColsCacheRef = React.useRef({});
  const clusteringColsCacheRef = React.useRef({});
  const statsColsCacheRef = React.useRef({});
  const statsFilterValuesCacheRef = React.useRef({});
  const gatingColsCacheRef = React.useRef({});
  const trackingColsCacheRef = React.useRef({});
  const gatingRelayoutTimerRef = React.useRef(null);
  const plotDataPathsKey = useMemo(
    () => (plotData.datasets || []).map((d) => String(d.path || "").trim()).join("||"),
    [plotData.datasets]
  );
  const clusteringPathsKey = useMemo(
    () => (clustering.datasets || []).map((d) => String(d.path || "").trim()).join("||"),
    [clustering.datasets]
  );
  const statsPathsKey = useMemo(
    () => (statsState.datasets || []).map((d) => String(d.path || "").trim()).join("||"),
    [statsState.datasets]
  );
  const gatingPathsKey = useMemo(
    () => (gatingState.datasets || []).map((d) => String(d.path || "").trim()).join("||"),
    [gatingState.datasets]
  );
  const trackingTablePath = useMemo(
    () => String(trackingState.path_to_table || "").trim(),
    [trackingState.path_to_table]
  );
  const hasPlotRun = Boolean(plotJob.job_id);
  const hasSegSession =
    Boolean(segJob.job_id) ||
    (segJob.status && segJob.status !== "idle") ||
    Boolean(segJob.error) ||
    Boolean(segJob.log) ||
    Boolean(segJob.preview_path) ||
    ((segJob.preview_paths || []).length > 0);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.activeModule, JSON.stringify(activeModule));
  }, [activeModule]);

  const handleSelectHomeSection = (sectionId) => {
    setHomeSection(sectionId);
    if (typeof window === "undefined") return;
    window.requestAnimationFrame(() => {
      const target = document.getElementById(`home-${sectionId}`);
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  const handleOpenTutorial = (moduleName) => {
    const sectionId = MODULE_TUTORIAL_SECTION[moduleName];
    setActiveModule("Home");
    if (!sectionId) return;
    setHomeSection(sectionId);
    if (typeof window === "undefined") return;
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        const target = document.getElementById(`home-${sectionId}`);
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  };

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.plotJob, JSON.stringify(plotJob));
  }, [plotJob]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.segJob, JSON.stringify(segJob));
  }, [segJob]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.regJob, JSON.stringify(regJob));
  }, [regJob]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.fociJob, JSON.stringify(fociJob));
  }, [fociJob]);

  const datasets = useMemo(() => buildDatasets(rows), [rows]);
  const allDetectedColumns = useMemo(
    () => Array.from(new Set(rows.flatMap((r) => (r.columns || []).map((c) => String(c))))).sort(),
    [rows]
  );
  const hasControl = datasets.some((d) => d.is_control);

  const updateRow = (idx, patch) => {
    setRows((prev) => prev.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  };

  const addRow = () => setRows((prev) => [...prev, emptyRow()]);
  const removeRow = (idx) => setRows((prev) => prev.filter((_, i) => i !== idx));
  const toggleDatasetCollapse = (rowId) => {
    setCollapsedById((prev) => ({ ...prev, [rowId]: !prev[rowId] }));
  };
  const setAllCollapsed = (collapsed) => {
    setCollapsedById(
      Object.fromEntries(rows.map((r) => [r.id, collapsed]))
    );
  };

  const callApi = async (path, payload) => {
    let res;
    try {
      res = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (err) {
      if (err instanceof TypeError) {
        throw new Error("Failed to fetch API. Check if backend is running at http://127.0.0.1:8000.");
      }
      throw err;
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    return res.json();
  };

  const setPlotDataStatusMsg = (text, level = "info") => {
    setPlotDataStatus({ text, level });
  };

  useEffect(() => {
    if (!showPlotConfig) return;
    const targets = rows
      .map((row, idx) => ({ row, idx }))
      .filter(({ row }) => {
        const p = row.path?.trim();
        if (!p) return false;
        if ((row.columns || []).length > 0) return false;
        return !attemptedColumnsRef.current.has(p);
      });

    if (targets.length === 0) return;
    let cancelled = false;

    (async () => {
      const loaded = await Promise.all(
        targets.map(async ({ row, idx }) => {
          const path = row.path.trim();
          attemptedColumnsRef.current.add(path);
          try {
            const res = await callApi("/nma/datasets/columns", { path });
            return { idx, columns: res.columns || [] };
          } catch {
            return { idx, columns: [] };
          }
        })
      );

      if (cancelled) return;
      setRows((prev) =>
        prev.map((r, i) => {
          const hit = loaded.find((x) => x.idx === i);
          if (!hit || hit.columns.length === 0) return r;
          const areaGuess = hit.columns.find((c) => c.toLowerCase().includes("area")) || hit.columns[0] || r.area_col || "Area";
          const niiGuess = hit.columns.find((c) => c.toLowerCase().includes("nii")) || hit.columns[0] || r.nii_col || "NII";
          return {
            ...r,
            columns: hit.columns,
            area_col: r.area_col && hit.columns.includes(r.area_col) ? r.area_col : areaGuess,
            nii_col: r.nii_col && hit.columns.includes(r.nii_col) ? r.nii_col : niiGuess,
          };
        })
      );
    })();

    return () => {
      cancelled = true;
    };
  }, [rows, showPlotConfig]);

  useEffect(() => {
    const datasets = plotData.datasets || [];
    const targets = datasets
      .map((d, idx) => ({ d, idx }))
      .filter(({ d }) => String(d.path || "").trim());
    if (targets.length === 0) {
      setPlotData((prev) => {
        if ((prev.columns || []).length === 0 && (prev.categoricalColumns || []).length === 0 && (prev.controlOptions || []).length === 0 && !prev.columnsWarning) return prev;
        return { ...prev, columns: [], categoricalColumns: [], controlOptions: [], columnsWarning: "" };
      });
      return;
    }
    let cancelled = false;
    (async () => {
      const loaded = await Promise.all(
        targets.map(async ({ d, idx }) => {
          const path = String(d.path || "").trim();
          if (plotDataColsCacheRef.current[path]) {
            return { idx, path, ...plotDataColsCacheRef.current[path] };
          }
          try {
            const res = await callApi("/nma/datasets/columns", { path });
            const cols = res.columns || [];
            const categorical = res.categorical_columns || [];
            plotDataColsCacheRef.current[path] = { columns: cols, categorical };
            return { idx, path, columns: cols, categorical };
          } catch {
            return { idx, path, columns: [], categorical: [] };
          }
        })
      );
      if (cancelled) return;
      const valid = loaded.filter((x) => x.columns.length > 0);
      const firstCols = valid[0]?.columns || [];
      const firstCategorical = valid[0]?.categorical || [];
      const mismatch = valid.some((x) =>
        x.columns.length !== firstCols.length ||
        x.columns.some((c, i) => c !== firstCols[i])
      );
      setPlotData((prev) => {
        const nextDatasets = (prev.datasets || []).map((d, i) => {
          const hit = loaded.find((x) => x.idx === i);
          if (!hit) return d;
          if (sameArray(d.columns || [], hit.columns || [])) return d;
          return { ...d, columns: hit.columns };
        });
        const keepIfExists = (key) => (firstCols.includes(prev[key]) ? prev[key] : "");
        const nextWarning = mismatch
          ? "CSV columns are not identical. Use files with exactly the same columns and order."
          : "";
        const didDatasetsChange = nextDatasets.some((d, i) => d !== (prev.datasets || [])[i]);
        const sameColumns = sameArray(prev.columns || [], firstCols || []);
        const sameCategorical = sameArray(prev.categoricalColumns || [], firstCategorical || []);
        const sameAxes =
          keepIfExists("x") === prev.x &&
          keepIfExists("y") === prev.y &&
          keepIfExists("hue") === prev.hue &&
          keepIfExists("size") === prev.size;
        if (!didDatasetsChange && sameColumns && sameCategorical && sameAxes && nextWarning === (prev.columnsWarning || "")) {
          return prev;
        }
        return {
          ...prev,
          datasets: nextDatasets,
          columns: firstCols,
          categoricalColumns: firstCategorical,
          x: keepIfExists("x"),
          y: keepIfExists("y"),
          hue: keepIfExists("hue"),
          size: keepIfExists("size"),
          columnsWarning: nextWarning,
        };
      });
      try {
        const condRes = await callApi("/graphs/conditions", {
          datasets: targets.map(({ d }) => ({
            name: String(d.name || "").trim(),
            path: String(d.path || "").trim(),
          })),
        });
        if (cancelled) return;
        const nextConditions = condRes.conditions || [];
        setPlotData((prev) => {
          const validControl = prev.control && nextConditions.includes(prev.control) ? prev.control : "";
          if (sameArray(prev.controlOptions || [], nextConditions) && prev.control === validControl) return prev;
          return { ...prev, controlOptions: nextConditions, control: validControl };
        });
      } catch {
        if (cancelled) return;
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [plotDataPathsKey]);

  useEffect(() => {
    const datasets = clustering.datasets || [];
    const targets = datasets
      .map((d, idx) => ({ d, idx }))
      .filter(({ d }) => String(d.path || "").trim());
    if (targets.length === 0) {
      setClustering((prev) => {
        if ((prev.columnsAll || []).length === 0 && (prev.numericColumns || []).length === 0 && (prev.columns || []).length === 0) return prev;
        return { ...prev, columnsAll: [], numericColumns: [], columns: [] };
      });
      return;
    }
    let cancelled = false;
    (async () => {
      const loaded = await Promise.all(
        targets.map(async ({ d, idx }) => {
          const path = String(d.path || "").trim();
          if (clusteringColsCacheRef.current[path]) {
            return { idx, ...clusteringColsCacheRef.current[path] };
          }
          try {
            const res = await callApi("/nma/datasets/columns", { path });
            const payload = {
              columns: res.columns || [],
              numeric: res.numeric_columns || [],
            };
            clusteringColsCacheRef.current[path] = payload;
            return { idx, ...payload };
          } catch {
            return { idx, columns: [], numeric: [] };
          }
        })
      );
      if (cancelled) return;
      const valid = loaded.filter((x) => x.columns.length > 0);
      const firstCols = valid[0]?.columns || [];
      const firstNumeric = valid[0]?.numeric || [];
      setClustering((prev) => {
        const keepNumeric = (prev.columns || []).filter((c) => firstNumeric.includes(c));
        const changed =
          !sameArray(prev.columnsAll || [], firstCols) ||
          !sameArray(prev.numericColumns || [], firstNumeric) ||
          !sameArray(prev.columns || [], keepNumeric);
        if (!changed) return prev;
        return {
          ...prev,
          columnsAll: firstCols,
          numericColumns: firstNumeric,
          columns: keepNumeric.length ? keepNumeric : firstNumeric.slice(0, Math.min(8, firstNumeric.length)),
        };
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [clusteringPathsKey]);

  useEffect(() => {
    const datasets = statsState.datasets || [];
    const targets = datasets
      .map((d, idx) => ({ d, idx }))
      .filter(({ d }) => String(d.path || "").trim());
    if (targets.length === 0) {
      setStatsState((prev) => {
        if ((prev.columns || []).length === 0) return prev;
        return {
          ...prev,
          columns: [],
          categoricalColumns: [],
          numeric_col: "",
          group_col: "",
          group_col1: "",
          group_col2: "",
          category_col: "",
          condition_col: "",
          filters: (prev.filters || [makeStatsFilterRow()]).map((filter) => ({ ...filter, column: "", values: [] })),
          filterValueOptions: {},
        };
      });
      return;
    }
    let cancelled = false;
    (async () => {
      const loaded = await Promise.all(
        targets.map(async ({ d, idx }) => {
          const path = String(d.path || "").trim();
          if (statsColsCacheRef.current[path]) {
            return { idx, ...statsColsCacheRef.current[path] };
          }
          try {
            const res = await callApi("/nma/datasets/columns", { path });
            const entry = {
              columns: res.columns || [],
              categoricalColumns: res.categorical_columns || [],
            };
            statsColsCacheRef.current[path] = entry;
            return { idx, ...entry };
          } catch {
            return { idx, columns: [], categoricalColumns: [] };
          }
        })
      );
      if (cancelled) return;
      const valid = loaded.filter((x) => x.columns.length > 0);
      const firstCols = valid[0]?.columns || [];
      const firstCategorical = valid[0]?.categoricalColumns || [];
      setStatsState((prev) => {
        const keep = (k) => (prev[k] && firstCols.includes(prev[k]) ? prev[k] : "");
        const nextFilters = (prev.filters || [makeStatsFilterRow()]).map((filter) => {
          if (!filter.column || firstCols.includes(filter.column)) {
            return filter;
          }
          return { ...filter, column: "", values: [] };
        });
        const nextFilterValueOptions = Object.fromEntries(
          Object.entries(prev.filterValueOptions || {}).filter(([column]) => firstCols.includes(column))
        );
        if (sameArray(prev.columns || [], firstCols || [])
          && sameArray(prev.categoricalColumns || [], firstCategorical || [])
          && keep("numeric_col") === prev.numeric_col
          && keep("group_col") === prev.group_col
          && keep("group_col1") === prev.group_col1
          && keep("group_col2") === prev.group_col2
          && keep("category_col") === prev.category_col
          && keep("condition_col") === prev.condition_col
          && JSON.stringify(nextFilters) === JSON.stringify(prev.filters || [])
          && JSON.stringify(nextFilterValueOptions) === JSON.stringify(prev.filterValueOptions || {})) return prev;
        return {
          ...prev,
          columns: firstCols,
          categoricalColumns: firstCategorical,
          numeric_col: keep("numeric_col"),
          group_col: keep("group_col"),
          group_col1: keep("group_col1"),
          group_col2: keep("group_col2"),
          category_col: keep("category_col"),
          condition_col: keep("condition_col"),
          filters: nextFilters,
          filterValueOptions: nextFilterValueOptions,
        };
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [statsPathsKey]);

  useEffect(() => {
    const paths = (statsState.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => String(d.path || "").trim())
      .filter(Boolean);
    const filterColumns = Array.from(new Set(
      (statsState.filters || [])
        .map((filter) => String(filter.column || "").trim())
        .filter(Boolean)
    ));

    if (!paths.length || !filterColumns.length) {
      setStatsState((prev) => {
        if (!Object.keys(prev.filterValueOptions || {}).length) return prev;
        const keepColumns = new Set(
          (prev.filters || [])
            .map((filter) => String(filter.column || "").trim())
            .filter(Boolean)
        );
        const nextOptions = Object.fromEntries(
          Object.entries(prev.filterValueOptions || {}).filter(([column]) => keepColumns.has(column))
        );
        if (JSON.stringify(nextOptions) === JSON.stringify(prev.filterValueOptions || {})) return prev;
        const nextFilters = (prev.filters || []).map((filter) => {
          const opts = nextOptions[filter.column] || [];
          return opts.length ? { ...filter, values: (filter.values || []).filter((value) => opts.includes(value)) } : filter;
        });
        return { ...prev, filters: nextFilters, filterValueOptions: nextOptions };
      });
      return;
    }

    let cancelled = false;
    (async () => {
      const loaded = await Promise.all(
        filterColumns.map(async (column) => {
          const cacheKey = `${paths.join("||")}::${column}`;
          if (statsFilterValuesCacheRef.current[cacheKey]) {
            return { column, values: statsFilterValuesCacheRef.current[cacheKey] };
          }
          try {
            const res = await callApi("/datasets/column-values", { paths, column, limit: 200 });
            const values = (res.values || []).map(normalizeFilterOption).filter(Boolean);
            statsFilterValuesCacheRef.current[cacheKey] = values;
            return { column, values };
          } catch {
            return { column, values: [] };
          }
        })
      );
      if (cancelled) return;
      setStatsState((prev) => {
        const nextOptions = { ...(prev.filterValueOptions || {}) };
        for (const item of loaded) {
          nextOptions[item.column] = item.values || [];
        }
        const nextFilters = (prev.filters || []).map((filter) => {
          const opts = nextOptions[filter.column] || [];
          return {
            ...filter,
            values: (filter.values || []).filter((value) => opts.includes(value)),
          };
        });
        if (JSON.stringify(nextOptions) === JSON.stringify(prev.filterValueOptions || {})
          && JSON.stringify(nextFilters) === JSON.stringify(prev.filters || [])) return prev;
        return { ...prev, filters: nextFilters, filterValueOptions: nextOptions };
      });
    })();

    return () => {
      cancelled = true;
    };
  }, [statsState.datasets, statsState.filters]);

  useEffect(() => {
    const datasets = gatingState.datasets || [];
    const targets = datasets
      .map((d, idx) => ({ d, idx }))
      .filter(({ d }) => String(d.path || "").trim());
    if (targets.length === 0) {
      setGatingState((prev) => {
        if ((prev.columns || []).length === 0 && (prev.numericColumns || []).length === 0) return prev;
        return { ...prev, columns: [], numericColumns: [], x_col: "", y_col: "" };
      });
      return;
    }
    let cancelled = false;
    (async () => {
      const loaded = await Promise.all(
        targets.map(async ({ d, idx }) => {
          const path = String(d.path || "").trim();
          if (gatingColsCacheRef.current[path]) {
            return { idx, ...gatingColsCacheRef.current[path] };
          }
          try {
            const res = await callApi("/nma/datasets/columns", { path });
            const payload = {
              columns: res.columns || [],
              numeric: res.numeric_columns || [],
            };
            gatingColsCacheRef.current[path] = payload;
            return { idx, ...payload };
          } catch {
            return { idx, columns: [], numeric: [] };
          }
        })
      );
      if (cancelled) return;
      const valid = loaded.filter((x) => x.columns.length > 0);
      const firstCols = valid[0]?.columns || [];
      const firstNumeric = valid[0]?.numeric || [];
      setGatingState((prev) => {
        const keep = (k) => (prev[k] && firstNumeric.includes(prev[k]) ? prev[k] : "");
        if (
          sameArray(prev.columns || [], firstCols) &&
          sameArray(prev.numericColumns || [], firstNumeric) &&
          keep("x_col") === prev.x_col &&
          keep("y_col") === prev.y_col
        ) return prev;
        return {
          ...prev,
          columns: firstCols,
          numericColumns: firstNumeric,
          x_col: keep("x_col"),
          y_col: keep("y_col"),
        };
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [gatingPathsKey]);

  useEffect(() => {
    const path = trackingTablePath;
    if (!path) {
      setTrackingState((prev) => {
        if ((prev.columns || []).length === 0 && !prev.image_col) return prev;
        return { ...prev, columns: [], image_col: "" };
      });
      return;
    }
    let cancelled = false;
    (async () => {
      let cols = [];
      if (trackingColsCacheRef.current[path]) {
        cols = trackingColsCacheRef.current[path];
      } else {
        try {
          const res = await callApi("/nma/datasets/columns", { path });
          cols = res.columns || [];
          trackingColsCacheRef.current[path] = cols;
        } catch {
          cols = [];
        }
      }
      if (cancelled) return;
      setTrackingState((prev) => {
        const imgCols = (cols || []).filter((c) => String(c || "").toLowerCase().includes("image_name"));
        const keepImageCol = prev.image_col && imgCols.includes(prev.image_col) ? prev.image_col : "";
        if (sameArray(prev.columns || [], cols) && keepImageCol === prev.image_col) return prev;
        return {
          ...prev,
          columns: cols,
          image_col: keepImageCol,
        };
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [trackingTablePath]);

  const handleDownloadTable = () => {
    if (!step2Percentages) return;
    const quadrantOrder = ["LR", "LI", "N", "I", "SR", "S", "SI"];
    const datasetNames = Array.from(
      new Set(
        Object.values(step2Percentages)
          .flatMap((v) => Object.keys(v))
          .concat((step2Traces || []).map((t) => t.name).filter(Boolean))
      )
    );
    const header = ["Quadrant", ...datasetNames];
    const lines = [header.map(csvCell).join(",")];
    quadrantOrder.forEach((q) => {
      const row = [q];
      datasetNames.forEach((name) => {
        const val = step2Percentages[q]?.[name];
        row.push(val != null ? val.toFixed(1) : "");
      });
      lines.push(row.map(csvCell).join(","));
    });
    const blob = new Blob([`${lines.join("\n")}\n`], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "quadrant_proportions.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const downloadStatsTableCsv = (table) => {
    if (!table?.columns?.length) return;
    const cols = table.columns.map((c) => String(c));
    const lines = [cols.map(csvCell).join(",")];
    (table.rows || []).forEach((row) => {
      const vals = cols.map((c) => csvCell(row?.[c] ?? ""));
      lines.push(vals.join(","));
    });
    const blob = new Blob([`${lines.join("\n")}\n`], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const name = String(table.name || "stats_result").replace(/\s+/g, "_").toLowerCase();
    a.href = url;
    a.download = `${name}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const downloadStatsLogTxt = () => {
    const text = String(statsState.log || "");
    if (!text.trim()) return;
    const blob = new Blob([text], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "statistics_log.txt";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const copyStatsLogTxt = async () => {
    const text = String(statsState.log || "");
    if (!text.trim()) return;
    await copyText(text);
  };

  const pickCsvPath = async () => {
    const res = await fetch(`${API_BASE}/system/pick-csv`, {
      method: "POST",
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    return res.json();
  };

  const pickDirectoryPath = async () => {
    const res = await fetch(`${API_BASE}/system/pick-directory`, {
      method: "POST",
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    return res.json();
  };

  const handleStartSegmentation = async (payload) => {
    if (["starting", "queued", "running", "canceling"].includes(segJob.status)) {
      return;
    }
    scrollToTopSmooth();
    setStatus("Starting segmentation...");
    setStatusLevel("info");
    setSegJob((prev) => ({
      ...prev,
      status: "starting",
      message: "Starting...",
      error: "",
    }));
    try {
      if (payload?.preview) {
        setLastSegPreviewPayload(payload);
      }
      const res = await callApi("/segmentation/start", payload);
      setSegJob({
        job_id: res.job_id,
        status: res.status || "queued",
        progress: 0,
        message: "Queued",
        log: "",
        preview_path: "",
        preview_paths: [],
        preview_index: payload?.preview_index ?? null,
        error: "",
      });
      setSegPreviewNonce((n) => n + 1);
    } catch (err) {
      setSegJob((prev) => ({ ...prev, status: "idle" }));
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  const handleStopSegmentation = async () => {
    if (!segJob.job_id) return;
    try {
      const res = await fetch(`${API_BASE}/segmentation/stop/${segJob.job_id}`, { method: "POST" });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
      }
      setSegJob((prev) => ({ ...prev, status: "canceling", message: "Stop requested..." }));
      setStatus("Stop requested...");
      setStatusLevel("info");
    } catch (err) {
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  const handleStartRegistration = async (payload) => {
    if (["starting", "queued", "running", "canceling"].includes(regJob.status)) {
      return;
    }
    const rows = payload?.images_data?.rows || [];
    const channels = payload?.images_data?.channels || [];
    const idToName = Object.fromEntries(channels.map((c) => [c.id, c.name || c.id]));
    const savePath = String(payload?.reg_data?.save_path || "").trim();
    const reference = payload?.reg_data?.reference;
    const moving = payload?.reg_data?.moving || [];
    const errs = [];
    if (!savePath) errs.push("Please define an output path (Saving path).");
    if (!reference) errs.push("Select a reference channel.");
    if (!moving.length) errs.push("Select at least one moving channel.");
    if (!rows.length) errs.push("No conditions loaded (use Load images).");
    rows.forEach((r, idx) => {
      [reference, ...moving].filter(Boolean).forEach((chId) => {
        if (!String(r[chId] || "").trim()) {
          errs.push(`Row ${idx + 1}: empty path for '${idToName[chId] || chId}'.`);
        }
      });
    });
    if (errs.length) {
      setStatus(errs.join("\n"));
      setStatusLevel("error");
      return;
    }
    scrollToTopSmooth();
    setStatus("Starting registration...");
    setStatusLevel("info");
    setRegJob((prev) => ({ ...prev, status: "starting", message: "Starting...", error: "" }));
    try {
      const res = await callApi("/registration/start", payload);
      setRegJob({
        job_id: res.job_id,
        status: res.status || "queued",
        progress: 0,
        done: 0,
        total: 0,
        message: "Queued",
        log: "",
        error: "",
      });
    } catch (err) {
      setRegJob((prev) => ({ ...prev, status: "idle" }));
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  const handleStopRegistration = async () => {
    if (!regJob.job_id) return;
    try {
      const res = await fetch(`${API_BASE}/registration/stop/${regJob.job_id}`, { method: "POST" });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
      }
      setRegJob((prev) => ({ ...prev, status: "canceling", message: "Stop requested..." }));
      setStatus("Registration stop requested...");
      setStatusLevel("info");
    } catch (err) {
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  const loadFociChannels = async (pkl_path) => {
    const res = await callApi("/foci/channels", { pkl_path });
    return (res.channels || []).map((c) => ({ label: c, value: c }));
  };

  const handleStartFoci = async (payload) => {
    if (["starting", "queued", "running", "canceling"].includes(fociJob.status)) return;
    scrollToTopSmooth();
    setStatus("Starting foci overlay...");
    setStatusLevel("info");
    setFociJob((prev) => ({ ...prev, status: "starting", message: "Starting...", error: "" }));
    try {
      const res = await callApi("/foci/start", payload);
      setFociJob({
        job_id: res.job_id,
        status: res.status || "queued",
        progress: 0,
        message: "Queued",
        log: "",
        error: "",
      });
    } catch (err) {
      setFociJob((prev) => ({ ...prev, status: "idle" }));
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  const handleStopFoci = async () => {
    if (!fociJob.job_id) return;
    try {
      const res = await fetch(`${API_BASE}/foci/stop/${fociJob.job_id}`, { method: "POST" });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
      }
      setFociJob((prev) => ({ ...prev, status: "canceling", message: "Stop requested..." }));
      setStatus("Foci stop requested...");
      setStatusLevel("info");
    } catch (err) {
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  const handleResetSegmentationUi = () => {
    setSegJob({ ...DEFAULT_SEG_JOB });
    setSegPreviewPage(0);
    setSegPreviewNonce((n) => n + 1);
    setLastSegPreviewPayload(null);
    setStatus("");
    setStatusLevel("info");
    setSegPanelResetKey((k) => k + 1);
  };

  const handleStep1 = async () => {
    setShowPlotConfig(false);
    setStatus("Computing step 1...");
    setStatusLevel("info");
    try {
      const payload = {
        params: { datasets },
        sample_per_ds: 2000,
      };
      const data = await callApi("/nma/settings/compute", payload);
      setStep1Sample(data.sample);
      setStep1Stats(data.stats);
      setStep1GraphLimits(data.axis ? [data.axis.y[0], data.axis.y[1], data.axis.x[0], data.axis.x[1]] : null);
      setSdArea(round2(data.sd_factors.sd_area));
      setSdNii(round2(data.sd_factors.sd_nii));
      const fig = buildStep1Figure(
        data.sample,
        data.stats,
        data.axis ? [data.axis.y[0], data.axis.y[1], data.axis.x[0], data.axis.x[1]] : null,
        data.sd_factors.sd_nii,
        data.sd_factors.sd_area
      );
      setStep1Figure(fig);
      setThresholds(computeThresholds(data.stats, data.sd_factors.sd_nii, data.sd_factors.sd_area));
      setStatus("Step 1 ready. Adjust sliders and continue when OK.");
      setStatusLevel("success");
      setStep1Ready(true);
    } catch (err) {
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  const handleAutoDbscan = async () => {
    setStatus("Running DBSCAN...");
    setStatusLevel("info");
    try {
      const payload = { params: { datasets } };
      const data = await callApi("/nma/settings/auto-dbscan", payload);
      setSdNii(round2(data.sd_factors.sd_nii));
      setSdArea(round2(data.sd_factors.sd_area));
      if (step1Stats && step1GraphLimits && step1Sample) {
        setStep1Figure(buildStep1Figure(step1Sample, step1Stats, step1GraphLimits, data.sd_factors.sd_nii, data.sd_factors.sd_area));
      }
      if (step1Stats) {
        setThresholds(computeThresholds(step1Stats, data.sd_factors.sd_nii, data.sd_factors.sd_area));
      }
      setStatus("DBSCAN applied. Update the step 2 figure.");
      setStatusLevel("success");
    } catch (err) {
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  const handleStep2 = async () => {
    setStatus("Generating step 2 figure...");
    setStatusLevel("info");
    try {
      const payload = {
        params: { datasets },
        include_sample: true,
        include_all_datasets: true,
        sd_nii: sdNii,
        sd_area: sdArea,
        thresholds,
      };
      const data = await callApi("/nma/settings/figure", payload);
      const traces = (data.figure?.data || []).filter(
        (t) => t?.mode?.includes("markers") || t?.type === "scattergl"
      );
      setStep2Traces(traces);
      const stats = step1Stats || data.stats;
      const graphLimits = data.graph_limits;
      setStep2Stats(stats);
      setStep2GraphLimits(graphLimits);
      setStep2Figure(buildStep2Figure(traces, stats, graphLimits, thresholds, sdNii, sdArea, true));
      setStep2Percentages(computeQuadrantPercentages(traces, thresholds, stats, sdArea));
      setFinalMode(false);
      setStatus("Step 2 ready.");
      setStatusLevel("success");
      return true;
    } catch (err) {
      setStatus(err.message);
      setStatusLevel("error");
      return false;
    }
  };

  const handleComplete = async () => {
    if (!step2Traces || !step2Stats || !step2GraphLimits) {
      setStatus("Generate the Step 2 figure first.");
      setStatusLevel("error");
      return;
    }
    if (!step1Stats) {
      setStatus("Run step 1 first.");
      setStatusLevel("error");
      return;
    }
    const fig = buildStep2Figure(
      step2Traces,
      step2Stats,
      step2GraphLimits,
      thresholds,
      sdNii,
      sdArea,
      true,
      "black",
      "black"
    );
    setStep2Figure(fig);
    setFinalMode(true);
    setStep2Percentages(computeQuadrantPercentages(step2Traces, thresholds, step2Stats, sdArea));
    try {
      await callApi("/nma/settings/save", {
        name: datasets.find((d) => d.is_control)?.name || "control",
        mean_nii: step1Stats.mu_x,
        std_nii: step1Stats.sd_x,
        mean_area: step1Stats.mu_y,
        std_area: step1Stats.sd_y,
        sd_nii: sdNii,
        sd_area: sdArea,
        graph_limits: step1GraphLimits || step2GraphLimits || [0, 0, 0, 0],
        thresholds,
      });
      setDownloadReady(true);
      setShowPlotConfig(true);
      setStatus("Completed. Final figure ready.");
      setStatusLevel("success");
    } catch (err) {
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  const handleLoadSettings = async (file) => {
    setStatus("Loading settings...");
    setStatusLevel("info");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/nma/settings/upload`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
      }
      const data = await res.json();

      // Apply settings
      setSdArea(round2(data.sd_area));
      setSdNii(round2(data.sd_nii));
      setThresholds(data.thresholds);
      setStep1Stats({
        mu_x: data.mean_nii,
        sd_x: data.std_nii,
        mu_y: data.mean_area,
        sd_y: data.std_area,
      });
      setStep1GraphLimits(data.graph_limits);
      setStep1Ready(true);

      // If datasets exist, build step2 immediately
      if (datasets.length > 0) {
        const payload = {
          params: { datasets },
          include_sample: true,
          include_all_datasets: true,
          sd_nii: data.sd_nii,
          sd_area: data.sd_area,
          thresholds: data.thresholds,
        };
        const figRes = await callApi("/nma/settings/figure", payload);
        const traces = (figRes.figure?.data || []).filter(
          (t) => t?.mode?.includes("markers") || t?.type === "scattergl"
        );
        const stats = {
          mu_x: data.mean_nii,
          sd_x: data.std_nii,
          mu_y: data.mean_area,
          sd_y: data.std_area,
        };
        const graphLimits = figRes.graph_limits || data.graph_limits;
        setStep2Traces(traces);
        setStep2Stats(stats);
        setStep2GraphLimits(graphLimits);
        const finalFig = buildStep2Figure(
          traces,
          stats,
          graphLimits,
          data.thresholds,
          data.sd_nii,
          data.sd_area,
          true,
          "black",
          "black"
        );
        setStep2Figure(finalFig);
        setStep2Percentages(computeQuadrantPercentages(traces, data.thresholds, stats, data.sd_area));
        setFinalMode(true);
        setDownloadReady(true);
        setShowPlotConfig(true);
        setStep(2);
      } else {
        // No datasets: show final plot with no points
        const stats = {
          mu_x: data.mean_nii,
          sd_x: data.std_nii,
          mu_y: data.mean_area,
          sd_y: data.std_area,
        };
        const graphLimits = data.graph_limits;
        const finalFig = buildStep2Figure(
          [],
          stats,
          graphLimits,
          data.thresholds,
          data.sd_nii,
          data.sd_area,
          true,
          "black",
          "black"
        );
        setStep2Figure(finalFig);
        setFinalMode(true);
        setDownloadReady(true);
        setShowPlotConfig(true);
        setStep(2);
      }

      setStatus("Settings loaded.");
      setStatusLevel("success");
    } catch (err) {
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  const updateDotConfig = (patch) => {
    setPlotConfig((prev) => ({ ...prev, dot: { ...prev.dot, ...patch } }));
  };

  const updateHeatmapConfig = (patch) => {
    setPlotConfig((prev) => ({ ...prev, heatmap: { ...prev.heatmap, ...patch } }));
  };

  const toOptionalNumber = (value) => {
    if (value === "" || value == null) return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  };

  const handlePlotAll = async () => {
    if (!plotSavePath.trim()) {
      setStatus("Choose an output folder before plotting.");
      setStatusLevel("error");
      return;
    }
    scrollToTopSmooth();
    setStatus("Starting plot generation...");
    setStatusLevel("info");

    try {
      const payload = {
        params: { datasets },
        output_dir: plotSavePath.trim(),
        kind: plotConfig.kind,
        dot: {
          column1: plotConfig.dot.column1 || null,
          column2: plotConfig.dot.column2 || null,
          hue_min: toOptionalNumber(plotConfig.dot.hue_min),
          hue_max: toOptionalNumber(plotConfig.dot.hue_max),
          size_min: toOptionalNumber(plotConfig.dot.size_min),
          size_max: toOptionalNumber(plotConfig.dot.size_max),
          sample_size: toOptionalNumber(plotConfig.dot.sample_size),
          palette: plotConfig.dot.palette || null,
          single: !!plotConfig.dot.single,
          overtime: !!plotConfig.dot.overtime,
        },
        heatmap: {
          single: !!plotConfig.heatmap.single,
          overtime: !!plotConfig.heatmap.overtime,
          jointplot: !!plotConfig.heatmap.jointplot,
          palette: plotConfig.heatmap.palette || null,
        },
      };

      const res = await callApi("/nma/plots/start", payload);
      setPlotJob({
        job_id: res.job_id,
        status: res.status || "queued",
        progress: 0,
        message: "Queued",
        files: [],
        output_dir: plotSavePath.trim(),
        error: "",
      });
    } catch (err) {
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  useEffect(() => {
    if (!plotJob.job_id) return;
    if (plotJob.status === "completed" || plotJob.status === "failed") return;

    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/nma/plots/status/${plotJob.job_id}`);
        if (res.status === 404) {
          setPlotJob({ ...DEFAULT_PLOT_JOB });
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        setPlotJob((prev) => ({ ...prev, ...data }));
        if (data.status === "completed") {
          setStatus(data.message || "Plots completed.");
          setStatusLevel("success");
        } else if (data.status === "failed") {
          setStatus(data.error || data.message || "Plot failed.");
          setStatusLevel("error");
        }
      } catch {
        // keep polling
      }
    }, 1200);

    return () => clearInterval(timer);
  }, [plotJob.job_id, plotJob.status]);

  useEffect(() => {
    if (!plotJob.files || plotJob.files.length === 0) {
      setCurrentPlotIndex(0);
      return;
    }
    // Keep focus on the most recently generated figure.
    setCurrentPlotIndex(plotJob.files.length - 1);
  }, [plotJob.files]);

  useEffect(() => {
    if (!segJob.job_id) return;
    if (["completed", "failed", "canceled"].includes(segJob.status)) return;

    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/segmentation/status/${segJob.job_id}`);
        if (res.status === 404) {
          setSegJob({ ...DEFAULT_SEG_JOB });
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        setSegJob((prev) => {
          const next = { ...prev, ...data };
          if (
            next.preview_path &&
            (
              next.preview_path !== prev.preview_path ||
              next.progress !== prev.progress ||
              next.status !== prev.status
            )
          ) {
            setSegPreviewNonce((n) => n + 1);
          }
          return next;
        });
        if (data.status === "completed") {
          setStatus(data.message || "Segmentation completed.");
          setStatusLevel("success");
        } else if (data.status === "failed") {
          setStatus(data.error || data.message || "Segmentation failed.");
          setStatusLevel("error");
        } else if (data.status === "canceled") {
          setStatus(data.message || "Segmentation canceled.");
          setStatusLevel("info");
        }
      } catch {
        // keep polling
      }
    }, 900);

    return () => clearInterval(timer);
  }, [segJob.job_id, segJob.status]);

  useEffect(() => {
    if (!regJob.job_id) return;
    if (["completed", "failed", "canceled"].includes(regJob.status)) return;

    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/registration/status/${regJob.job_id}`);
        if (res.status === 404) {
          setRegJob({ ...DEFAULT_REG_JOB });
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        setRegJob((prev) => ({ ...prev, ...data }));
        if (data.status === "completed") {
          setStatus(data.message || "Registration completed.");
          setStatusLevel("success");
        } else if (data.status === "failed") {
          setStatus(data.error || data.message || "Registration failed.");
          setStatusLevel("error");
        } else if (data.status === "canceled") {
          setStatus(data.message || "Registration canceled.");
          setStatusLevel("info");
        }
      } catch {
        // keep polling
      }
    }, 900);

    return () => clearInterval(timer);
  }, [regJob.job_id, regJob.status]);

  useEffect(() => {
    if (!fociJob.job_id) return;
    if (["completed", "failed", "canceled"].includes(fociJob.status)) return;
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/foci/status/${fociJob.job_id}`);
        if (res.status === 404) {
          setFociJob({ ...DEFAULT_FOCI_JOB });
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        setFociJob((prev) => ({ ...prev, ...data }));
        if (data.status === "completed") {
          setStatus(data.message || "Foci overlay completed.");
          setStatusLevel("success");
        } else if (data.status === "failed") {
          setStatus(data.error || data.message || "Foci overlay failed.");
          setStatusLevel("error");
        } else if (data.status === "canceled") {
          setStatus(data.message || "Foci overlay canceled.");
          setStatusLevel("info");
        }
      } catch {
        // keep polling
      }
    }, 900);
    return () => clearInterval(timer);
  }, [fociJob.job_id, fociJob.status]);

  useEffect(() => {
    setSegPreviewPage(0);
  }, [segJob.preview_paths, segJob.preview_index, segJob.job_id]);

  useEffect(() => {
    if (plotJob.job_id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/nma/plots/active`);
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        if (data?.job?.job_id) {
          setPlotJob((prev) => ({ ...DEFAULT_PLOT_JOB, ...prev, ...data.job }));
        }
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [plotJob.job_id]);

  useEffect(() => {
    if (segJob.job_id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/segmentation/active`);
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        if (data?.job?.job_id) {
          setSegJob((prev) => ({ ...DEFAULT_SEG_JOB, ...prev, ...data.job }));
        }
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [segJob.job_id]);

  useEffect(() => {
    if (regJob.job_id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/registration/active`);
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        if (data?.job?.job_id) {
          setRegJob((prev) => ({ ...DEFAULT_REG_JOB, ...prev, ...data.job }));
        }
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [regJob.job_id]);

  useEffect(() => {
    if (fociJob.job_id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/foci/active`);
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        if (data?.job?.job_id) {
          setFociJob((prev) => ({ ...DEFAULT_FOCI_JOB, ...prev, ...data.job }));
        }
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [fociJob.job_id]);

  useEffect(() => () => {
    if (gatingRelayoutTimerRef.current) {
      clearTimeout(gatingRelayoutTimerRef.current);
      gatingRelayoutTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!gatingState.figure) return;
    if (gatingLoading || gatingApplying) return;
    handleGatingPreview({ fromDrag: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gatingState.color_by_dataset]);

  const handleSave = async () => {
    setStatus("Saving settings...");
    setStatusLevel("info");
    try {
      if (!step1Stats) throw new Error("Run step 1 first.");
      const payload = {
        name: datasets.find((d) => d.is_control)?.name || "control",
        mean_nii: step1Stats.mu_x,
        std_nii: step1Stats.sd_x,
        mean_area: step1Stats.mu_y,
        std_area: step1Stats.sd_y,
        sd_nii: sdNii,
        sd_area: sdArea,
        graph_limits: step1GraphLimits || [0, 0, 0, 0],
        thresholds,
      };
      await callApi("/nma/settings/save", payload);
      setStatus("Settings saved successfully.");
      setStatusLevel("success");
    } catch (err) {
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

  const parseCommaList = (txt) => String(txt || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const parseIntList = (txt) => parseCommaList(txt)
    .map((s) => Number(s))
    .filter((n) => Number.isFinite(n))
    .map((n) => Math.trunc(n));

  const handlePlotDataPreview = async () => {
    const datasets = (plotData.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => ({
        name: String(d.name || "").trim(),
        path: String(d.path || "").trim(),
      }))
      .filter((d) => d.path);
    if (!datasets.length) {
      setPlotDataStatusMsg("Select at least one dataset with a valid CSV path.", "error");
      return;
    }
    if (plotData.columnsWarning) {
      setPlotDataStatusMsg(plotData.columnsWarning, "error");
      return;
    }
    const gt = plotData.graph_type || "scatter";
    if (PLOT_TYPES_REQUIRE_XY.has(gt) && (!plotData.x || !plotData.y)) {
      setPlotDataStatusMsg("Select X and Y for this plot type.", "error");
      return;
    }
    if (!PLOT_TYPES_REQUIRE_XY.has(gt) && PLOT_TYPES_REQUIRE_Y.has(gt) && !plotData.y) {
      setPlotDataStatusMsg("Select Y for this plot type.", "error");
      return;
    }
    const effectiveGraphType = (gt === "line" && !!plotData.line_rolling) ? "rolling-average" : gt;
    if (effectiveGraphType === "rolling-average") {
      const nVal = plotData.n === "" ? null : Number(plotData.n);
      if (!Number.isFinite(nVal) || nVal <= 0) {
        setPlotDataStatusMsg("Rolling average requires n > 0.", "error");
        return;
      }
    }
    if (effectiveGraphType === "cpd") {
      const fs = parseIntList(plotData.framesText);
      if (fs.length < 2) {
        setPlotDataStatusMsg("CPD requires at least 2 frames.", "error");
        return;
      }
    }
    if ((gt === "violin" || gt === "box" || gt === "dot" || gt === "bar") && plotData.x && !(plotData.categoricalColumns || []).includes(plotData.x)) {
      setPlotDataStatusMsg("For violin/box/dot/bar, choose a categorical column on X (or leave it empty).", "error");
      return;
    }
    scrollToTopSmooth();
    setPlotDataStatusMsg("Generating interactive preview...", "info");
    setPlotDataLoading(true);
    try {
      const shouldUseFrames = effectiveGraphType === "cpd" || effectiveGraphType === "rolling-average" || (gt === "line" && (!plotData.x || plotData.x === "Frame"));
      const payload = {
        datasets,
        graph_type: effectiveGraphType,
        x: effectiveGraphType === "cpd" ? null : (PLOT_TYPES_SUPPORT_X.has(gt) ? (plotData.x || null) : null),
        y: effectiveGraphType === "cpd" ? null : (plotData.y || null),
        hue: effectiveGraphType === "cpd" ? null : (plotData.hue || null),
        size: effectiveGraphType === "cpd" ? null : (plotData.size || null),
        violin_box: !!plotData.violin_box,
        violin_points: !!plotData.violin_points,
        box_outliers: !!plotData.box_outliers,
        compute_auc: !!plotData.compute_auc,
        control: effectiveGraphType === "cpd" ? (String(plotData.control || "").trim() || null) : null,
        conditions: [],
        frames: shouldUseFrames ? parseIntList(plotData.framesText) : [],
        dot: !!plotData.dot,
        n: effectiveGraphType === "rolling-average" ? (plotData.n === "" ? null : Number(plotData.n)) : null,
      };
      const res = await callApi("/graphs/preview", payload);
      setPlotData((prev) => ({
        ...prev,
        figure: res.figure || null,
        columns: res.columns || prev.columns || [],
        message: res.message || "",
      }));
      if (res.columns?.length) {
        setPlotData((prev) => {
          const safe = (k) => (prev[k] && res.columns.includes(prev[k]) ? prev[k] : "");
          return { ...prev, x: safe("x"), y: safe("y"), hue: safe("hue"), size: safe("size") };
        });
      }
      setPlotDataStatusMsg(res.message || "Preview ready.", "success");
    } catch (err) {
      setPlotDataStatusMsg(err.message, "error");
    } finally {
      setPlotDataLoading(false);
    }
  };

  const handleClusteringPreview = async () => {
    const datasets = (clustering.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => ({
        name: String(d.name || "").trim(),
        path: String(d.path || "").trim(),
      }))
      .filter((d) => d.path);
    if (!datasets.length) {
      setClusteringStatus({ level: "error", text: "Select at least one dataset." });
      return;
    }
    if (!(clustering.columns || []).length) {
      setClusteringStatus({ level: "error", text: "Select at least one numeric feature." });
      return;
    }
    scrollToTopSmooth();
    setClusteringLoading(true);
    setClusteringStatus({ level: "info", text: "Running UMAP preview..." });
    try {
      const payload = {
        datasets,
        columns: clustering.columns,
        method: clustering.method || "umap",
        n_neighbors: Number(clustering.n_neighbors || 15),
        min_dist: Number(clustering.min_dist ?? 0.1),
        metric: clustering.metric || "euclidean",
        scale: !!clustering.scale,
        max_points: Number(clustering.max_points || 12000),
        color_by: clustering.use_clusters ? null : (clustering.color_by || null),
        use_clusters: !!clustering.use_clusters,
        n_clusters: clustering.use_clusters ? Number(clustering.n_clusters || 8) : null,
      };
      const res = await callApi("/clustering/umap/preview", payload);
      setClustering((prev) => ({
        ...prev,
        figure: res.figure || null,
        columnsAll: res.columns || prev.columnsAll || [],
        numericColumns: res.numeric_columns || prev.numericColumns || [],
        message: res.message || "",
      }));
      setClusteringStatus({ level: "success", text: res.message || "Preview ready." });
    } catch (err) {
      setClusteringStatus({ level: "error", text: err.message || "UMAP preview failed." });
    } finally {
      setClusteringLoading(false);
    }
  };

  const handleClusteringElbow = async () => {
    const datasets = (clustering.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => ({
        name: String(d.name || "").trim(),
        path: String(d.path || "").trim(),
      }))
      .filter((d) => d.path);
    if (!datasets.length) {
      setClusteringStatus({ level: "error", text: "Select at least one dataset." });
      return;
    }
    if (!(clustering.columns || []).length) {
      setClusteringStatus({ level: "error", text: "Select at least one numeric feature." });
      return;
    }
    scrollToTopSmooth();
    setClusteringElbowLoading(true);
    setClusteringStatus({ level: "info", text: "Generating elbow plot..." });
    try {
      const payload = {
        datasets,
        columns: clustering.columns,
        method: clustering.method || "umap",
        n_neighbors: Number(clustering.n_neighbors || 15),
        min_dist: Number(clustering.min_dist ?? 0.1),
        metric: clustering.metric || "euclidean",
        scale: !!clustering.scale,
        max_points: Number(clustering.max_points || 12000),
        k_min: Number(clustering.k_min || 2),
        k_max: Number(clustering.k_max || 12),
      };
      const res = await callApi("/clustering/elbow/preview", payload);
      setClustering((prev) => ({ ...prev, elbowFigure: res.figure || null }));
      setClusteringStatus({ level: "success", text: res.message || "Elbow plot ready." });
    } catch (err) {
      setClusteringStatus({ level: "error", text: err.message || "Elbow plot failed." });
    } finally {
      setClusteringElbowLoading(false);
    }
  };

  const handleStatsRun = async () => {
    const method = statsState.method || "oneway";
    const datasets = (statsState.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => String(d.path || "").trim())
      .filter(Boolean);
    if (!datasets.length) {
      setStatsStatus({ level: "error", text: "Select at least one dataset." });
      return;
    }
    if (method === "oneway" && (!statsState.numeric_col || !statsState.group_col)) {
      setStatsStatus({ level: "error", text: "One-way requires numeric and group columns." });
      return;
    }
    if (method === "twoway" && (!statsState.numeric_col || !statsState.group_col1 || !statsState.group_col2)) {
      setStatsStatus({ level: "error", text: "Two-way requires numeric, factor A and factor B." });
      return;
    }
    if (method === "chi2" && (!statsState.group_col || !statsState.category_col)) {
      setStatsStatus({ level: "error", text: "Chi-square requires group and category columns." });
      return;
    }
    if (method === "chi2-subgroups" && (!statsState.group_col || !statsState.condition_col)) {
      setStatsStatus({ level: "error", text: "Chi-square subgroups requires group and condition columns." });
      return;
    }

    const pairs = String(statsState.pairs_text || "")
      .split(";")
      .map((s) => s.trim())
      .filter(Boolean);
    const filters = (statsState.filters || [])
      .map((filter) => ({
        column: String(filter.column || "").trim(),
        values: (filter.values || []).map(normalizeFilterOption).filter(Boolean),
      }))
      .filter((filter) => filter.column);
    if (filters.some((filter) => filter.values.length === 0)) {
      setStatsStatus({ level: "error", text: "Each active subset filter needs at least one selected value." });
      return;
    }

    scrollToTopSmooth();
    setStatsLoading(true);
    setStatsStatus({ level: "info", text: "Running statistical analysis..." });
    try {
      const payload = {
        paths: datasets,
        method,
        numeric_col: statsState.numeric_col || null,
        group_col: statsState.group_col || null,
        group_col1: statsState.group_col1 || null,
        group_col2: statsState.group_col2 || null,
        category_col: statsState.category_col || null,
        condition_col: statsState.condition_col || null,
        alpha: Number(statsState.alpha || 0.05),
        expected_min: Number(statsState.expected_min || 5.0),
        correction_method: statsState.correction_method || "auto",
        pairs_of_interest: pairs,
        filters,
      };
      const res = await callApi("/stats/run", payload);
      setStatsState((prev) => ({
        ...prev,
        tables: res.tables || [],
        log: res.log || "",
        message: res.message || "",
      }));
      setStatsStatus({ level: "success", text: res.message || "Analysis complete." });
    } catch (err) {
      setStatsStatus({ level: "error", text: err.message || "Stats run failed." });
    } finally {
      setStatsLoading(false);
    }
  };

  const parseOptNumber = (v) => {
    if (v === "" || v == null) return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  };

  const handleGatingPreview = async ({ overrideBounds = null, fromDrag = false } = {}) => {
    const datasets = (gatingState.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => ({
        name: String(d.name || "").trim(),
        path: String(d.path || "").trim(),
      }))
      .filter((d) => d.path);
    if (!datasets.length) {
      setGatingStatus({ level: "error", text: "Select at least one dataset." });
      return;
    }
    if (!gatingState.x_col || !gatingState.y_col) {
      setGatingStatus({ level: "error", text: "Select X and Y columns." });
      return;
    }
    if (!fromDrag) {
      scrollToTopSmooth();
    }
    setGatingLoading(true);
    setGatingStatus({ level: "info", text: fromDrag ? "Updating gate preview..." : "Generating gating preview..." });
    try {
      const payload = {
        datasets,
        x_col: gatingState.x_col,
        y_col: gatingState.y_col,
        x_min: overrideBounds?.x_min ?? parseOptNumber(gatingState.x_min),
        x_max: overrideBounds?.x_max ?? parseOptNumber(gatingState.x_max),
        y_min: overrideBounds?.y_min ?? parseOptNumber(gatingState.y_min),
        y_max: overrideBounds?.y_max ?? parseOptNumber(gatingState.y_max),
        q_low: Number(gatingState.q_low ?? 0.05),
        q_high: Number(gatingState.q_high ?? 0.95),
        max_points: Number(gatingState.max_points || 12000),
        color_by_dataset: !!gatingState.color_by_dataset,
      };
      const res = await callApi("/filters/preview", payload);
      setGatingState((prev) => ({
        ...prev,
        figure: res.figure || null,
        tables: res.tables || [],
        message: res.message || "",
        x_min: String(res.bounds?.x_min ?? prev.x_min ?? ""),
        x_max: String(res.bounds?.x_max ?? prev.x_max ?? ""),
        y_min: String(res.bounds?.y_min ?? prev.y_min ?? ""),
        y_max: String(res.bounds?.y_max ?? prev.y_max ?? ""),
      }));
      setGatingStatus({ level: "success", text: res.message || "Preview ready." });
    } catch (err) {
      setGatingStatus({ level: "error", text: err.message || "Gating preview failed." });
    } finally {
      setGatingLoading(false);
    }
  };

  const handleGatingApply = async () => {
    const datasets = (gatingState.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => ({
        name: String(d.name || "").trim(),
        path: String(d.path || "").trim(),
      }))
      .filter((d) => d.path);
    if (!datasets.length) {
      setGatingStatus({ level: "error", text: "Select at least one dataset." });
      return;
    }
    if (!gatingState.x_col || !gatingState.y_col) {
      setGatingStatus({ level: "error", text: "Select X and Y columns." });
      return;
    }
    if (!String(gatingState.output_dir || "").trim()) {
      setGatingStatus({ level: "error", text: "Choose an output directory to save gated CSVs." });
      return;
    }
    scrollToTopSmooth();
    setGatingApplying(true);
    setGatingStatus({ level: "info", text: "Applying gate and writing files..." });
    try {
      const payload = {
        datasets,
        x_col: gatingState.x_col,
        y_col: gatingState.y_col,
        x_min: parseOptNumber(gatingState.x_min),
        x_max: parseOptNumber(gatingState.x_max),
        y_min: parseOptNumber(gatingState.y_min),
        y_max: parseOptNumber(gatingState.y_max),
        q_low: Number(gatingState.q_low ?? 0.05),
        q_high: Number(gatingState.q_high ?? 0.95),
        max_points: Number(gatingState.max_points || 12000),
        color_by_dataset: !!gatingState.color_by_dataset,
        output_dir: String(gatingState.output_dir || "").trim(),
      };
      const res = await callApi("/filters/apply", payload);
      setGatingState((prev) => ({
        ...prev,
        tables: res.tables || prev.tables || [],
        files: res.files || [],
        message: res.message || "",
        output_dir: res.output_dir || prev.output_dir || "",
        x_min: String(res.bounds?.x_min ?? prev.x_min ?? ""),
        x_max: String(res.bounds?.x_max ?? prev.x_max ?? ""),
        y_min: String(res.bounds?.y_min ?? prev.y_min ?? ""),
        y_max: String(res.bounds?.y_max ?? prev.y_max ?? ""),
      }));
      setGatingStatus({ level: "success", text: res.message || "Gating complete." });
    } catch (err) {
      setGatingStatus({ level: "error", text: err.message || "Gating apply failed." });
    } finally {
      setGatingApplying(false);
    }
  };

  const handleGatingRelayout = (evt) => {
    if (!evt) return;
    const shape0 = evt["shapes[0]"];
    const pick = (keyA, keyB, fallback) => {
      const a = evt[keyA];
      const b = evt[keyB];
      if (a != null) return a;
      if (b != null) return b;
      return fallback;
    };
    const nextX0 = shape0?.x0 ?? pick("shapes[0].x0", "shapes[0].x1", null);
    const nextX1 = shape0?.x1 ?? pick("shapes[0].x1", "shapes[0].x0", null);
    const nextY0 = shape0?.y0 ?? pick("shapes[0].y0", "shapes[0].y1", null);
    const nextY1 = shape0?.y1 ?? pick("shapes[0].y1", "shapes[0].y0", null);
    if (nextX0 == null || nextX1 == null || nextY0 == null || nextY1 == null) return;

    const xMin = Math.min(Number(nextX0), Number(nextX1));
    const xMax = Math.max(Number(nextX0), Number(nextX1));
    const yMin = Math.min(Number(nextY0), Number(nextY1));
    const yMax = Math.max(Number(nextY0), Number(nextY1));
    if (![xMin, xMax, yMin, yMax].every((n) => Number.isFinite(n))) return;

    const prevXMin = Number(gatingState.x_min);
    const prevXMax = Number(gatingState.x_max);
    const prevYMin = Number(gatingState.y_min);
    const prevYMax = Number(gatingState.y_max);
    if (
      Number.isFinite(prevXMin) && Number.isFinite(prevXMax) && Number.isFinite(prevYMin) && Number.isFinite(prevYMax) &&
      Math.abs(prevXMin - xMin) < 1e-9 &&
      Math.abs(prevXMax - xMax) < 1e-9 &&
      Math.abs(prevYMin - yMin) < 1e-9 &&
      Math.abs(prevYMax - yMax) < 1e-9
    ) return;

    setGatingState((prev) => ({
      ...prev,
      x_min: String(xMin),
      x_max: String(xMax),
      y_min: String(yMin),
      y_max: String(yMax),
    }));
    if (gatingRelayoutTimerRef.current) {
      clearTimeout(gatingRelayoutTimerRef.current);
      gatingRelayoutTimerRef.current = null;
    }
    gatingRelayoutTimerRef.current = setTimeout(() => {
      handleGatingPreview({
        overrideBounds: { x_min: xMin, x_max: xMax, y_min: yMin, y_max: yMax },
        fromDrag: true,
      });
    }, 220);
  };

  const trackingFramePayload = (override = {}) => ({
    table_path: String((override.table_path ?? trackingState.table_path) || "").trim(),
    frame: Number(override.frame ?? trackingState.frame ?? 0),
    image_dir: String((override.image_dir ?? trackingState.image_dir) || "").trim() || null,
    image_col: (override.image_col ?? trackingState.image_col) || null,
    preview_cache_dir: String((override.preview_cache_dir ?? trackingState.preview_cache_dir) || "").trim() || null,
    trail_window: Number(override.trail_window ?? trackingState.trail_window ?? 7),
    show_complete_trail: !!(override.show_complete_trail ?? trackingState.show_complete_trail),
  });

  const applyTrackingPreviewResponse = (res) => {
    setTrackingState((prev) => ({
      ...prev,
      table_path: res.table_path || prev.table_path,
      image_col: res.image_col || prev.image_col,
      preview_cache_dir: res.preview_cache_dir || prev.preview_cache_dir || "",
      preview_image_path: res.preview_image_path || "",
      preview_nonce: Number(prev.preview_nonce || 0) + 1,
      frame: Number(res.frame ?? prev.frame ?? 0),
      max_frame: Number(res.max_frame ?? prev.max_frame ?? 0),
      figure: res.figure || null,
      total_rows: Number(res.total_rows ?? prev.total_rows ?? 0),
      total_tracks: Number(res.total_tracks ?? prev.total_tracks ?? 0),
      message: res.message || "",
    }));
  };

  const createTrackingUndoCheckpoint = async () => {
    const tablePath = String(trackingState.table_path || "").trim();
    if (!tablePath) {
      throw new Error("Run automatic tracking first.");
    }
    const res = await callApi("/tracking/checkpoint/create", { table_path: tablePath });
    return String(res.checkpoint_path || "").trim();
  };

  const handleTrackingRunAutomatic = async () => {
    if (!String(trackingState.path_to_table || "").trim()) {
      setTrackingStatus({ level: "error", text: "Select the input Results.csv table." });
      return;
    }
    if (!String(trackingState.image_dir || "").trim()) {
      setTrackingStatus({ level: "error", text: "Select the image folder. It is required for tracking preview and validation." });
      return;
    }
    if (!String(trackingState.image_col || "").trim()) {
      setTrackingStatus({ level: "error", text: "Select the CSV column that contains image file names." });
      return;
    }
    scrollToTopSmooth();
    setTrackingRunning(true);
    setTrackingStatus({ level: "info", text: "Running automatic tracking..." });
    try {
      const payload = {
        path_to_table: String(trackingState.path_to_table || "").trim(),
        image_dir: String(trackingState.image_dir || "").trim(),
        image_col: trackingState.image_col || "",
        max_distance: Number(trackingState.max_distance || 30),
        time_window: Number(trackingState.time_window || 5),
        max_split_distance: Number(trackingState.max_split_distance || 10),
        max_gap_closing_distance: Number(trackingState.max_gap_closing_distance || 30),
      };
      const res = await callApi("/tracking/run", payload);
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({ ...prev, selected: [] }));
      setTrackingStatus({ level: "success", text: res.message || "Automatic tracking complete." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: err.message || "Tracking run failed." });
    } finally {
      setTrackingRunning(false);
    }
  };

  const handleTrackingGoToCorrection = () => {
    if (!String(trackingState.table_path || "").trim()) {
      setTrackingStatus({ level: "error", text: "Run automatic tracking first." });
      return;
    }
    setTrackingState((prev) => ({ ...prev, workflow_stage: "menu" }));
    setTrackingStatus({ level: "info", text: "Choose the next action: save results or correct tracks." });
  };

  const handleTrackingOpenCorrection = () => {
    if (!String(trackingState.table_path || "").trim()) {
      setTrackingStatus({ level: "error", text: "Run automatic tracking first." });
      return;
    }
    setTrackingState((prev) => ({ ...prev, workflow_stage: "correction" }));
    setTrackingStatus({ level: "info", text: "Manual correction enabled." });
  };

  const handleTrackingSaveResults = async (includeImages = true) => {
    if (!String(trackingState.table_path || "").trim()) {
      setTrackingStatus({ level: "error", text: "Run automatic tracking first." });
      return;
    }
    if (!String(trackingState.save_results_dir || "").trim()) {
      setTrackingStatus({ level: "error", text: "Select a destination folder to save results." });
      return;
    }
    setTrackingLoadingFrame(true);
    setTrackingStatus({ level: "info", text: "Saving tracking results..." });
    try {
      const res = await callApi("/tracking/save-results", {
        table_path: String(trackingState.table_path || "").trim(),
        output_dir: String(trackingState.save_results_dir || "").trim(),
        preview_cache_dir: String(trackingState.preview_cache_dir || "").trim() || null,
        include_images: !!includeImages,
      });
      setTrackingStatus({ level: "success", text: res.message || "Results saved." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: err.message || "Failed to save tracking results." });
    } finally {
      setTrackingLoadingFrame(false);
    }
  };

  const handleTrackingUndo = async () => {
    const checkpointPath = String(trackingState.undo_checkpoint_path || "").trim();
    if (!checkpointPath) {
      setTrackingStatus({ level: "error", text: "No undo checkpoint is available yet." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Undoing last tracking action..." });
    try {
      const res = await callApi("/tracking/checkpoint/restore", {
        ...trackingFramePayload(),
        checkpoint_path: checkpointPath,
      });
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({
        ...prev,
        selected: [],
        selected_markers: [],
        undo_checkpoint_path: "",
      }));
      setTrackingStatus({ level: "success", text: res.message || "Last action undone." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: err.message || "Undo failed." });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleTrackingSaveProgress = async () => {
    if (!String(trackingState.table_path || "").trim()) {
      setTrackingStatus({ level: "error", text: "Run automatic tracking first." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Saving tracking progress..." });
    try {
      const res = await callApi("/tracking/progress/save", trackingFramePayload());
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({
        ...prev,
        table_path: res.saved_table_path || prev.table_path,
        saved_progress_path: res.saved_table_path || prev.saved_progress_path,
      }));
      setTrackingStatus({ level: "success", text: res.message || "Progress saved." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: err.message || "Save progress failed." });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleTrackingRefreshFrame = async (override = {}) => {
    if (!String(trackingState.table_path || "").trim()) {
      setTrackingStatus({ level: "error", text: "Run automatic tracking first or provide a tracked table." });
      return;
    }
    setTrackingLoadingFrame(true);
    setTrackingStatus({ level: "info", text: "Updating tracking preview..." });
    try {
      const res = await callApi("/tracking/preview", trackingFramePayload(override));
      applyTrackingPreviewResponse(res);
      setTrackingStatus({ level: "success", text: res.message || "Preview updated." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: err.message || "Tracking preview failed." });
    } finally {
      setTrackingLoadingFrame(false);
    }
  };

  const handleTrackingStepFrame = async (delta) => {
    const current = Number(trackingState.frame || 0);
    const maxFrame = Number(trackingState.max_frame || 0);
    const target = Math.max(0, Math.min(maxFrame, current + delta));
    if (target === current) return;
    const cacheDir = String(trackingState.preview_cache_dir || "").trim();
    if (cacheDir) {
      const frameName = String(target).padStart(5, "0");
      const pngPath = `${cacheDir}/${frameName}.png`;
      setTrackingState((prev) => ({
        ...prev,
        frame: target,
        preview_image_path: pngPath,
      }));
      return;
    }
    setTrackingState((prev) => ({ ...prev, frame: target }));
    await handleTrackingRefreshFrame({ frame: target });
  };

  const handleTrackingViewerClick = async (evt) => {
    if (String(trackingState.workflow_stage || "step1") !== "correction") return;
    if (!String(trackingState.table_path || "").trim()) return;
    const imgEl = evt?.currentTarget;
    if (!imgEl) return;
    const rect = imgEl.getBoundingClientRect();
    const rx = (evt.clientX - rect.left) / Math.max(1, rect.width);
    const ry = (evt.clientY - rect.top) / Math.max(1, rect.height);
    const naturalW = Number(imgEl.naturalWidth || trackingState.viewer_w || 0);
    const naturalH = Number(imgEl.naturalHeight || trackingState.viewer_h || 0);
    const x = rx * naturalW;
    const y = ry * naturalH;
    if (!Number.isFinite(x) || !Number.isFinite(y)) return;
    try {
      const res = await callApi("/tracking/select-point", {
        ...trackingFramePayload(),
        x,
        y,
        max_distance: 35,
      });
      const picked = res.selection;
      setTrackingState((prev) => {
        const already = (prev.selected || []).some(
          (s) => s.frame === picked.frame && s.cell === picked.cell && s.track_id === picked.track_id
        );
        if (already) return prev;
        const nextSelected = [...(prev.selected || []), picked];
        const nextMarkers = [...(prev.selected_markers || []), { frame: Number(picked.frame), x: Number(res.x), y: Number(res.y) }];
        return { ...prev, selected: nextSelected, selected_markers: nextMarkers };
      });
      setTrackingStatus({ level: "success", text: res.message || "Track selected." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: err.message || "No track found at clicked position." });
    }
  };

  const handleTrackingDelete = async () => {
    if (!(trackingState.selected || []).length) {
      setTrackingStatus({ level: "error", text: "Select at least one point/track first." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Deleting selected tracks..." });
    try {
      const undoCheckpointPath = await createTrackingUndoCheckpoint();
      const res = await callApi("/tracking/edit/delete", {
        ...trackingFramePayload(),
        selections: trackingState.selected || [],
      });
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({ ...prev, selected: [], selected_markers: [], undo_checkpoint_path: undoCheckpointPath }));
      setTrackingStatus({ level: "success", text: res.message || "Tracks deleted." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: err.message || "Delete tracks failed." });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleTrackingLink = async () => {
    if ((trackingState.selected || []).length < 2) {
      setTrackingStatus({ level: "error", text: "Select at least two points to link tracks." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Linking selected tracks..." });
    try {
      const undoCheckpointPath = await createTrackingUndoCheckpoint();
      const targetFrame = Math.max(...(trackingState.selected || []).map((s) => Number(s.frame || 0)));
      const res = await callApi("/tracking/edit/link", {
        ...trackingFramePayload({ frame: targetFrame }),
        selections: trackingState.selected || [],
      });
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({
        ...prev,
        selected: [],
        selected_markers: [],
        undo_checkpoint_path: undoCheckpointPath,
      }));
      setTrackingStatus({ level: "success", text: res.message || "Tracks linked." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: err.message || "Link tracks failed." });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleTrackingDivision = async () => {
    if ((trackingState.selected || []).length !== 3) {
      setTrackingStatus({ level: "error", text: "Select exactly 3 cells: one mother and two daughters." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Applying cell division..." });
    try {
      const undoCheckpointPath = await createTrackingUndoCheckpoint();
      const targetFrame = Math.max(...(trackingState.selected || []).map((s) => Number(s.frame || 0)));
      const res = await callApi("/tracking/edit/division", {
        ...trackingFramePayload({ frame: targetFrame }),
        selections: trackingState.selected || [],
      });
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({
        ...prev,
        selected: [],
        selected_markers: [],
        undo_checkpoint_path: undoCheckpointPath,
      }));
      setTrackingStatus({ level: "success", text: res.message || "Cell division linked." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: err.message || "Cell division failed." });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleTrackingUnlink = async () => {
    if (!(trackingState.selected || []).length) {
      setTrackingStatus({ level: "error", text: "Select one or more cells first." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Unlinking selected cells..." });
    try {
      const undoCheckpointPath = await createTrackingUndoCheckpoint();
      const targetFrame = Math.max(...(trackingState.selected || []).map((s) => Number(s.frame || 0)));
      const res = await callApi("/tracking/edit/unlink", {
        ...trackingFramePayload({ frame: targetFrame }),
        selections: trackingState.selected || [],
      });
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({ ...prev, selected: [], selected_markers: [], undo_checkpoint_path: undoCheckpointPath }));
      setTrackingStatus({ level: "success", text: res.message || "Selected cells unlinked." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: err.message || "Unlink failed." });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleResetNma = () => {
    const ok = window.confirm("Reset NMA settings and return to initial state?");
    if (!ok) return;
    setRows(initialNmaRows());
    setCollapsedById({});
    setStep(1);
    setStep1Ready(false);
    setStatus("");
    setStatusLevel("info");
    setStep1Figure(null);
    setStep1Stats(null);
    setStep1GraphLimits(null);
    setStep1Sample(null);
    setSdArea(1.0);
    setSdNii(1.0);
    setThresholds({
      v_up: 0,
      v_mid: 0,
      v_down: 0,
      v_down2: 0,
      y_high: 0,
      y_low: 0,
    });
    setStep2Figure(null);
    setStep2Traces(null);
    setStep2Stats(null);
    setStep2GraphLimits(null);
    setFinalMode(false);
    setDownloadReady(false);
    setStep2Percentages(null);
    setShowPlotConfig(false);
    setPlotConfig(initialPlotConfig());
    setPlotSavePath("");
    setPlotJob({ ...DEFAULT_PLOT_JOB });
    setCurrentPlotIndex(0);
    setShowNmaPreviewWhilePlotting(false);
    attemptedColumnsRef.current = new Set();
  };

  const handleResetRegistrationUi = () => {
    if (["starting", "queued", "running", "canceling"].includes(regJob.status || "idle")) return;
    const ok = window.confirm("Reset Image Registration screen to a clean state?");
    if (!ok) return;
    setRegJob({ ...DEFAULT_REG_JOB });
    setRegPanelResetKey((k) => k + 1);
    setStatus("");
    setStatusLevel("info");
  };

  const handleResetFociUi = () => {
    if (["starting", "queued", "running", "canceling"].includes(fociJob.status || "idle")) return;
    const ok = window.confirm("Reset Foci Overlay screen to a clean state?");
    if (!ok) return;
    setFociJob({ ...DEFAULT_FOCI_JOB });
    setFociPanelResetKey((k) => k + 1);
    setStatus("");
    setStatusLevel("info");
  };

  const handleResetPlotDataUi = () => {
    if (plotDataLoading) return;
    const ok = window.confirm("Reset Plot Data screen to a clean state?");
    if (!ok) return;
    setPlotData(initialPlotDataState());
    setPlotDataStatus({ level: "info", text: "" });
    setPlotDataLoading(false);
    plotDataColsCacheRef.current = {};
  };

  const handleResetClusteringUi = () => {
    if (clusteringLoading || clusteringElbowLoading) return;
    const ok = window.confirm("Reset Clustering screen to a clean state?");
    if (!ok) return;
    setClustering(initialClusteringState());
    setClusteringStatus({ level: "info", text: "" });
    setClusteringLoading(false);
    setClusteringElbowLoading(false);
    clusteringColsCacheRef.current = {};
  };

  const handleResetStatisticsUi = () => {
    if (statsLoading) return;
    const ok = window.confirm("Reset Statistics screen to a clean state?");
    if (!ok) return;
    setStatsState(initialStatsState());
    setStatsStatus({ level: "info", text: "" });
    setStatsLoading(false);
    statsColsCacheRef.current = {};
    statsFilterValuesCacheRef.current = {};
  };

  const handleResetGatingUi = () => {
    if (gatingLoading || gatingApplying) return;
    const ok = window.confirm("Reset Gating screen to a clean state?");
    if (!ok) return;
    setGatingState(initialGatingState());
    setGatingStatus({ level: "info", text: "" });
    setGatingLoading(false);
    setGatingApplying(false);
    gatingColsCacheRef.current = {};
  };

  const handleResetTrackingUi = () => {
    if (trackingRunning || trackingLoadingFrame || trackingEditing) return;
    const ok = window.confirm("Reset Tracking screen to a clean state?");
    if (!ok) return;
    setTrackingState(initialTrackingState());
    setTrackingStatus({ level: "info", text: "" });
    setTrackingRunning(false);
    setTrackingLoadingFrame(false);
    setTrackingEditing(false);
  };

  return (
    <div className="app">
      <div className="top-shell">
        <header className="topbar">
          <div className="topbar-brand">
            <div className="topbar-logo-slot" aria-hidden="true">
              <span className="topbar-logo-mark">fN</span>
            </div>
            <div>
              <div className="logo">forNMA</div>
              <div className="subtitle">{activeModule}</div>
            </div>
          </div>
          {activeModule === "NMA" && step1Ready && (
            <div className="stepper">
              <div className={`chip ${step === 1 ? "active" : ""}`}>Step 1</div>
              <div className={`chip ${step === 2 ? "active" : ""}`}>Step 2</div>
            </div>
          )}
        </header>
        <nav className="module-menu" aria-label="forNMA stages">
          {FORNMA_STAGES.map((stage) => (
            <Button
              key={stage}
              type="button"
              className={`module-chip ${stage === activeModule ? "active" : ""}`}
              data-state={stage === activeModule ? "active" : "inactive"}
              onClick={() => {
                setActiveModule(stage);
              }}
            >
              <span className="module-chip-label">{stage}</span>
            </Button>
          ))}
        </nav>
      </div>

      <div className="layout">
        {activeModule === "Home" ? (
          <>
            <HomeLeftPanel activeSection={homeSection} onSelectSection={handleSelectHomeSection} />
            <main className="content">
              <section className="home-stack">
                <div id="home-about" className="section home-section-card">
                  <div className="home-hero">
                    <div className="home-logo-box">forNMA</div>
                    <div>
                      <h2>About forNMA</h2>
                      <p className="hint hint-muted">
                        forNMA is a microscopy analysis environment that brings registration, segmentation, gating,
                        foci inspection, NMA workflows, plotting, clustering, statistics, and tracking into a single interface.
                      </p>
                    </div>
                  </div>
                  <div className="home-meta-grid">
                    <div className="home-info-card">
                      <h4>What the software does</h4>
                      <p className="hint hint-muted">
                        The goal of this home page is to guide new users through the platform, explain the workflow,
                        and centralize learning materials for each module.
                      </p>
                    </div>
                    <div className="home-info-card">
                      <h4>Developed by</h4>
                      <p className="hint hint-muted">
                        Add here the authors, lab, institution, and collaborators responsible for the software.
                      </p>
                    </div>
                    <div className="home-info-card">
                      <h4>Contact</h4>
                      <p className="hint hint-muted">
                        Add email addresses, GitHub links, and any preferred support or citation contact information.
                      </p>
                    </div>
                  </div>
                </div>

                <div id="home-article" className="section home-section-card">
                  <h3>Article</h3>
                  <p className="hint hint-muted">
                    Reserve this section for the publication that originated the software, including citation text,
                    DOI, journal information, and a short summary of the scientific context.
                  </p>
                </div>

                <div id="home-tutorial-registration" className="section home-section-card">
                  <h3>Image Registration Tutorial</h3>
                  <p className="hint hint-muted">
                    Explain how to organize channels and conditions, choose a reference channel, and run registration safely.
                  </p>
                </div>

                <div id="home-tutorial-segmentation" className="section home-section-card">
                  <h3>Segmentation Tutorial</h3>
                  <p className="hint hint-muted">
                    Introduce the image table, nucleus detection channel, segmentation method, and per-channel settings.
                  </p>
                </div>

                <div id="home-tutorial-gating" className="section home-section-card">
                  <h3>Gating Tutorial</h3>
                  <p className="hint hint-muted">
                    Describe how to load datasets, pick X/Y columns, preview the gate, and save filtered outputs.
                  </p>
                </div>

                <div id="home-tutorial-foci" className="section home-section-card">
                  <h3>Foci Overlay Tutorial</h3>
                  <p className="hint hint-muted">
                    Describe how to select `.pkl` folders, choose channels, and generate overlays and profile outputs.
                  </p>
                </div>

                <div id="home-tutorial-nma" className="section home-section-card">
                  <h3>NMA Tutorial</h3>
                  <p className="hint hint-muted">
                    Explain the control dataset, threshold generation, manual adjustments, and settings export workflow.
                  </p>
                </div>

                <div id="home-tutorial-plot" className="section home-section-card">
                  <h3>Plot Data Tutorial</h3>
                  <p className="hint hint-muted">
                    Describe how to load CSV files, choose plot types, map columns, and interpret the generated views.
                  </p>
                </div>

                <div id="home-tutorial-clustering" className="section home-section-card">
                  <h3>Clustering Tutorial</h3>
                  <p className="hint hint-muted">
                    Introduce feature selection, embedding settings, color strategies, and elbow-plot-assisted clustering.
                  </p>
                </div>

                <div id="home-tutorial-statistics" className="section home-section-card">
                  <h3>Statistics Tutorial</h3>
                  <p className="hint hint-muted">
                    Outline when to use one-way, two-way, and chi-square analyses, and how to prepare the input tables.
                  </p>
                </div>

                <div id="home-tutorial-tracking" className="section home-section-card">
                  <h3>Tracking Tutorial</h3>
                  <p className="hint hint-muted">
                    Explain the automatic tracking step, correction workflow, linking, unlinking, cell division, and final export.
                  </p>
                </div>

                <div id="home-resources" className="section home-section-card">
                  <h3>Resources</h3>
                  <p className="hint hint-muted">
                    Add quick links and micro-tutorials for GitHub, repository navigation, issue reporting, releases, and documentation.
                  </p>
                </div>
              </section>
            </main>
          </>
        ) : activeModule === "Segmentation" ? (
          <>
            <SegmentationLeftPanel
              key={`seg-panel-${segPanelResetKey}`}
              onPickDirectory={async () => {
                try {
                  const res = await pickDirectoryPath();
                  return res.path || "";
                } catch {
                  return "";
                }
              }}
              onStartSegmentation={handleStartSegmentation}
              onStopSegmentation={handleStopSegmentation}
              onResetSegmentation={handleResetSegmentationUi}
              segJob={segJob}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Segmentation")}>
                    Tutorial
                  </button>
                  <button
                    className="ghost btn-small"
                    onClick={handleResetSegmentationUi}
                    disabled={["starting", "queued", "running", "canceling"].includes(segJob.status || "idle")}
                  >
                    Reset
                  </button>
                </div>
                <p className="hint">Run segmentation and monitor progress in real time.</p>
                {hasSegSession ? (
                  <div className="section tracking-viewer-section">
                    <h3>Execution progress</h3>
                    <div className="progress-wrap">
                      <div
                        className={`progress-fill ${segJob.status === "starting" || segJob.status === "running" || segJob.status === "queued" || segJob.status === "canceling" ? "running" : ""}`}
                        style={{ width: `${Math.max(0, Math.min(100, segJob.progress || 0))}%` }}
                      />
                    </div>
                    <div className="hint">
                      {segJob.message || "Waiting to start."}
                    </div>
                    {segJob.error && <Status level="error" text={segJob.error} />}
                    <div className="section">
                      <h4>
                        Segmentation preview{Number.isInteger(segJob.preview_index) ? ` (image ${segJob.preview_index + 1})` : ""}
                      </h4>
                      {lastSegPreviewPayload && Number.isInteger(segJob.preview_index) && (
                        <div className="row row-right">
                          <button
                            className="secondary btn-small"
                            onClick={() =>
                              handleStartSegmentation({
                                ...lastSegPreviewPayload,
                                preview: true,
                                preview_index: (Number(segJob.preview_index) || 0) + 1,
                              })
                            }
                            disabled={["starting", "queued", "running", "canceling"].includes(segJob.status)}
                          >
                            Preview next image
                          </button>
                        </div>
                      )}
                      {(segJob.preview_paths || []).length > 0 ? (
                        <>
                          <div className="viewer-toolbar">
                            <button
                              className="ghost btn-small"
                              onClick={() => setSegPreviewPage((p) => Math.max(0, p - 1))}
                              disabled={segPreviewPage <= 0}
                            >
                              ◀
                            </button>
                            <span className="viewer-counter">
                              {Math.min((segPreviewPage * 2) + 1, segJob.preview_paths.length)}-{Math.min((segPreviewPage * 2) + 2, segJob.preview_paths.length)} / {segJob.preview_paths.length}
                            </span>
                            <button
                              className="ghost btn-small"
                              onClick={() => setSegPreviewPage((p) => {
                                const maxPage = Math.max(0, Math.ceil((segJob.preview_paths.length || 0) / 2) - 1);
                                return Math.min(maxPage, p + 1);
                              })}
                              disabled={((segPreviewPage + 1) * 2) >= segJob.preview_paths.length}
                            >
                              ▶
                            </button>
                          </div>
                          <div className="plot-thumbs plot-thumbs-right">
                            {(segJob.preview_paths || []).slice(segPreviewPage * 2, segPreviewPage * 2 + 2).map((path) => (
                              (() => {
                                const meta = previewMeta(path);
                                return (
                                  <a
                                    key={path}
                                    href={`${API_BASE}/segmentation/file?path=${encodeURIComponent(path)}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="thumb-card"
                                  >
                                    <span>
                                      {meta.condition ? `Condition: ${meta.condition}` : ""}
                                      {meta.condition && meta.channel ? " | " : ""}
                                      {meta.channel ? `Channel: ${meta.channel}` : ""}
                                    </span>
                                    <img
                                      src={`${API_BASE}/segmentation/file?path=${encodeURIComponent(path)}&v=${segPreviewNonce}`}
                                      alt={path.split("/").pop()}
                                    />
                                    <span>{path.split("/").pop()}</span>
                                  </a>
                                );
                              })()
                            ))}
                          </div>
                        </>
                      ) : segJob.preview_path ? (
                        <a
                          href={`${API_BASE}/segmentation/file?path=${encodeURIComponent(segJob.preview_path)}`}
                          target="_blank"
                          rel="noreferrer"
                          className="thumb-card viewer-single"
                        >
                          <img
                            src={`${API_BASE}/segmentation/file?path=${encodeURIComponent(segJob.preview_path)}&v=${segPreviewNonce}`}
                            alt={segJob.preview_path.split("/").pop()}
                          />
                          <span>{segJob.preview_path.split("/").pop()}</span>
                        </a>
                      ) : (
                        <p className="hint">No preview image yet.</p>
                      )}
                    </div>
                    <div className="section">
                      <h4>Log</h4>
                      <pre className="seg-log">{segJob.log || "No logs yet."}</pre>
                    </div>
                  </div>
                ) : (
                  <div className="section">
                    <p className="hint">No execution started yet. Use Preview or Run to begin.</p>
                  </div>
                )}
              </section>
            </main>
          </>
        ) : activeModule === "Gating" ? (
          <>
            <GatingLeftPanel
              onPickCsv={async () => {
                const res = await pickCsvPath();
                return res.path || "";
              }}
              onPickDirectory={async () => {
                const res = await pickDirectoryPath();
                return res.path || "";
              }}
              onPreview={handleGatingPreview}
              onApply={handleGatingApply}
              status={gatingStatus}
              loading={gatingLoading}
              applying={gatingApplying}
              state={gatingState}
              setState={setGatingState}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Gating")}>
                    Tutorial
                  </button>
                  <button className="ghost btn-small" onClick={handleResetGatingUi} disabled={gatingLoading || gatingApplying}>
                    Reset
                  </button>
                </div>
                {(gatingLoading || gatingApplying) && (
                  <div className="preview-loading">
                    <div className="spinner" />
                    <div className="hint">{gatingLoading ? "Generating preview..." : "Applying gate..."}</div>
                  </div>
                )}
                {gatingState.figure ? (
                  <PlotPanel
                    figure={gatingState.figure}
                    onRelayout={handleGatingRelayout}
                    config={{
                      displayModeBar: false,
                      displaylogo: false,
                      responsive: true,
                      scrollZoom: false,
                      edits: { shapePosition: true },
                    }}
                  />
                ) : (
                  <p className="hint">Select datasets, set gate axes, and run Preview gate.</p>
                )}
                {(gatingState.tables || []).length ? (
                  <>
                    {(gatingState.tables || []).map((t) => (
                      <StatsTableView key={`gating-${t.name}`} table={t} onDownload={downloadStatsTableCsv} />
                    ))}
                  </>
                ) : null}
                {(gatingState.files || []).length ? (
                  <div className="section">
                    <h3>Saved files</h3>
                    <pre className="seg-log">{(gatingState.files || []).join("\n")}</pre>
                  </div>
                ) : null}
              </section>
            </main>
          </>
        ) : activeModule === "Tracking" ? (
          <>
            <TrackingLeftPanel
              onPickCsv={async () => {
                const res = await pickCsvPath();
                return res.path || "";
              }}
              onPickDirectory={async () => {
                const res = await pickDirectoryPath();
                return res.path || "";
              }}
              onRunAutomatic={handleTrackingRunAutomatic}
              onGoToCorrection={handleTrackingGoToCorrection}
              onOpenCorrection={handleTrackingOpenCorrection}
              onSaveResults={handleTrackingSaveResults}
              onRefreshFrame={handleTrackingRefreshFrame}
              onPrevFrame={() => handleTrackingStepFrame(-1)}
              onNextFrame={() => handleTrackingStepFrame(1)}
              onDeleteTracks={handleTrackingDelete}
              onLinkTracks={handleTrackingLink}
              status={trackingStatus}
              state={trackingState}
              setState={setTrackingState}
              running={trackingRunning}
              loadingFrame={trackingLoadingFrame}
              editing={trackingEditing}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Tracking")}>
                    Tutorial
                  </button>
                  <button className="ghost btn-small" onClick={handleResetTrackingUi} disabled={trackingRunning || trackingLoadingFrame || trackingEditing}>
                    Reset
                  </button>
                </div>
                {String(trackingState.workflow_stage || "step1") === "step1" && trackingRunning && (
                  <div className="tracking-run-feedback">
                    <div className="spinner" />
                    <div className="hint hint-muted">
                      Automatic tracking is running. This may take a little while depending on the table size.
                    </div>
                  </div>
                )}
                {(trackingState.preview_image_path || trackingRunning || trackingLoadingFrame || trackingEditing) ? (
                  <div className="section">
                    <h3>Tracking viewer</h3>
                    {String(trackingState.workflow_stage || "step1") === "correction" && (
                      <div className="row" style={{ marginBottom: 8 }}>
                        <button
                          className="ghost"
                          title="Remove the current highlighted selections without changing the tracking table."
                          onClick={() => setTrackingState((prev) => ({ ...prev, selected: [], selected_markers: [] }))}
                          disabled={!(trackingState.selected || []).length}
                        >
                          Clear selection
                        </button>
                        <button className="ghost" title="Restore the table and viewer to the state before the last edit action." onClick={handleTrackingUndo} disabled={!String(trackingState.undo_checkpoint_path || "").trim() || trackingEditing || trackingLoadingFrame || trackingRunning}>
                          Undo
                        </button>
                        <button className="ghost" title="Save the current corrected table to a temporary checkpoint so you can keep working without losing progress." onClick={handleTrackingSaveProgress} disabled={trackingEditing || trackingLoadingFrame || trackingRunning || !String(trackingState.table_path || "").trim()}>
                          Save progress
                        </button>
                        <button className="ghost" title="Link the selected cells into the same track. Across frames, the earliest selected cell becomes the base track." onClick={handleTrackingLink} disabled={(trackingState.selected || []).length < 2}>
                          Link selected
                        </button>
                        <button className="ghost" title="Mark a cell division using exactly 3 selections: the mother cell in the earlier frame and the two daughter cells in the later frame." onClick={handleTrackingDivision} disabled={(trackingState.selected || []).length !== 3}>
                          Cell division
                        </button>
                        <button className="ghost" title="Cut the selected track from that point onward. The chosen cell keeps the old family before that frame, and gets a new number/color from the selected frame to the end." onClick={handleTrackingUnlink} disabled={(trackingState.selected || []).length < 1}>
                          Unlink
                        </button>
                        <button className="ghost" title="Delete the selected track completely from the table and from the rendered tracking view." onClick={handleTrackingDelete} disabled={!(trackingState.selected || []).length}>
                          Delete track
                        </button>
                      </div>
                    )}
                    <div className="viewer-toolbar">
                      <button
                        className="ghost btn-small"
                        title="Show the previous frame in the tracking viewer."
                        onClick={() => handleTrackingStepFrame(-1)}
                        disabled={trackingLoadingFrame || trackingRunning || trackingEditing || Number(trackingState.frame || 0) <= 0}
                      >
                        ◀
                      </button>
                      <span className="viewer-counter">
                        {(Number(trackingState.frame || 0) + 1)} / {(Number(trackingState.max_frame || 0) + 1)}
                      </span>
                      <button
                        className="ghost btn-small"
                        title="Show the next frame in the tracking viewer."
                        onClick={() => handleTrackingStepFrame(1)}
                        disabled={trackingLoadingFrame || trackingRunning || trackingEditing || Number(trackingState.frame || 0) >= Number(trackingState.max_frame || 0)}
                      >
                        ▶
                      </button>
                    </div>
                    {trackingState.preview_image_path ? (
                      <div className="thumb-card viewer-single" style={{ cursor: "crosshair" }}>
                        <div style={{ position: "relative", width: "100%" }}>
                          {(trackingRunning || trackingLoadingFrame || trackingEditing) && (
                            <div className="viewer-overlay">
                              <div className="spinner" />
                              <div className="hint hint-muted">
                                {trackingRunning ? "Running automatic tracking..." : (trackingEditing ? "Applying correction..." : "Updating frame...")}
                              </div>
                            </div>
                          )}
                          <img
                            src={`${API_BASE}/tracking/file?path=${encodeURIComponent(trackingState.preview_image_path)}&v=${trackingState.preview_nonce || 0}`}
                            alt={`tracking-frame-${trackingState.frame || 0}`}
                            onLoad={(e) => {
                              const w = Number(e.currentTarget.naturalWidth || 0);
                              const h = Number(e.currentTarget.naturalHeight || 0);
                              setTrackingState((prev) => ({ ...prev, viewer_w: w, viewer_h: h }));
                            }}
                            onClick={handleTrackingViewerClick}
                          />
                          {(trackingState.selected_markers || [])
                            .filter((m) => Number(m.frame) === Number(trackingState.frame || 0))
                            .map((m, i) => {
                              const w = Number(trackingState.viewer_w || 0);
                              const h = Number(trackingState.viewer_h || 0);
                              if (!w || !h) return null;
                              return (
                                <span
                                  key={`trk-marker-${i}`}
                                  style={{
                                    position: "absolute",
                                    left: `calc(${(Number(m.x) / w) * 100}% - 6px)`,
                                    top: `calc(${(Number(m.y) / h) * 100}% - 6px)`,
                                    width: 12,
                                    height: 12,
                                    borderRadius: "50%",
                                    background: "#ffd400",
                                    border: "2px solid #6a4f00",
                                    pointerEvents: "none",
                                  }}
                                />
                              );
                            })}
                        </div>
                        <span>{trackingState.preview_image_path.split("/").pop()}</span>
                      </div>
                    ) : (
                      <p className="hint hint-muted">
                        Running tracking. The viewer will appear as soon as the first frame is ready.
                        {trackingState.preview_cache_dir ? ` Cache: ${trackingState.preview_cache_dir}` : ""}
                      </p>
                    )}
                    {(trackingState.selected_markers || []).filter((m) => Number(m.frame) === Number(trackingState.frame || 0)).length > 0 && (
                      <div className="hint hint-muted">
                        {(trackingState.selected_markers || [])
                          .filter((m) => Number(m.frame) === Number(trackingState.frame || 0))
                          .map((m, i) => `#${i + 1} x=${Number(m.x).toFixed(1)}, y=${Number(m.y).toFixed(1)}`)
                          .join(" | ")}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="hint hint-muted">Run automatic tracking first. The tracking viewer will appear when frames are available.</p>
                )}
	                {trackingState.saved_progress_path && (
	                  <p className="hint hint-muted">Saved progress file: {trackingState.saved_progress_path}</p>
	                )}
	                <p className="hint hint-muted">Rows: {trackingState.total_rows || 0} | Tracks: {trackingState.total_tracks || 0} | Frame: {trackingState.frame || 0}/{trackingState.max_frame || 0}</p>
	              </section>
	            </main>
          </>
        ) : activeModule === "Foci Overlay" ? (
          <>
            <FociOverlayLeftPanel
              key={`foci-panel-${fociPanelResetKey}`}
              onPickDirectory={async () => {
                try {
                  const res = await pickDirectoryPath();
                  return res.path || "";
                } catch {
                  return "";
                }
              }}
              onStartFoci={handleStartFoci}
              onStopFoci={handleStopFoci}
              onLoadFociChannels={loadFociChannels}
              fociJob={fociJob}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Foci Overlay")}>
                    Tutorial
                  </button>
                  <button
                    className="ghost btn-small"
                    onClick={handleResetFociUi}
                    disabled={["starting", "queued", "running", "canceling"].includes(fociJob.status || "idle")}
                  >
                    Reset
                  </button>
                </div>
                {fociJob.job_id ? (
                  <div className="section">
                    <h3>Execution progress</h3>
                    <div className="progress-wrap">
                      <div
                        className={`progress-fill ${["starting", "running", "queued", "canceling"].includes(fociJob.status) ? "running" : ""}`}
                        style={{ width: `${Math.max(0, Math.min(100, fociJob.progress || 0))}%` }}
                      />
                    </div>
                    <div className="hint">{fociJob.message || "Waiting to start."}</div>
                    {fociJob.error && <Status level="error" text={fociJob.error} />}
                    <div className="section">
                      <h4>Log</h4>
                      <pre className="seg-log">{fociJob.log || "No logs yet."}</pre>
                    </div>
                  </div>
                ) : (
                  <div className="section">
                    <p className="hint">No foci overlay started yet. Use Run Overlay to begin.</p>
                  </div>
                )}
              </section>
            </main>
          </>
        ) : activeModule === "Statistics" ? (
          <>
            <StatsLeftPanel
              onPickCsv={async () => {
                const res = await pickCsvPath();
                return res.path || "";
              }}
              onRun={handleStatsRun}
              status={statsStatus}
              loading={statsLoading}
              state={statsState}
              setState={setStatsState}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Statistics")}>
                    Tutorial
                  </button>
                  <button className="ghost btn-small" onClick={handleResetStatisticsUi} disabled={statsLoading}>
                    Reset
                  </button>
                </div>
                {statsLoading && (
                  <div className="preview-loading">
                    <div className="spinner" />
                    <div className="hint">Running analysis...</div>
                  </div>
                )}
                {(statsState.tables || []).length ? (
                  <>
                    {(statsState.tables || []).map((t) => (
                      <StatsTableView key={`stats-${t.name}`} table={t} onDownload={downloadStatsTableCsv} />
                    ))}
                    <div className="section">
                      <div className="row row-between">
                        <h3>Log</h3>
                        <div className="row">
                          <button className="ghost btn-small" onClick={copyStatsLogTxt} disabled={!String(statsState.log || "").trim()}>
                            Copy TXT
                          </button>
                          <button className="ghost btn-small" onClick={downloadStatsLogTxt} disabled={!String(statsState.log || "").trim()}>
                            Download TXT
                          </button>
                        </div>
                      </div>
                      <pre className="seg-log">{statsState.log || "No logs yet."}</pre>
                    </div>
                  </>
                ) : (
                  <p className="hint">Select datasets, configure a test, and click Run.</p>
                )}
              </section>
            </main>
          </>
        ) : activeModule === "Clustering" ? (
          <>
            <ClusteringLeftPanel
              onPickCsv={async () => {
                const res = await pickCsvPath();
                return res.path || "";
              }}
              onPreview={handleClusteringPreview}
              onElbow={handleClusteringElbow}
              status={clusteringStatus}
              loading={clusteringLoading}
              elbowLoading={clusteringElbowLoading}
              state={clustering}
              setState={setClustering}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Clustering")}>
                    Tutorial
                  </button>
                  <button className="ghost btn-small" onClick={handleResetClusteringUi} disabled={clusteringLoading || clusteringElbowLoading}>
                    Reset
                  </button>
                </div>
                {(clusteringLoading || clusteringElbowLoading) && (
                  <div className="preview-loading">
                    <div className="spinner" />
                    <div className="hint">{clusteringLoading ? "Running embedding..." : "Generating elbow..."}</div>
                  </div>
                )}
                {clustering.figure ? (
                  <PlotPanel figure={clustering.figure} />
                ) : (
                  <p className="hint">Select datasets and numeric features, then run UMAP.</p>
                )}
                {clustering.elbowFigure && (
                  <div className="section">
                    <h3>Elbow Plot</h3>
                    <PlotPanel figure={clustering.elbowFigure} />
                  </div>
                )}
              </section>
            </main>
          </>
        ) : activeModule === "Plot Data" ? (
          <>
            <PlotDataLeftPanel
              onPickCsv={async () => {
                const res = await pickCsvPath();
                return res.path || "";
              }}
              onPreview={handlePlotDataPreview}
              status={plotDataStatus}
              loading={plotDataLoading}
              setStatusExternal={setPlotDataStatusMsg}
              graphState={plotData}
              setGraphState={setPlotData}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Plot Data")}>
                    Tutorial
                  </button>
                  <button className="ghost btn-small" onClick={handleResetPlotDataUi} disabled={plotDataLoading}>
                    Reset
                  </button>
                </div>
                {plotDataLoading && (
                  <div className="preview-loading">
                    <div className="spinner" />
                    <div className="hint">Generating preview...</div>
                  </div>
                )}
                {plotData.figure ? (
                  <PlotPanel figure={plotData.figure} />
                ) : (
                  <p className="hint">Configure data and click `Plot preview` to render an interactive graph.</p>
                )}
              </section>
            </main>
          </>
        ) : activeModule === "Image Registration" ? (
          <>
            <RegistrationLeftPanel
              key={`reg-panel-${regPanelResetKey}`}
              onPickDirectory={async () => {
                try {
                  const res = await pickDirectoryPath();
                  return res.path || "";
                } catch {
                  return "";
                }
              }}
              onStartRegistration={handleStartRegistration}
              onStopRegistration={handleStopRegistration}
              regJob={regJob}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Image Registration")}>
                    Tutorial
                  </button>
                  <button
                    className="ghost btn-small"
                    onClick={handleResetRegistrationUi}
                    disabled={["starting", "queued", "running", "canceling"].includes(regJob.status || "idle")}
                  >
                    Reset
                  </button>
                </div>
                {regJob.job_id ? (
                  <div className="section">
                    <div className="status info">
                      Registration can be slow and memory-intensive. Keep this window open and avoid running other heavy tasks.
                      If needed, reduce the number of images/channels per run.
                    </div>
                    <h3>Execution progress</h3>
                    <div className="progress-wrap">
                      <div
                        className={`progress-fill ${["starting", "running", "queued", "canceling"].includes(regJob.status) ? "running" : ""}`}
                        style={{ width: `${Math.max(0, Math.min(100, regJob.progress || 0))}%` }}
                      />
                    </div>
                    <div className="hint">
                      {regJob.message || "Waiting to start."}
                    </div>
                    {(regJob.total || 0) > 0 && (
                      <div className="hint">{regJob.done || 0} / {regJob.total || 0} conditions</div>
                    )}
                    {regJob.error && <Status level="error" text={regJob.error} />}
                    <div className="section">
                      <h4>Log</h4>
                      <pre className="seg-log">{regJob.log || "No logs yet."}</pre>
                    </div>
                  </div>
                ) : (
                  <div className="section">
                    <p className="hint">No registration started yet. Use Run Registration to begin.</p>
                  </div>
                )}
              </section>
            </main>
          </>
        ) : (
          <>
        <Card as="aside" className="panel" variant="panel">
          <h3>NMA Settings</h3>
          <p className="hint">Add at least one control only if you want to create new settings. If loading existing settings, this is not required.</p>
          <div className="row row-right">
            <Button className="ghost btn-small" onClick={() => setAllCollapsed(true)}>Minimize all</Button>
            <Button className="ghost btn-small" onClick={() => setAllCollapsed(false)}>Expand all</Button>
          </div>

          {rows.map((row, idx) => (
            <Card className="dataset" variant="dataset" key={row.id}>
              <div className="row dataset-header-row">
                <div className="dataset-title">
                  {row.name?.trim() || `Dataset ${idx + 1}`}{row.is_control ? " (Control)" : ""}
                </div>
                <Button className="ghost btn-small" onClick={() => toggleDatasetCollapse(row.id)}>
                  {collapsedById[row.id] ? "Expand" : "Minimize"}
                </Button>
              </div>
              {!collapsedById[row.id] && (
                <>
                  <div className="row">
                    <div style={{ flex: 1 }}>
                      <FieldTitle title="Dataset name" tip="Friendly name used to identify this dataset throughout the NMA workflow." className="field-head" />
                      <input
                        className="input"
                        placeholder="Name"
                        value={row.name}
                        onChange={(e) => updateRow(idx, { name: e.target.value })}
                      />
                    </div>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={row.is_control}
                        onChange={(e) => updateRow(idx, { is_control: e.target.checked })}
                      />
                      Control
                    </label>
                  </div>
                  <div className="row path-row">
                    <div style={{ flex: 1 }}>
                      <FieldTitle title="CSV path" tip="Results table used as input for this NMA dataset." className="field-head" />
                      <input
                        className="input"
                        placeholder="/path/Results.csv"
                        value={row.path}
                        onChange={(e) => updateRow(idx, { path: e.target.value })}
                      />
                    </div>
                    <Button
                      className="ghost"
                      title="Choose a CSV file for this NMA dataset."
                      onClick={async () => {
                        setStatus("Opening file picker...");
                        setStatusLevel("info");
                        try {
                          const res = await pickCsvPath();
                          updateRow(idx, { path: res.path || "" });
                          setStatus("Path selected.");
                          setStatusLevel("success");
                        } catch (err) {
                          setStatus(err.message);
                          setStatusLevel("error");
                        }
                      }}
                    >
                      Browse CSV
                    </Button>
                  </div>
                  <div className="row">
                    <div style={{ flex: 1 }}>
                      <FieldTitle title="Area column" tip="Column used as the Area axis/input for NMA calculations." className="field-head" />
                      <select
                        className="input"
                        value={row.area_col}
                        onChange={(e) => updateRow(idx, { area_col: e.target.value })}
                      >
                        {(row.columns || ["Area"]).map((c) => (
                          <option key={`area-${idx}-${c}`} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                    <div style={{ flex: 1 }}>
                      <FieldTitle title="NII column" tip="Column used as the NII axis/input for NMA calculations." className="field-head" />
                      <select
                        className="input"
                        value={row.nii_col}
                        onChange={(e) => updateRow(idx, { nii_col: e.target.value })}
                      >
                        {(row.columns || ["NII"]).map((c) => (
                          <option key={`nii-${idx}-${c}`} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="row row-right">
                    <Button
                      className="ghost"
                      title="Read the CSV header and populate the Area/NII selectors for this dataset."
                      onClick={async () => {
                        setStatus("Loading columns...");
                        setStatusLevel("info");
                        try {
                          const res = await callApi("/nma/datasets/columns", { path: row.path });
                          const cols = res.columns || [];
                          const areaGuess = cols.find((c) => c.toLowerCase().includes("area")) || cols[0] || "Area";
                          const niiGuess = cols.find((c) => c.toLowerCase().includes("nii")) || cols[0] || "NII";
                          updateRow(idx, { columns: cols, area_col: areaGuess, nii_col: niiGuess });
                          setStatus("Columns loaded.");
                          setStatusLevel("success");
                        } catch (err) {
                          setStatus(err.message);
                          setStatusLevel("error");
                        }
                      }}
                      disabled={!row.path.trim()}
                    >
                      Load columns
                    </Button>
                    {rows.length > 1 && (
                      <Button className="ghost" onClick={() => removeRow(idx)}>Remove</Button>
                    )}
                  </div>
                </>
              )}
            </Card>
          ))}

          <Button className="secondary" onClick={addRow}>Add dataset</Button>

          <div className="section">
            {!showPlotConfig ? (
              <>
                <h4>Control</h4>
                <div className="row">
                  <div className="metric">
                    <label>Area SD <Tip text="Number of standard deviations applied to Area to define vertical spread of thresholds/ellipse." /></label>
                    <input
                      type="number"
                      step="0.1"
                      value={Number.isFinite(sdArea) ? sdArea.toFixed(2) : ""}
                      onChange={(e) => {
                        const v = round2(parseFloat(e.target.value || "0"));
                        setSdArea(v);
                        if (step1Stats) {
                          setThresholds(computeThresholds(step1Stats, sdNii, v));
                        }
                      }}
                    />
                  </div>
                  <div className="metric">
                    <label>NII SD <Tip text="Number of standard deviations applied to NII to define horizontal spread of thresholds/ellipse." /></label>
                    <input
                      type="number"
                      step="0.1"
                      value={Number.isFinite(sdNii) ? sdNii.toFixed(2) : ""}
                      onChange={(e) => {
                        const v = round2(parseFloat(e.target.value || "0"));
                        setSdNii(v);
                        if (step1Stats) {
                          setThresholds(computeThresholds(step1Stats, v, sdArea));
                        }
                      }}
                    />
                  </div>
                </div>
                <Button className="secondary" onClick={handleAutoDbscan}>Auto (DBSCAN)</Button>
              </>
            ) : (
              <>
                <div className="row row-between">
                  <h4 style={{ margin: 0 }}>NMA analysis</h4>
                  <Button className="ghost btn-small" onClick={() => setShowPlotConfig(false)}>
                    Back to NMA settings
                  </Button>
                </div>
                <p className="hint">Choose how you want to plot NMA (dot plot or heatmap).</p>
                <div className="row">
                  <label
                    className="radio"
                  >
                    <input
                      type="radio"
                      name="plot-kind"
                      checked={plotConfig.kind === "dot"}
                      onChange={() => setPlotConfig((prev) => ({ ...prev, kind: "dot" }))}
                    />
                    Dot plot
                    <Tip text="Dot plot: each nucleus is displayed as an individual point." />
                  </label>
                  <label
                    className="radio"
                  >
                    <input
                      type="radio"
                      name="plot-kind"
                      checked={plotConfig.kind === "heatmap"}
                      onChange={() => setPlotConfig((prev) => ({ ...prev, kind: "heatmap" }))}
                    />
                    Heatmap
                    <Tip text="Heatmap: show density patterns, useful for larger datasets." />
                  </label>
                </div>
                {plotConfig.kind === "dot" ? (
                  <>
                    <div className="hint">
                      Dot plot options <Tip text="These selectors use columns detected from your loaded dataset tables." />
                    </div>
                    <FieldTitle title="Color by (column1)" tip="Choose which dataset column controls marker color." className="field-head" />
                    <div className="row">
                      <select
                        className="input"
                        value={plotConfig.dot.column1}
                        onChange={(e) => updateDotConfig({ column1: e.target.value })}
                        disabled={allDetectedColumns.length === 0}
                      >
                        <option value="">
                          {allDetectedColumns.length ? "Color by (column1)" : "Load columns first"}
                        </option>
                        {allDetectedColumns.map((c) => (
                          <option key={`dot-c1-${c}`} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                    <FieldTitle title="Size by (column2)" tip="Choose which dataset column controls marker size." className="field-head" />
                    <div className="row">
                      <select
                        className="input"
                        value={plotConfig.dot.column2}
                        onChange={(e) => updateDotConfig({ column2: e.target.value })}
                        disabled={allDetectedColumns.length === 0}
                      >
                        <option value="">
                          {allDetectedColumns.length ? "Size by (column2)" : "Load columns first"}
                        </option>
                        {allDetectedColumns.map((c) => (
                          <option key={`dot-c2-${c}`} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                    <div className="row">
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Hue minimum" tip="Optional lower bound for the color scale. Leave empty for automatic scaling." className="field-head" />
                        <input
                          className="input"
                          type="number"
                          placeholder="Hue min (optional)"
                          value={plotConfig.dot.hue_min}
                          onChange={(e) => updateDotConfig({ hue_min: e.target.value })}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Hue maximum" tip="Optional upper bound for the color scale. Leave empty for automatic scaling." className="field-head" />
                        <input
                          className="input"
                          type="number"
                          placeholder="Hue max (optional)"
                          value={plotConfig.dot.hue_max}
                          onChange={(e) => updateDotConfig({ hue_max: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="row">
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Size minimum" tip="Optional lower bound for marker size scaling." className="field-head" />
                        <input
                          className="input"
                          type="number"
                          placeholder="Size min (optional)"
                          value={plotConfig.dot.size_min}
                          onChange={(e) => updateDotConfig({ size_min: e.target.value })}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Size maximum" tip="Optional upper bound for marker size scaling." className="field-head" />
                        <input
                          className="input"
                          type="number"
                          placeholder="Size max (optional)"
                          value={plotConfig.dot.size_max}
                          onChange={(e) => updateDotConfig({ size_max: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="row">
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Sample size" tip="Optional limit on how many nuclei are sampled into the dot plot." className="field-head" />
                        <input
                          className="input"
                          type="number"
                          min="1"
                          placeholder="Sample size (optional)"
                          value={plotConfig.dot.sample_size}
                          onChange={(e) => updateDotConfig({ sample_size: e.target.value })}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Palette" tip="Optional color palette used for the dot plot." className="field-head" />
                        <select
                          className="input"
                          value={plotConfig.dot.palette}
                          onChange={(e) => updateDotConfig({ palette: e.target.value })}
                        >
                          <option value="">Palette (optional)</option>
                          {PALETTE_OPTIONS.map((p) => (
                            <option key={`pal-${p}`} value={p}>{p}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="check-grid">
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={plotConfig.dot.single}
                          onChange={(e) => updateDotConfig({ single: e.target.checked })}
                        />
                        Single plot
                        <Tip text="Combine all datasets in one view." />
                      </label>
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={plotConfig.dot.overtime}
                          onChange={(e) => updateDotConfig({ overtime: e.target.checked })}
                        />
                        Overtime
                        <Tip text="Use time-sequence style when temporal data is available." />
                      </label>
                    </div>
                  </>
                ) : (
                  <>
                    <FieldTitle title="Heatmap palette" tip="Color palette used for heatmap rendering." className="field-head" />
                    <div className="row">
                      <select
                        className="input"
                        value={plotConfig.heatmap.palette}
                        onChange={(e) => updateHeatmapConfig({ palette: e.target.value })}
                      >
                        <option value="">Palette (optional)</option>
                        {PALETTE_OPTIONS.map((p) => (
                          <option key={`heat-pal-${p}`} value={p}>{p}</option>
                        ))}
                      </select>
                    </div>
                    <div className="check-grid">
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={plotConfig.heatmap.single}
                          onChange={(e) => updateHeatmapConfig({ single: e.target.checked })}
                        />
                        Single plot
                        <Tip text="Combine all datasets in one heatmap view." />
                      </label>
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={plotConfig.heatmap.overtime}
                          onChange={(e) => updateHeatmapConfig({ overtime: e.target.checked })}
                        />
                        Overtime
                        <Tip text="Use time-sequence heatmap when temporal data is available." />
                      </label>
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={plotConfig.heatmap.jointplot}
                          onChange={(e) => updateHeatmapConfig({ jointplot: e.target.checked })}
                        />
                        Jointplot
                        <Tip text="Include marginal histograms alongside the heatmap." />
                      </label>
                    </div>
                  </>
                )}
                <FieldTitle title="Saving path" tip="Directory where NMA plots and outputs will be saved." className="field-head" />
                <div className="row path-row">
                  <input
                    className="input"
                    placeholder="Folder to save NMA results"
                    value={plotSavePath}
                    onChange={(e) => setPlotSavePath(e.target.value)}
                  />
                  <Button
                    className="ghost"
                    title="Choose where the generated NMA plots should be saved."
                    onClick={async () => {
                      try {
                        const res = await pickDirectoryPath();
                        setPlotSavePath(res.path || "");
                      } catch (err) {
                        setStatus(err.message);
                        setStatusLevel("error");
                      }
                    }}
                  >
                    Browse
                  </Button>
                </div>
                <Button
                  className="primary"
                  title="Generate all NMA plots with the current plotting settings and save them to the selected folder."
                  onClick={handlePlotAll}
                  disabled={!plotSavePath.trim() || datasets.length === 0 || (plotJob.status === "running" || plotJob.status === "queued")}
                >
                  Plot all
                </Button>
                <div className="hint">
                  Generate plots with current settings and save them to the chosen folder.
                </div>
              </>
            )}
          </div>

          {!showPlotConfig && step === 2 && (
            <div className="section">
              <h4>Thresholds</h4>
              {Object.keys(thresholds).map((k) => (
                <div className="row" key={k}>
                  <label className="label">{k}</label>
                  <div className="readonly">{Number(thresholds[k]).toFixed(3)}</div>
                </div>
              ))}
            </div>
          )}

          {!showPlotConfig && (
            <div className="section">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pkl,.pickle"
                style={{ display: "none" }}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleLoadSettings(f);
                }}
              />
              <Button
                className="secondary"
                onClick={() => fileInputRef.current?.click()}
                disabled={step1Ready}
              >
                Load settings
              </Button>
              {!step1Ready && (
                <Button className="primary" onClick={handleStep1} disabled={!hasControl}>Create Settings</Button>
              )}
              {step1Ready && (
                <div className="wizard-actions">
                  <Button className="secondary" onClick={() => setStep(1)} disabled={step === 1}>Previous</Button>
                  {step === 1 ? (
                    <Button
                      className="primary"
                      onClick={async () => {
                        const ok = await handleStep2();
                        if (ok) setStep(2);
                      }}
                    >
                      Next
                    </Button>
                  ) : (
                    <Button className="primary" onClick={handleComplete}>Complete</Button>
                  )}
                </div>
              )}
            </div>
          )}
          <Status level={statusLevel} text={status} />
        </Card>

        <main className="content">
          <div className="row row-right">
            <button className="ghost btn-small" onClick={() => handleOpenTutorial("NMA")}>
              Tutorial
            </button>
            <button
              className="ghost btn-small"
              onClick={handleResetNma}
              disabled={plotJob.status === "running" || plotJob.status === "queued"}
            >
              Reset
            </button>
          </div>
          {!step1Ready ? (
            <section>
              <p className="hint">No settings loaded yet. Use `Load settings` or `Create Settings` to start.</p>
            </section>
          ) : (
            <>
          {step === 1 && (
            <section>
              <h2>Step 1 · Control ellipse</h2>
              <p className="hint">Adjust SDs or use auto-DBSCAN.</p>
              <div className="plot-shell">
                <div className="slider-vertical">
                  <label>Area SD <Tip text="Adjust Area standard deviation for threshold and ellipse height." /></label>
                  <input
                    type="range"
                    min="0"
                    max="5"
                    step="0.1"
                    value={5 - sdArea}
                  onChange={(e) => {
                      const v = round2(5 - parseFloat(e.target.value || "0"));
                      setSdArea(v);
                      if (step1Stats && step1GraphLimits && step1Sample) {
                        setStep1Figure(buildStep1Figure(step1Sample, step1Stats, step1GraphLimits, sdNii, v));
                        setThresholds(computeThresholds(step1Stats, sdNii, v));
                      }
                    }}
                  />
                  <span className="slider-value">{sdArea.toFixed(2)}</span>
                </div>
                <PlotPanel figure={step1Figure} />
              </div>
              <div className="slider-horizontal">
                <label>NII SD <Tip text="Adjust NII standard deviation for threshold and ellipse width." /></label>
                <input
                  type="range"
                  min="0"
                  max="5"
                  step="0.1"
                  value={sdNii}
                  onChange={(e) => {
                    const v = round2(parseFloat(e.target.value || "0"));
                    setSdNii(v);
                    if (step1Stats && step1GraphLimits && step1Sample) {
                      setStep1Figure(buildStep1Figure(step1Sample, step1Stats, step1GraphLimits, v, sdArea));
                      setThresholds(computeThresholds(step1Stats, v, sdArea));
                    }
                  }}
                />
                <span className="slider-value">{sdNii.toFixed(2)}</span>
              </div>
            </section>
          )}

          {step === 2 && (
            <section>
              <h2>Step 2 · Threshold lines</h2>
              {!showPlotConfig && <p className="hint">Use additional datasets for reference.</p>}
              {(showPlotConfig && hasPlotRun && !showNmaPreviewWhilePlotting) ? (
                <div className="hint">
                  NMA preview and quadrant table are minimized while plotting.
                  <Button
                    className="ghost btn-small"
                    style={{ marginLeft: 8 }}
                    onClick={() => setShowNmaPreviewWhilePlotting(true)}
                  >
                    Show preview
                  </Button>
                </div>
              ) : (
                <>
                  {showPlotConfig && hasPlotRun && (
                    <div className="row row-right" style={{ marginBottom: 8 }}>
                      <Button
                        className="ghost btn-small"
                        onClick={() => setShowNmaPreviewWhilePlotting(false)}
                      >
                        Minimize preview
                      </Button>
                    </div>
                  )}
                  {step2Figure ? (
                    <PlotPanel
                      figure={step2Figure}
                      config={{ displayModeBar: false, editable: !finalMode, edits: { shapePosition: true } }}
                      onRelayout={(ev) => {
                        if (finalMode) return;
                        if (!step2GraphLimits || !step2Stats || !step2Traces) return;
                        const getShape = (idx) => {
                          const x0 = ev[`shapes[${idx}].x0`];
                          const x1 = ev[`shapes[${idx}].x1`];
                          return x0 ?? x1;
                        };
                        const v_down = getShape(2);
                        const v_down2 = getShape(3);
                        const v_mid = getShape(4);
                        const v_up = getShape(5);
                        if (v_down == null && v_down2 == null && v_mid == null && v_up == null) return;
                        const next = {
                          ...thresholds,
                          v_down: v_down ?? thresholds.v_down,
                          v_down2: v_down2 ?? thresholds.v_down2,
                          v_mid: v_mid ?? thresholds.v_mid,
                          v_up: v_up ?? thresholds.v_up,
                        };
                        setThresholds(next);
                        setStep2Figure(buildStep2Figure(step2Traces, step2Stats, step2GraphLimits, next, sdNii, sdArea, true));
                        setStep2Percentages(computeQuadrantPercentages(step2Traces, next, step2Stats, sdArea));
                        setFinalMode(false);
                      }}
                    />
                  ) : (
                    <div className="hint">Click Next to generate the Step 2 figure.</div>
                  )}
                  {step2Percentages && (
                    (() => {
                      const datasetNames = Array.from(
                        new Set(
                          Object.values(step2Percentages).flatMap((v) => Object.keys(v)).concat(
                            (step2Traces || []).map((t) => t.name).filter(Boolean)
                          )
                        )
                      );
                      return (
                        <div className="percentages">
                          <h3>Quadrant distribution (%)</h3>
                          <div className="percent-table">
                            <div className="percent-row header">
                              <div className="cell">Quadrant</div>
                              {datasetNames.map((name) => (
                                <div className="cell" key={`h-${name}`}>{name}</div>
                              ))}
                            </div>
                            {["LR", "LI", "N", "I", "SR", "S", "SI"].map((q) => (
                              <div className="percent-row" key={`q-${q}`}>
                                <div className="cell">{q}</div>
                                {datasetNames.map((name) => (
                                  <div className="cell" key={`${q}-${name}`}>
                                    {step2Percentages[q]?.[name] != null ? step2Percentages[q][name].toFixed(1) : "-"}
                                  </div>
                                ))}
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })()
                  )}
                </>
              )}
              {(!showPlotConfig || !hasPlotRun || showNmaPreviewWhilePlotting) && finalMode && downloadReady && (
                <div className="section">
                  <Button
                    className="primary"
                    onClick={() => {
                      window.location.href = `${API_BASE}/nma/settings/download`;
                    }}
                  >
                    Download settings
                  </Button>
                  <Button
                    className="secondary"
                    onClick={handleDownloadTable}
                    disabled={!step2Percentages}
                  >
                    Download table
                  </Button>
                </div>
              )}
              {showPlotConfig && (
                <div className="section">
                  <h3>Plot progress</h3>
                  <div className="progress-wrap">
                    <div
                      className={`progress-fill ${plotJob.status === "running" || plotJob.status === "queued" ? "running" : ""}`}
                      style={{ width: `${Math.max(0, Math.min(100, plotJob.progress || 0))}%` }}
                    />
                  </div>
                  <div className="hint">{plotJob.message || "Waiting to start."}</div>
                  {plotJob.files?.length > 0 && (
                    <div className="plot-viewer">
                      <div className="viewer-toolbar">
                        <Button
                          className="ghost btn-small"
                          onClick={() => setCurrentPlotIndex((i) => Math.max(0, i - 1))}
                          disabled={currentPlotIndex <= 0}
                        >
                          ◀
                        </Button>
                        <span className="viewer-counter">
                          {currentPlotIndex + 1} / {plotJob.files.length}
                        </span>
                        <Button
                          className="ghost btn-small"
                          onClick={() => setCurrentPlotIndex((i) => Math.min(plotJob.files.length - 1, i + 1))}
                          disabled={currentPlotIndex >= plotJob.files.length - 1}
                        >
                          ▶
                        </Button>
                      </div>
                      <a
                        href={`${API_BASE}/nma/plots/file?path=${encodeURIComponent(plotJob.files[currentPlotIndex])}`}
                        target="_blank"
                        rel="noreferrer"
                        className="thumb-card viewer-single"
                      >
                        <img
                          src={`${API_BASE}/nma/plots/file?path=${encodeURIComponent(plotJob.files[currentPlotIndex])}`}
                          alt={plotJob.files[currentPlotIndex].split("/").pop()}
                        />
                        <span>{plotJob.files[currentPlotIndex].split("/").pop()}</span>
                      </a>
                    </div>
                  )}
                </div>
              )}
            </section>
          )}
            </>
          )}
        </main>
          </>
        )}
      </div>
    </div>
  );
}
