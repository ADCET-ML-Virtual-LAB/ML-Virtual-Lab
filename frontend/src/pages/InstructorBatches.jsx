import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { instructorApi } from "../api/instructor.js";
import "./InstructorConsole.css";

// The instructor's own batches as cards (name and academic year only).
export default function InstructorBatches() {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    instructorApi
      .batches()
      .then(setBatches)
      .catch(() => setError("Could not load your batches. Please try again."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  if (loading) return <div className="page-loading">Loading batches…</div>;

  return (
    <div className="ic-page">
      <h1 className="ic-page__title">Batches</h1>

      {error && (
        <div className="alert alert--error ic-alert">
          <span>{error}</span>
          <button type="button" className="btn btn--sm btn--ghost" onClick={load}>
            Retry
          </button>
        </div>
      )}

      {!error && batches.length === 0 && (
        <div className="ic-empty">
          No batches have been assigned to you yet. Please contact the administrator.
        </div>
      )}

      <div className="ic-batch-grid">
        {batches.map((batch) => (
          <Link to={`/batches/${batch.id}`} key={batch.id} className="ic-batch-card">
            <div className="ic-batch-card__banner">{batch.name}</div>
            <div className="ic-batch-card__body">
              <span className="ic-batch-card__label">Academic Year</span>
              <span className="ic-batch-card__year">{batch.academic_year}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
