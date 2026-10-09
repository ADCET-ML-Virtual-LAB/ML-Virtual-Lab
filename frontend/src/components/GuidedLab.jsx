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
 * Recharts-based chart renderer for lab outputs.
 * Supports: scatter points, line series.
 * data = { labels, datasets: [{ label, data: [{x,y}|number], type: "scatter"|"line"|"bar", color }] }
 */
import {
  LineChart, Line, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart
} from "recharts";

function GuidedLabChart({ data }) {
  if (!data || !data.datasets || data.datasets.length === 0) return null;

  const COLORS = ["#2563eb", "#16a34a", "#d97706", "#9333ea", "#dc2626"];

  // Normalize data to a format suitable for Recharts ComposedChart
  // We need a unified data array where each object has an 'x' or 'name' and then values for each dataset.
  
  // If no datasets have explicit x/y coordinates, use index-based grouping
  const isIndexed = data.datasets.every(ds => typeof ds.data[0] !== 'object');

  if (isIndexed) {
    const maxLen = Math.max(...data.datasets.map(ds => ds.data.length));
    const unifiedData = Array.from({ length: maxLen }).map((_, i) => {
      const row = { name: data.labels ? data.labels[i] : i };
      data.datasets.forEach((ds, di) => {
        row[`dataset_${di}`] = ds.data[i];
      });
      return row;
    });

    return (
      <div className="guided-lab__chart" style={{ height: "350px", width: "100%" }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={unifiedData} margin={{ top: 10, right: 10, bottom: 10, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#cbd5e1' }} />
            <YAxis tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ borderRadius: '6px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}
            />
            <Legend wrapperStyle={{ fontSize: '13px' }} />
            {data.datasets.map((ds, di) => {
              const color = ds.color || COLORS[di % COLORS.length];
              if (ds.type === "scatter") {
                return <Scatter key={di} name={ds.label} dataKey={`dataset_${di}`} fill={color} />;
              }
              return (
                <Line
                  key={di}
                  type="monotone"
                  name={ds.label}
                  dataKey={`dataset_${di}`}
                  stroke={color}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 6 }}
                />
              );
            })}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Scatter/XY data
  return (
    <div className="guided-lab__chart" style={{ height: "350px", width: "100%" }}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis type="number" dataKey="x" name="X" tick={{ fontSize: 12 }} />
          <YAxis type="number" dataKey="y" name="Y" tick={{ fontSize: 12 }} />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
          <Legend />
          {data.datasets.map((ds, di) => {
            const color = ds.color || COLORS[di % COLORS.length];
            const formattedData = ds.data.map((d, i) => (typeof d === 'object' ? d : { x: i, y: d }));
            
            if (ds.type === "line") {
              // Hack to draw lines in a ScatterChart using Recharts
              return (
                <Scatter
                  key={di}
                  name={ds.label}
                  data={formattedData}
                  fill={color}
                  line={{ stroke: color, strokeWidth: 2 }}
                  shape="circle"
                />
              );
            }
            return (
              <Scatter
                key={di}
                name={ds.label}
                data={formattedData}
                fill={color}
                shape="circle"
              />
            );
          })}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
