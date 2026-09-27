import { Routes, Route } from "react-router-dom";

// Pages — one stub per screen, fill in per the README issue breakdown.
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import ExperimentPage from "./pages/ExperimentPage.jsx";
import StudentDashboard from "./pages/StudentDashboard.jsx";
import InstructorDashboard from "./pages/InstructorDashboard.jsx";
import AdminPanel from "./pages/AdminPanel.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/experiments/:slug" element={<ExperimentPage />} />
      <Route path="/dashboard" element={<StudentDashboard />} />
      <Route path="/instructor" element={<InstructorDashboard />} />
      <Route path="/admin" element={<AdminPanel />} />
    </Routes>
  );
}
