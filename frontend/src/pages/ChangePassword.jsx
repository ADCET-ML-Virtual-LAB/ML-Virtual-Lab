import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { authApi } from "../api/auth.js";

export default function ChangePassword() {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (newPassword !== confirm) {
      setError("Passwords do not match");
      return;
    }
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setLoading(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      await refreshUser();
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to change password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">Set your password</h1>
        <p className="auth-subtitle">
          Your account was created with a temporary password. Please set a new one before continuing.
        </p>
        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="alert alert--error">{error}</div>}
          <label className="form-label">
            Current (temporary) password
            <input
              type="password"
              className="form-input"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </label>
          <label className="form-label">
            New password
            <input
              type="password"
              className="form-input"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
            />
          </label>
          <label className="form-label">
            Confirm new password
            <input
              type="password"
              className="form-input"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
          </label>
          <button type="submit" className="btn btn--primary btn--full" disabled={loading}>
            {loading ? "Saving…" : "Set password"}
          </button>
        </form>
      </div>
    </div>
  );
}
