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
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="mt-3 text-sm text-gray-500">Memuat...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-white shadow-lg transition-transform duration-200 lg:static lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-16 items-center gap-2 border-b px-6">
          <span className="text-xl">🏥</span>
          <span className="text-lg font-semibold">RSUD Ajibarang</span>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-4">
          {navItems.map((item) => {
            const active = location.pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                <span>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t p-4 text-xs text-gray-400">
          RSUD Ajibarang v1.0
        </div>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 items-center justify-between border-b bg-white px-4 lg:px-6">
          <button
            className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 lg:hidden"
            onClick={() => setSidebarOpen(true)}
            aria-label="Toggle sidebar"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <div className="flex-1" />

          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user?.username}
              <span className="ml-1.5 rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">
                {user?.role}
              </span>
            </span>
            <button
              onClick={logout}
              className="rounded-lg px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
            >
              Logout
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
