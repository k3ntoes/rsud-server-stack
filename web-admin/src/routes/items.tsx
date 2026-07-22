import { useState } from "react";
import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import Modal from "../components/Modal";
import { useItems, useCreateItem, useUpdateItem, useDeleteItem } from "../hooks/useMasterData";

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/items",
  component: ItemsPage,
});

function ItemsPage() {
  const { data: items, isLoading, error } = useItems();
  const createItem = useCreateItem();
  const updateItem = useUpdateItem();
  const deleteItem = useDeleteItem();

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
        await updateItem.mutateAsync({ id: editing.id, name: trimmed });
      } else {
        await createItem.mutateAsync(trimmed);
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
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Item Inspeksi</h1>
        <button
          onClick={openCreate}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          + Tambah Item
        </button>
      </div>

      <div className="rounded-xl border bg-white">
        <div className="border-b px-4 py-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cari item..."
            className="w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
          />
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-sm text-gray-400">Memuat...</div>
        ) : error ? (
          <div className="p-8 text-center text-sm text-red-500">Gagal memuat data.</div>
        ) : filtered?.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-400">
            {search ? "Tidak ada hasil." : "Belum ada item. Klik 'Tambah Item' untuk memulai."}
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3">Nama</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {filtered?.map((item) => (
                <tr key={item.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{item.name}</td>
                  <td className="px-4 py-3">
                    {item.is_active ? (
                      <span className="inline-flex rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
                        Aktif
                      </span>
                    ) : (
                      <span className="inline-flex rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">
                        Nonaktif
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => openEdit(item.id, item.name)}
                      className="rounded px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => {
                        if (window.confirm(`Hapus item "${item.name}"?`)) {
                          deleteItem.mutate(item.id);
                        }
                      }}
                      className="ml-1 rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50 transition-colors"
                    >
                      Hapus
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "Edit Item Inspeksi" : "Tambah Item Inspeksi"}
      >
        <label className="mb-1.5 block text-sm font-medium text-gray-700">Nama Item</label>
        <input
          type="text"
          value={nameInput}
          onChange={(e) => setNameInput(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
          placeholder="Masukkan nama item"
          autoFocus
          onKeyDown={(e) => e.key === "Enter" && handleSave()}
        />
        {saveError && (
          <p className="mt-2 text-sm text-red-600">{saveError}</p>
        )}
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={() => setModalOpen(false)}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Batal
          </button>
          <button
            onClick={handleSave}
            disabled={!nameInput.trim() || createItem.isPending || updateItem.isPending}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60 transition-colors"
          >
            {createItem.isPending || updateItem.isPending ? "Menyimpan..." : "Simpan"}
          </button>
        </div>
      </Modal>
    </div>
  );
}
