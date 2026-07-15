import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/log-interaction", label: "Log Interaction" },
  { to: "/hcps", label: "HCP Directory" },
];

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        Field<span>Copilot</span>
      </div>
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.end}
          className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
        >
          {link.label}
        </NavLink>
      ))}
    </nav>
  );
}
