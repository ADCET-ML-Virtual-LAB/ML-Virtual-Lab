import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { instructorApi } from "../api/instructor.js";
import { formatScore } from "../utils/format.js";
import "./InstructorConsole.css";

// One student's submitted assignment: marks at the top, then every question with
// the correct answer, the student's answer and a correct/incorrect mark.
export default function InstructorSubmission() {
  const { batchId, experimentId, studentId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    setData(null);
    instructorApi
      .submission(batchId, experimentId, studentId)
      .then(setData)
      .catch((err) =>
        setError(
          err.response?.status === 404
            ? "This submission is not available. The assignment may not be submitted yet."
            : "Could not load this submission. Please try again."
        )
      )
      .finally(() => setLoading(false));
  }, [batchId, experimentId, studentId]);

  useEffect(load, [load]);

  const back = (
    <Link to={`/batches/${batchId}/assignments/${experimentId}/status`} className="ic-back">
      ← Back to assignment status
    </Link>
  );

  if (loading) return <div className="page-loading">Loading submission…</div>;

  if (error || !data) {
    return (
      <div>
        {back}
        <div className="alert alert--error ic-alert">
          <span>{error || "Submission not found."}</span>
          <button type="button" className="btn btn--sm btn--ghost" onClick={load}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      {back}
      <h1 className="ic-page__title">
        Experiment {data.experiment_number}: {data.experiment_title}
      </h1>

      <div className="card ic-info">
        <div className="ic-info__item">
          <span className="ic-info__label">Student</span>
          <span>{data.student.full_name}</span>
        </div>
        <div className="ic-info__item">
          <span className="ic-info__label">URN</span>
          <span>{data.student.urn || "—"}</span>
        </div>
        <div className="ic-info__item">
          <span className="ic-info__label">Marks secured</span>
          <strong>{data.score == null ? "—" : formatScore(data.score)}</strong>
        </div>
      </div>

      <ol className="ic-quiz ic-submission">
        {data.questions.map((q) => (
          <li key={q.question_id} className="ic-quiz__question">
            <div className="ic-quiz__head">
              <p className="ic-quiz__text">{q.question_text}</p>
              <span className={`badge ${q.is_correct ? "badge--green" : "badge--red"}`}>
                {q.is_correct ? "Correct" : "Incorrect"}
              </span>
            </div>
            <ul className="ic-quiz__options">
              {q.options.map((o) => {
                const chosen = o.id === q.selected_option_id;
                const cls = [
                  "ic-quiz__option",
                  o.is_correct ? "ic-quiz__option--correct" : "",
                  chosen && !o.is_correct ? "ic-quiz__option--wrong" : "",
                ].join(" ");
                return (
                  <li key={o.id} className={cls}>
                    <span>{o.option_text}</span>
                    <span className="ic-quiz__tags">
                      {chosen && <span className="badge badge--blue">Student's answer</span>}
                      {o.is_correct && <span className="badge badge--green">Correct answer</span>}
                    </span>
                  </li>
                );
              })}
            </ul>
            {q.selected_option_id == null && <p className="ic-muted">No answer was recorded for this question.</p>}
          </li>
        ))}
      </ol>
    </div>
  );
}
