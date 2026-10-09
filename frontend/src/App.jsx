import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import Layout from "./components/Layout.jsx";

// Pages
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import ChangePassword from "./pages/ChangePassword.jsx";
import ExperimentPage from "./pages/ExperimentPage.jsx";
import StudentDashboard from "./pages/StudentDashboard.jsx";
import InstructorDashboard from "./pages/InstructorDashboard.jsx";
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

/** Routes for admin and instructor only. */
function RequireInstructorOrAdmin() {
  const { user } = useAuth();
  if (!user || (user.role !== "admin" && user.role !== "instructor"))
    return <Navigate to="/" replace />;
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
          <Route path="/experiments/:slug" element={<ExperimentPage />} />
          <Route path="/dashboard" element={<StudentDashboard />} />

          {/* Instructor + Admin */}
          <Route element={<RequireInstructorOrAdmin />}>
            <Route path="/instructor" element={<InstructorDashboard />} />
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