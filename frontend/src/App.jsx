import React, { useMemo, useState } from "react";
import Plotly from "plotly.js-dist-min";

const API_BASE = "http://127.0.0.1:8000";

const emptyRow = () => ({
  name: "",
  path: "",
  area_col: "Area",
  nii_col: "NII",
  is_control: false,
  columns: null,
});

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

function PlotPanel({ figure, config, onRelayout }) {
  const ref = React.useRef(null);

  React.useEffect(() => {
    if (!ref.current || !figure) return;
    Plotly.react(ref.current, figure.data, figure.layout, config || { displayModeBar: false });
    if (onRelayout && ref.current?.on) {
      if (ref.current.removeAllListeners) {
        ref.current.removeAllListeners("plotly_relayout");
      }
      ref.current.on("plotly_relayout", onRelayout);
    }
  }, [figure]);

  return <div className="plot" ref={ref} />;
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
  const [rows, setRows] = useState([{
    ...emptyRow(),
    name: "Control",
    is_control: true,
  }]);

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

  const datasets = useMemo(() => buildDatasets(rows), [rows]);
  const hasControl = datasets.some((d) => d.is_control);

  const updateRow = (idx, patch) => {
    setRows((prev) => prev.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  };

  const addRow = () => setRows((prev) => [...prev, emptyRow()]);
  const removeRow = (idx) => setRows((prev) => prev.filter((_, i) => i !== idx));

  const callApi = async (path, payload) => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    return res.json();
  };

  const handleStep1 = async () => {
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
      setSdArea(data.sd_factors.sd_area);
      setSdNii(data.sd_factors.sd_nii);
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
      setSdNii(data.sd_factors.sd_nii);
      setSdArea(data.sd_factors.sd_area);
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
      setStatus("Completed. Final figure ready.");
      setStatusLevel("success");
    } catch (err) {
      setStatus(err.message);
      setStatusLevel("error");
    }
  };

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

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <div className="logo">forNMA</div>
          <div className="subtitle">NMA Settings</div>
        </div>
        <div className="stepper">
          <div className={`chip ${step === 1 ? "active" : ""}`}>Step 1</div>
          <div className={`chip ${step === 2 ? "active" : ""}`}>Step 2</div>
        </div>
      </header>

      <div className="layout">
        <aside className="panel">
          <h3>Datasets</h3>
          <p className="hint">Mark at least one control. Paths must be local.</p>

          {rows.map((row, idx) => (
            <div className="dataset" key={idx}>
              <div className="row">
                <input
                  className="input"
                  placeholder="Name"
                  value={row.name}
                  onChange={(e) => updateRow(idx, { name: e.target.value })}
                />
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={row.is_control}
                    onChange={(e) => updateRow(idx, { is_control: e.target.checked })}
                  />
                  Control
                </label>
              </div>
              <input
                className="input"
                placeholder="/path/Results.csv"
                value={row.path}
                onChange={(e) => updateRow(idx, { path: e.target.value })}
              />
              <div className="row">
                <select
                  className="input"
                  value={row.area_col}
                  onChange={(e) => updateRow(idx, { area_col: e.target.value })}
                >
                  {(row.columns || ["Area"]).map((c) => (
                    <option key={`area-${idx}-${c}`} value={c}>{c}</option>
                  ))}
                </select>
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
              <div className="row row-right">
                <button
                  className="ghost"
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
                </button>
                {rows.length > 1 && (
                  <button className="ghost" onClick={() => removeRow(idx)}>Remove</button>
                )}
              </div>
            </div>
          ))}

          <button className="secondary" onClick={addRow}>Add dataset</button>

          <div className="section">
            <h4>Control</h4>
            <div className="row">
              <div className="metric">
                <label>Area SD</label>
                <input
                  type="number"
                  step="0.1"
                  value={sdArea}
                  onChange={(e) => {
                    const v = parseFloat(e.target.value || "0");
                    setSdArea(v);
                    if (step1Stats) {
                      setThresholds(computeThresholds(step1Stats, sdNii, v));
                    }
                  }}
                />
              </div>
              <div className="metric">
                <label>NII SD</label>
                <input
                  type="number"
                  step="0.1"
                  value={sdNii}
                  onChange={(e) => {
                    const v = parseFloat(e.target.value || "0");
                    setSdNii(v);
                    if (step1Stats) {
                      setThresholds(computeThresholds(step1Stats, v, sdArea));
                    }
                  }}
                />
              </div>
            </div>
            <button className="secondary" onClick={handleAutoDbscan}>Auto (DBSCAN)</button>
          </div>

          {step === 2 && (
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

          <div className="section">
            {!step1Ready && (
              <button className="primary" onClick={handleStep1} disabled={!hasControl}>Create Settings</button>
            )}
            {step1Ready && (
              <div className="wizard-actions">
                <button className="secondary" onClick={() => setStep(1)} disabled={step === 1}>Previous</button>
                {step === 1 ? (
                  <button
                    className="primary"
                    onClick={async () => {
                      const ok = await handleStep2();
                      if (ok) setStep(2);
                    }}
                  >
                    Next
                  </button>
                ) : (
                  <button className="primary" onClick={handleComplete}>Complete</button>
                )}
              </div>
            )}
          </div>

          <Status level={statusLevel} text={status} />
        </aside>

        <main className="content">
          {step === 1 && (
            <section>
              <h2>Step 1 · Control ellipse</h2>
              <p className="hint">Adjust SDs or use auto-DBSCAN.</p>
              <div className="plot-shell">
                <div className="slider-vertical">
                  <label>Area SD</label>
                  <input
                    type="range"
                    min="0"
                    max="5"
                    step="0.1"
                    value={5 - sdArea}
                    onChange={(e) => {
                      const v = 5 - parseFloat(e.target.value || "0");
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
                <label>NII SD</label>
                <input
                  type="range"
                  min="0"
                  max="5"
                  step="0.1"
                  value={sdNii}
                  onChange={(e) => {
                    const v = parseFloat(e.target.value || "0");
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
              <p className="hint">Use additional datasets for reference.</p>
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
              {finalMode && downloadReady && (
                <div className="section">
                  <button
                    className="primary"
                    onClick={() => {
                      window.location.href = `${API_BASE}/nma/settings/download`;
                    }}
                  >
                    Download settings
                  </button>
                </div>
              )}
            </section>
          )}
        </main>
      </div>
    </div>
  );
}
