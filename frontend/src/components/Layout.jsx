import { Outlet } from "react-router-dom";
import Navbar from "./Navbar.jsx";
import "./Layout.css";

export default function Layout() {
  return (
    <>
      <Navbar />
      <main className="layout__main">
        <Outlet />
      </main>
    </>
  );
}