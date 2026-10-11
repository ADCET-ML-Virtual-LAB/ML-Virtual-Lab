# Instructor Console — Phase 10 (Assignment section)

Frontend only. Uses the Phase 7 endpoints.

## What changed
- **Sidebar**: new "Assignment" group listing `Assignment 1 … N` (published experiments).
- **Assignment page** (`/batches/:batchId/assignments/:experimentId`): experiment number and title only, then the
  questions with the correct answers marked. **Assignment Status** button top right.
- **Assignment Status** (`.../status`): three columns — Student (name, URN underneath), Marks Scored (percentage or
  "Not Submitted"), View Submission. The button is disabled for "Not Submitted" with the hover text
  "Assignment still not submitted". Search by name or URN, sortable headers, 25 per page, **Download CSV**
  for this assignment only.
- **Submission page** (`.../status/:studentId`): experiment number and title, student, URN and marks secured at the
  top; each question shows the options with the correct answer, the student's answer and a Correct / Incorrect mark.
- Loading, error (with Retry) and empty states on all three pages. An experiment without an assignment shows
  "No assignment available" and hides the status and download buttons.

## Files
New: `src/pages/InstructorAssignment.jsx`, `src/pages/InstructorAssignmentStatus.jsx`,
`src/pages/InstructorSubmission.jsx`, `src/utils/format.js`
Changed: `src/App.jsx`, `src/api/instructor.js`, `src/pages/InstructorBatchWorkspace.jsx`,
`src/pages/InstructorConsole.css`

## Apply
```powershell
$repo = "D:\Virtual Lab\ML-Virtual-Lab"
$zip = "$env:USERPROFILE\Downloads\ML-Virtual-Lab-instructor-console-phase10-assignment-patch.zip"
Expand-Archive -LiteralPath $zip -DestinationPath $repo -Force
cd "$repo\frontend"
npm run build
npm run dev
```
