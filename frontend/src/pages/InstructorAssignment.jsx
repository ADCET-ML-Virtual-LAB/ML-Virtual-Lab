import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { instructorApi } from "../api/instructor.js";
import AnswerKey from "../components/AnswerKey.jsx";
import "./InstructorConsole.css";

// Assignment for one experiment: experiment number and title only (no other
// experiment sections), then the questions with their correct answers.
export default function InstructorAssignment() {
  const { batchId, experimentId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setData(null);
    instructorApi
      .assignmentContent(experimentId)
      .then((d) => !cancelled && setData(d))
      .catch((err) => {
        if (cancelled) return;
        setError(
          err.response?.status === 404
            ? "This assignment is not available."
            : "Could not load this assignment. Please try again."
        );
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [experimentId, reloadKey]);

  if (loading) return <div className="page-loading">Loading assignment…</div>;

  if (error || !data) {
    return (
      <div className="alert alert--error ic-alert">
        <span>{error || "Assignment not found."}</span>
        <button type="button" className="btn btn--sm btn--ghost" onClick={() => setReloadKey((k) => k + 1)}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="ic-header">
        <h1 className="ic-page__title">
          Experiment {data.experiment_number}: {data.experiment_title}
        </h1>
        {data.assignment && (
          <Link to={`/batches/${batchId}/assignments/${experimentId}/status`} className="btn btn--primary btn--sm">
            Assignment Status
          </Link>
        )}
      </div>

      <section className="card ic-section">
        <h2 className="ic-section__heading">Assignment</h2>
        <AnswerKey quiz={data.assignment} emptyText="No assignment available for this experiment yet." />
      </section>
    </div>
  );
}
