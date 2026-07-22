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

  const cards = [
    { label: "Menunggu Approve", value: stats.pendingCount, color: "text-amber-600", bg: "bg-amber-50" },
    { label: "Total Ruangan", value: stats.roomCount, color: "text-blue-600", bg: "bg-blue-50" },
    { label: "Inspeksi", value: "📊", color: "text-purple-600", bg: "bg-purple-50" },
    { label: "Skor Bulan Ini", value: "📈", color: "text-green-600", bg: "bg-green-50" },
  ];

  return (
    <div>
      <h1 className="mb-6 text-xl font-semibold text-gray-900">Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((s) => (
          <div key={s.label} className={`rounded-xl border p-5 ${s.bg}`}>
            <p className="text-sm text-gray-500">{s.label}</p>
            <p className={`mt-2 text-2xl font-bold ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 rounded-xl border bg-white p-8 text-center text-gray-400">
        <p className="text-lg">🏥</p>
        <p className="mt-2 text-sm">
          Selamat datang di dashboard RSUD Ajibarang. Gunakan menu sidebar untuk mengelola data.
        </p>
      </div>
    </div>
  );
}
