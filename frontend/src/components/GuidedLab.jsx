import { useState, useCallback } from "react";
import "./GuidedLab.css";

/**
 * GuidedLab — Module 5 (Parametric/Guided Lab).
 *
 * Completely client-side. The `lab_config` JSON from the experiment defines:
 *   {
 *     description: string,
 *     parameters: [
 *       { key: string, label: string, type: "range"|"number"|"select",
 *         min?: number, max?: number, step?: number, default: any,
 *         options?: [{ label, value }]  (for "select")
 *       }
 *     ],
 *     compute: string   // JS function body as a string, called with params object,
 *                       // must return { labels: string[], datasets: [...Chart.js datasets] }
 *   }
 *
 * The `compute` string is eval'd in the browser — this is intentional; the
 * content is authored by admins, not students.  Student code runs via Pyodide
 * in the CodeEditor, not here.
 */
export default function GuidedLab({ labConfig }) {
  const [params, setParams] = useState(() => {
    if (!labConfig?.parameters) return {};
    return Object.fromEntries(
      labConfig.parameters.map((p) => [p.key, p.default])
    );
  });
  const [chartData, setChartData] = useState(null);
  const [error, setError] = useState("");

  const handleParamChange = useCallback((key, value) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  }, []);

  function handleRun() {
    setError("");
    if (!labConfig?.compute) {
      setError("No compute function defined for this lab.");
      return;
    }
    try {
      // eslint-disable-next-line no-new-func
      const computeFn = new Function("params", labConfig.compute);
      const result = computeFn(params);
      setChartData(result);
    } catch (e) {
      setError(`Lab error: ${e.message}`);
    }
  }

  if (!labConfig) {
    return (
      <div className="guided-lab guided-lab--empty">
        <p>No interactive lab configured for this experiment yet.</p>
      </div>
    );
  }

  return (
    <div className="guided-lab">
      {labConfig.description && (
        <p className="guided-lab__desc">{labConfig.description}</p>
      )}

      <div className="guided-lab__controls">
        {(labConfig.parameters || []).map((param) => (
          <div key={param.key} className="guided-lab__param">
            <label className="form-label">
              {param.label}
              {param.type === "range" && (
                <div className="guided-lab__range-row">
                  <input
                    type="range"
                    min={param.min ?? 0}
                    max={param.max ?? 100}
                    step={param.step ?? 1}
                    value={params[param.key]}
                    onChange={(e) => handleParamChange(param.key, Number(e.target.value))}
                    className="guided-lab__slider"
                  />
                  <span className="guided-lab__range-val">{params[param.key]}</span>
                </div>
              )}
              {param.type === "number" && (
                <input
                  type="number"
                  min={param.min}
                  max={param.max}
                  step={param.step ?? 1}
                  value={params[param.key]}
                  onChange={(e) => handleParamChange(param.key, Number(e.target.value))}
                  className="form-input"
                />
              )}
              {param.type === "select" && (
                <select
                  value={params[param.key]}
                  onChange={(e) => handleParamChange(param.key, e.target.value)}
                  className="form-select"
                >
                  {(param.options || []).map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              )}
            </label>
          </div>
        ))}
      </div>

      <button className="btn btn--primary" onClick={handleRun}>
        Run Lab
      </button>

      {error && <div className="alert alert--error">{error}</div>}

      {chartData && (
        <div className="guided-lab__output">
          <GuidedLabChart data={chartData} />
        </div>
      )}
    </div>
  );
}

/**
 * Simple SVG-based chart renderer for lab outputs.
 * Supports: scatter points, line series.
 * data = { labels, datasets: [{ label, data: [{x,y}|number], type: "scatter"|"line"|"bar", color }] }
 */
function GuidedLabChart({ data }) {
  if (!data) return null;

  // Determine if datasets have {x,y} or plain numeric values
  const allPoints = data.datasets.flatMap((ds) =>
    ds.data.map((d, i) =>
      typeof d === "object" ? d : { x: i, y: d }
    )
  );

  if (allPoints.length === 0) {
    return <div className="guided-lab__no-data">No data to display.</div>;
  }

  const W = 480, H = 280, PAD = 40;
  const xs = allPoints.map((p) => p.x);
  const ys = allPoints.map((p) => p.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const rangeX = maxX - minX || 1, rangeY = maxY - minY || 1;

  const toSvgX = (x) => PAD + ((x - minX) / rangeX) * (W - 2 * PAD);
  const toSvgY = (y) => H - PAD - ((y - minY) / rangeY) * (H - 2 * PAD);

  const COLORS = ["#2563eb", "#16a34a", "#d97706", "#9333ea", "#dc2626"];

  return (
    <div className="guided-lab__chart">
      <svg viewBox={`0 0 ${W} ${H}`} className="guided-lab__svg">
        {/* Axes */}
        <line x1={PAD} y1={PAD} x2={PAD} y2={H - PAD} stroke="#cbd5e1" strokeWidth={1} />
        <line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} stroke="#cbd5e1" strokeWidth={1} />

        {/* Datasets */}
        {data.datasets.map((ds, di) => {
          const color = ds.color || COLORS[di % COLORS.length];
          const points = ds.data.map((d, i) =>
            typeof d === "object" ? d : { x: i, y: d }
          );
          const type = ds.type || "line";

          if (type === "scatter") {
            return points.map((p, pi) => (
              <circle
                key={pi}
                cx={toSvgX(p.x)}
                cy={toSvgY(p.y)}
                r={3}
                fill={color}
                opacity={0.8}
              />
            ));
          }

          // Line chart
          const d = points
            .map((p, i) => `${i === 0 ? "M" : "L"}${toSvgX(p.x)},${toSvgY(p.y)}`)
            .join(" ");
          return <path key={di} d={d} stroke={color} strokeWidth={2} fill="none" />;
        })}
      </svg>

      {/* Legend */}
      <div className="guided-lab__legend">
        {data.datasets.map((ds, di) => (
          <span key={di} className="guided-lab__legend-item">
            <span
              className="guided-lab__legend-dot"
              style={{ background: ds.color || COLORS[di % COLORS.length] }}
            />
            {ds.label}
          </span>
        ))}
      </div>
    </div>
  );
}
