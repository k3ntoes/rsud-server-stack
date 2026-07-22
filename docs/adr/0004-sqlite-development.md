# ADR-0004: SQLite + aiosqlite untuk Development, PostgreSQL untuk Production

**Status**: Accepted

Development environment menggunakan **SQLite + aiosqlite** sebagai database, sementara production deployment menggunakan **PostgreSQL + asyncpg**. Perbedaan driver ini diakomodasi melalui environment variable `DATABASE_URL`.

## Context

Proyek ini membutuhkan database relasional dengan dukungan async Python. Pada tahap development awal, menyiapkan PostgreSQL di setiap lingkungan developer menambah friction dan overhead. Keputusan ini memisahkan database engine berdasarkan lingkungan.

## Driver Stack

| Lingkungan | Driver | Connection String |
|-----------|--------|-------------------|
| Development | `sqlite+aiosqlite:///./rsud.db` | File-based, zero setup |
| Test | `sqlite+aiosqlite://` | In-memory, auto-cleanup per test |
| Production | `postgresql+asyncpg://user:pass@host:5432/db` | Full PostgreSQL via docker-compose |

## Pertimbangan

- **aiosqlite** adalah SQLite driver async yang kompatibel dengan SQLAlchemy AsyncSession — kode yang sama berjalan di dev dan prod tanpa refactor
- Semua query menggunakan SQLAlchemy ORM (bukan raw SQL), sehingga perbedaan SQL dialect tertangani secara otomatis
- Fitur PostgreSQL yang tidak ada di SQLite (array, JSONB, full-text search) tidak digunakan — semua data dalam bentuk tabel normalized
- Migration (Alembic) harus kompatibel dengan kedua engine — constraint dan default value ditulis dalam SQLAlchemy DDL

## Konsekuensi

- Developer cukup clone repo dan `uv run alembic upgrade head` — tanpa setup PostgreSQL
- Test menggunakan in-memory SQLite — cepat, tidak ada I/O disk
- Migration harus di-test di kedua engine sebelum production deploy
- `PYTHONPATH=.` diperlukan saat menjalankan command dengan `uv run` — uv tidak menambahkan current working directory ke Python path secara default
- Fitur PostgreSQL-native (CONCURRENTLY, partial index, exclusion constraints) tidak dapat digunakan
- Enum type menggunakan String di SQLite — pastikan migration kompatibel

## Related

- Lihat `backend/app/config.py` untuk default dev configuration
- Lihat `docker-compose.yml` untuk production PostgreSQL setup
