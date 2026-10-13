# Development History

What was built, in order. Each step that changed the database came with a one-off script in `backend/scripts/`
(see the README, "Upgrading an existing database").

## Student console
1. **Section completion**: `SectionCompletion` table and **Mark Completed** saved in the database; Title / Overview
   section with `experiments.overview`; assignment prerequisites include the manual sections and Guided Lab.
   (`migrate_student_section_tracking`)
2. **Quiz best score**: Pre-Quiz and Post-Quiz keep one best-score record per student and quiz in
   `student_quiz_progress`; no attempt history. (`migrate_quiz_best_score_only`)
3. **Quiz screens**: Start Now screen, This Attempt versus My Best Score, completion tick after the saved status is
   fetched back.
4. **Fixes**: Code Exercise tick and saved state restored; the Assignment click re-fetches status from the backend;
   the experiment status rule based on ticks only; experiment numbers fixed to 1 to 10 (`order_index`, unique).
5. **Code editor fixes**: valid `from ... import ...` lines accepted; `if __name__ == "__main__":` blocks run; the
   button reads Submit.
6. **Navigation**: new navbar with profile menu, Home page, Experiments page, left sidebar inside an experiment,
   read-only Profile page.
7. **Progress**: View Progress with overall percentage and expandable experiments, Assignment Scores page, circles
   instead of ticks, review of a submitted assignment (correct answer, own answer, Correct/Incorrect).

## Instructor console
8. **Backend**: instructor-only `/instructor/*` API, one instructor per batch (unique `batch_id`; a second assignment
   returns 409), admins removed from instructor endpoints, instructor tests. (`migrate_one_instructor_per_batch`)
9. **Shell**: instructor navbar, Home, Batches cards, batch workspace with Batch information and student list.
10. **Experiments section**: sidebar submenu, read-only experiment content with answer keys, Students Status table.
11. **Assignment section**: assignment page, Assignment Status table, submission page.
12. **Excel downloads**: both downloads are `.xlsx` with merged detail rows on top (`openpyxl`).
13. Shared helpers: `utils/contentFormat.js` (video links and theory text for both consoles), `DataTable`
    (search, sorting, 25 per page), `AnswerKey`.

## Content
14. **Code Exercise problem statement**: optional `experiments.code_problem_statement`, shown above the editor.
    (`migrate_code_problem_statement`)
15. **Linear Regression experiment**: loaded as experiment 8 with `scripts/load_linear_regression.py`
    (Pre-Quiz, Post-Quiz and Assignment of 10 questions each; Code Exercise on the Salary dataset with
    `random_state=42`, answer stored in `result`).
16. **Code Exercise by Mark Completed**: the Code Exercise is completed with Mark Completed like Theory and Video and counts
    for every experiment; Submit only shows Matched or Mismatched, and a code match is no longer needed to unlock the
    Assignment. The editor starts with a minimal snippet (`result = None`). Experiments can name a dataset file
    (`experiments.code_dataset_url`) that is copied into the browser's Python environment; the Linear Regression dataset is
    `frontend/public/datasets/Salary_dataset.csv`. (`migrate_code_dataset_url`)
