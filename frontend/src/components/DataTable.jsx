import { useMemo, useState } from "react";

const PAGE_SIZE = 25;

function compare(a, b) {
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).toLowerCase().localeCompare(String(b).toLowerCase(), undefined, { numeric: true });
}

/**
 * Table with search, click-to-sort headers and pagination (25 per page).
 *
 * columns: [{ key, label, value(row) -> string|number used for sorting, render?(row) }]
 * searchText(row) -> the text the search box matches against.
 * Search, sort and paging run in the browser on the loaded rows.
 */
export default function DataTable({
  columns,
  rows,
  rowKey,
  searchText,
  searchPlaceholder,
  emptyMessage,
  initialSort,
  pageSize = PAGE_SIZE,
}) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState(initialSort || { key: columns[0].key, dir: "asc" });
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const matching = q ? rows.filter((row) => searchText(row).toLowerCase().includes(q)) : rows;
    const column = columns.find((c) => c.key === sort.key);
    if (!column) return matching;
    const factor = sort.dir === "asc" ? 1 : -1;
    return [...matching].sort((a, b) => compare(column.value(a), column.value(b)) * factor);
  }, [rows, query, sort, columns, searchText]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const current = Math.min(page, pageCount);
  const start = (current - 1) * pageSize;
  const visible = filtered.slice(start, start + pageSize);

  function toggleSort(key) {
    setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" }));
    setPage(1);
  }

  if (rows.length === 0) return <div className="ic-empty">{emptyMessage}</div>;

  return (
    <>
      <input
        type="search"
        className="form-input ic-search"
        placeholder={searchPlaceholder}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setPage(1);
        }}
        aria-label={searchPlaceholder}
      />

      <div className="ic-table-wrap">
        <table className="ic-table">
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key}>
                  <button type="button" className="ic-sort" onClick={() => toggleSort(c.key)}>
                    {c.label}
                    {sort.key === c.key ? (sort.dir === "asc" ? " ▲" : " ▼") : ""}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="ic-table__empty">
                  No students match your search.
                </td>
              </tr>
            ) : (
              visible.map((row) => (
                <tr key={rowKey(row)}>
                  {columns.map((c) => (
                    <td key={c.key}>{c.render ? c.render(row) : c.value(row)}</td>
                  ))}
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
            <button type="button" className="btn btn--sm btn--ghost" disabled={current === 1} onClick={() => setPage(current - 1)}>
              Previous
            </button>
            <span>
              Page {current} of {pageCount}
            </span>
            <button type="button" className="btn btn--sm btn--ghost" disabled={current === pageCount} onClick={() => setPage(current + 1)}>
              Next
            </button>
          </div>
        </div>
      )}
    </>
  );
}
