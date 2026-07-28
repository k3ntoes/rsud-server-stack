# ADR-0009: Room-Item Many-to-Many Relationship

**Status**: Accepted

Memisahkan item inspeksi dari daftar global menjadi daftar spesifik per ruangan melalui relasi many-to-many.

## Context

Sejak awal proyek, `inspection_items` bersifat **global** — semua item berlaku untuk semua ruangan. Validasi di `inspection/services.py` memeriksa bahwa **semua** active items di-score saat submission:

```python
all_items = await db.execute(
    select(InspectionItem).where(InspectionItem.is_active == True)
)
active_ids = {item.id for item in all_items.scalars().all()}
submitted_ids = {d.item_id for d in data.details}
missing = active_ids - submitted_ids
if missing:
    raise ValueError(f"Missing items: {sorted(missing)}")
```

**Masalah:** Di RSUD Ajibarang, tidak semua ruangan memiliki item inspeksi yang sama. Contoh:
- Ruang operasi punya item "Kebersihan meja operasi" yang tidak relevan untuk ruang tunggu
- Kamar mandi punya item yang berbeda dari ruang administrasi
- Setiap tipe ruangan (rawat inap, ICU, poliklinik, gudang) punya daftar item spesifik

## Keputusan

### 1. Tabel Pivot `room_items`

Tambah tabel pivot `room_items` untuk relasi many-to-many:

```python
class RoomItem(Base):
    __tablename__ = "room_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("inspection_items.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("room_id", "item_id", name="uq_room_item"),
    )
```

### 2. Perilaku Item Baru (B2)

Item baru yang dibuat via `/api/inspection-items` **tidak otomatis terasosiasi ke room manapun**.
Admin harus secara eksplisit meng-assign item ke room melalui UI (dari halaman room atau halaman item).

### 3. UI Management (A3 — Kedua Arah)

Admin bisa mengatur relasi dari dua arah:

- **Dari halaman Room** — melihat semua item yang terasosiasi dengan room tertentu, menambah/menghapus item dari room
- **Dari halaman Item** — melihat semua room yang menggunakan item tertentu, menambah/menghapus room dari item

### 4. Validasi Submission Ketat (D1)

Saat inspeksi di-submit, validasi berubah dari "semua active items" menjadi "semua item yang terasosiasi dengan room tersebut":

```python
room_items = await db.execute(
    select(RoomItem).where(RoomItem.room_id == data.room_id)
)
room_item_ids = {ri.item_id for ri in room_items.scalars().all()}
submitted_ids = {d.item_id for d in data.details}
missing = room_item_ids - submitted_ids
if missing:
    raise ValueError(f"Missing items for room: {sorted(missing)}")
```

Item yang tidak terasosiasi dengan room akan ditolak (tidak bisa di-submit untuk room tersebut).

### 5. Android Sync (C2 — All Relations)

Endpoint baru `GET /api/room-items?since=...` mengembalikan semua relasi room↔item sekaligus. Android membangun mapping lokal (`roomId → [itemId, ...]`) untuk mode offline.

Response format:
```json
{
  "data": [
    { "room_id": 1, "item_id": 1 },
    { "room_id": 1, "item_id": 2 },
    { "room_id": 2, "item_id": 1 }
  ],
  "synced_at": "2026-07-28T12:00:00Z"
}
```

### 6. Migrasi Data (E1 — Auto-Assign)

Saat migration dijalankan, semua item aktif akan di-assign ke semua room aktif:

```sql
INSERT INTO room_items (room_id, item_id, created_at)
SELECT r.id, i.id, NOW()
FROM rooms r, inspection_items i
WHERE r.is_active = true AND i.is_active = true;
```

Ini memastikan backward compatibility — tidak ada perubahan perilaku setelah deploy.

### 7. API Endpoints Baru

| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| GET | `/api/room-items` | Bearer | Sync all relations (`?since=`) |
| GET | `/api/rooms/{id}/items` | Bearer | List items for a room |
| POST | `/api/rooms/{id}/items` | Admin | Assign item to room `{ "item_id": 1 }` |
| DELETE | `/api/rooms/{id}/items/{item_id}` | Admin | Remove item from room |
| GET | `/api/inspection-items/{id}/rooms` | Bearer | List rooms for an item |
| POST | `/api/inspection-items/{id}/rooms` | Admin | Assign room to item `{ "room_id": 1 }` |
| DELETE | `/api/inspection-items/{id}/rooms/{room_id}` | Admin | Remove room from item |

## Pertimbangan yang Ditolak

| Alternatif | Alasan Ditolak |
|-----------|----------------|
| One-to-Many (setiap item khusus satu room) | Item tidak bisa di-reuse antar room — menyebabkan duplikasi data dan inkonsistensi nama |
| Item baru auto-assign ke semua room (B1) | Tidak bersih secara desain — item baru harus di-assign dengan sengaja, bukan default |
| Validasi longgar (D2 — item tidak wajib lengkap) | Checklist inspeksi RS harus lengkap — tidak boleh ada item yang sengaja dilewati |
| Android sync per-room (C1 — lazy) | Mode offline membutuhkan semua data di-pull terlebih dahulu |
| Biarkan data existing tidak ter-assign (E2) | Merusak workflow yang sudah berjalan — semua room akan gagal submit karena missing items |
| Hanya UI dari satu arah (A1 atau A2) | Admin perlu fleksibilitas — kadang ingin lihat dari sisi room, kadang dari sisi item |

## Konsekuensi

- Backward compatible — data lama tetap berfungsi karena migrasi auto-assign
- Android perlu endpoint sync baru untuk room-items
- UI frontend perlu komponen baru untuk manage relasi room↔item (dua arah)
- Validasi submission berubah dari `all active items` → `items assigned to room`
- Tidak ada perubahan di tabel `inspections` / `inspection_details` — data historis tetap valid (item_id sudah tersimpan sebagai snapshot)
- Unit test perlu update: test validasi submission harus pakai room-specific items
- API contract Android perlu update: tambah endpoint room-items sync

## Referensi

- Database schema: `docs/01-database-schema.md`
- Android API contract: `docs/android-to-be-api-contract.md`
- Master data module: `backend/app/modules/master/`
- Inspection submission logic: `backend/app/modules/inspection/services.py`
- ADR-0001: React + Vite Frontend Stack
- ADR-0002: Multi-Photo Schema
