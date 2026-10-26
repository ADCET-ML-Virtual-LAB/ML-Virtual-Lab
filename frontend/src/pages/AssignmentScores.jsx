import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { dashboardApi } from "../api/dashboard.js";
import "./AssignmentScores.css";

// Assignment Scores: exactly three columns. Values come from saved backend state.
function scoreCell(exp) {
  if (!exp.has_assignment) return "Assignment not Available";
  if (exp.assignment === "completed") {
    return exp.assignment_score != null ? `${exp.assignment_score}%` : "Submitted";
  }
  return "Not Submitted";
}

export default function AssignmentScores() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardApi
      .student()
      .then(setRows)
      .catch(() => setError("Failed to load your assignment scores. Please refresh and try again."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading">Loading assignment scores…</div>;

  return (
    <div className="scores-page">
      <Link to="/dashboard" className="scores-page__back">← View Progress</Link>
      <h1 className="scores-page__title">Assignment Scores</h1>

      {error && <div className="alert alert--error">{error}</div>}

      {!error && rows.length === 0 && (
        <p className="scores-page__empty">No experiments available yet.</p>
      )}

      {!error && rows.length > 0 && (
        <div className="scores-page__table-wrap">
          <table className="scores-page__table">
            <thead>
              <tr>
                <th>Experiment No.</th>
                <th>Experiment Name</th>
                <th>Assignment Score</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((exp) => (
                <tr key={exp.experiment_id}>
                  <td>{exp.experiment_number}</td>
                  <td>{exp.experiment_title}</td>
                  <td>{scoreCell(exp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
