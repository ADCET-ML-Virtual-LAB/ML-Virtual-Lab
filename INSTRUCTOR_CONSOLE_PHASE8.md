# Instructor Console — Phase 8 (shell, Home, Batches, Batch section)

Frontend only. Needs the Phase 7 backend.

## What changed
- **Navbar**: instructors see Home, Batches and the profile menu (My Profile, Log out). Students are
  unchanged (Home, Experiments, View Progress). Admins see Home, Experiments, Admin; the old
  "Instructor" link is gone.
- **Home**: instructors see Virtual Lab content from `src/content/instructorHomeContent.js`
  (PLACEHOLDER text, replace it with the approved content; no React change needed).
- **Batches** (`/batches`): cards with batch name and academic year only. Empty state message when no
  batch is assigned; error state with Retry.
- **Batch workspace** (`/batches/:batchId`): header, left sidebar and content. The Batch section shows
  batch name, academic year, instructor, and the student list (URN, Name) with search, sort (click a
  column header) and pagination (10 per page). Shows empty, no-match and error states.
- **Routing**: `/batches*` is instructors only. Admins can no longer open instructor pages. Instructors
  who open `/experiments*` are sent to `/batches` (they see experiments inside a batch in the next phase).
  The old `/instructor` route is removed.

## Not in this phase
Experiments and Assignment sidebar sections, status tables, submission view and CSV downloads
(Phases 9 and 10).

## Files
New: `src/api/instructor.js`, `src/content/instructorHomeContent.js`, `src/pages/InstructorBatches.jsx`,
`src/pages/InstructorBatchWorkspace.jsx`, `src/pages/InstructorBatchInfo.jsx`, `src/pages/InstructorConsole.css`
Changed: `src/App.jsx`, `src/components/Navbar.jsx`, `src/pages/Home.jsx`, `CLAUDE.md`

## Optional cleanup
`src/pages/InstructorDashboard.jsx` and `.css` are no longer used. Delete them when you are happy:
```powershell
Remove-Item "$repo\frontend\src\pages\InstructorDashboard.jsx","$repo\frontend\src\pages\InstructorDashboard.css"
```

## Known gaps (deferred to the admin phase)
`GET /quizzes/{quiz_id}` still returns answer keys to any instructor or admin without a batch or
published check. Students never get `is_correct` from it, the student UI does not call it, and the
instructor console does not use it.

## Apply
```powershell
$repo = "D:\Virtual Lab\ML-Virtual-Lab"
$zip = "$env:USERPROFILE\Downloads\ML-Virtual-Lab-instructor-console-phase8-shell-patch.zip"
Expand-Archive -LiteralPath $zip -DestinationPath $repo -Force
cd "$repo\frontend"
npm run build
npm run dev
```
