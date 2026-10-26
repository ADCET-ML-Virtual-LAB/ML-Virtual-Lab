# Instructor Console

For instructors only: administrators and students cannot open these pages or call these endpoints. An instructor
sees only the batch they are assigned to. Each batch has exactly one instructor (enforced in the database); one
instructor can have several batches.

Instructors cannot add or edit batches, students or experiment content, and cannot attempt quizzes or submit
assignments. Students' Pre-Quiz and Post-Quiz scores are never shown to instructors. Saved assignment scores are
shown immediately, as percentages.

## Navigation
- Navbar: **Home**, **Batches**, and a profile icon with **My Profile** and **Log out**.
- **Home**: Virtual Lab content (placeholder text in `frontend/src/content/instructorHomeContent.js`).
- An instructor who opens `/experiments` is sent to `/batches`; experiments are viewed inside a batch.

## Batches (`/batches`)
Cards for the instructor's batches showing the batch name and academic year. If no batch is assigned, a message
says so. A failed load shows an error with a Retry button.

## Batch workspace (`/batches/:batchId`)
A left sidebar with three sections: **Batch**, **Experiments** and **Assignment**. Experiments and Assignment each
expand to a submenu of the published experiments (`1. Title ...` and `Assignment 1 ...`).

### Batch (default)
Batch name, academic year and instructor, then the enrolled students with **URN** and **Name**. The list has search
(name or URN), sorting by clicking a column header, and pagination (25 per page).

### Experiments
Opening an experiment shows its number and title and the same sections and content as the student page, without
Guided Lab and Code Exercise: Title / Overview, Aim / Learning Objectives, Pre-Quiz, Video, Theory / Reading
Material, Post-Quiz and Assignment. The quizzes and the assignment show every question with the correct answer
marked; nothing can be attempted.

The **Students Status** button (top right) opens a table of **URN**, **Name** and **Status**
(Not Attempted, In Progress or Completed, using the student status rule) with search, sorting and 25 rows per page.
No section-level detail is shown. **Download Excel** exports this table for the open experiment only.

### Assignment
Opening an assignment shows the experiment number and title only, then the assignment questions with the correct
answers marked. If the experiment has no assignment, a message says so.

The **Assignment Status** button (top right) opens a table with four columns: **URN**, **Name**, **Marks Scored**
(percentage, or Not Submitted) and **View Submission**. It has search, sorting and 25 rows per page. For a student who
has not submitted, the button is disabled and its hover text says the assignment is still not submitted.
**Download Excel** exports this table for the open assignment only.

**View Submission** opens a page with the experiment number and title, the student, their URN and marks secured, then
every question with the correct answer, the student's answer and a Correct or Incorrect mark.

## Excel downloads
Both downloads are `.xlsx` files. Batch, Academic Year, Experiment No. and Experiment Name sit in merged rows at the
top, followed by a table: URN, Student Name and Status (or Marks (%) for assignments). File names:
`batch_<name>_<year>_experiment_<n>_status.xlsx` and `batch_<name>_<year>_experiment_<n>_assignment_scores.xlsx`.

## States
All pages show loading and error states (with Retry where it applies), and empty-state messages for no batches,
no students, no matching search results, no experiments and no assignment.

## API
All endpoints are under `/instructor` (see `openapi.yaml`). They require the instructor role and check that the batch
belongs to the instructor.

| Endpoint | Purpose |
|---|---|
| `GET /instructor/batches` | The instructor's batches |
| `GET /instructor/batches/{batch_id}` | Batch information and students |
| `GET /instructor/experiments` | Published experiments |
| `GET /instructor/experiments/{experiment_id}` | Read-only content with answer keys |
| `GET /instructor/experiments/{experiment_id}/assignment` | Assignment questions with answers |
| `GET /instructor/batches/{batch_id}/experiments/{experiment_id}/status` | Students Status table |
| `GET .../status/export` | Excel download of the Students Status table |
| `GET .../assignment-status` | Assignment Status table |
| `GET .../assignment-status/export` | Excel download of the Assignment Status table |
| `GET .../assignment-status/{student_id}` | One student's submission with correctness |
