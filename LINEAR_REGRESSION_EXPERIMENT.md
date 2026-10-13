# Linear Regression experiment (experiment number 8) + Code Exercise problem statement

Includes the earlier "problem statement" patch, so apply only this zip.

## What it does
- Adds an optional `code_problem_statement` to experiments; shown above the code editor in the student's
  Code Exercise section (migration: `migrate_code_problem_statement`).
- `scripts/load_linear_regression.py` replaces the demo experiment numbered 8 with Linear Regression
  (slug `linear-regression-experiment`). Other experiments are untouched. Safe to re-run.
- Content lives in `scripts/linear_regression_content.py` (edit there and re-run the loader).
- Overview = Home Overview and Basic Details overview combined. Learning objectives are written as one sentence
  (the Aim section shows them in a paragraph). References are added at the end of Theory.
- Pre-Quiz, Post-Quiz, Assignment: 10 questions each, one correct option each. Assignment has no deadline
  and the score is shown immediately.
- Code Exercise: the student stores the rounded predictions for the test subset in `result`
  (LinearRegression, `train_test_split(test_size=0.2, random_state=42)`). Expected result, matched exactly:
  `[115791.21, 71499.28, 102597.87, 75268.8, 55478.79, 60190.7]`
- No Guided Lab content for this experiment.

## Apply
```powershell
$repo = "D:\Virtual Lab\ML-Virtual-Lab"
$zip = "$env:USERPROFILE\Downloads\ML-Virtual-Lab-linear-regression-experiment-patch.zip"
Expand-Archive -LiteralPath $zip -DestinationPath $repo -Force
cd "$repo\backend"
.\venv\Scripts\Activate.ps1
python -m scripts.migrate_code_problem_statement
python -m pytest -q
python -m scripts.load_linear_regression
cd "$repo\frontend"
npm run build
```
