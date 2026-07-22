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
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600 text-3xl text-white shadow-lg">
            🏥
          </div>
          <h1 className="text-2xl font-bold text-gray-900">RSUD Ajibarang</h1>
          <p className="mt-1 text-sm text-gray-500">Sistem Inspeksi PPI</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-xl border bg-white p-6 shadow-sm"
        >
          <div className="mb-4">
            <label
              htmlFor="username"
              className="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              placeholder="Masukkan username"
              autoFocus
            />
          </div>

          <div className="mb-6">
            <label
              htmlFor="password"
              className="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              placeholder="Masukkan password"
            />
          </div>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Memproses..." : "Masuk"}
          </button>
        </form>
      </div>
    </div>
  );
}
