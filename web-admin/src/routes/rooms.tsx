import { useState, useMemo, useEffect } from "react";
import { createRoute } from "@tanstack/react-router";
import { protectedRoute } from "./_protected";
import MasterDataPage from "../components/MasterDataPage";
import Modal from "../components/Modal";
import {
  useRooms,
  useCreateRoom,
  useUpdateRoom,
  useDeleteRoom,
  useItemsAll,
  useAllRoomItems,
  useRoomItemsByRoom,
  useAssignItemToRoom,
  useUnassignItemFromRoom,
  useReorderRoomItems,
  type Room,
} from "../hooks/useMasterData";
import { useAuth } from "../hooks/useAuth";

function RoomsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin_ppi";
  const [itemModalRoom, setItemModalRoom] = useState<Room | null>(null);
  const { data: allItems } = useItemsAll();
  const { data: allRoomItems } = useAllRoomItems();
  const { data: roomItems } = useRoomItemsByRoom(itemModalRoom?.id ?? 0);
  const assignItem = useAssignItemToRoom();
  const unassignItem = useUnassignItemFromRoom();
  const reorderItems = useReorderRoomItems();

  // Urutan lokal item (ADR-0013): sinkron dari API, lalu diubah via tombol ▲/▼
  const [localItemOrder, setLocalItemOrder] = useState<number[]>([]);
  useEffect(() => {
    if (roomItems) {
      setLocalItemOrder(roomItems.map((ri) => ri.item_id));
    }
  }, [roomItems]);

  const orderedRoomItems = useMemo(() => {
    if (!roomItems) return [];
    const idxOf = new Map(localItemOrder.map((id, i) => [id, i]));
    return [...roomItems].sort(
      (a, b) => (idxOf.get(a.item_id) ?? 0) - (idxOf.get(b.item_id) ?? 0),
    );
  }, [roomItems, localItemOrder]);

  const itemName = (itemId: number) =>
    allItems?.find((i) => i.id === itemId)?.name ?? `Item #${itemId}`;

  const handleMove = async (index: number, delta: number) => {
    if (!itemModalRoom) return;
    const target = index + delta;
    if (target < 0 || target >= orderedRoomItems.length) return;
    const next = [...localItemOrder];
    [next[index], next[target]] = [next[target], next[index]];
    setLocalItemOrder(next);
    try {
      await reorderItems.mutateAsync({ roomId: itemModalRoom.id, itemIds: next });
    } catch {
      // Rollback optimistik saat server menolak — kembali ke urutan terakhir dari API
      if (roomItems) setLocalItemOrder(roomItems.map((ri) => ri.item_id));
    }
  };

  const assignedItemIds = new Set(roomItems?.map((ri) => ri.item_id) ?? []);

  // Build map: roomId → item names
  const itemNameMap = useMemo(() => {
    const items = allItems ?? [];
    const itemById = new Map(items.map((i) => [i.id, i.name]));

    const roomItemMap = new Map<number, string[]>();
    for (const ri of allRoomItems ?? []) {
      const name = itemById.get(ri.item_id);
      if (!name) continue;
      const list = roomItemMap.get(ri.room_id);
      if (list) {
        list.push(name);
      } else {
        roomItemMap.set(ri.room_id, [name]);
      }
    }
    return roomItemMap;
  }, [allItems, allRoomItems]);

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
        renderBadges={(room) =>
          (itemNameMap.get(room.id) ?? []).map((name) => (
            <span
              key={name}
              className="inline-flex items-center rounded-full bg-teal-50 px-2.5 py-0.5 text-xs font-medium text-teal-700 ring-1 ring-inset ring-teal-200/60"
            >
              {name}
            </span>
          ))
        }
      />

      <Modal
        open={!!itemModalRoom}
        onClose={() => setItemModalRoom(null)}
        title={`Item Inspeksi — ${itemModalRoom?.name ?? ""}`}
      >
        <div className="mb-5">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-muted">
            Urutan Checklist
          </p>
          {orderedRoomItems.length === 0 ? (
            <p className="rounded-lg bg-navy-50/60 px-3 py-2.5 text-sm text-ink-subtle">
              Belum ada item ter-assign. Centang item di bawah untuk menambah.
            </p>
          ) : (
            <div className="space-y-1.5">
              {orderedRoomItems.map((ri, idx) => {
                const isFirst = idx === 0;
                const isLast = idx === orderedRoomItems.length - 1;
                const pending = reorderItems.isPending;
                return (
                  <div
                    key={ri.id}
                    className="flex items-center gap-2 rounded-lg border border-navy-100/60 bg-surface px-3 py-2 transition-colors"
                  >
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-teal-50 text-xs font-semibold text-teal-700 ring-1 ring-inset ring-teal-200/60">
                      {idx + 1}
                    </span>
                    <span className="flex-1 text-sm text-ink">{itemName(ri.item_id)}</span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleMove(idx, -1)}
                        disabled={isFirst || pending}
                        aria-label={`Pindah ke atas: ${itemName(ri.item_id)}`}
                        title="Naik"
                        className="btn-ghost h-7 w-7 p-0 text-xs disabled:cursor-not-allowed disabled:opacity-30"
                      >
                        ▲
                      </button>
                      <button
                        onClick={() => handleMove(idx, 1)}
                        disabled={isLast || pending}
                        aria-label={`Pindah ke bawah: ${itemName(ri.item_id)}`}
                        title="Turun"
                        className="btn-ghost h-7 w-7 p-0 text-xs disabled:cursor-not-allowed disabled:opacity-30"
                      >
                        ▼
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
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
