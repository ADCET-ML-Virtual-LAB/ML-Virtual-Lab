import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import "./Navbar.css";

const ROLE_LABEL = { student: "Student", instructor: "Instructor", admin: "Admin" };

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Close the profile menu when the page changes.
  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  // Close on outside click or Escape.
  useEffect(() => {
    if (!menuOpen) return undefined;
    function onPointerDown(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    }
    function onKeyDown(e) {
      if (e.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [menuOpen]);

  function handleLogout() {
    setMenuOpen(false);
    logout();
    navigate("/login");
  }

  const initial = (user?.full_name || "?").trim().charAt(0).toUpperCase();

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
                Home
              </NavLink>
              {user.role === "instructor" && (
                <NavLink to="/batches" className="navbar__link">
                  Batches
                </NavLink>
              )}
              {user.role !== "instructor" && (
                <NavLink to="/experiments" className="navbar__link">
                  Experiments
                </NavLink>
              )}
              {user.role === "student" && (
                <NavLink to="/dashboard" className="navbar__link">
                  View Progress
                </NavLink>
              )}
              {user.role === "admin" && (
                <NavLink to="/admin" className="navbar__link">
                  Admin
                </NavLink>
              )}

              <div className="navbar__profile" ref={menuRef}>
                <button
                  type="button"
                  className="navbar__avatar"
                  aria-haspopup="menu"
                  aria-expanded={menuOpen}
                  aria-label="Profile menu"
                  onClick={() => setMenuOpen((open) => !open)}
                >
                  {initial}
                </button>
                {menuOpen && (
                  <div className="navbar__menu" role="menu">
                    <div className="navbar__menu-header">
                      <strong>{user.full_name}</strong>
                      <span>{ROLE_LABEL[user.role] || user.role}</span>
                    </div>
                    <NavLink to="/profile" className="navbar__menu-item" role="menuitem">
                      My Profile
                    </NavLink>
                    <button
                      type="button"
                      className="navbar__menu-item navbar__menu-item--button"
                      role="menuitem"
                      onClick={handleLogout}
                    >
                      Log out
                    </button>
                  </div>
                )}
              </div>
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
