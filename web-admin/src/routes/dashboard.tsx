import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import { useInspections } from "../hooks/useInspections";
import { useRooms } from "../hooks/useMasterData";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/dashboard",
  component: DashboardPage,
});

function useDashboardStats() {
  const { data: pendingList } = useInspections({ status: "PENDING" });
  const { data: rooms } = useRooms();

  return {
    pendingCount: pendingList?.length ?? "—",
    roomCount: rooms?.length ?? "—",
  };
}

function DashboardPage() {
  const stats = useDashboardStats();

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
                {stats.pendingCount}
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
              <p className="stat-value text-navy-600">{stats.roomCount}</p>
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
              <p className="stat-value text-teal-600">—</p>
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
              <p className="stat-value text-navy-600">—</p>
            </div>
          </div>
        </div>
      </div>

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
