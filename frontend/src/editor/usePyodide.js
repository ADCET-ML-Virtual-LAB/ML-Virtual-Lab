import { useState, useRef, useCallback } from "react";

/**
 * usePyodide — manages the lifecycle of the Pyodide Web Worker.
 *
 * Returns:
 *   { status, stdout, run, reset }
 *
 * status: "idle" | "loading" | "ready" | "running" | "done" | "error"
 */
export function usePyodide() {
  const workerRef = useRef(null);
  const [status, setStatus] = useState("idle");
  const [stdout, setStdout] = useState([]);
  const [result, setResult] = useState(null); // { output, error }

  function ensureWorker() {
    if (workerRef.current) return workerRef.current;

    // Create worker using Vite's worker import syntax
    const worker = new Worker(
      new URL("./pyodideWorker.js", import.meta.url),
      { type: "classic" }
    );
    workerRef.current = worker;
    return worker;
  }

  const run = useCallback((code, allowedImports) => {
    return new Promise((resolve, reject) => {
      setStdout([]);
      setResult(null);
      setStatus("loading");

      const worker = ensureWorker();

      function handleMessage(e) {
        const { type, text, output, error } = e.data;
        if (type === "ready") {
          setStatus("running");
          worker.postMessage({ type: "run", code, allowedImports });
        } else if (type === "stdout") {
          setStdout((prev) => [...prev, text]);
        } else if (type === "result") {
          worker.removeEventListener("message", handleMessage);
          setStatus(error ? "error" : "done");
          setResult({ output, error });
          resolve({ output, error });
        }
      }

      worker.addEventListener("message", handleMessage);

      // If worker is already ready (not first run), kick off directly
      if (status === "ready" || status === "done" || status === "error") {
        setStatus("running");
        worker.postMessage({ type: "run", code, allowedImports });
        // Remove the ready listener above and rely only on result
      }
    });
  }, [status]);

  const reset = useCallback(() => {
    if (workerRef.current) {
      workerRef.current.terminate();
      workerRef.current = null;
    }
    setStatus("idle");
    setStdout([]);
    setResult(null);
  }, []);

  return { status, stdout, result, run, reset };
}
