import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import "./Navbar.css";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="navbar">
      <div className="navbar__inner">
        <NavLink to="/" className="navbar__brand">
          ML Virtual Lab
        </NavLink>

        <nav className="navbar__links">
          {user ? (
            <>
              <NavLink to="/" end className="navbar__link">
                Experiments
              </NavLink>
              <NavLink to="/dashboard" className="navbar__link">
                My Progress
              </NavLink>
              {(user.role === "instructor" || user.role === "admin") && (
                <NavLink to="/instructor" className="navbar__link">
                  Instructor
                </NavLink>
              )}
              {user.role === "admin" && (
                <NavLink to="/admin" className="navbar__link">
                  Admin
                </NavLink>
              )}
              <span className="navbar__user">{user.full_name}</span>
              <button onClick={handleLogout} className="btn btn--ghost btn--sm">
                Log out
              </button>
            </>
          ) : (
            <NavLink to="/login" className="navbar__link">
              Log in
            </NavLink>
          )}
        </nav>
      </div>
    </header>
  );
}