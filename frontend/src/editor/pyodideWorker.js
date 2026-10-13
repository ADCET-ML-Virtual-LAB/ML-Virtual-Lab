/**
 * pyodideWorker.js — runs in a Web Worker so student code can't freeze the UI.
 *
 * Messages received:
 *   { type: "run", code: string, allowedImports: string[], files?: { [name]: text } }
 *   files are written into the working directory before the code runs, so the student's
 *   code can read them (for example pd.read_csv("Salary_dataset.csv")).
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
  const { type, code, allowedImports, files } = event.data;
  if (type !== "run") return;

  await pyodideReady;

  // Make the experiment's dataset file(s) available to the student's code.
  for (const [name, text] of Object.entries(files || {})) {
    pyodide.FS.writeFile(name, text);
  }

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
    if isinstance(_node, _ast.Import):
        # "import numpy as np": each alias is a module name.
        for _alias in _node.names:
            _top = _alias.name.split('.')[0]
            if _top not in _allowed:
                _bad.append(_top)
    elif isinstance(_node, _ast.ImportFrom):
        # "from sklearn.linear_model import LinearRegression": only the module
        # (sklearn.linear_model) is checked. The imported names are not modules.
        if _node.level == 0 and _node.module:
            _top = _node.module.split('.')[0]
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
    # Run as a script: "if __name__ == '__main__':" blocks must execute.
    _locals = {"__name__": "__main__"}
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
