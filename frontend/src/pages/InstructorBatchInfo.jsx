import { useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import "./InstructorConsole.css";

const PAGE_SIZE = 25;

// Batch section: batch information and the enrolled students (URN and name).
// Search, sort and pagination run in the browser on the loaded roster.
export default function InstructorBatchInfo() {
  const { batch } = useOutletContext();
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState({ key: "urn", dir: "asc" });
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const rows = batch.students.filter(
      (s) =>
        !q ||
        s.full_name.toLowerCase().includes(q) ||
        (s.urn || "").toLowerCase().includes(q)
    );
    const factor = sort.dir === "asc" ? 1 : -1;
    return [...rows].sort((a, b) => {
      const av = (sort.key === "urn" ? a.urn || "" : a.full_name).toLowerCase();
      const bv = (sort.key === "urn" ? b.urn || "" : b.full_name).toLowerCase();
      return av.localeCompare(bv, undefined, { numeric: true }) * factor;
    });
  }, [batch.students, query, sort]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const current = Math.min(page, pageCount);
  const start = (current - 1) * PAGE_SIZE;
  const visible = filtered.slice(start, start + PAGE_SIZE);

  function toggleSort(key) {
    setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" }));
    setPage(1);
  }

  function arrow(key) {
    if (sort.key !== key) return "";
    return sort.dir === "asc" ? " ▲" : " ▼";
  }

  return (
    <div>
      <h1 className="ic-page__title">Batch</h1>

      <div className="card ic-info">
        <div className="ic-info__item">
          <span className="ic-info__label">Batch name</span>
          <span>{batch.name}</span>
        </div>
        <div className="ic-info__item">
          <span className="ic-info__label">Academic year</span>
          <span>{batch.academic_year}</span>
        </div>
        <div className="ic-info__item">
          <span className="ic-info__label">Instructor</span>
          <span>{batch.instructor_name}</span>
        </div>
      </div>

      <h2 className="ic-section-title">Students</h2>

      {batch.students.length === 0 ? (
        <div className="ic-empty">No students are enrolled in this batch yet.</div>
      ) : (
        <>
          <input
            type="search"
            className="form-input ic-search"
            placeholder="Search by name or URN"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
            aria-label="Search students by name or URN"
          />

          <div className="ic-table-wrap">
            <table className="ic-table">
              <thead>
                <tr>
                  <th>
                    <button type="button" className="ic-sort" onClick={() => toggleSort("urn")}>
                      URN{arrow("urn")}
                    </button>
                  </th>
                  <th>
                    <button type="button" className="ic-sort" onClick={() => toggleSort("name")}>
                      Name{arrow("name")}
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {visible.length === 0 ? (
                  <tr>
                    <td colSpan={2} className="ic-table__empty">
                      No students match your search.
                    </td>
                  </tr>
                ) : (
                  visible.map((s) => (
                    <tr key={s.id}>
                      <td>{s.urn || "—"}</td>
                      <td>{s.full_name}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {filtered.length > 0 && (
            <div className="ic-pager">
              <span>
                Showing {start + 1}–{start + visible.length} of {filtered.length}
              </span>
              <div className="ic-pager__buttons">
                <button
                  type="button"
                  className="btn btn--sm btn--ghost"
                  disabled={current === 1}
                  onClick={() => setPage(current - 1)}
                >
                  Previous
                </button>
                <span>
                  Page {current} of {pageCount}
                </span>
                <button
                  type="button"
                  className="btn btn--sm btn--ghost"
                  disabled={current === pageCount}
                  onClick={() => setPage(current + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
