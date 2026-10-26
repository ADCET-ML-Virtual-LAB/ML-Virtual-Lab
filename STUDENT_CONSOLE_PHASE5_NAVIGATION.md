# Phase 5 — Navigation, Home, Experiments page, left sidebar, Profile
Frontend only. No backend change, no migration.

- Navbar: Home, Experiments, View Progress (students), profile icon menu (My Profile, Log out). Instructor/Admin keep their existing links until their phases.
- Home: general ML content only, edited in `frontend/src/content/homeContent.js` (DRAFT text — replace with the approved content).
- Experiments page (`/experiments`): the list of experiments; each opens its workspace.
- Experiment workspace: left sidebar (all sections in the approved order, ticks from saved backend state, assignment lock behaviour unchanged) replaces the tabs.
- Profile (`/profile`): read-only name, email, roll no. (students), role. Final fields still to be decided.
