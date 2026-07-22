import { useState, useEffect } from "react";
import { Link, Outlet, useLocation, useNavigate } from "@tanstack/react-router";
import { useAuth } from "../hooks/useAuth";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: "📊" },
  { to: "/rooms", label: "Ruangan", icon: "🏥" },
  { to: "/items", label: "Item Inspeksi", icon: "📋" },
  { to: "/inspections", label: "Inspeksi", icon: "✅" },
  { to: "/analytics", label: "Analitik", icon: "📈" },
];

export default function Layout() {
  const { user, isLoading, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      navigate({ to: "/login" });
    }
  }, [isLoading, user, navigate]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-canvas">
        <div className="text-center animate-fade-in">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-[2.5px] border-teal-500 border-t-transparent" />
          <p className="mt-3 text-sm text-ink-muted">Memuat...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-canvas">
      {/* Overlay mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/40 backdrop-blur-sm lg:hidden animate-fade-in"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ═══ Sidebar — Navy planograph ═══ */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-navy-800 shadow-plan-lg transition-transform duration-300 ease-out lg:static lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand */}
        <div className="flex h-16 items-center gap-3 border-b border-navy-700/50 px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-plan bg-teal-500/15 text-sm">
            🏥
          </div>
          <div>
            <p className="text-sm font-semibold text-navy-100">RSUD Ajibarang</p>
            <p className="text-[11px] leading-tight text-navy-400">Sistem Inspeksi PPI</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-0.5 overflow-y-auto p-3">
          {navItems.map((item) => {
            const active = location.pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={active ? "nav-item-active" : "nav-item"}
                onClick={() => setSidebarOpen(false)}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
                {active && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-teal-400" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="border-t border-navy-700/30 p-4">
          <p className="text-[11px] text-navy-500">
            &copy; 2026 RSUD Ajibarang
            <br />
            v1.0 &middot; Planograph UI
          </p>
        </div>
      </aside>

      {/* ═══ Main Area ═══ */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-navy-100/70 bg-surface px-4 lg:px-6">
          <button
            className="btn-ghost -ml-1 lg:hidden"
            onClick={() => setSidebarOpen(true)}
            aria-label="Toggle sidebar"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <div className="flex-1" />

          <div className="flex items-center gap-3">
            <span className="text-sm text-ink-muted">
              {user?.username}
              <span className="ml-1.5 rounded-full bg-navy-100 px-2 py-0.5 text-[11px] font-medium text-navy-600">
                {user?.role}
              </span>
            </span>
            <div className="h-5 w-px bg-navy-200/60" />
            <button
              onClick={logout}
              className="btn-ghost text-xs text-ink-muted hover:text-danger"
            >
              Keluar
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
