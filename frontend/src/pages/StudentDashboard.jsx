import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { dashboardApi } from "../api/dashboard.js";
import { SECTION_LABELS } from "../constants/sections.js";
import "./StudentDashboard.css";

// View Progress. Every status here comes from the saved backend state.
const STATUS_LABEL = {
  not_started: "Not Attempted",
  in_progress: "In Progress",
  completed: "Completed",
};

const STATUS_BADGE = {
  not_started: "badge--gray",
  in_progress: "badge--yellow",
  completed: "badge--green",
};

// Overall progress = completed sections / all sections across the published
// experiments, as a whole-number percentage. It shows 100% only when every
// section is completed.
function overallPercent(rows) {
  let total = 0;
  let done = 0;
  rows.forEach((row) => {
    (row.sections || []).forEach((section) => {
      total += 1;
      if (section.completed) done += 1;
    });
  });
  if (total === 0) return 0;
  if (done === total) return 100;
  return Math.min(99, Math.round((done / total) * 100));
}

export default function StudentDashboard() {
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openId, setOpenId] = useState(null);

  useEffect(() => {
    dashboardApi
      .student()
      .then(setProgress)
      .catch(() => setError("Failed to load your progress. Please refresh and try again."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading">Loading your progress…</div>;

  const percent = overallPercent(progress);

  return (
    <div className="student-dash">
      <div className="student-dash__header">
        <div>
          <h1 className="student-dash__title">View Progress</h1>
          {!error && (
            <div className="student-dash__overall">
              <span className="student-dash__overall-label">Overall progress</span>
              <strong className="student-dash__overall-value">{percent}%</strong>
            </div>
          )}
        </div>
        <Link to="/dashboard/assignment-scores" className="btn btn--primary">
          View Assignment Scores
        </Link>
      </div>

      {!error && (
        <div
          className="student-dash__bar"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent}
          aria-label="Overall progress"
        >
          <div className="student-dash__bar-fill" style={{ width: `${percent}%` }} />
        </div>
      )}

      {error && <div className="alert alert--error">{error}</div>}

      {progress.length === 0 && !error && (
        <p className="student-dash__empty">No experiments available yet.</p>
      )}

      <div className="progress-list">
        {progress.map((exp) => {
          const open = openId === exp.experiment_id;
          return (
            <div key={exp.experiment_id} className="progress-item">
              <button
                type="button"
                className="progress-item__head"
                aria-expanded={open}
                onClick={() => setOpenId(open ? null : exp.experiment_id)}
              >
                <span className="progress-item__number">
                  {String(exp.experiment_number).padStart(2, "0")}
                </span>
                <span className="progress-item__title">{exp.experiment_title}</span>
                <span className={`badge ${STATUS_BADGE[exp.overall_status]}`}>
                  {STATUS_LABEL[exp.overall_status]}
                </span>
                <span className="progress-item__chevron" aria-hidden="true">
                  {open ? "▾" : "▸"}
                </span>
              </button>

              {open && (
                <ul className="progress-item__sections">
                  {(exp.sections || []).map((section) => (
                    <li key={section.key} className="progress-section">
                      <span
                        className={`progress-section__dot ${section.completed ? "progress-section__dot--done" : ""}`}
                        role="img"
                        aria-label={section.completed ? "Completed" : "Not completed"}
                      />
                      <span className="progress-section__label">
                        {SECTION_LABELS[section.key] || section.key}
                      </span>
                      {section.completed && (
                        <span className="progress-section__done">Completed</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
