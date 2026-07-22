# ADR-0005: Async ORM Strategy — `joinedload` over `selectinload`

**Status**: Accepted

Semua query async di SQLAlchemy yang membutuhkan eager loading relasi menggunakan **`joinedload`** (SQL JOIN) daripada **`selectinload`** (query terpisah). Keputusan ini diambil setelah `selectinload` menyebabkan `MissingGreenlet` error pada test dengan aiosqlite.

## Context

SQLAlchemy 2.0 async session (`AsyncSession`) menggunakan greenlet internally untuk context switching. `selectinload` dan `subqueryload` menjalankan query terpisah saat relasi diakses, yang memicu greenlet switch. Dalam test environment dengan aiosqlite, greenlet switch ini gagal karena SQLite connection bersamaan tidak didukung.

## Detail Masalah

- `selectinload` di async context memicu `MissingGreenlet` ketika data relasi diakses setelah session di-`await`
- Test dengan in-memory SQLite sangat rentan karena aiosqlite tidak mendukung concurrent queries dalam satu session
- Masalah muncul di semua endpoint yang mengembalikan Inspection dengan details dan photos

## Solusi

```python
# Sebelum (MissingGreenlet di async test):
from sqlalchemy.orm import selectinload
stmt = select(Inspection).options(selectinload(Inspection.details))

# Sesudah (single JOIN, no greenlet):
from sqlalchemy.orm import joinedload
stmt = select(Inspection).options(joinedload(Inspection.details))
result = await db.execute(stmt)
inspection = result.unique().scalar_one_or_none()
```

Pola yang digunakan di semua endpoint inspection:
1. Query dengan `joinedload` chain: `joinedload(Inspection.details).joinedload(InspectionDetail.photos)`
2. Panggil `.unique()` di Result sebelum `.scalars()` untuk deduplikasi baris akibat JOIN
3. Setelah commit, refetch inspection dengan joinedload — `db.refresh()` tidak load relasi

## Konsekuensi

- Tidak ada `MissingGreenlet` di async context — kompatibel dengan aiosqlite
- `.unique()` diperlukan karena JOIN bisa menghasilkan baris duplikat (1 inspection × N details)
- `joinedload` mungkin transfer data lebih besar dari `selectinload` untuk row dengan banyak relasi — tetapi inspection items biasanya <20 item per inspeksi
- Semua 5 fungsi inspection (submit, list, get, approve, reject) menggunakan pola yang konsisten

## Referensi

- Lihat `backend/app/modules/inspection/services.py` untuk implementasi
