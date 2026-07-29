# Pola `renderBadges` + `useAllRoomItems` — Badge Item di Tabel Ruangan

> **Status:** ✅ Implemented  
> **Tanggal:** 29 Juli 2026  
> **Tujuan:** Dokumentasi pola frontend untuk menampilkan nama-nama item inspeksi sebagai badge di setiap baris tabel ruangan.

---

## 1. Ringkasan

Menampilkan nama-nama item inspeksi yang terasosiasi dengan suatu ruangan sebagai **badge** di tabel, sehingga user langsung melihat item apa saja yang wajib diinspeksi di ruangan tersebut tanpa perlu membuka modal.

## 2. Arsitektur Pola

```
┌─────────────────────────────────────────────────────────────────┐
│                         Flow Data                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GET /api/inspection-items?per_page=10000                       │
│    → useItemsAll()        → allItems: Item[]                   │
│                               ↓                                 │
│  GET /api/room-items                                            │
│    → useAllRoomItems()    → allRoomItems: RoomItem[]           │
│                               ↓                                 │
│  useMemo() → itemNameMap: Map<roomId, string[]>                 │
│                               ↓                                 │
│  renderBadges={(room) => itemNameMap.get(room.id)?.map(...)}   │
│                               ↓                                 │
│  MasterDataPage → kolom "Item Inspeksi" dengan badge            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Komponen Kunci

### 3.1. Hook `useAllRoomItems()`

**File:** `web-admin/src/hooks/useMasterData.ts`

```typescript
interface SyncResponse<T> {
  data: T[];
  synced_at: string;
}

export interface RoomItem {
  id: number;
  room_id: number;
  item_id: number;
  created_at: string;
}

export function useAllRoomItems() {
  return useQuery({
    queryKey: ["room-items", "all"],
    queryFn: () =>
      apiRequest<SyncResponse<RoomItem>>("/api/room-items").then((r) => r.data),
  });
}
```

**Cara kerja:**
- Fetch semua relasi room↔item dari `GET /api/room-items`
- Backend mengembalikan `SyncResponse` → hook me-unwrap `.data` langsung
- Query key `["room-items", "all"]` — cache terpisah dari `useRoomItemsByRoom()` yang pakai `["room-items", "room", roomId]`

**Backend endpoint:**
```
GET /api/room-items
→ {
    "data": [
      { "id": 1, "room_id": 1, "item_id": 1, "created_at": "..." },
      { "id": 2, "room_id": 1, "item_id": 2, "created_at": "..." }
    ],
    "synced_at": "2026-07-29T..."
  }
```

### 3.2. Mapping `itemNameMap` via `useMemo`

**File:** `web-admin/src/routes/rooms.tsx`

```typescript
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
```

**Algoritma:**
1. `useItemsAll()` → `allItems: Item[]` (semua item dengan nama)
2. `useAllRoomItems()` → `allRoomItems: RoomItem[]` (semua pivot)
3. `useMemo` → **join manual**: `itemById[ri.item_id]` untuk setiap pivot
4. Hasil: `Map<roomId, string[]>` — nama item per room

**Mengapa `useMemo`?** — mencegah re-join pada setiap render. Hanya re-join jika `allItems` atau `allRoomItems` berubah (cache TanStack Query mengupdate data).

### 3.3. Prop `renderBadges` di `MasterDataPage`

**File:** `web-admin/src/components/MasterDataPage.tsx`

**Interface:**
```typescript
interface MasterDataPageProps<T extends Entity> {
  // ...
  renderBadges?: (item: T) => React.ReactNode;
  // ...
}
```

**Cara kerja di dalam komponen:**
```typescript
const columns: ColumnDef<T>[] = [
  // ... kolom Nama
  // ... kolom Status
  ...(renderBadges
    ? [
        {
          id: "badges",
          header: "Item Inspeksi",
          cell: ({ row }: { row: { original: T } }) => (
            <div className="flex flex-wrap gap-1">
              {renderBadges(row.original)}
            </div>
          ),
        } as ColumnDef<T>,
      ]
    : []),
  // ... kolom Aksi
];
```

**Logika:**
- Kolom badges **hanya muncul** jika prop `renderBadges` diberikan
- Jika tidak diberikan → kolom tidak ada (zero bloat)
- `flex flex-wrap gap-1` — badge akan wrap ke baris berikutnya jika terlalu banyak

### 3.4. Penggunaan di Rooms Page

**File:** `web-admin/src/routes/rooms.tsx`

```typescript
<MasterDataPage<Room>
  // ... props lainnya
  renderBadges={(room) =>
    (itemNameMap.get(room.id) ?? []).map((name) => (
      <span
        key={name}
        className="inline-flex items-center rounded-full bg-teal-50
                   px-2.5 py-0.5 text-xs font-medium text-teal-700
                   ring-1 ring-inset ring-teal-200/60"
      >
        {name}
      </span>
    ))
  }
/>
```

**Style badge:**
- `bg-teal-50` — background hijau muda
- `text-teal-700` — teks hijau tua
- `ring-1 ring-inset ring-teal-200/60` — border subtle
- `text-xs` — teks kecil
- `rounded-full` — bentuk pill

## 4. Manajemen Cache & Invalidasi

### Query Keys

| Hook | Query Key | 
|------|-----------|
| `useItemsAll()` | `["items-all"]` |
| `useAllRoomItems()` | `["room-items", "all"]` |
| `useAssignItemToRoom()` | invalidate `["room-items"]` + `["rooms"]` |
| `useUnassignItemFromRoom()` | invalidate `["room-items"]` + `["rooms"]` |

### Prefix Matching

TanStack Query v5 menggunakan **prefix matching** untuk invalidasi. Ketika mutation `useAssignItemToRoom` sukses:

```typescript
qc.invalidateQueries({ queryKey: ["room-items"] });
```

Ini meng-invalidate **semua** query yang key-nya dimulai dengan `["room-items"]`, yaitu:
- `["room-items", "all"]` — data untuk badges
- `["room-items", "room", roomId]` — data untuk modal assign

### Flow Mutasi → Badge Update

```
User assign item ke room via modal
  → useAssignItemToRoom().mutateAsync()
    → POST /api/rooms/{roomId}/items (success)
      → invalidateQueries(["room-items"]) → refetch useAllRoomItems()
      → invalidateQueries(["rooms"]) → refetch useRooms()
        → useMemo recompute → itemNameMap update
          → renderBadges render ulang dengan data baru
```

Tidak perlu refresh manual — semuanya otomatis via cache invalidation TanStack Query.

## 5. Perbandingan: Fetch All vs Fetch Per-Room

| Aspek | Fetch All (`useAllRoomItems`) | Fetch Per-Room (`useRoomItemsByRoom`) |
|-------|-------------------------------|----------------------------------------|
| Jumlah request | 1 request untuk semua room | 1 request per room (N+1 problem) |
| Cocok untuk | Badges di tabel (banyak room) | Modal assign (satu room spesifik) |
| Ukuran data | ~30-200 baris pivot | ~5-15 baris pivot |
| Cache key | `["room-items", "all"]` | `["room-items", "room", roomId]` |
| Digunakan di | `renderBadges` | `assignedItemIds` (modal checkbox) |

**Keduanya digunakan bersamaan** di `rooms.tsx` — `useAllRoomItems()` untuk badges tabel, `useRoomItemsByRoom()` untuk checkbox di modal.

## 6. Cara Pakai untuk Halaman Lain (items.tsx)

Pola yang sama bisa diterapkan di halaman Items untuk menampilkan badge nama-nama room yang menggunakan item tertentu:

```typescript
// Di items.tsx
const { data: allRooms } = useRoomsAll();
const { data: allRoomItems } = useAllRoomItems();

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

// Kirim ke MasterDataPage
<MasterDataPage<Item>
  // ...
  renderBadges={(item) =>
    (roomNameMap.get(item.id) ?? []).map((name) => (
      <span key={name} className="...">{name}</span>
    ))
  }
/>
```

> **Catatan:** Pastikan `per_page` di backend cukup besar (`le=10000`) untuk menampung semua data rooms/items saat menggunakan `useRoomsAll()` / `useItemsAll()`.

## 7. Troubleshooting

| Masalah | Penyebab | Solusi |
|---------|----------|--------|
| Badge tidak muncul | `renderBadges` tidak di-pass ke `MasterDataPage` | Cek prop `renderBadges` di `rooms.tsx` |
| Badge tidak update setelah assign/unassign | Cache tidak ter-invalidate | Cek `onSuccess` di mutation — harus `invalidateQueries(["room-items"])` |
| Error `renderBadges is not defined` | Prop tidak di-destructure di `MasterDataPage` | Tambah `renderBadges` ke destructuring parameter |
| Badge kosong untuk semua room | `allItems` atau `allRoomItems` undefined | Cek apakah endpoint `/api/items` dan `/api/room-items` merespon 200 |
| Data tidak fresh | Query cache terlalu lama | Set `staleTime` atau panggil `invalidateQueries` manual |

## 8. Referensi

- `web-admin/src/routes/rooms.tsx` — implementasi utama
- `web-admin/src/components/MasterDataPage.tsx` — komponen generic dengan `renderBadges` prop
- `web-admin/src/hooks/useMasterData.ts` — hook `useAllRoomItems()`, `useItemsAll()`
- `backend/app/modules/master/api.py` — endpoint `/api/room-items`, `/api/rooms/{id}/items`
- ADR-0009: Room-Item Many-to-Many Relationship
- `docs/10-pagination-architecture.md` — penjelasan limit `per_page=10000`
