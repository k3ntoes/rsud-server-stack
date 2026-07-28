import { useState } from "react";
import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import MasterDataPage from "../components/MasterDataPage";
import Modal from "../components/Modal";
import {
  useRooms,
  useCreateRoom,
  useUpdateRoom,
  useDeleteRoom,
  useItems,
  useRoomItemsByRoom,
  useAssignItemToRoom,
  useUnassignItemFromRoom,
  type Room,
} from "../hooks/useMasterData";
import { useAuth } from "../hooks/useAuth";

function RoomsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin_ppi";
  const [itemModalRoom, setItemModalRoom] = useState<Room | null>(null);
  const { data: allItems } = useItems();
  const { data: roomItems } = useRoomItemsByRoom(itemModalRoom?.id ?? 0);
  const assignItem = useAssignItemToRoom();
  const unassignItem = useUnassignItemFromRoom();

  const assignedItemIds = new Set(roomItems?.map((ri) => ri.item_id) ?? []);

  const handleToggleItem = async (itemId: number) => {
    if (!itemModalRoom) return;
    if (assignedItemIds.has(itemId)) {
      await unassignItem.mutateAsync({ roomId: itemModalRoom.id, itemId });
    } else {
      await assignItem.mutateAsync({ roomId: itemModalRoom.id, itemId });
    }
  };

  return (
    <>
      <MasterDataPage<Room>
        title="Ruangan"
        subtitle="Kelola daftar ruangan untuk inspeksi kebersihan"
        addLabel="Tambah Ruangan"
        searchPlaceholder="Cari ruangan..."
        entityLabel="Nama Ruangan"
        inputPlaceholder="Masukkan nama ruangan"
        modalEditTitle="Edit Ruangan"
        modalAddTitle="Tambah Ruangan"
        emptyIcon="🏥"
        emptyText="Belum ada ruangan. Klik 'Tambah Ruangan' untuk memulai."
        useList={useRooms}
        useCreate={useCreateRoom}
        useUpdate={useUpdateRoom}
        useDelete={useDeleteRoom}
        renderActions={(room) =>
          isAdmin && (
            <button
              onClick={() => setItemModalRoom(room)}
              className="btn-ghost text-xs"
            >
              Item
            </button>
          )
        }
      />

      <Modal
        open={!!itemModalRoom}
        onClose={() => setItemModalRoom(null)}
        title={`Item Inspeksi — ${itemModalRoom?.name ?? ""}`}
      >
        <p className="mb-4 text-sm text-ink-muted">
          Centang item yang harus diperiksa di ruangan ini.
        </p>
        <div className="max-h-80 space-y-2 overflow-y-auto">
          {allItems?.map((item) => (
            <label
              key={item.id}
              className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-navy-50"
            >
              <input
                type="checkbox"
                checked={assignedItemIds.has(item.id)}
                onChange={() => handleToggleItem(item.id)}
                className="h-4 w-4 rounded border-navy-300 text-teal-600 focus:ring-teal-500"
              />
              <span className="text-sm text-ink">{item.name}</span>
            </label>
          ))}
          {!allItems?.length && (
            <p className="py-8 text-center text-sm text-ink-subtle">
              Belum ada item inspeksi.
            </p>
          )}
        </div>
      </Modal>
    </>
  );
}

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/rooms",
  component: RoomsPage,
});
