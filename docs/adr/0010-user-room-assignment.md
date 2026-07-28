# ADR-0010: User-Room Assignment (Inspector & Supervisor)

**Status**: Accepted

Menambahkan relasi many-to-many antara User (role `inspector` dan `supervisor`) dengan Room, sehingga setiap petugas hanya bisa melakukan inspeksi/approval pada room yang di-assign ke mereka.

## Context

Sejak awal proyek, **tidak ada relasi** antara User dan Room — seorang inspector bisa mengirim inspeksi ke room manapun, dan supervisor bisa melihat/menyetujui inspeksi dari semua room. Tidak ada mekanisme tanggung jawab atau filtering per petugas.

**Masalah:**
1. Petugas kebersihan (`inspector`) di RSUD Ajibarang memiliki tanggung jawab spesifik per ruangan — petugas A hanya membersihkan ruang rawat inap, petugas B hanya membersihkan ICU
2. Supervisor juga memiliki tanggung jawab per ruangan — supervisor A mengawasi UGD dan Rawat Inap, supervisor B mengawasi ICU dan Poliklinik
3. Tidak ada filter default di halaman approval — supervisor melihat semua inspeksi dari seluruh RS tanpa prioritas
4. Tidak ada dasar untuk laporan akuntabilitas per petugas per ruangan

## Keputusan

### 1. Tabel Pivot `user_rooms`

Tabel pivot terpisah dari `room_items` (domain berbeda — user vs item):

```python
class UserRoom(Base):
    __tablename__ = "user_rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("user_id", "room_id", name="uq_user_room"),
    )
```

Relasi many-to-many — satu user bisa di-assign ke banyak room, satu room bisa di-assign ke banyak user.

### 2. Role Coverage

Relasi `user_rooms` berlaku untuk role:
- **`inspector`** — membatasi room yang bisa di-inspeksi
- **`supervisor`** — membatasi room yang muncul di daftar approval (default filter)

`admin_ppi` tidak perlu di-assign — mereka bisa mengelola semua data dari dashboard.

### 3. Validasi Submission (Inspector)

Saat submit inspeksi (`POST /api/inspections`), sistem memvalidasi:

```python
# Cek apakah room di-assign ke inspector ini
assignment = await db.execute(
    select(UserRoom).where(
        UserRoom.user_id == current_user.id,
        UserRoom.room_id == data.room_id,
    )
)
if assignment.scalar_one_or_none() is None:
    raise ValueError(f"Room {data.room_id} is not assigned to you")
```

### 4. Filter Approval (Supervisor)

Supervisor membuka halaman approval — default filter hanya menampilkan inspeksi untuk room yang di-assign:

```python
# Default: hanya room yang di-assign
assigned_room_ids = await db.execute(
    select(UserRoom.room_id).where(UserRoom.user_id == current_user.id)
)
room_ids = [r for r in assigned_room_ids.scalars().all()]

# Tapi supervisor bisa override filter "Lihat semua room"
if not show_all:
    query = query.where(Inspection.room_id.in_(room_ids))
```

Implementasi dengan query parameter `?show_all=true` pada `GET /api/inspections`.

### 5. Android Sync

Endpoint sync: user hanya menerima room yang di-assign ke dirinya — tidak perlu full mapping seperti room-items.

**Endpoint**: `GET /api/auth/me/rooms?since=...`

Response:
```json
{
  "data": [
    { "id": 1, "name": "UGD", "is_active": true },
    { "id": 2, "name": "ICU", "is_active": true }
  ],
  "synced_at": "2026-07-28T12:00:00Z"
}
```

Android menyimpan daftar room ini dan hanya menampilkan room yang relevan pada petugas tersebut.

### 6. UI Management

Admin PPI bisa mengatur asosiasi user↔room dari **kedua arah**:
- **Dari halaman User** (pengguna) — daftar checkbox semua room, centang room mana yang ditanggung user tersebut
- **Dari halaman Room** — daftar checkbox semua inspector & supervisor, centang siapa yang bertanggung jawab

### 7. Migrasi Data (F1 — Auto-Assign)

Saat migration dijalankan, semua user dengan role `inspector` dan `supervisor` akan di-assign ke semua room aktif:

```sql
INSERT INTO user_rooms (user_id, room_id, created_at)
SELECT u.id, r.id, NOW()
FROM users u, rooms r
WHERE u.role IN ('inspector', 'supervisor')
  AND u.is_active = true
  AND r.is_active = true;
```

Backward compatible — workflow tidak berubah setelah deploy.

### 8. API Endpoints Baru

| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| GET | `/api/auth/me/rooms` | Bearer | List room assignments for current user (`?since=`) |
| GET | `/api/rooms/{id}/users` | Admin | List users assigned to a room |
| POST | `/api/rooms/{id}/users` | Admin | Assign user to room `{ "user_id": 1 }` |
| DELETE | `/api/rooms/{id}/users/{user_id}` | Admin | Remove user from room |
| GET | `/api/auth/users/{id}/rooms` | Admin | List rooms assigned to a user |
| POST | `/api/auth/users/{id}/rooms` | Admin | Assign room to user `{ "room_id": 1 }` |
| DELETE | `/api/auth/users/{id}/rooms/{room_id}` | Admin | Remove room from user |

### 9. Perubahan Endpoint Existing

| Endpoint | Perubahan |
|----------|-----------|
| `POST /api/inspections` | Validasi `room_id` terhadap `user_rooms` untuk role `inspector` |
| `GET /api/inspections` | Filter default berdasarkan `user_rooms` untuk role `supervisor` (kecuali `?show_all=true`) |
| `GET /api/auth/users` | Masing-masing user menyertakan daftar room IDs yang di-assign |

## Pertimbangan yang Ditolak

| Alternatif | Alasan Ditolak |
|-----------|----------------|
| Hanya untuk inspector (B) | Supervisor juga bertanggung jawab atas room tertentu — perlu filter approval |
| Satu tabel dengan room_items (B) | User dan Item adalah domain berbeda — mencampur mereka di satu tabel pivot melanggar separation of concern |
| Supervisor selalu lihat semua room (default global) | Supervisor kewalahan dengan semua inspeksi — prioritas harus ke room tanggung jawabnya |
| Backup approval via delegasi otomatis | Over-engineered untuk kebutuhan saat ini — toggle "Lihat semua room" sudah cukup |
| `admin_ppi` juga perlu assign room | Admin PPI mengelola semua data — tidak perlu dibatasi |

## Konsekuensi

- Backward compatible — migrasi auto-assign semua existing user ke semua room
- Android perlu endpoint `GET /api/auth/me/rooms` untuk filter daftar room di perangkat petugas
- UI frontend perlu komponen baru untuk manage asosiasi user↔room (dua arah)
- Validasi submission inspeksi bertambah: cek `user_rooms` untuk role `inspector`
- Filter default approval untuk `supervisor`: hanya room yang di-assign
- Tidak ada perubahan di tabel `inspections` — data historis tetap valid
- Admin dapat mengatur beban kerja per petugas dengan assign/remove room

## Referensi

- ADR-0003: JWT Layered Auth
- ADR-0008: User Management & Monitoring
- ADR-0009: Room-Item Many-to-Many Relationship
- `backend/app/modules/auth/` — auth module
- `backend/app/modules/master/` — master data module
- `backend/app/modules/inspection/services.py` — submission validation
