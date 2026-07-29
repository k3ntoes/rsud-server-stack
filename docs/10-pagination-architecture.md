# Arsitektur Pagination — RSUD Ajibarang Server Stack

> **Review date:** July 29, 2026  
> **Scope:** Backend (Python/FastAPI) + Frontend (React/TypeScript)  
> **Status:** ✅ Implemented, 136 tests pass

---

## 1. Ringkasan

Pagination diimplementasikan secara **server-driven** (offset/limit) untuk 4 module:

| Module | Endpoint | Frontend Hook |
|--------|----------|---------------|
| Users | `GET /api/auth/users` | `useUsers()` |
| Rooms | `GET /api/rooms` | `useRooms()` |
| Inspection Items | `GET /api/inspection-items` | `useItems()` |
| Inspections | `GET /api/inspections` | `useInspections()` |

---

## 2. Layer Overview

```
Backend                          Frontend
─────────                        ────────
core/pagination.py  ◄── Pydantic model + factory
core/sorting.py     ◄── Allowlist-based ORDER BY

    │                                    │
    ▼                                    ▼
modules/*/api.py    ◄── Query params     hooks/*.ts    ◄── Query builder
modules/*/services.py ◄── offset/limit   components/DataTable.tsx ◄── @tanstack/react-table
```

---

## 3. Backend: `core/pagination.py`

**File:** `backend/app/core/pagination.py`

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int          # (total + per_page - 1) // per_page


def paginate(items: list, total: int, page: int, per_page: int):
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=max(1, (total + per_page - 1) // per_page),
    )
```

### Design Decisions

| Aspek | Keputusan | Alasan |
|-------|-----------|--------|
| **Generic** | `Generic[T]` via `TypeVar` | Reusable untuk Room, User, Item, Inspection |
| **`total_pages`** | Dihitung backend-side | FE tidak perlu hitung manual |
| **`max(1, ...)`** | Minimal 1 page | Standar API response, tidak masalah walau data kosong |
| **Return type** | `dict` (via Pydantic) | FastAPI auto-serialize ke JSON |

---

## 4. Backend: `core/sorting.py`

**File:** `backend/app/core/sorting.py`

```python
_SORTABLE = {
    User: {"username", "role", "is_active", "created_at"},
    Room: {"name", "is_active", "updated_at"},
    InspectionItem: {"name", "is_active", "updated_at"},
    Inspection: {"business_date", "status", "created_at", "room_id"},
}


def apply_sorting(query, model, sort_by, sort_order):
    allowed = _SORTABLE.get(model)
    if not allowed or sort_by not in allowed:
        return query            # fallback — no sorting
    col = getattr(model, sort_by, None)
    if col is None:
        return query
    order_fn = desc if sort_order == "desc" else asc
    return query.order_by(order_fn(col))
```

### Allowlist Pattern ✅

- **Mencegah SQL injection** — hanya column names yang terdaftar yang bisa dipakai
- **Reusable** — cukup tambah entry di `_SORTABLE` dict untuk model baru
- **Fallback safe** — jika column tidak valid, return query tanpa sorting

---

## 5. Backend Services: Dual Mode (Sync vs Paginated)

**File:** `backend/app/modules/master/services.py`

Fungsi `list_rooms()` dan `list_items()` punya **dual return type** untuk mendukung Android sync:

```python
async def list_rooms(
    db, since: datetime | None = None,
    page: int = 1, per_page: int = 20, ...
) -> tuple[list[Room], int] | list[Room]:
    """
    If `since` is provided, returns unpaginated list (Android sync mode).
    Otherwise returns (paginated_list, total_count).
    """
    if since:
        return list(result.scalars().all())         # ← return list saja

    # Web admin: paginated
    return list(result.scalars().all()), total       # ← return tuple
```

### Trade-off

| Approach | Pro | Kontra |
|----------|-----|--------|
| **Dual return type** (saat ini) | Satu endpoint untuk Android + Web | Type checker harus handle 2 return type |
| Pisah 2 fungsi terpisah | Type-safe | Duplikasi kode, over-engineering untuk scale saat ini |

**Keputusan:** Dual mode cukup untuk sekarang. Jika makin kompleks, bisa dipisah jadi `list_rooms_sync()` dan `list_rooms_paginated()`.

---

## 6. API Layer: Query Parameter Convention

Semua endpoint paginated mengikuti pola yang konsisten:

```python
@router.get("/rooms")
async def get_rooms(
    since: str | None = Query(None),                    # Android sync (optional)
    page: int = Query(1, ge=1),                         # 1-indexed
    per_page: int = Query(20, ge=1, le=10000),           # max 10000 (get-all pattern)
    search: str | None = Query(None),                    # global search
    sort_by: str | None = Query(None),                   # column name
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),  # regex validated
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    ...
```

> **Catatan:** Endpoint master data (`/rooms`, `/inspection-items`) menggunakan `le=10000` karena frontend punya pola "get all" (`useRoomsAll()`, `useItemsAll()`) yang mengirim `per_page=10000`. Endpoint auth & inspection tetap `le=100` karena hanya dipakai dengan pagination normal via DataTable.

### Validasi

- `page` — minimal 1 (`ge=1`)
- `per_page` — antara 1-10000 untuk master data; 1-100 untuk auth & inspection
- `sort_order` — hanya `"asc"` atau `"desc"` via regex `pattern`
- `sort_order` — hanya `"asc"` atau `"desc"` via regex `pattern`
- `sort_by` — divalidasi oleh allowlist di `sorting.py`

---

## 7. Flow Example: GET /api/rooms

```
Request:
  GET /api/rooms?page=1&per_page=20&search=UGD&sort_by=name&sort_order=asc

Flow:
  1. master/api.py → terima query params
  2. list_rooms() → bangun query + count_query
     - search: WHERE name ILIKE '%UGD%'
     - sort: ORDER BY name ASC
     - offset: 0, limit: 20
  3. Return (items, total)
  4. paginate(items, total, 1, 20)

Response:
  {
    "items": [{ "id": 1, "name": "UGD", ... }],
    "total": 3,
    "page": 1,
    "per_page": 20,
    "total_pages": 1
  }
```

---

## 8. Frontend: `DataTable.tsx`

**File:** `web-admin/src/components/DataTable.tsx`

Menggunakan `@tanstack/react-table` dengan **manual server-driven mode**:

```typescript
const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,         // server-driven
    manualSorting: true,             // server-driven
    enableSorting: true,
    enableMultiSort: false,          // single column sort only
    pageCount: totalPages,
    state: { pagination, sorting: sorting ?? [] },
    onPaginationChange,
    onSortingChange: onSortingChange ?? (() => {}),
});
```

### Fitur DataTable

| Fitur | Status |
|-------|--------|
| Server-driven pagination | ✅ |
| Server-driven sorting | ✅ |
| Page size selector (10/20/50/100) | ✅ |
| Page numbers with ellipsis | ✅ |
| Previous/Next buttons | ✅ |
| Sort indicator icons (↑↓) | ✅ |
| Loading skeleton | ✅ |
| Error state | ✅ |
| Empty state | ✅ |
| Row click handler | ✅ |

---

## 9. Frontend Hooks: Query Key Design

Semua hooks mengikuti pattern yang konsisten:

```typescript
// useRooms
queryKey: ["rooms", page, perPage, search, sortBy, sortOrder]

// useUsers
queryKey: ["users", page, perPage, search, sortBy, sortOrder]

// useInspections
queryKey: ["inspections", params, page, perPage, sortBy, sortOrder]
```

**Query key granular** — setiap kombinasi filter/sort/page punya cache sendiri (`@tanstack/react-query`).
**Mudah di-invalidate** — mutation success cukup `invalidateQueries({ queryKey: ["rooms"] })`.

### Parameter Mapping

| FE Hook Param | Backend Query Param | Konversi |
|---------------|---------------------|----------|
| `page` (0-indexed) | `page` (1-indexed) | `page + 1` |
| `perPage` | `per_page` | langsung |
| `search` | `search` | langsung |
| `sortBy` | `sort_by` | langsung |
| `sortOrder` | `sort_order` | langsung |

---

## 10. Temuan & Catatan

| # | Issue | Severity | Detail |
|---|-------|----------|--------|
| 1 | **Dual return type** di `list_rooms()`/`list_items()` | 🟡 | Pragmatis untuk sekarang. Pisah jadi 2 fungsi jika makin kompleks |
| 2 | **No N+1 guard** di count_query inspection filter | 🟢 | Count query jalan 2x (filter + total), masih acceptable |
| 3 | **`max(1, ...)`** di `total_pages` | 🟢 | Total pages = 1 walau 0 data. Standar API, tidak masalah |
| 4 | **No `total_pages` validation** | 🟢 | Jika total = 0, total_pages = 1, page valid, items kosong. Perilaku benar |
| 5 | **`per_page` limit tidak seragam** | 🟢 | Master data `le=10000` untuk get-all pattern, auth/inspection `le=100` untuk pagination normal |

---

## 11. Security Checklist

| Aspek | Status | Mekanisme |
|-------|--------|-----------|
| SQL Injection via `sort_by` | ✅ Terproteksi | Allowlist di `_SORTABLE` dict |
| SQL Injection via `search` | ✅ Terproteksi | SQLAlchemy `ilike()` dengan parameter binding |
| Page number overflow | ✅ Terproteksi | Jika page > total_pages, return items kosong (bukan error) |
| DoS via large `per_page` | ✅ Terproteksi | `le=100` (auth/inspection) atau `le=10000` (master) di Query param |
| Auth untuk paginated endpoint | ✅ Terproteksi | Dependency injection (`get_current_user`, `get_admin_user`) |

---

## 12. Related Files

| File | Role |
|------|------|
| `backend/app/core/pagination.py` | Pydantic model + pagination factory |
| `backend/app/core/sorting.py` | Allowlist-based ORDER BY |
| `backend/app/modules/auth/api.py` | Users endpoint dengan pagination |
| `backend/app/modules/auth/services.py` | `list_users()` dengan count query |
| `backend/app/modules/inspection/api.py` | Inspections endpoint dengan pagination |
| `backend/app/modules/inspection/services.py` | `list_inspections()` dengan count query |
| `backend/app/modules/master/api.py` | Rooms + Items endpoint dengan pagination |
| `backend/app/modules/master/services.py` | `list_rooms()` + `list_items()` dual mode |
| `web-admin/src/components/DataTable.tsx` | Reusable table dengan pagination + sorting |
| `web-admin/src/components/Icons.tsx` | Sort indicator icons |
| `web-admin/src/components/MasterDataPage.tsx` | Master data CRUD dengan pagination |
| `web-admin/src/hooks/useMasterData.ts` | `useRooms()`, `useItems()`, `useItemsAll()` |
| `web-admin/src/hooks/useUsers.ts` | `useUsers()` |
| `web-admin/src/hooks/useInspections.ts` | `useInspections()` |
| `web-admin/src/hooks/useDebounce.ts` | Debounce untuk search input |
