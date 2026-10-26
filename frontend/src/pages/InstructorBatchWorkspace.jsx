import { useCallback, useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useParams } from "react-router-dom";
import { instructorApi } from "../api/instructor.js";
import "./InstructorConsole.css";

// One batch, opened fully: header, left sidebar and the selected section.
// Sections: Batch (default), Experiments and Assignment (each with a submenu of the
// published experiments).
function SidebarGroup({ label, open, onToggle, active, error, onRetry, experiments, linkFor, linkLabel }) {
  return (
    <>
      <button
        type="button"
        className={`ic-sidebar__link ic-sidebar__group${active ? " active" : ""}`}
        aria-expanded={open}
        onClick={onToggle}
      >
        <span>{label}</span>
        <span aria-hidden="true">{open ? "▾" : "▸"}</span>
      </button>
      {open && (
        <div className="ic-sidebar__submenu">
          {error && (
            <button type="button" className="ic-sidebar__note" onClick={onRetry}>
              Could not load experiments. Retry
            </button>
          )}
          {!error && experiments.length === 0 && (
            <span className="ic-sidebar__note">No experiments published yet.</span>
          )}
          {experiments.map((e) => (
            <NavLink key={e.id} to={linkFor(e)} className="ic-sidebar__sublink">
              {linkLabel(e)}
            </NavLink>
          ))}
        </div>
      )}
    </>
  );
}

export default function InstructorBatchWorkspace() {
  const { batchId } = useParams();
  const location = useLocation();
  const [batch, setBatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [experiments, setExperiments] = useState([]);
  const [experimentsError, setExperimentsError] = useState(false);
  const [experimentsOpen, setExperimentsOpen] = useState(false);
  const [assignmentsOpen, setAssignmentsOpen] = useState(false);

  const loadExperiments = useCallback(() => {
    setExperimentsError(false);
    instructorApi
      .experiments()
      .then(setExperiments)
      .catch(() => setExperimentsError(true));
  }, []);

  useEffect(loadExperiments, [loadExperiments]);

  // Keep a submenu open while one of its pages is showing.
  const insideExperiments = location.pathname.includes(`/batches/${batchId}/experiments/`);
  const insideAssignments = location.pathname.includes(`/batches/${batchId}/assignments/`);
  useEffect(() => {
    if (insideExperiments) setExperimentsOpen(true);
  }, [insideExperiments]);
  useEffect(() => {
    if (insideAssignments) setAssignmentsOpen(true);
  }, [insideAssignments]);

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    setBatch(null);
    instructorApi
      .batch(batchId)
      .then(setBatch)
      .catch((err) => {
        const code = err.response?.status;
        setError(
          code === 403 || code === 404
            ? "This batch is not available to you."
            : "Could not load this batch. Please try again."
        );
      })
      .finally(() => setLoading(false));
  }, [batchId]);

  useEffect(load, [load]);

  if (loading) return <div className="page-loading">Loading batch…</div>;

  if (error || !batch) {
    return (
      <div className="ic-page">
        <Link to="/batches" className="ic-back">← All batches</Link>
        <div className="alert alert--error ic-alert">
          <span>{error || "Batch not found."}</span>
          <button type="button" className="btn btn--sm btn--ghost" onClick={load}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="ic-workspace">
      <aside className="ic-sidebar">
        <Link to="/batches" className="ic-back">← All batches</Link>
        <div className="ic-sidebar__batch">
          <strong>{batch.name}</strong>
          <span>{batch.academic_year}</span>
        </div>
        <nav className="ic-sidebar__nav">
          <NavLink to={`/batches/${batchId}`} end className="ic-sidebar__link">
            Batch
          </NavLink>

          <SidebarGroup
            label="Experiments"
            open={experimentsOpen}
            onToggle={() => setExperimentsOpen((o) => !o)}
            active={insideExperiments}
            error={experimentsError}
            onRetry={loadExperiments}
            experiments={experiments}
            linkFor={(e) => `/batches/${batchId}/experiments/${e.id}`}
            linkLabel={(e) => `${e.number}. ${e.title}`}
          />
          <SidebarGroup
            label="Assignment"
            open={assignmentsOpen}
            onToggle={() => setAssignmentsOpen((o) => !o)}
            active={insideAssignments}
            error={experimentsError}
            onRetry={loadExperiments}
            experiments={experiments}
            linkFor={(e) => `/batches/${batchId}/assignments/${e.id}`}
            linkLabel={(e) => `Assignment ${e.number}`}
          />
        </nav>
      </aside>

      <section className="ic-content">
        <Outlet context={{ batch }} />
      </section>
    </div>
  );
}
