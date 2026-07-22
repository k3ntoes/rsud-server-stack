import { useState, useEffect } from "react";
import { createRoute, useNavigate } from "@tanstack/react-router";
import { rootRoute } from "./__root";
import { useAuth } from "../hooks/useAuth";

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/login",
  component: LoginPage,
});

function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate({ to: "/dashboard" });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!username || !password) {
      setError("Username dan password harus diisi");
      return;
    }
    setLoading(true);
    try {
      await login(username, password);
      navigate({ to: "/dashboard" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login gagal");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-canvas p-4">
      {/* Decorative planograph grid pattern */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(11, 26, 46, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(11, 26, 46, 0.08) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      {/* Decorative accent blob */}
      <div className="pointer-events-none absolute -right-32 -top-32 h-96 w-96 rounded-full bg-teal-500/5 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-navy-500/5 blur-3xl" />

      <div className="relative w-full max-w-sm animate-slide-up">
        {/* Brand */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-plan-xl bg-navy-800 text-2xl shadow-plan-lg">
            🏥
          </div>
          <h1 className="text-2xl font-bold text-ink">RSUD Ajibarang</h1>
          <p className="mt-1 text-sm text-ink-muted">Sistem Inspeksi PPI</p>
        </div>

        {/* Login card */}
        <form onSubmit={handleSubmit} className="card-plan p-6">
          <div className="mb-4">
            <label htmlFor="username" className="label-plan">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-plan"
              placeholder="Masukkan username"
              autoFocus
            />
          </div>

          <div className="mb-5">
            <label htmlFor="password" className="label-plan">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-plan"
              placeholder="Masukkan password"
            />
          </div>

          {error && (
            <div className="mb-4 animate-fade-in rounded-plan border border-danger-border bg-danger-muted px-3 py-2 text-sm text-danger">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Memproses...
              </span>
            ) : (
              "Masuk"
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-ink-subtle">
          &copy; 2026 RSUD Ajibarang &middot; Planograph UI
        </p>
      </div>
    </div>
  );
}
