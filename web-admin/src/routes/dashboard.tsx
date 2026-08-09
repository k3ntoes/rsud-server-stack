import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import { useDashboardData, currentWeekMonth } from "../hooks/useAnalytics";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/dashboard",
  component: DashboardPage,
});

function formatMonth(yearMonth: string) {
  const [year, month] = yearMonth.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString("id-ID", {
    month: "long",
    year: "numeric",
  });
}

function DashboardPage() {
  const { data } = useDashboardData();

  const currentMonth = currentWeekMonth();
  const pendingCount = data?.pending_count ?? "—";
  const roomCount = data?.total_rooms ?? "—";

  // Monthly stats fall back to the latest month with data (backend), or null
  // when there is no data at all — render an informative empty state then.
  const statsMonth = data?.year_month ?? null;
  const hasMonthlyData = statsMonth != null;
  const fallbackMonth =
    hasMonthlyData && statsMonth !== currentMonth ? statsMonth : null;
  const monthlyCount = hasMonthlyData
    ? (data?.monthly_inspection_count ?? "—")
    : "—";
  const avgScore =
    hasMonthlyData && data?.avg_score_pct != null
      ? `${data.avg_score_pct}%`
      : "—";

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">
            Ringkasan inspeksi kebersihan RSUD Ajibarang
          </p>
        </div>
      </div>

      {/* Stat cards — bento grid asymmetrical */}
      <div className="grid grid-cols-12 gap-4">
        {/* Large card — Pending count */}
        <div className="col-span-12 sm:col-span-6 lg:col-span-7">
          <div className="stat-card flex items-center gap-5">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-plan-lg bg-warning-muted">
              <span className="text-2xl">⏳</span>
            </div>
            <div>
              <p className="stat-label">Menunggu Persetujuan</p>
              <p className="stat-value text-warning">
                {pendingCount}
              </p>
            </div>
          </div>
        </div>

        {/* Small card — Rooms */}
        <div className="col-span-12 sm:col-span-6 lg:col-span-5">
          <div className="stat-card flex items-center gap-5">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-plan-lg bg-navy-50">
              <span className="text-2xl">🏥</span>
            </div>
            <div>
              <p className="stat-label">Total Ruangan</p>
              <p className="stat-value text-navy-600">{roomCount}</p>
            </div>
          </div>
        </div>

        {/* Small card — Month inspections */}
        <div className="col-span-12 sm:col-span-6 lg:col-span-5">
          <div className="stat-card flex items-center gap-5">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-plan-lg bg-teal-50">
              <span className="text-2xl">📋</span>
            </div>
            <div>
              <p className="stat-label">Inspeksi Bulan Ini</p>
              <p
                className={`stat-value ${hasMonthlyData ? "text-teal-600" : "text-ink-subtle"}`}
              >
                {monthlyCount}
              </p>
            </div>
          </div>
        </div>

        {/* Large card — Score */}
        <div className="col-span-12 sm:col-span-6 lg:col-span-7">
          <div className="stat-card flex items-center gap-5">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-plan-lg bg-navy-50">
              <span className="text-2xl">📊</span>
            </div>
            <div>
              <p className="stat-label">Skor Rata-rata Bulan Ini</p>
              <p
                className={`stat-value ${hasMonthlyData ? "text-navy-600" : "text-ink-subtle"}`}
              >
                {avgScore}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Fallback / empty-state notices */}
      {fallbackMonth && (
        <div className="mt-6 flex items-start gap-3 rounded-plan-lg border border-warning-border bg-warning-muted px-4 py-3 text-sm text-warning">
          <span className="text-base leading-none">⚠️</span>
          <p>
            Belum ada inspeksi bulan ini — menampilkan data{" "}
            <strong>{formatMonth(fallbackMonth)}</strong>.
          </p>
        </div>
      )}
      {data && !hasMonthlyData && (
        <div className="mt-6 empty-state py-10">
          <span className="empty-state-icon">📊</span>
          <p className="empty-state-text">
            Belum ada data inspeksi. Statistik bulanan muncul setelah inspeksi
            disetujui.
          </p>
        </div>
      )}

      {/* Welcome section */}
      <div className="mt-6 card-plan p-8">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-plan-lg bg-teal-50 text-xl">
            🏥
          </div>
          <div>
            <h2 className="text-base font-semibold text-ink">
              Selamat datang di Dashboard RSUD Ajibarang
            </h2>
            <p className="mt-0.5 text-sm text-ink-muted">
              Gunakan menu sidebar untuk mengelola data master, menyetujui
              inspeksi, atau melihat analitik.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
