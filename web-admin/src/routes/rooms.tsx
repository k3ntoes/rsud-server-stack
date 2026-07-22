import { useState } from "react";
import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import Modal from "../components/Modal";
import { useRooms, useCreateRoom, useUpdateRoom, useDeleteRoom } from "../hooks/useMasterData";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/rooms",
  component: RoomsPage,
});

function RoomsPage() {
  const { data: rooms, isLoading, error } = useRooms();
  const createRoom = useCreateRoom();
  const updateRoom = useUpdateRoom();
  const deleteRoom = useDeleteRoom();

  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<{ id: number; name: string } | null>(null);
  const [nameInput, setNameInput] = useState("");
  const [saveError, setSaveError] = useState("");

  const openCreate = () => {
    setEditing(null);
    setNameInput("");
    setSaveError("");
    setModalOpen(true);
  };

  const openEdit = (id: number, name: string) => {
    setEditing({ id, name });
    setNameInput(name);
    setSaveError("");
    setModalOpen(true);
  };

  const handleSave = async () => {
    const trimmed = nameInput.trim();
    if (!trimmed) return;
    setSaveError("");
    try {
      if (editing) {
        await updateRoom.mutateAsync({ id: editing.id, name: trimmed });
      } else {
        await createRoom.mutateAsync(trimmed);
      }
      setModalOpen(false);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Gagal menyimpan");
    }
  };

  const filtered = rooms?.filter((r) =>
    r.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Ruangan</h1>
          <p className="page-subtitle">
            Kelola daftar ruangan untuk inspeksi kebersihan
          </p>
        </div>
        <button onClick={openCreate} className="btn-primary">
          + Tambah Ruangan
        </button>
      </div>

      <div className="card-plan overflow-hidden">
        <div className="border-b border-navy-100/50 px-4 py-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cari ruangan..."
            className="input-plan max-w-xs"
          />
        </div>

        {isLoading ? (
          <div className="p-8">
            <div className="skeleton mb-3 h-5 w-3/4" />
            <div className="skeleton mb-3 h-5 w-1/2" />
            <div className="skeleton h-5 w-2/3" />
          </div>
        ) : error ? (
          <div className="empty-state">
            <span className="empty-state-icon">⚠️</span>
            <p className="empty-state-text">Gagal memuat data.</p>
          </div>
        ) : filtered?.length === 0 ? (
          <div className="empty-state">
            <span className="empty-state-icon">{search ? "🔍" : "🏥"}</span>
            <p className="empty-state-text">
              {search
                ? "Tidak ada hasil."
                : "Belum ada ruangan. Klik 'Tambah Ruangan' untuk memulai."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-plan">
              <thead>
                <tr>
                  <th>Nama</th>
                  <th>Status</th>
                  <th className="text-right">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {filtered?.map((r) => (
                  <tr key={r.id}>
                    <td className="font-medium text-ink">{r.name}</td>
                    <td>
                      {r.is_active ? (
                        <span className="badge-approved">Aktif</span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-navy-100/40 px-2.5 py-0.5 text-xs font-medium text-navy-500 ring-1 ring-inset ring-navy-200/50">
                          Nonaktif
                        </span>
                      )}
                    </td>
                    <td className="text-right">
                      <button
                        onClick={() => openEdit(r.id, r.name)}
                        className="btn-ghost text-xs"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => {
                          if (
                            window.confirm(`Hapus ruangan "${r.name}"?`)
                          ) {
                            deleteRoom.mutate(r.id);
                          }
                        }}
                        className="btn-ghost text-xs text-ink-muted hover:text-danger"
                      >
                        Hapus
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "Edit Ruangan" : "Tambah Ruangan"}
      >
        <label className="label-plan">Nama Ruangan</label>
        <input
          type="text"
          value={nameInput}
          onChange={(e) => setNameInput(e.target.value)}
          className="input-plan"
          placeholder="Masukkan nama ruangan"
          autoFocus
          onKeyDown={(e) => e.key === "Enter" && handleSave()}
        />
        {saveError && (
          <p className="mt-2 animate-fade-in text-sm text-danger">{saveError}</p>
        )}
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={() => setModalOpen(false)}
            className="btn-secondary"
          >
            Batal
          </button>
          <button
            onClick={handleSave}
            disabled={
              !nameInput.trim() ||
              createRoom.isPending ||
              updateRoom.isPending
            }
            className="btn-primary"
          >
            {createRoom.isPending || updateRoom.isPending
              ? "Menyimpan..."
              : "Simpan"}
          </button>
        </div>
      </Modal>
    </div>
  );
}
