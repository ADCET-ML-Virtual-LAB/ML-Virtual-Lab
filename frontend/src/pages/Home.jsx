import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { experimentsApi } from "../api/experiments.js";
import { useAuth } from "../context/AuthContext.jsx";
import "./Home.css";

export default function Home() {
  const { user } = useAuth();
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    experimentsApi
      .list()
      .then(setExperiments)
      .catch(() => setError("Failed to load experiments."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading">Loading experiments…</div>;

  return (
    <div className="home">
      <div className="home__hero">
        <h1 className="home__title">ML Virtual Lab</h1>
        <p className="home__subtitle">
          Explore classical Machine Learning experiments through theory, interactive labs and guided
          code exercises — all in your browser.
        </p>
        <p className="home__greeting">Welcome, {user?.full_name} 👋</p>
      </div>

      {error && <div className="alert alert--error">{error}</div>}

      {experiments.length === 0 && !error && (
        <div className="home__empty">
          No experiments published yet. Check back soon!
        </div>
      )}

      <div className="experiment-grid">
        {experiments.map((exp, idx) => (
          <Link to={`/experiments/${exp.slug}`} key={exp.id} className="exp-card">
            <div className="exp-card__index">{String(idx + 1).padStart(2, "0")}</div>
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
