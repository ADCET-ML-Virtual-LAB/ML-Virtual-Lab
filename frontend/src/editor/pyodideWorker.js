/**
 * pyodideWorker.js — runs in a Web Worker so student code can't freeze the UI.
 *
 * Messages received:
 *   { type: "run", code: string, allowedImports: string[] }
 *
 * Messages sent:
 *   { type: "ready" }
 *   { type: "stdout", text: string }
 *   { type: "result", output: any, error: null }
 *   { type: "result", output: null, error: string }
 */

// We load Pyodide via importScripts so it's bundled with the worker.
// The CDN URL is replaced with the npm package at build time via Vite.
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js");

let pyodide = null;

async function initPyodide() {
  pyodide = await loadPyodide({
    stdout: (text) => self.postMessage({ type: "stdout", text }),
    stderr: (text) => self.postMessage({ type: "stdout", text }),
  });
  self.postMessage({ type: "ready" });
}

const pyodideReady = initPyodide();

self.onmessage = async (event) => {
  const { type, code, allowedImports } = event.data;
  if (type !== "run") return;

  await pyodideReady;

  // ── Import whitelist check (AST-level) ─────────────────────────────────────
  // We do a quick Python-side AST walk to block disallowed imports before
  // running anything.  This is a defence-in-depth measure; the real security
  // boundary is that code runs in the browser (sandboxed by the browser's
  // security model), not on the server.
  const allowed = allowedImports || [];
  const checkCode = `
import ast as _ast, sys as _sys

_code = ${JSON.stringify(code)}
_allowed = ${JSON.stringify(allowed)}

_tree = _ast.parse(_code)
_bad = []
for _node in _ast.walk(_tree):
    if isinstance(_node, (_ast.Import, _ast.ImportFrom)):
        for _alias in getattr(_node, 'names', []):
            _top = _alias.name.split('.')[0]
            if _top not in _allowed:
                _bad.append(_top)
        _mod = getattr(_node, 'module', None)
        if _mod:
            _top = _mod.split('.')[0]
            if _top not in _allowed:
                _bad.append(_top)

if _bad:
    raise ImportError(f"Disallowed import(s): {', '.join(set(_bad))}. Allowed: {', '.join(_allowed)}")
`;

  try {
    if (allowed.length > 0) {
      await pyodide.runPythonAsync(checkCode);
    }

    // ── Load numpy/pandas/sklearn if needed ───────────────────────────────────
    const needsMicropip = allowed.filter((m) =>
      !["builtins", "math", "statistics", "itertools", "functools", "collections", "random", "json"].includes(m)
    );
    if (needsMicropip.length > 0) {
      await pyodide.loadPackagesFromImports(code);
    }

    // ── Run the student code ──────────────────────────────────────────────────
    // We capture the last expression value as the "output" for comparison.
    const wrappedCode = `
import json as _json

_output = None
try:
    _locals = {}
    exec(${JSON.stringify(code)}, _locals)
    # Try to grab a variable named "result" or "output" if the student set one
    _output = _locals.get("result", _locals.get("output", None))
    # Serialize to something JSON-safe
    if hasattr(_output, "tolist"):
        _output = _output.tolist()
    elif hasattr(_output, "to_dict"):
        _output = _output.to_dict()
    _json.dumps(_output)  # check it's serialisable
except Exception as _e:
    raise _e
_output
`;
    const result = await pyodide.runPythonAsync(wrappedCode);
    // Convert pyodide proxies to JS values
    const jsResult = result?.toJs ? result.toJs({ dict_converter: Object.fromEntries }) : result;
    self.postMessage({ type: "result", output: jsResult, error: null });
  } catch (err) {
    self.postMessage({ type: "result", output: null, error: String(err) });
  }
};
