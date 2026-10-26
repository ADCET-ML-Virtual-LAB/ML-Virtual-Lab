import { useCallback, useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";
import { instructorApi } from "../api/instructor.js";
import DataTable from "../components/DataTable.jsx";
import { excelFileName, saveBlob } from "../utils/download.js";
import "./InstructorConsole.css";

const STATUS = {
  not_started: { label: "Not Attempted", badge: "badge--gray", rank: 0 },
  in_progress: { label: "In Progress", badge: "badge--yellow", rank: 1 },
  completed: { label: "Completed", badge: "badge--green", rank: 2 },
};

const COLUMNS = [
  { key: "urn", label: "URN", value: (r) => r.urn || "" , render: (r) => r.urn || "—" },
  { key: "name", label: "Name", value: (r) => r.full_name },
  {
    key: "status",
    label: "Status",
    value: (r) => STATUS[r.status].rank,
    render: (r) => <span className={`badge ${STATUS[r.status].badge}`}>{STATUS[r.status].label}</span>,
  },
];

// Students Status for one experiment: Not Attempted / In Progress / Completed per student.
export default function InstructorExperimentStatus() {
  const { batchId, experimentId } = useParams();
  const { batch } = useOutletContext();
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
      .statusTable(batchId, experimentId)
      .then(setTable)
      .catch(() => setError("Could not load student statuses. Please try again."))
      .finally(() => setLoading(false));
  }, [batchId, experimentId]);

  useEffect(load, [load]);

  async function handleDownload() {
    setDownloading(true);
    setDownloadError("");
    try {
      const blob = await instructorApi.exportStatus(batchId, experimentId);
      saveBlob(blob, excelFileName(batch, table.experiment_number, "status"));
    } catch {
      setDownloadError("The download failed. Please try again.");
    } finally {
      setDownloading(false);
    }
  }

  if (loading) return <div className="page-loading">Loading student statuses…</div>;

  if (error || !table) {
    return (
      <div className="alert alert--error ic-alert">
        <span>{error || "Status not available."}</span>
        <button type="button" className="btn btn--sm btn--ghost" onClick={load}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <Link to={`/batches/${batchId}/experiments/${experimentId}`} className="ic-back">
        ← Back to experiment
      </Link>
      <div className="ic-header">
        <h1 className="ic-page__title">
          Experiment {table.experiment_number}: {table.experiment_title} — Students Status
        </h1>
        <button type="button" className="btn btn--primary btn--sm" onClick={handleDownload} disabled={downloading}>
          {downloading ? "Preparing…" : "Download Excel"}
        </button>
      </div>

      {downloadError && <div className="alert alert--error">{downloadError}</div>}

      <DataTable
        columns={COLUMNS}
        rows={table.rows}
        rowKey={(r) => r.student_id}
        searchText={(r) => `${r.full_name} ${r.urn || ""}`}
        searchPlaceholder="Search by name or URN"
        emptyMessage="No students are enrolled in this batch yet."
        initialSort={{ key: "urn", dir: "asc" }}
      />
    </div>
  );
}
