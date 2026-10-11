import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import Layout from "./components/Layout.jsx";

// Pages
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import ChangePassword from "./pages/ChangePassword.jsx";
import Experiments from "./pages/Experiments.jsx";
import ExperimentPage from "./pages/ExperimentPage.jsx";
import Profile from "./pages/Profile.jsx";
import StudentDashboard from "./pages/StudentDashboard.jsx";
import AssignmentScores from "./pages/AssignmentScores.jsx";
import InstructorBatches from "./pages/InstructorBatches.jsx";
import InstructorBatchWorkspace from "./pages/InstructorBatchWorkspace.jsx";
import InstructorBatchInfo from "./pages/InstructorBatchInfo.jsx";
import InstructorExperiment from "./pages/InstructorExperiment.jsx";
import InstructorExperimentStatus from "./pages/InstructorExperimentStatus.jsx";
import InstructorAssignment from "./pages/InstructorAssignment.jsx";
import InstructorAssignmentStatus from "./pages/InstructorAssignmentStatus.jsx";
import InstructorSubmission from "./pages/InstructorSubmission.jsx";
import AdminPanel from "./pages/AdminPanel.jsx";

/** Routes that require a logged-in user. Redirects to /login if not. */
function RequireAuth() {
  const { user, loading } = useAuth();
  if (loading) return <div className="page-loading">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  // If still on temporary password, send to change-password page
  if (user.must_change_password) return <Navigate to="/change-password" replace />;
  return <Outlet />;
}

/** Routes only for admin users. */
function RequireAdmin() {
  const { user } = useAuth();
  if (user?.role !== "admin") return <Navigate to="/" replace />;
  return <Outlet />;
}

/** Routes only for students (their own progress pages). */
function RequireStudent() {
  const { user } = useAuth();
  if (user?.role !== "student") return <Navigate to="/" replace />;
  return <Outlet />;
}

/** Instructor console routes: instructors only (admins and students are sent Home). */
function RequireInstructor() {
  const { user } = useAuth();
  if (user?.role !== "instructor") return <Navigate to="/" replace />;
  return <Outlet />;
}

/** Instructors see experiments only inside a batch, never through the student pages. */
function RequireNotInstructor() {
  const { user } = useAuth();
  if (user?.role === "instructor") return <Navigate to="/batches" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />
      <Route path="/change-password" element={<ChangePassword />} />

      {/* Authenticated layout */}
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route element={<RequireNotInstructor />}>
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/experiments/:slug" element={<ExperimentPage />} />
          </Route>
          <Route path="/profile" element={<Profile />} />

          {/* Student only */}
          <Route element={<RequireStudent />}>
            <Route path="/dashboard" element={<StudentDashboard />} />
            <Route path="/dashboard/assignment-scores" element={<AssignmentScores />} />
          </Route>

          {/* Instructor console (instructors only) */}
          <Route element={<RequireInstructor />}>
            <Route path="/batches" element={<InstructorBatches />} />
            <Route path="/batches/:batchId" element={<InstructorBatchWorkspace />}>
              <Route index element={<InstructorBatchInfo />} />
              <Route path="experiments/:experimentId" element={<InstructorExperiment />} />
              <Route path="experiments/:experimentId/status" element={<InstructorExperimentStatus />} />
              <Route path="assignments/:experimentId" element={<InstructorAssignment />} />
              <Route path="assignments/:experimentId/status" element={<InstructorAssignmentStatus />} />
              <Route path="assignments/:experimentId/status/:studentId" element={<InstructorSubmission />} />
            </Route>
          </Route>

          {/* Admin only */}
          <Route element={<RequireAdmin />}>
            <Route path="/admin" element={<AdminPanel />} />
          </Route>
        </Route>
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}