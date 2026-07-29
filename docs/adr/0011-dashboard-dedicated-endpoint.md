# ADR-0011: Dedicated Dashboard Endpoint — `GET /api/analytics/dashboard`

**Status**: Accepted

Menggabungkan 4 kartu statistik dashboard (pending count, total rooms, monthly inspection count, average score) menjadi **satu endpoint** khusus, menggantikan pola 3 panggilan API terpisah.

---

## Context

Halaman dashboard sebelumnya membutuhkan **3 panggilan API terpisah** untuk menampilkan 4 kartu statistik:

| Kartu | Endpoint | Tujuan |
|-------|----------|--------|
| ⏳ Menunggu Persetujuan | `GET /api/inspections?status=PENDING&page=1&per_page=1` | Ambil `total` pending |
| 🏥 Total Ruangan | `GET /api/rooms?per_page=10000` | Hitung `items.length` |
| 📋 Inspeksi Bulan Ini | `GET /api/analytics/summary` | Ambil `monthly_inspection_count` |
| 📊 Skor Rata-rata | `GET /api/analytics/summary` | Ambil `avg_score_pct` |

**Masalah:**
1. **3 round-trip HTTP** — dashboard harus menunggu 3 response sebelum render
2. **Over-fetching** — endpoint `/api/inspections` dengan `per_page=1` hanya untuk dapat `total` field, data items tidak dipakai
3. **Over-fetching** — endpoint `/api/rooms` dengan `per_page=10000` fetch semua data room hanya untuk `.length`
4. **Cache fragmentation** — 3 query key terpisah di React Query, invalidasi tidak atomik
5. **Frontend complexity** — 3 hook berbeda harus di-import, di-coordinate, error handling masing-masing

## Keputusan

### 1. Satu Endpoint Khusus: `GET /api/analytics/dashboard`

```python
@router.get("/dashboard", response_model=DashboardOut)
async def dashboard_data(
    year_month: str | None = Query(None, description="YYYY-MM, defaults to current"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_supervisor_user),
):
    return await get_dashboard_data(db, year_month)
```

### 2. Response Format

```json
{
  "pending_count": 5,
  "total_rooms": 12,
  "monthly_inspection_count": 34,
  "avg_score_pct": 82.5
}
```

| Field | Tipe | Sumber Data | Deskripsi |
|-------|------|-------------|-----------|
| `pending_count` | int | `SELECT COUNT(*) FROM inspections WHERE status = 'PENDING'` | Jumlah inspeksi menunggu approval |
| `total_rooms` | int | `SELECT COUNT(*) FROM rooms WHERE is_active = TRUE` | Jumlah ruangan aktif |
| `monthly_inspection_count` | int | `SUM(room_monthly_stats.inspection_count)` | Total inspeksi bulan ini |
| `avg_score_pct` | float | `SUM(total_score) / SUM(max_score) * 100` | Rata-rata skor bulan ini (0–100) |

### 3. Query Strategy — 3 Aggregate Queries dalam 1 Service Function

```python
async def get_dashboard_data(db, year_month=None) -> dict:
    # 1. Pending count — aggregate query
    pending = await db.execute(
        select(func.count(Inspection.id)).where(Inspection.status == "PENDING")
    )

    # 2. Active rooms count — aggregate query
    rooms = await db.execute(
        select(func.count(Room.id)).where(Room.is_active == True)
    )

    # 3. Monthly stats from pre-computed RoomMonthlyStats
    stats = await db.execute(
        select(RoomMonthlyStats).where(RoomMonthlyStats.year_month == ym)
    )
    # Aggregate di memory (rows < 50, negligible)
    monthly_inspections = sum(r.inspection_count for r in rows)
    avg_pct = round(total_score / max_score * 100, 1) if max_score > 0 else 0.0
```

Ketiga query adalah **aggregate query** (COUNT, SUM) — eksekusi sangat cepat, tidak ada N+1.

### 4. Schema Pydantic

```python
class DashboardOut(BaseModel):
    pending_count: int
    total_rooms: int
    monthly_inspection_count: int
    avg_score_pct: float
```

### 5. Frontend — 1 Hook Menggantikan 3

```typescript
// Sebelum: 3 hook
const { data: pendingList } = useInspections({ status: "PENDING" }, 0, 1);
const { data: rooms } = useRoomsAll();
const { data: summary } = useDashboardSummary();

// Sesudah: 1 hook
const { data } = useDashboardData();
```

### 6. Query Key Design

```typescript
queryKey: ["dashboard", ym],  // bersih, cache terpusat
```

### 7. Auth Dependency

Endpoint menggunakan `get_supervisor_user` — hanya Supervisor dan Admin PPI yang bisa mengakses. Inspector mendapat 403.

```
GET /api/analytics/dashboard
→ 200 OK (supervisor/admin)
→ 403 Forbidden (inspector)
```

---

## Pertimbangan yang Ditolak

| Alternatif | Alasan Ditolak |
|-----------|----------------|
| **Tetap 3 panggilan terpisah** (status quo) | 3× round-trip, over-fetching, complex frontend code — masalah utama yang ingin diperbaiki |
| **Nested query di endpoint `/api/inspections`** | Endpoint inspection tidak seharusnya tahu soal room count atau monthly stats — violation of separation of concerns |
| **Computed column di database (materialized view)** | Over-engineering untuk 4 aggregate query sederhana. Tambah latency di writes, maintenance overhead |
| **GraphQL endpoint** | Full-blown GraphQL untuk 1 halaman dashboard adalah overkill. FastAPI + REST sudah cukup |
| **Server-Sent Events (SSE) / WebSocket** | Data dashboard tidak realtime — page load saja cukup. Refresh manual atau polling periodik sudah memadai |
| **Cache Redis terpisah** | Query aggregate sangat cepat (< 10ms). Redis hanya akan nambah infrastruktur tanpa benefit signifikan di scale saat ini |

## Konsekuensi

- ✅ **1 round-trip HTTP** — dashboard render lebih cepat
- ✅ **Zero over-fetching** — endpoint hanya return 4 angka, tanpa data items/list yang tidak dipakai
- ✅ **Frontend simplification** — dari 3 hook + 3 error/loading state jadi 1 hook
- ✅ **Cache atomik** — 1 query key, 1 cache entry, invalidasi bersih
- ✅ **Backward compatible** — endpoint lama tetap ada (`/api/analytics/summary`, `/api/rooms`, `/api/inspections`)
- ❌ **Endpoint baru perlu auth supervisor** — dashboard tidak bisa diakses inspector (sama seperti endpoint analytics lainnya — bukan regresi)
- ⚠️ **Android juga dapat manfaat** — `GET /api/analytics/dashboard` bisa dipakai Android untuk halaman serupa

## Perubahan yang Dilakukan

### Backend

| File | Perubahan |
|------|-----------|
| `backend/app/modules/analytics/schemas.py` | Tambah `DashboardSummaryOut` dan `DashboardOut` |
| `backend/app/modules/analytics/services.py` | Tambah `get_dashboard_summary()` dan `get_dashboard_data()` |
| `backend/app/modules/analytics/api.py` | Tambah `GET /summary` dan `GET /dashboard` |
| `backend/app/modules/master/api.py` | Naikkan `per_page` limit `le=100` → `le=10000` (memungkinkan `useRoomsAll()` bekerja) |

### Frontend

| File | Perubahan |
|------|-----------|
| `web-admin/src/hooks/useAnalytics.ts` | Tambah `useDashboardSummary()` dan `useDashboardData()` |
| `web-admin/src/routes/dashboard.tsx` | Ganti 3 hook jadi 1 `useDashboardData()`, hapus import `useInspections`, `useRoomsAll` |


### Test

Semua test existing pass — endpoint baru tidak mengubah perilaku endpoint lama.

```
18 passed in 11.42s (tests/test_analytics.py)
14 passed in 6.43s  (tests/test_master.py)
```

## Referensi

- Architecture: `docs/04-architecture.md`
- Analytics module: `backend/app/modules/analytics/`
  - `backend/app/modules/analytics/CONTEXT.md` — desain pre-computed analytics aggregation
- Dashboard page: `web-admin/src/routes/dashboard.tsx`
- Hook: `web-admin/src/hooks/useAnalytics.ts`
- ADR-0009: Room-Item Many-to-Many
- ADR-0010: User-Room Assignment
