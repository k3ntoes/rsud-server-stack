import { useState } from "react";
import { createRoute, useNavigate } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import { useInspections } from "../hooks/useInspections";
import { useRooms } from "../hooks/useMasterData";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/inspections",
  component: InspectionsPage,
});

const STATUSES = ["", "PENDING", "APPROVED", "REJECTED"] as const;
const STATUS_LABELS: Record<string, string> = { "": "Semua", PENDING: "Menunggu", APPROVED: "Disetujui", REJECTED: "Ditolak" };

function InspectionsPage() {
  const [statusFilter, setStatusFilter] = useState("PENDING");
  const { data: inspections, isLoading, error } = useInspections(
    statusFilter ? { status: statusFilter } : {},
  );
  const { data: rooms } = useRooms();
  const navigate = useNavigate();

  const roomMap = new Map(rooms?.map((r) => [r.id, r.name]) ?? []);

  const statusBadge = (s: string) => {
    switch (s) {
      case "PENDING":
        return <span className="inline-flex rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700">Menunggu</span>;
      case "APPROVED":
        return <span className="inline-flex rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">Disetujui</span>;
      case "REJECTED":
        return <span className="inline-flex rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700">Ditolak</span>;
      default:
        return <span className="inline-flex rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">{s}</span>;
    }
  };

  return (
    <div>
      <h1 className="mb-6 text-xl font-semibold text-gray-900">Inspeksi</h1>

      {/* Status filter tabs */}
      <div className="mb-4 flex gap-1 rounded-lg bg-gray-100 p-1 w-fit">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
              statusFilter === s
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {STATUS_LABELS[s]}
          </button>
        ))}
      </div>

      <div className="rounded-xl border bg-white">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-gray-400">Memuat...</div>
        ) : error ? (
          <div className="p-8 text-center text-sm text-red-500">Gagal memuat data.</div>
        ) : !inspections?.length ? (
          <div className="p-8 text-center text-sm text-gray-400">
            {statusFilter === "PENDING"
              ? "Tidak ada inspeksi menunggu."
              : "Belum ada data inspeksi."}
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3">Tanggal</th>
                <th className="px-4 py-3">Ruangan</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-center">Item</th>
                <th className="px-4 py-3 text-right">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {inspections.map((i) => (
                <tr key={i.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-700">{i.business_date}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {roomMap.get(i.room_id) ?? `Ruangan #${i.room_id}`}
                  </td>
                  <td className="px-4 py-3">{statusBadge(i.status)}</td>
                  <td className="px-4 py-3 text-center text-gray-600">{i.detail_count}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => navigate({ to: '/inspections/$inspectionId', params: { inspectionId: String(i.id) } })}
                      className="rounded px-2.5 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 transition-colors"
                    >
                      Detail
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
