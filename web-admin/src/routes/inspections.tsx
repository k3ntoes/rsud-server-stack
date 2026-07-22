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
const STATUS_LABELS: Record<string, string> = {
  "": "Semua",
  PENDING: "Menunggu",
  APPROVED: "Disetujui",
  REJECTED: "Ditolak",
};

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
        return <span className="badge-pending">Menunggu</span>;
      case "APPROVED":
        return <span className="badge-approved">Disetujui</span>;
      case "REJECTED":
        return <span className="badge-rejected">Ditolak</span>;
      default:
        return (
          <span className="inline-flex items-center rounded-full bg-navy-100/40 px-2.5 py-0.5 text-xs font-medium text-navy-500 ring-1 ring-inset ring-navy-200/50">
            {s}
          </span>
        );
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Inspeksi</h1>
          <p className="page-subtitle">
            Daftar inspeksi kebersihan harian
          </p>
        </div>
      </div>

      {/* Status filter tabs */}
      <div className="mb-4 tab-group">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={statusFilter === s ? "tab-item-active" : "tab-item"}
          >
            {STATUS_LABELS[s]}
          </button>
        ))}
      </div>

      <div className="card-plan overflow-hidden">
        {isLoading ? (
          <div className="p-8">
            <div className="skeleton mb-3 h-5 w-full" />
            <div className="skeleton mb-3 h-5 w-3/4" />
            <div className="skeleton h-5 w-5/6" />
          </div>
        ) : error ? (
          <div className="empty-state">
            <span className="empty-state-icon">⚠️</span>
            <p className="empty-state-text">Gagal memuat data.</p>
          </div>
        ) : !inspections?.length ? (
          <div className="empty-state">
            <span className="empty-state-icon">✅</span>
            <p className="empty-state-text">
              {statusFilter === "PENDING"
                ? "Tidak ada inspeksi menunggu."
                : "Belum ada data inspeksi."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-plan">
              <thead>
                <tr>
                  <th>Tanggal</th>
                  <th>Ruangan</th>
                  <th>Status</th>
                  <th className="text-center">Item</th>
                  <th className="text-right">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {inspections.map((i) => (
                  <tr key={i.id}>
                    <td className="text-ink-muted">{i.business_date}</td>
                    <td className="font-medium text-ink">
                      {roomMap.get(i.room_id) ?? `Ruangan #${i.room_id}`}
                    </td>
                    <td>{statusBadge(i.status)}</td>
                    <td className="text-center text-ink-muted">
                      {i.detail_count}
                    </td>
                    <td className="text-right">
                      <button
                        onClick={() =>
                          navigate({
                            to: "/inspections/$inspectionId",
                            params: {
                              inspectionId: String(i.id),
                            },
                          })
                        }
                        className="btn-ghost text-xs"
                      >
                        Detail
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
