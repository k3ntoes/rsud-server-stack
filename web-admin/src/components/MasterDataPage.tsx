import { useState } from "react";
import type { UseMutationResult } from "@tanstack/react-query";
import Modal from "./Modal";

interface Entity {
  id: number;
  name: string;
  is_active?: boolean;
}

interface MasterDataPageProps<T extends Entity> {
  title: string;
  subtitle: string;
  addLabel: string;
  searchPlaceholder: string;
  entityLabel: string;
  inputPlaceholder: string;
  modalEditTitle: string;
  modalAddTitle: string;
  emptyIcon: string;
  emptyText: string;
  emptySearchText?: string;
  editLabel?: string;
  deleteLabel?: string;
  // Hooks
  useList: () => {
    data: T[] | undefined;
    isLoading: boolean;
    error: Error | null;
  };
  useCreate: () => UseMutationResult<T, Error, string>;
  useUpdate: () => UseMutationResult<T, Error, { id: number; name: string }>;
  useDelete: () => UseMutationResult<void, Error, number>;
}

export default function MasterDataPage<T extends Entity>({
  title,
  subtitle,
  addLabel,
  searchPlaceholder,
  entityLabel,
  inputPlaceholder,
  modalEditTitle,
  modalAddTitle,
  emptyIcon,
  emptyText,
  emptySearchText = "Tidak ada hasil.",
  editLabel = "Edit",
  deleteLabel = "Hapus",
  useList,
  useCreate,
  useUpdate,
  useDelete,
}: MasterDataPageProps<T>) {
  const { data: items, isLoading, error } = useList();
  const create = useCreate();
  const update = useUpdate();
  const del = useDelete();

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
        await update.mutateAsync({ id: editing.id, name: trimmed });
      } else {
        await create.mutateAsync(trimmed);
      }
      setModalOpen(false);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Gagal menyimpan");
    }
  };

  const filtered = items?.filter((r) =>
    r.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">{title}</h1>
          <p className="page-subtitle">{subtitle}</p>
        </div>
        <button onClick={openCreate} className="btn-primary">
          + {addLabel}
        </button>
      </div>

      <div className="card-plan overflow-hidden">
        <div className="border-b border-navy-100/50 px-4 py-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={searchPlaceholder}
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
            <span className="empty-state-icon">{search ? "🔍" : emptyIcon}</span>
            <p className="empty-state-text">
              {search ? emptySearchText : emptyText}
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
                {filtered?.map((item) => (
                  <tr key={item.id}>
                    <td className="font-medium text-ink">{item.name}</td>
                    <td>
                      {item.is_active !== undefined && item.is_active ? (
                        <span className="badge-approved">Aktif</span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-navy-100/40 px-2.5 py-0.5 text-xs font-medium text-navy-500 ring-1 ring-inset ring-navy-200/50">
                          Nonaktif
                        </span>
                      )}
                    </td>
                    <td className="text-right">
                      <button
                        onClick={() => openEdit(item.id, item.name)}
                        className="btn-ghost text-xs"
                      >
                        {editLabel}
                      </button>
                      <button
                        onClick={() => {
                          if (
                            window.confirm(`Hapus ${entityLabel.toLowerCase()} "${item.name}"?`)
                          ) {
                            del.mutate(item.id);
                          }
                        }}
                        className="btn-ghost text-xs text-ink-muted hover:text-danger"
                      >
                        {deleteLabel}
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
        title={editing ? modalEditTitle : modalAddTitle}
      >
        <label className="label-plan">{entityLabel}</label>
        <input
          type="text"
          value={nameInput}
          onChange={(e) => setNameInput(e.target.value)}
          className="input-plan"
          placeholder={inputPlaceholder}
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
              create.isPending ||
              update.isPending
            }
            className="btn-primary"
          >
            {create.isPending || update.isPending
              ? "Menyimpan..."
              : "Simpan"}
          </button>
        </div>
      </Modal>
    </div>
  );
}
