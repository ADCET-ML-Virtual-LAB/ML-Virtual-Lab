import { useState } from "react";
import Editor from "@monaco-editor/react";
import { usePyodide } from "../editor/usePyodide.js";
import { codeSubmissionsApi } from "../api/codeSubmissions.js";
import "./CodeEditor.css";

/**
 * CodeEditor — Module 6 (Client-side Code Execution Engine).
 *
 * Props:
 *   experiment    — full experiment object (id, starter_code, allowed_imports)
 *   onSubmitted   — callback called with CodeSubmissionOut after successful submit
 */
export default function CodeEditor({ experiment, onSubmitted }) {
  const [code, setCode] = useState(experiment?.starter_code || "# Write your Python code here\n");
  const { status, stdout, result, run } = usePyodide();
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);
  const [submitError, setSubmitError] = useState("");

  const isRunning = status === "loading" || status === "running";

  async function handleRun() {
    const allowedImports = experiment?.allowed_imports || [];
    await run(code, allowedImports);
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
        {result && (
          <button
            className="btn btn--ghost"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? "Submitting…" : "Submit for feedback"}
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

      {/* Note about client-side execution */}
      <p className="code-editor__note">
        Your code runs entirely in your browser via Pyodide (Python in WebAssembly). It never
        reaches our servers.
      </p>
    </div>
  );
}
