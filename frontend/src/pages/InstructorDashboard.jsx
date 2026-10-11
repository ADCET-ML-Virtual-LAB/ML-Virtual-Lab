import { useState, useEffect } from "react";
import { batchesApi } from "../api/batches.js";
import { dashboardApi } from "../api/dashboard.js";
import "./InstructorDashboard.css";

const OVERALL_LABEL = {
  not_started: "Not started",
  in_progress: "Ongoing",
  completed: "Completed",
};

const OVERALL_BADGE = {
  not_started: "badge--gray",
  in_progress: "badge--yellow",
  completed: "badge--green",
};

export default function InstructorDashboard() {
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState("");
  const [progressData, setProgressData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    batchesApi
      .list()
      .then((data) => {
        setBatches(data);
        if (data.length > 0) {
          setSelectedBatch(data[0].id);
        }
      })
      .catch(() => setError("Failed to load batches."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedBatch) return;
    setTableLoading(true);
    dashboardApi
      .instructor(selectedBatch)
      .then(setProgressData)
      .catch(() => setError("Failed to load student progress."))
      .finally(() => setTableLoading(false));
  }, [selectedBatch]);

  function handleExport() {
    if (!selectedBatch) return;
    dashboardApi.exportCsv(selectedBatch).then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const batch = batches.find(b => b.id === selectedBatch);
      a.download = `batch_${batch?.name}_${batch?.academic_year}_progress.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    });
  }

  if (loading) return <div className="page-loading">Loading dashboard…</div>;

  const activeBatch = batches.find((b) => b.id === selectedBatch);
  const experimentsList = progressData[0]?.experiments || [];

  return (
    <div className="inst-dash">
      <div className="inst-dash__header">
        <h1 className="inst-dash__title">Instructor Dashboard</h1>
      </div>

      {error && <div className="alert alert--error">{error}</div>}

      <div className="inst-dash__controls card">
        <label className="form-label inst-dash__batch-select">
          Select Batch
          <select
            className="form-select"
            value={selectedBatch}
            onChange={(e) => setSelectedBatch(e.target.value)}
          >
            {batches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} ({b.academic_year})
              </option>
            ))}
          </select>
        </label>
        
        <button
          className="btn btn--primary"
          onClick={handleExport}
          disabled={!selectedBatch || progressData.length === 0}
        >
          Export CSV
        </button>
      </div>

      <div className="inst-dash__content">
        {tableLoading ? (
          <div className="page-loading">Loading student data…</div>
        ) : progressData.length === 0 ? (
          <div className="inst-dash__empty card">
            No students enrolled in {activeBatch?.name || "this batch"} yet.
          </div>
        ) : (
          <div className="table-wrapper card">
            <table className="inst-dash__table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Roll No</th>
                  {experimentsList.map((exp) => (
                    <th key={exp.experiment_id}>{exp.experiment_title}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {progressData.map((student) => (
                  <tr key={student.student_id}>
                    <td>
                      <strong>{student.student_name}</strong>
                    </td>
                    <td>{student.roll_number || "—"}</td>
                    {student.experiments.map((exp) => (
                      <td key={exp.experiment_id}>
                        <div className="inst-dash__cell-status">
                          <span className={`badge ${OVERALL_BADGE[exp.overall_status]}`}>
                            {OVERALL_LABEL[exp.overall_status]}
                          </span>
                        </div>
                        <div className="inst-dash__cell-assignment">
                          Assignment:{" "}
                          {exp.assignment_status === "completed"
                            ? exp.assignment_score != null
                              ? `${exp.assignment_score}%`
                              : "Submitted"
                            : "Not submitted"}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="inst-dash__note">
              Overall status also counts each student's self-assessment quizzes, which are not shown here.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
