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
      return (
        <span className="badge-pending rounded-full px-3 py-1 text-xs">
          Menunggu
        </span>
      );
    case "APPROVED":
      return (
        <span className="badge-approved rounded-full px-3 py-1 text-xs">
          Disetujui
        </span>
      );
    case "REJECTED":
      return (
        <span className="badge-rejected rounded-full px-3 py-1 text-xs">
          Ditolak
        </span>
      );
    default:
      return null;
  }
}

function scoreBadge(score: number) {
  const labels = ["Berisiko", "Minor", "Sesuai Standar"];
  if (score === 0)
    return (
      <span className="inline-flex rounded-full bg-danger-muted px-2.5 py-0.5 text-xs font-medium text-danger ring-1 ring-inset ring-danger-border">
        {score} — {labels[0]}
      </span>
    );
  if (score === 1)
    return (
      <span className="inline-flex rounded-full bg-warning-muted px-2.5 py-0.5 text-xs font-medium text-warning ring-1 ring-inset ring-warning-border">
        {score} — {labels[1]}
      </span>
    );
  return (
    <span className="inline-flex rounded-full bg-success-muted px-2.5 py-0.5 text-xs font-medium text-success ring-1 ring-inset ring-success-border">
      {score} — {labels[2]}
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

  const roomName =
    rooms?.find((r) => r.id === insp?.room_id)?.name ??
    `Ruangan #${insp?.room_id}`;

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
    return (
      <div className="card-plan p-8 text-center">
        <div className="skeleton mx-auto mb-3 h-5 w-48" />
        <div className="skeleton mx-auto h-4 w-32" />
      </div>
    );
  }

  if (error || !insp) {
    return (
      <div className="empty-state card-plan p-8">
        <span className="empty-state-icon">🔍</span>
        <p className="empty-state-text">Inspeksi tidak ditemukan.</p>
        <button
          onClick={() => navigate({ to: "/inspections" })}
          className="btn-secondary mt-4"
        >
          Kembali
        </button>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      {/* Back button */}
      <button
        onClick={() => navigate({ to: "/inspections" })}
        className="btn-ghost mb-4 gap-1.5 text-ink-muted"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Kembali
      </button>

      {/* Header card */}
      <div className="card-plan mb-6 p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold text-ink">{roomName}</h1>
              {statusBadge(insp.status)}
            </div>
            <p className="mt-1 text-sm text-ink-muted">
              {insp.business_date} &middot;{" "}
              {new Date(insp.created_at).toLocaleTimeString("id-ID")}
            </p>
          </div>
        </div>

        {insp.rejection_reason && (
          <div className="mt-4 animate-slide-up rounded-plan border border-danger-border bg-danger-muted p-3 text-sm text-danger">
            <span className="font-semibold">Alasan ditolak:</span>{" "}
            {insp.rejection_reason}
          </div>
        )}

        {insp.status === "PENDING" && (
          <div className="mt-6 flex gap-3 border-t border-navy-100/50 pt-4">
            <button
              onClick={handleApprove}
              disabled={approve.isPending}
              className="btn-primary"
            >
              {approve.isPending ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Memproses...
                </span>
              ) : (
                "Setujui"
              )}
            </button>
            <button
              onClick={() => {
                setRejectReason("");
                setRejectOpen(true);
              }}
              className="btn-danger"
            >
              Tolak
            </button>
          </div>
        )}
      </div>

      {/* Items table */}
      <div className="card-plan overflow-hidden">
        <div className="border-b border-navy-100/50 px-4 py-3 font-medium text-ink">
          Item Inspeksi ({insp.details.length})
        </div>
        {insp.details.length === 0 ? (
          <div className="empty-state">
            <p className="empty-state-text">Tidak ada item.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-plan">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Skor</th>
                  <th>Foto</th>
                </tr>
              </thead>
              <tbody>
                {insp.details.map((d) => (
                  <tr key={d.id}>
                    <td className="font-medium text-ink">
                      {d.item_name_snapshot}
                    </td>
                    <td>{scoreBadge(d.score)}</td>
                    <td>
                      {d.photos.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {d.photos.map((p) => (
                            <span
                              key={p.id}
                              className="inline-flex items-center gap-1 rounded-plan border border-navy-100/50 bg-navy-50/50 px-2 py-0.5 text-xs text-navy-500"
                            >
                              <span className="text-[10px]">📷</span>
                              {p.photo_file_name.slice(0, 12)}…
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs text-ink-subtle">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Reject modal */}
      <Modal
        open={rejectOpen}
        onClose={() => setRejectOpen(false)}
        title="Tolak Inspeksi"
      >
        <label className="label-plan">Alasan penolakan</label>
        <textarea
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          rows={3}
          className="input-plan resize-none"
          placeholder="Masukkan alasan..."
          autoFocus
        />
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={() => setRejectOpen(false)}
            className="btn-secondary"
          >
            Batal
          </button>
          <button
            onClick={handleReject}
            disabled={!rejectReason.trim() || reject.isPending}
            className="btn-danger"
          >
            {reject.isPending ? "Memproses..." : "Tolak"}
          </button>
        </div>
      </Modal>
    </div>
  );
}
