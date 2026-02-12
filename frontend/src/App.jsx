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

function PlotPanel({ figure }) {
  const ref = React.useRef(null);

  React.useEffect(() => {
    if (!ref.current || !figure) return;
    Plotly.react(ref.current, figure.data, figure.layout, { displayModeBar: false });
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
      const fig = buildStep1Figure(data.sample, data.stats, data.axis ? [data.axis.y[0], data.axis.y[1], data.axis.x[0], data.axis.x[1]] : null, data.sd_factors.sd_nii, data.sd_factors.sd_area);
      setStep1Figure(fig);
      // Initialize thresholds for step 2 from step 1 defaults (do not expose in step 1 UI)
      const t = data.figure?.data?.reduce((acc, d) => {
        if (!d?.name) return acc;
        if (["v_up", "v_mid", "v_down", "v_down2"].includes(d.name)) {
          acc[d.name] = d.x?.[0] ?? acc[d.name];
        }
        if (d.name === "y_high") acc.y_high = d.y?.[0] ?? acc.y_high;
        if (d.name === "y_low") acc.y_low = d.y?.[0] ?? acc.y_low;
        return acc;
      }, { ...thresholds });
      if (t) setThresholds(t);
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
      setStep2Figure(data.figure);
      setStatus("Step 2 ready.");
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
                  onChange={(e) => setSdArea(parseFloat(e.target.value || "0"))}
                />
              </div>
              <div className="metric">
                <label>NII SD</label>
                <input
                  type="number"
                  step="0.1"
                  value={sdNii}
                  onChange={(e) => setSdNii(parseFloat(e.target.value || "0"))}
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
                  <input
                    type="number"
                    value={thresholds[k]}
                    onChange={(e) =>
                      setThresholds((prev) => ({
                        ...prev,
                        [k]: parseFloat(e.target.value || "0"),
                      }))
                    }
                  />
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
                <button className="primary" onClick={() => setStep(2)} disabled={step === 2}>Next</button>
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
              <PlotPanel figure={step2Figure} />
            </section>
          )}
        </main>
      </div>
    </div>
  );
}
