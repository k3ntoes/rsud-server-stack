# ADR-0006: Test Strategy — pytest-asyncio + In-Memory SQLite

**Status**: Accepted

Unit test backend menggunakan **pytest + pytest-asyncio** dengan **in-memory SQLite** (`sqlite+aiosqlite://`). Test terisolasi per fungsi dengan create/drop tables di setiap sesi.

## Context

Backend menggunakan SQLAlchemy async session. Testing async code memerlukan event loop management dan isolation database. In-memory SQLite memberikan kecepatan maksimal tanpa setup eksternal.

## Test Architecture

```python
# conftest.py — pola dependency override
@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

## Cakupan Test

| Modul | Test Count | Coverage |
|-------|-----------|----------|
| Auth | 11 | Login (success, invalid, inactive, nonexistent), /me (auth, no token, wrong type, wrong signature), refresh (with/without cookie), logout |
| Master | 14 | Rooms + Items CRUD, duplicate, soft-delete, not-found, non-admin 403 |
| Inspection | 10 | Submit, duplicate 409, list (supervisor OK, inspector 403), detail, approve, reject, reject with reason, approve-already-approved 400, inspector-can't-approve 403, not-found 404 |

## Key Decisions

- **`@pytest.mark.asyncio`** pada setiap test function — pytest-asyncio manage event loop lifecycle
- **`app.dependency_overrides[get_db]`** untuk inject test database — FastAPI native pattern
- **In-memory SQLite** — `sqlite+aiosqlite://` (tanpa path file) — clean isolation
- **Create/drop tables** per test function — isolation penuh tanpa side effect
- **httpx AsyncClient** untuk integration test — FastAPI TestClient tidak support async natively
- **`PYTHONPATH=.`** diperlukan — `uv run` tidak menambahkan cwd ke Python path

## What Not To Do

- Jangan gunakan `selectinload` di test — akan trigger `MissingGreenlet` (lihat ADR-0005)
- Jangan gunakan TestClient FastAPI untuk async test — gunakan httpx AsyncClient
- Jangan override `event_loop` fixture — pytest-asyncio manage secara otomatis

## Menjalankan Test

```bash
cd backend && PYTHONPATH=. uv run pytest tests/ -v
```

## Konsekuensi

- 35 test, semuanya passing dalam ~18s
- Tidak ada dependency ke PostgreSQL — cocok untuk CI
- Test isolation sempurna — create/drop tables per test
- Developer cukup `uv sync --group dev && make test`
