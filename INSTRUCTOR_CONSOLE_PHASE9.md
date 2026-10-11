# Instructor Console — Phase 9 (Experiments section)

Frontend only. Uses the Phase 7 endpoints.

## What changed
- **Sidebar**: "Experiments" expands to the published experiments (`N. Title`). It stays open while an
  experiment page is showing.
- **Experiment page** (`/batches/:batchId/experiments/:experimentId`): read-only content with section tabs in
  the student order, without Guided Lab and Code Exercise: Title / Overview, Aim / Learning Objectives,
  Pre-Quiz, Video, Theory / Reading Material, Post-Quiz, Assignment. Quizzes and the assignment show
  every question with the correct answer marked; nothing can be attempted. **Students Status** button
  top right.
- **Students Status** (`.../status`): URN, Name, Status (Not Attempted / In Progress / Completed) with search by
  name or URN, sortable headers, 25 rows per page, and **Download CSV** for this experiment only.
- Loading, error (with Retry) and empty states on both pages.

## Files
New: `src/pages/InstructorExperiment.jsx`, `src/pages/InstructorExperimentStatus.jsx`,
`src/components/AnswerKey.jsx`, `src/components/DataTable.jsx`, `src/utils/contentFormat.js`,
`src/utils/download.js`
Changed: `src/App.jsx`, `src/api/instructor.js`, `src/pages/InstructorBatchWorkspace.jsx`,
`src/pages/InstructorConsole.css`, `src/pages/ExperimentPage.jsx`

`ExperimentPage.jsx` (student) changed only to import `toEmbedUrl` and `simpleMarkdown` from the new
shared `utils/contentFormat.js` instead of defining them itself. No behaviour change.

## Apply
```powershell
$repo = "D:\Virtual Lab\ML-Virtual-Lab"
$zip = "$env:USERPROFILE\Downloads\ML-Virtual-Lab-instructor-console-phase9-experiments-patch.zip"
Expand-Archive -LiteralPath $zip -DestinationPath $repo -Force
cd "$repo\frontend"
npm run build
npm run dev
```
