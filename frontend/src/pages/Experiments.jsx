import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { experimentsApi } from "../api/experiments.js";
import "./Experiments.css";

// Lists the lab's experiments. Each card opens that experiment's workspace.
export default function Experiments() {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    experimentsApi
      .list()
      .then(setExperiments)
      .catch(() => setError("Failed to load experiments. Please refresh and try again."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading">Loading experiments…</div>;

  return (
    <div className="experiments-page">
      <h1 className="experiments-page__title">Experiments</h1>
      <p className="experiments-page__subtitle">Choose an experiment to begin.</p>

      {error && <div className="alert alert--error">{error}</div>}

      {experiments.length === 0 && !error && (
        <div className="experiments-page__empty">No experiments published yet. Check back soon!</div>
      )}

      <div className="experiment-grid">
        {experiments.map((exp) => (
          <Link to={`/experiments/${exp.slug}`} key={exp.id} className="exp-card">
            <div className="exp-card__index">{String(exp.order_index).padStart(2, "0")}</div>
            <div className="exp-card__body">
              <h2 className="exp-card__title">{exp.title}</h2>
              <p className="exp-card__aim">{exp.aim}</p>
            </div>
            <span className="exp-card__arrow">→</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
