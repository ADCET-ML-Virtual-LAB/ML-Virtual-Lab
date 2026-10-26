# Phase 4b — Code editor fixes
- Import check: `from sklearn.linear_model import LinearRegression` was wrongly rejected (the imported name was checked as a module). Now only the module is checked.
- `if __name__ == "__main__":` blocks (used in the starter code) now run.
- Button renamed from "Submit for feedback" to "Submit".
Not changed: how the expected result is defined/compared (waiting for the real expected results).
