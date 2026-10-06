import { NavLink } from "react-router-dom";
import "./Navbar.css";

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar__inner">
        <NavLink to="/" className="navbar__brand">
          ML Virtual Lab
        </NavLink>

        <nav className="navbar__links">
          <NavLink to="/" end className="navbar__link">
            Home
          </NavLink>
          <NavLink to="/login" className="navbar__link">
            Login
          </NavLink>
        </nav>
      </div>
    </header>
  );
}