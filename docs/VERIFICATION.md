# Verifikasi CLAUDE.md — Auto-Read Test

## Tujuan

Memastikan AI tools (Freebuff, Cursor, Claude Code, dll) membaca `CLAUDE.md` dan `knowledge.md` secara otomatis di awal sesi.

## Tes 1: Graphify Query (Wajib)

**Langkah:**

1. Buka terminal di project root
2. Jalankan AI tool (Freebuff/Cursor/Claude Code) dalam sesi **baru**
3. Ketik prompt berikut:

```
Bagaimana alur login di aplikasi ini? Jangan baca file langsung.
```

**Expected Behavior (✅ PASS):** Agent menjalankan `graphify query "Bagaimana alur login?"` sebelum membaca file.

**Failure Behavior (❌ FAIL):** Agent langsung `grep`, `read_files`, atau `code-searcher` tanpa graphify query.

## Tes 2: Context7 (Jika perlu dokumentasi library)

**Langkah:**

1. Dalam sesi baru, ketik:

```
Apa cara terbaik menggunakan SQLAlchemy joinedload di FastAPI async?
```

**Expected Behavior (✅ PASS):** Agent load `skill("context7-mcp")` → `resolve-library-id` → `query-docs`.

**Failure Behavior (❌ FAIL):** Agent pakai `researcher_web` / `read_url` / `skill("find-docs")`.

## Tes 3: CODING-RULES.md Wajib Dibaca Sebelum Claim/Implement

**Langkah:**

1. Dalam sesi baru, minta: _"Buat issue baru untuk nambah logging di auth module"_
2. Lihat apakah agent membaca `CODING-RULES.md` sebelum atau setelah `bd create`

**Expected Behavior (✅ PASS):** Agent membaca `CODING-RULES.md` (YAGNI/KISS/DRY, safety, research workflow) **sebelum** `bd create` atau `bd update --claim`.

**Failure Behavior (❌ FAIL):** Agent `bd create` / `bd update --claim` tanpa baca `CODING-RULES.md` dulu.

## Tes 4: Issue-Driven Changes

**Langkah:**

1. Dalam sesi baru, minta: _"Tambah komentar TODO di `backend/app/main.py`"_
2. Lihat apakah agent membuat Beads issue dulu sebelum mengedit

**Expected Behavior (✅ PASS):** Agent menjalankan `bd create` sebelum mengubah file (setelah baca `CODING-RULES.md`).

**Failure Behavior (❌ FAIL):** Agent langsung edit tanpa issue.

## Cara Interpretasi Hasil

| Skenario | Artinya |
|----------|---------|
| ✅ Tes 1 PASS + Tes 2 PASS | CLAUDE.md + AGENTS.md terbaca ✅ |
| ✅ Tes 1 PASS, ❌ Tes 2 FAIL | Hanya Graphify rules yang terbaca (mungkin agent skip load skill) |
| ❌ Tes 1 FAIL | CLAUDE.md / AGENTS.md **tidak terbaca otomatis** — perlu konfigurasi manual |

## Perbaikan Jika Gagal

| AI Tool | Yang Perlu Dilakukan |
|---------|---------------------|
| **Freebuff** | Pastikan `knowledge.md` ada di root (auto-inject). `AGENTS.md` dan `CLAUDE.md` auto-read. |
| **Cursor** | Buat `.cursorrules` di root (copy dari `CLAUDE.md` atau `knowledge.md`). |
| **Claude Code** | `CLAUDE.md` auto-read. Jika tidak, cek versi dan dokumentasi. |
| **GitHub Copilot** | Buat `.github/copilot-instructions.md`. |
| **Lainnya** | Cek dokumentasi tool untuk file konfigurasi yang didukung. |

## File Terkait

| File | Fungsi | Auto-read? |
|------|--------|-----------|
| `knowledge.md` | Ultra-ringkas (prioritas mutlak) | ✅ Freebuff auto-inject |
| `CLAUDE.md` | Quick-reference lengkap | ✅ Freebuff, Claude Code |
| `AGENTS.md` | Detail workflow, exception, tabel | ✅ Freebuff auto-read |
| `.cursorrules` | (belum ada) | ✅ Cursor |
| `.github/copilot-instructions.md` | (belum ada) | ✅ GitHub Copilot |
