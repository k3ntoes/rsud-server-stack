# ADR-0013: Room-Item Ordering — Urutan Item Inspeksi per Ruangan

**Status**: Accepted

Menambahkan kolom `sort_order` pada pivot `room_items` agar item inspeksi per ruangan
tampil dalam urutan yang diatur admin, sehingga inspector tidak perlu scroll-scroll
atau bolak-balik mencari item saat melakukan inspeksi.

## Context

Sebelum keputusan ini, urutan item inspeksi **tidak pernah diatur**:

- `list_items_by_room()` di `master/services.py` mengambil item tanpa `ORDER BY` —
  urutan praktisnya mengikuti insertion order (`id`), bukan kebutuhan lapangan.
- Android membangun mapping `roomId → [itemId]` dari `GET /api/room-items` yang
  diurutkan `(room_id, item_id)` — lagi-lagi urutan `id`.

Inspector (aplikasi Android) mengalami masalah nyata: checklist item tampil acak.
Contoh urutan yang diinginkan: **lantai → tempat tidur → tembok → atap** — mengikuti
alur fisik inspeksi ruangan. Akibatnya inspector harus scroll bolak-balik mencari item
berikutnya, memperlambat inspeksi dan berisiko ada item terlewat.

## Keputusan

### 1. Kolom `sort_order` di tabel pivot `room_items`

```python
sort_order: Mapped[int] = mapped_column(Integer, default=0)
```

- **Per ruangan**, bukan global di `inspection_items` — konsisten dengan ADR-0009
  (tiap ruangan punya set item berbeda, jadi urutan inspeksinya pun wajar berbeda).
- **Backfill** data existing: `sort_order = item_id` → urutan tampilan saat ini
  tidak berubah setelah deploy.
- **Item baru** yang di-assign ke ruangan: append di paling akhir
  (`max(sort_order) + 1`) — tidak menyelinap ke posisi atas tanpa disadari.

### 2. Ordering deterministik

Semua query yang menampilkan item per ruangan memakai:

```sql
ORDER BY sort_order ASC, item_id ASC
```

`item_id` sebagai **tie-breaker** agar urutan deterministik ketika ada `sort_order`
bernilai sama.

### 3. Reorder ikut terkirim via sync (tombstone bump)

Mengubah urutan menaikkan `updated_at` pada baris pivot → sync incremental
`GET /api/room-items?since=` mengirim nilai `sort_order` baru → Android memperbarui
urutan lokal. Reorder hanya menyentuh baris pivot; **tidak perlu** bump parent
`Room.updated_at` / `InspectionItem.updated_at` — Android hanya butuh `sort_order`
terbaru dari pivot, bukan data room/item baru.

### 4. UI Web-Admin — Admin yang mengatur

- Admin PPI mengatur urutan dari halaman **Room** di web-admin.
- Mekanisme: tombol **▲/▼** per item — tanpa dependency library drag-and-drop
  (sejalan dengan filosofi minimal dependensi proyek, lihat ADR-0001).
- Inspector adalah **konsumen** — tidak bisa mengubah urutan di perangkat.

### 5. Android Contract

- `RoomItemOut` (response `/api/room-items` dan `/api/rooms/{id}/items`) bertambah
  field `sort_order`.
- Android mengurutkan item ruangan dengan `(sort_order, item_id)` saat membangun
  checklist inspeksi.
- Karena inspector mengisi item sesuai urutan checklist, `inspection_details`
  tersimpan berurutan → detail view web-admin otomatis rapi tanpa perubahan tambahan.

## Pertimbangan yang Ditolak

| Alternatif | Alasan Ditolak |
|-----------|----------------|
| `sort_order` global di `inspection_items` | Satu urutan untuk semua ruangan — tidak mengakomodasi ruangan dengan kebutuhan urutan berbeda (konsisten dengan alasan ADR-0009 memisahkan daftar item per ruangan) |
| Inspector mengatur urutan di Android | Menambah kompleksitas sync (urutan lokal per device) dan inspeksi bisa berbeda-beda antar inspector; urutan adalah data master, bukan preferensi pribadi |
| Drag & drop di web-admin | Butuh library/HTML5 DnD manual yang ribet di touch device; tombol ▲/▼ cukup untuk skala item per ruangan (umumnya < 20 item) |
| Item baru default `sort_order = 0` | Item baru menyelinap ke posisi awal tanpa disadari; append di akhir lebih intuitif |

## Konsekuensi

- Migrasi baru: tambah kolom `sort_order` di `room_items` + backfill `sort_order = item_id`.
- `list_items_by_room()` dan `GET /api/rooms/{id}/items` diurutkan `(sort_order, item_id)`.
- Endpoint reorder baru (admin) untuk tombol ▲/▼ — bentuk endpoint mengikuti
  konvensi existing (kemungkinan besar `PUT /api/rooms/{id}/items/reorder` dengan
  body daftar `item_id` terurut, atau operasi move per posisi).
- API contract Android perlu update: tambah `sort_order` di payload room-items.
- **Tidak terpengaruh:** validasi submission (semua item ruangan wajib di-score),
  snapshot `item_name_snapshot`, skor & analitik, urutan tampilan inspeksi lama
  (tetap mengikuti urutan submission via `inspection_details.id`).

## Referensi

- ADR-0009: Room-Item Many-to-Many Relationship — dasar pivot `room_items`
- Database schema: `docs/01-database-schema.md`
- Android API contract: `docs/android-to-be-api-contract.md`
- Master data module: `backend/app/modules/master/`
- Precedent kolom `sort_order`: `inspection_photos.sort_order` (ADR-0002)
