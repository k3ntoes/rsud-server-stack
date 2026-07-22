import { useState } from "react";
import { createRoute, useParams, useNavigate } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import Modal from "../components/Modal";
import {
  useInspection,
  useApproveInspection,
  useRejectInspection,
} from "../hooks/useInspections";
import { useRooms } from "../hooks/useMasterData";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/inspections/$inspectionId",
  component: InspectionDetailPage,
});

function statusBadge(status: string) {
  switch (status) {
    case "PENDING":
      return <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">Menunggu</span>;
    case "APPROVED":
      return <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700">Disetujui</span>;
    case "REJECTED":
      return <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700">Ditolak</span>;
    default:
      return null;
  }
}

function scoreBadge(score: number) {
  const labels = ["Berisiko", "Minor", "Sesuai Standar"];
  const colors = ["bg-red-50 text-red-700", "bg-amber-50 text-amber-700", "bg-green-50 text-green-700"];
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[score] ?? "bg-gray-100 text-gray-500"}`}>
      {score} — {labels[score] ?? "?"}
    </span>
  );
}

function InspectionDetailPage() {
  const { inspectionId } = useParams({ from: Route.id });
  const id = Number(inspectionId);
  const { data: insp, isLoading, error } = useInspection(id);
  const { data: rooms } = useRooms();
  const approve = useApproveInspection();
  const reject = useRejectInspection();
  const navigate = useNavigate();

  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const roomName = rooms?.find((r) => r.id === insp?.room_id)?.name ?? `Ruangan #${insp?.room_id}`;

  const handleApprove = async () => {
    if (!window.confirm("Setujui inspeksi ini?")) return;
    await approve.mutateAsync(id);
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) return;
    await reject.mutateAsync({ id, reason: rejectReason.trim() });
    setRejectOpen(false);
  };

  if (isLoading) {
    return <div className="rounded-xl border bg-white p-8 text-center text-sm text-gray-400">Memuat...</div>;
  }

  if (error || !insp) {
    return (
      <div className="rounded-xl border bg-white p-8 text-center text-sm text-red-500">
        Inspeksi tidak ditemukan.
      </div>
    );
  }

  return (
    <div>
      {/* Back button */}
      <button
        onClick={() => navigate({ to: "/inspections" })}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Kembali
      </button>

      {/* Header card */}
      <div className="mb-6 rounded-xl border bg-white p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">{roomName}</h1>
            <p className="mt-1 text-sm text-gray-500">
              {insp.business_date} &middot; {new Date(insp.created_at).toLocaleTimeString("id-ID")}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {statusBadge(insp.status)}
          </div>
        </div>

        {insp.rejection_reason && (
          <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            <span className="font-medium">Alasan ditolak:</span> {insp.rejection_reason}
          </div>
        )}

        {insp.status === "PENDING" && (
          <div className="mt-6 flex gap-3 border-t pt-4">
            <button
              onClick={handleApprove}
              disabled={approve.isPending}
              className="rounded-lg bg-green-600 px-5 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-60 transition-colors"
            >
              {approve.isPending ? "Memproses..." : "Setujui"}
            </button>
            <button
              onClick={() => { setRejectReason(""); setRejectOpen(true); }}
              className="rounded-lg border border-red-300 px-5 py-2 text-sm font-medium text-red-700 hover:bg-red-50 transition-colors"
            >
              Tolak
            </button>
          </div>
        )}
      </div>

      {/* Items table */}
      <div className="rounded-xl border bg-white">
        <div className="border-b px-4 py-3 font-medium text-gray-700">
          Item Inspeksi ({insp.details.length})
        </div>
        {insp.details.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-400">Tidak ada item.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3">Item</th>
                <th className="px-4 py-3">Skor</th>
                <th className="px-4 py-3">Foto</th>
              </tr>
            </thead>
            <tbody>
              {insp.details.map((d) => (
                <tr key={d.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{d.item_name_snapshot}</td>
                  <td className="px-4 py-3">{scoreBadge(d.score)}</td>
                  <td className="px-4 py-3">
                    {d.photos.length > 0 ? (
                      <div className="flex gap-1">
                        {d.photos.map((p) => (
                          <span
                            key={p.id}
                            className="inline-flex items-center rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-500"
                          >
                            📷 {p.photo_file_name.slice(0, 12)}…
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Reject modal */}
      <Modal open={rejectOpen} onClose={() => setRejectOpen(false)} title="Tolak Inspeksi">
        <label className="mb-1.5 block text-sm font-medium text-gray-700">Alasan penolakan</label>
        <textarea
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          rows={3}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 resize-none"
          placeholder="Masukkan alasan..."
          autoFocus
        />
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={() => setRejectOpen(false)}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Batal
          </button>
          <button
            onClick={handleReject}
            disabled={!rejectReason.trim() || reject.isPending}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60 transition-colors"
          >
            {reject.isPending ? "Memproses..." : "Tolak"}
          </button>
        </div>
      </Modal>
    </div>
  );
}
