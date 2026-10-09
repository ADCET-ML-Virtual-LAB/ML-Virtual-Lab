import { useState, useEffect } from "react";
import { dashboardApi } from "../api/dashboard.js";
import "./StudentDashboard.css";

const STATUS_LABEL = {
  not_started: "Not started",
  in_progress: "In progress",
  completed: "Completed",
  not_tracked: "—",
};

const STATUS_BADGE = {
  not_started: "badge--gray",
  in_progress: "badge--yellow",
  completed: "badge--green",
  not_tracked: "badge--gray",
};

export default function StudentDashboard() {
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardApi
      .student()
      .then(setProgress)
      .catch(() => setError("Failed to load your progress."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading">Loading your progress…</div>;

  const completed = progress.filter((p) => p.overall_status === "completed").length;

  return (
    <div className="student-dash">
      <div className="student-dash__header">
        <h1 className="student-dash__title">My Progress</h1>
        <p className="student-dash__summary">
          {completed} of {progress.length} experiments completed
        </p>
      </div>

      {error && <div className="alert alert--error">{error}</div>}

      {progress.length === 0 && !error && (
        <p className="student-dash__empty">No experiments available yet.</p>
      )}

      <div className="progress-grid">
        {progress.map((exp) => (
          <div key={exp.experiment_id} className="progress-card">
            <div className="progress-card__header">
              <h2 className="progress-card__title">{exp.experiment_title}</h2>
              <span className={`badge ${STATUS_BADGE[exp.overall_status]}`}>
                {STATUS_LABEL[exp.overall_status]}
              </span>
            </div>

            <div className="progress-card__steps">
              <ProgressStep label="Pre-Quiz" status={exp.pre_quiz} />
              <ProgressStep label="Guided Lab" status={exp.guided_lab} />
              <ProgressStep label="Code Exercise" status={exp.code_exercise} />
              <ProgressStep label="Post-Quiz" status={exp.post_quiz} />
              <ProgressStep
                label="Assignment"
                status={exp.assignment}
                score={exp.assignment_score}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProgressStep({ label, status, score }) {
  const icons = {
    not_started: "○",
    in_progress: "◑",
    completed: "●",
    not_tracked: "—",
  };
  const colors = {
    not_started: "var(--color-text-muted)",
    in_progress: "var(--color-warning)",
    completed: "var(--color-success)",
    not_tracked: "var(--color-border)",
  };

  return (
    <div className="progress-step">
      <span className="progress-step__icon" style={{ color: colors[status] }}>
        {icons[status]}
      </span>
      <span className="progress-step__label">{label}</span>
      {score != null && (
        <span className="progress-step__score">{score}%</span>
      )}
    </div>
  );
}
