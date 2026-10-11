# Phase 6 — View Progress, Assignment Scores, submitted-assignment review, sidebar circles
No database migration.

- View Progress: overall % (completed sections / all sections, published experiments), expandable experiment list with status and section circles, "View Assignment Scores" button.
- Assignment Scores (`/dashboard/assignment-scores`): 3 columns; "Not Submitted" / "Assignment not Available".
- Reopening a submitted assignment shows questions, correct answers, the student's answers and Correct/Incorrect.
- Experiment sidebar: empty circle = not completed, filled circle = completed (students only; the locked assignment keeps its lock icon).
- Backend: `/dashboards/student` rows gain `experiment_number`, `has_assignment`, `sections`; quiz/experiment responses gain `my_review` (submitting student only, after submission).
- Shared section names: `frontend/src/constants/sections.js`.
