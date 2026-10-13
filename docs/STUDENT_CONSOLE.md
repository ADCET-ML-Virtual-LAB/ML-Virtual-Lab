# Student Console

How the student console works today. The database is the source of truth for all progress: nothing is shown
as completed until the backend has saved it.

## Navigation
- Navbar: **Home**, **Experiments**, **View Progress**, and a profile icon with **My Profile** and **Log out**.
- **Home**: general Machine Learning content only (text in `frontend/src/content/homeContent.js`). It shows no progress,
  statuses or scores.
- **Experiments** (`/experiments`): cards for the published experiments, each with its fixed number (1 to 10).

## Experiment page
A left sidebar lists the sections in this fixed order, with a link back to all experiments:
1. Title / Overview
2. Aim / Learning Objectives
3. Pre-Quiz
4. Video
5. Theory / Reading Material (references go at the end of Theory)
6. Guided Lab
7. Code Exercise
8. Post-Quiz
9. Assignment

Each section shows an **empty circle** until it is complete and a **filled circle** once the saved record
confirms it. A section an experiment does not have is not counted. Section names are in
`frontend/src/constants/sections.js`.

## How each section is completed
| Section | Completed when |
|---|---|
| Title / Overview, Aim, Video, Theory, Guided Lab, Code Exercise | The student clicks **Mark Completed** and the backend has saved it. The circle changes only after the saved status is fetched back. If saving fails, the section stays incomplete and an error is shown. |
| Pre-Quiz, Post-Quiz | The quiz has been submitted at least once. No minimum score. |
| Assignment | The assignment submission has been accepted. No minimum score. |

## Pre-Quiz and Post-Quiz
- Opening the quiz first shows the experiment number, experiment title, **My Best Score** (or **Not attempted**) and
  a **Start Now** button. The questions appear only after Start Now.
- Unlimited attempts. The backend keeps one best-score record per student and quiz (no attempt history).
- After submitting, the result shows **This Attempt** and **My Best Score**; the section is completed. **Try Again**
  returns to the first screen. After switching tabs or refreshing, only the saved best score is shown.

## Code Exercise
- A Python editor that runs in the browser (Pyodide), starting with a minimal snippet in which `result` already exists.
  Students click **Run** to see the output and **Submit** to check it.
- An optional **problem statement** (set per experiment) is shown above the editor, and an optional **dataset file**
  is made available to the code (for example `pd.read_csv("Salary_dataset.csv")`).
- The answer is the value of the variable `result`. Submit sends it to the backend, which compares it with the hidden
  expected result (exact comparison) and shows **Matched** or **Mismatched**. Submitting never ticks the section.
- The section is completed with **Mark Completed**, available at any time, like Theory and Video.
- Imports are checked against the experiment's allowed libraries.

## Assignment
- One accepted submission per student; a second attempt is rejected.
- **Locked** until every earlier configured section is complete (Mark Completed sections including the Code Exercise,
  Pre-Quiz, Post-Quiz). A code match is not needed. The Assignment stays clickable. Clicking it fetches fresh status from the backend; if something is
  missing, a message lists the incomplete sections. This list is shown only after the click. The backend enforces
  the same rule on viewing and submitting.
- The score (a percentage) is shown right after submission.
- After submitting, the student can reopen the assignment and see each question with the correct answer, their own
  answer, and a Correct or Incorrect mark. The correct answers are sent only to the student who submitted, and only
  after submission.

## Experiment status
Based only on saved ticks:
- **Not Attempted**: no section is ticked.
- **In Progress**: at least one section is ticked but not all.
- **Completed**: every configured section is ticked, including the assignment.

A code submission, matched or not, is not progress.

## View Progress (`/dashboard`)
- **Overall progress**: completed sections divided by all configured sections across the published experiments, as a
  whole-number percentage (100% only when every section is complete).
- A list of the published experiments, collapsed, each showing its number, title and status. Selecting one expands
  it in place to show its sections with an empty or filled circle.
- A **View Assignment Scores** button at the top.

## Assignment Scores (`/dashboard/assignment-scores`)
A table with exactly three columns: **Experiment No.**, **Experiment Name**, **Assignment Score**. The score cell
shows the percentage, **Not Submitted**, or **Assignment not Available** if the experiment has no assignment.

## Profile (`/profile`)
Read-only: name, email, roll number (students) and role. The final fields are pending (see README, Pending work).
