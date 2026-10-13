import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { setToken } from "../api";

const links = [
  { to: "/", label: "Board", end: true },
  { to: "/add", label: "Add job" },
  { to: "/resume", label: "Resume" },
  { to: "/dashboard", label: "Insights" },
];

export default function Layout() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-paper/90 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto max-w-7xl px-4 h-14 flex items-center gap-4">
          <span className="font-display text-xl text-accent shrink-0">ApplyPilot</span>
          <nav className="flex gap-1 overflow-x-auto">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.end}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm whitespace-nowrap ${
                    isActive ? "bg-accent-soft text-accent font-medium" : "text-muted hover:text-ink"
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
          </nav>
          <button
            className="ml-auto text-sm text-muted hover:text-ink shrink-0"
            onClick={() => {
              setToken(null);
              navigate("/login");
            }}
          >
            Log out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
