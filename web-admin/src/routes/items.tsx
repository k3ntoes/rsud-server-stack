import { useState, useMemo } from "react";
import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import MasterDataPage from "../components/MasterDataPage";
import Modal from "../components/Modal";
import {
  useItems,
  useCreateItem,
  useUpdateItem,
  useDeleteItem,
  useRoomsAll,
  useAllRoomItems,
  useRoomsByItem,
  useAssignRoomToItem,
  useUnassignRoomFromItem,
  type Item,
} from "../hooks/useMasterData";
import { useAuth } from "../hooks/useAuth";

function ItemsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin_ppi";
  const [roomModalItem, setRoomModalItem] = useState<Item | null>(null);
  const { data: allRooms } = useRoomsAll();
  const { data: allRoomItems } = useAllRoomItems();
  const { data: itemRooms } = useRoomsByItem(roomModalItem?.id ?? 0);

  // Build map: itemId → room names
  const roomNameMap = useMemo(() => {
    const roomById = new Map(allRooms?.map((r) => [r.id, r.name]) ?? []);
    const map = new Map<number, string[]>();
    for (const ri of allRoomItems ?? []) {
      const name = roomById.get(ri.room_id);
      if (!name) continue;
      const list = map.get(ri.item_id);
      if (list) list.push(name);
      else map.set(ri.item_id, [name]);
    }
    return map;
  }, [allRooms, allRoomItems]);
  const assignRoom = useAssignRoomToItem();
  const unassignRoom = useUnassignRoomFromItem();

  const assignedRoomIds = new Set(itemRooms?.map((ri) => ri.room_id) ?? []);

  const handleToggle = async (roomId: number) => {
    if (!roomModalItem) return;
    if (assignedRoomIds.has(roomId)) {
      await unassignRoom.mutateAsync({
        itemId: roomModalItem.id,
        roomId,
      });
    } else {
      await assignRoom.mutateAsync({
        itemId: roomModalItem.id,
        roomId,
      });
    }
  };

  return (
    <>
      <MasterDataPage<Item>
        title="Item Inspeksi"
        subtitle="Kelola item yang dinilai dalam inspeksi kebersihan"
        addLabel="Tambah Item"
        searchPlaceholder="Cari item..."
        entityLabel="Nama Item"
        inputPlaceholder="Masukkan nama item"
        modalEditTitle="Edit Item Inspeksi"
        modalAddTitle="Tambah Item Inspeksi"
        emptyIcon="📋"
        emptyText="Belum ada item. Klik 'Tambah Item' untuk memulai."
        useList={useItems}
        useCreate={useCreateItem}
        useUpdate={useUpdateItem}
        useDelete={useDeleteItem}
        renderActions={(item) =>
          isAdmin && (
            <button
              onClick={() => setRoomModalItem(item)}
              className="btn-ghost text-xs"
            >
              Ruangan
            </button>
          )
        }
        renderBadges={(item) =>
          (roomNameMap.get(item.id) ?? []).map((name) => (
            <span
              key={name}
              className="inline-flex items-center rounded-full bg-navy-50 px-2.5 py-0.5 text-xs font-medium text-navy-700 ring-1 ring-inset ring-navy-200/60"
            >
              {name}
            </span>
          ))
        }
      />

      <Modal
        open={!!roomModalItem}
        onClose={() => setRoomModalItem(null)}
        title={`Ruangan — ${roomModalItem?.name ?? ""}`}
      >
        <p className="mb-4 text-sm text-ink-muted">
          Centang ruangan yang harus memeriksa item ini.
        </p>
        <div className="max-h-80 space-y-2 overflow-y-auto">
          {allRooms?.map((room) => (
            <label
              key={room.id}
              className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-navy-50"
            >
              <input
                type="checkbox"
                checked={assignedRoomIds.has(room.id)}
                onChange={() => handleToggle(room.id)}
                className="h-4 w-4 rounded border-navy-300 text-teal-600 focus:ring-teal-500"
              />
              <span className="text-sm text-ink">{room.name}</span>
            </label>
          ))}
          {!allRooms?.length && (
            <p className="py-8 text-center text-sm text-ink-subtle">
              Belum ada ruangan.
            </p>
          )}
        </div>
      </Modal>
    </>
  );
}

export const Route = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/items",
  component: ItemsPage,
});
