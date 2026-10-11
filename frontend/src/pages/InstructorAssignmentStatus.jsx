import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useOutletContext, useParams } from "react-router-dom";
import { instructorApi } from "../api/instructor.js";
import DataTable from "../components/DataTable.jsx";
import { csvFileName, saveBlob } from "../utils/download.js";
import { formatScore } from "../utils/format.js";
import "./InstructorConsole.css";

// Assignment Status for one experiment: student, saved marks (percentage) or
// "Not Submitted", and a View Submission action.
export default function InstructorAssignmentStatus() {
  const { batchId, experimentId } = useParams();
  const { batch } = useOutletContext();
  const navigate = useNavigate();
  const [table, setTable] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    setTable(null);
    instructorApi
      .assignmentTable(batchId, experimentId)
      .then(setTable)
      .catch(() => setError("Could not load assignment status. Please try again."))
      .finally(() => setLoading(false));
  }, [batchId, experimentId]);

  useEffect(load, [load]);

  async function handleDownload() {
    setDownloading(true);
    setDownloadError("");
    try {
      const blob = await instructorApi.exportAssignment(batchId, experimentId);
      saveBlob(blob, csvFileName(batch, table.experiment_number, "assignment_scores"));
    } catch {
      setDownloadError("The download failed. Please try again.");
    } finally {
      setDownloading(false);
    }
  }

  if (loading) return <div className="page-loading">Loading assignment status…</div>;

  if (error || !table) {
    return (
      <div className="alert alert--error ic-alert">
        <span>{error || "Assignment status not available."}</span>
        <button type="button" className="btn btn--sm btn--ghost" onClick={load}>
          Retry
        </button>
      </div>
    );
  }

  const columns = [
    
    { key: "urn", label: "URN", value: (r) => r.urn || "", render: (r) => r.urn || "—" },
    { key: "name", label: "Name", value: (r) => r.full_name },
    {
      key: "marks",
      label: "Marks Scored",
      value: (r) => (r.submitted ? r.score : -1),
      render: (r) =>
        r.submitted ? formatScore(r.score) : <span className="ic-muted">Not Submitted</span>,
    },
    {
      key: "action",
      label: "View Submission",
      value: (r) => (r.submitted ? 1 : 0),
      render: (r) => (
        <span className="ic-tip" title={r.submitted ? undefined : "Assignment still not submitted"}>
          <button
            type="button"
            className="btn btn--sm btn--ghost"
            disabled={!r.submitted}
            onClick={() => navigate(`/batches/${batchId}/assignments/${experimentId}/status/${r.student_id}`)}
          >
            View Submission
          </button>
        </span>
      ),
    },
  ];

  return (
    <div>
      <Link to={`/batches/${batchId}/assignments/${experimentId}`} className="ic-back">
        ← Back to assignment
      </Link>
      <div className="ic-header">
        <h1 className="ic-page__title">
          Experiment {table.experiment_number}: {table.experiment_title} — Assignment Status
        </h1>
        {table.has_assignment && (
          <button type="button" className="btn btn--primary btn--sm" onClick={handleDownload} disabled={downloading}>
            {downloading ? "Preparing…" : "Download CSV"}
          </button>
        )}
      </div>

      {downloadError && <div className="alert alert--error">{downloadError}</div>}

      {!table.has_assignment ? (
        <div className="ic-empty">No assignment is available for this experiment yet.</div>
      ) : (
        <DataTable
          columns={columns}
          rows={table.rows}
          rowKey={(r) => r.student_id}
          searchText={(r) => `${r.full_name} ${r.urn || ""}`}
          searchPlaceholder="Search by name or URN"
          emptyMessage="No students are enrolled in this batch yet."
          initialSort={{ key: "urn", dir: "asc" }}
        />
      )}
    </div>
  );
}
