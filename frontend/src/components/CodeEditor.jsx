import { useState } from "react";
import Editor from "@monaco-editor/react";
import { usePyodide } from "../editor/usePyodide.js";
import { codeSubmissionsApi } from "../api/codeSubmissions.js";
import "./CodeEditor.css";

/**
 * CodeEditor — Module 6 (Client-side Code Execution Engine).
 *
 * Props:
 *   experiment    — full experiment object (id, starter_code, allowed_imports, code_dataset_url)
 *   onSubmitted   — callback called with CodeSubmissionOut after successful submit
 *   canSubmit     — false for instructors/admins: they can run code but not submit it
 */
export default function CodeEditor({ experiment, onSubmitted, canSubmit = true }) {
  const [code, setCode] = useState(experiment?.starter_code || "# Write your Python code here\n");
  const { status, stdout, result, run } = usePyodide();
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);
  const [submitError, setSubmitError] = useState("");
  const [datasetError, setDatasetError] = useState("");

  // Optional dataset file: copied into the browser's Python environment under its file name.
  const datasetUrl = experiment?.code_dataset_url || "";
  const datasetName = datasetUrl
    ? new URL(datasetUrl, window.location.origin).pathname.split("/").pop()
    : "";

  const isRunning = status === "loading" || status === "running";

  async function handleRun() {
    const allowedImports = experiment?.allowed_imports || [];
    setDatasetError("");
    let files = {};
    if (datasetUrl) {
      try {
        const res = await fetch(datasetUrl);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        files = { [datasetName]: await res.text() };
      } catch {
        setDatasetError("Could not load the dataset file. Please check your connection and try again.");
        return;
      }
    }
    await run(code, allowedImports, files);
  }

  async function handleSubmit() {
    if (!result) return;
    setSubmitting(true);
    setSubmitError("");
    try {
      const sub = await codeSubmissionsApi.submit(
        experiment.id,
        code,
        result.error ? null : result.output,
        result.error || null
      );
      setSubmitResult(sub);
      onSubmitted?.(sub);
    } catch (err) {
      setSubmitError(err.response?.data?.detail || "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  const statusLabel = {
    idle: "Ready",
    loading: "Loading Pyodide…",
    running: "Running…",
    done: "Done",
    error: "Error",
  }[status] || "Ready";

  return (
    <div className="code-editor">
      {experiment?.allowed_imports?.length > 0 && (
        <div className="code-editor__imports">
          <strong>Allowed imports:</strong>{" "}
          {experiment.allowed_imports.join(", ")}
        </div>
      )}

      {datasetName && (
        <div className="code-editor__imports">
          <strong>Dataset file:</strong> {datasetName}
        </div>
      )}

      <div className="code-editor__monaco">
        <Editor
          height="350px"
          defaultLanguage="python"
          theme="vs-dark"
          value={code}
          onChange={(val) => setCode(val || "")}
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: "on",
          }}
        />
      </div>

      <div className="code-editor__toolbar">
        <button
          className="btn btn--primary"
          onClick={handleRun}
          disabled={isRunning}
        >
          {isRunning ? statusLabel : "▶ Run"}
        </button>
        {result && canSubmit && (
          <button
            className="btn btn--ghost"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? "Submitting…" : "Submit"}
          </button>
        )}
        <span className={`code-editor__status code-editor__status--${status}`}>
          {statusLabel}
        </span>
      </div>

      {/* stdout output */}
      {(stdout.length > 0 || result) && (
        <div className="code-editor__output">
          <div className="code-editor__output-label">Output</div>
          <pre className="code-editor__stdout">
            {stdout.join("\n")}
            {result?.error && (
              <span className="code-editor__error">{"\n" + result.error}</span>
            )}
            {result && !result.error && result.output != null && (
              <span className="code-editor__result">
                {"\n→ result: " + JSON.stringify(result.output)}
              </span>
            )}
          </pre>
        </div>
      )}

      {/* Submission feedback */}
      {submitResult && (
        <div className={`alert ${submitResult.status === "matched" ? "alert--success" : submitResult.status === "error" ? "alert--error" : "alert--info"}`}>
          <strong>
            {submitResult.status === "matched" ? "✓ Matched" : submitResult.status === "error" ? "✗ Error" : "≠ Mismatched"}
          </strong>{" "}
          — {submitResult.feedback_message}
        </div>
      )}

      {submitError && <div className="alert alert--error">{submitError}</div>}
      {datasetError && <div className="alert alert--error">{datasetError}</div>}

      {!canSubmit && (
        <p className="code-editor__note">View only: instructors and admins can run code but not submit it.</p>
      )}

      {/* Note about client-side execution */}
      <p className="code-editor__note">
        Your code runs entirely in your browser via Pyodide (Python in WebAssembly). It never
        reaches our servers.
      </p>
    </div>
  );
}
