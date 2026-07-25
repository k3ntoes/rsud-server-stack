# RSUD Ajibarang — Quick Reference for AI Agents

> **CLAUDE.md ini dibaca otomatis oleh AI tools tertentu (Claude Code, Cursor via CLAUDE.md).** Ringkasan cepat di bawah. Detail lengkap: `AGENTS.md` dan `CODING-RULES.md`.

---

## 🎯 Prioritas Eksplorasi Codebase (Hemat Token)

Gunakan urutan ini — jangan langsung baca file:

```
➊ graphify query "<pertanyaan>"    → pahami arsitektur & relasi kode internal
➋ skill("context7-mcp") → query-docs  → dokumentasi library eksternal
➌ impact({target: "symbolName"})   → analisis dampak sebelum edit
➍ Baca file spesifik               → hanya file yang disebut di atas
```

---

## ➊ Graphify — Pahami Codebase Internal

Graphify (v0.9.23) — **442 node, 1,013 edges**. Gunakan sebelum membaca file:

```bash
graphify query "Bagaimana alur login?"   # ~100-500 token vs ~ribuan token baca file
graphify path "User" "Room"              # jalur terpendek antar konsep
graphify explain "get_current_user"       # detail simbol/modul
```

- ✅ **WAJIB:** `graphify query` sebelum `read_files`/`grep`/`code-searcher`
- ❌ **JANGAN:** `grep`/`read_subtree` untuk arsitektur tingkat tinggi
- ❌ **JANGAN:** baca file secara buta tanpa tahu yang dicari

> Update setelah refactor besar: `graphify extract ./backend/ --code-only --no-viz && graphify extract ./web-admin/ --code-only --no-viz && graphify merge-graphs ./backend/graphify-out/graph.json ./web-admin/graphify-out/graph.json --out graphify-out/graph.json`

---

## ➋ Context7 — Dokumentasi Library Eksternal

Untuk **React, FastAPI, SQLAlchemy, Next.js, dll**. Jangan pakai `researcher_web`:

```python
skill("context7-mcp")                                     # load skill dulu
resolve-library-id(libraryName: "fastapi", query: "...")   # cari ID library
query-docs(libraryId: "/fastapi/fastapi", query: "...")    # fetch docs per konsep
```

| ✅ Context7 ~100-500 token | ❌ `researcher_web` + `read_url` ~2,000-5,000+ token |
|------------------------------|--------------------------------------------------------|

- ❌ **JANGAN** pakai `researcher_web`/`read_url` untuk dokumentasi library
- ❌ **JANGAN** gabung multiple konsep (routing + auth + caching) dalam satu query
- ⚠️ Jika server down → fallback `researcher_docs`, lalu `read_url` resmi

---

## ➌ GitNexus — Impact Analysis Sebelum Edit

<!-- gitnexus:start -->
**rsud-server-stack** — 1191 symbols, 2296 relationships, 78 execution flows.

### Always Do
- **`impact({target: "symbolName", direction: "upstream"})`** sebelum edit symbol apapun. Report blast radius ke user.
- **`detect_changes()`** sebelum commit — verifikasi hanya symbol yang diharapkan berubah.
- **WAJIB warning user** jika risiko HIGH/CRITICAL.
- **`query({search_query: "concept"})`** untuk execution flow — jangan grep.
- **`context({name: "symbolName"})`** untuk 360-degree view suatu symbol.

### Never Do
- JANGAN edit tanpa `impact()` dulu. JANGAN commit tanpa `detect_changes()`.
- JANGAN rename symbol dengan find-and-replace — pakai MCP `rename`.
- JANGAN abaikan HIGH/CRITICAL risk.

### Resources
| Resource | Use for |
|----------|---------|
| `gitnexus://repo/rsud-server-stack/context` | Overview & index freshness |
| `gitnexus://repo/rsud-server-stack/process/{name}` | Step-by-step execution trace |

> Index stale? `node .gitnexus/run.cjs analyze` (atau `npx gitnexus analyze`).
> Detail CLI: `.claude/skills/gitnexus/`
<!-- gitnexus:end -->

---

## ➍ Issue-Driven Changes

Sebelum modifikasi (kecuali trivial/typo):

```bash
bd create "Judul" --body "Deskripsi perubahan"
bd update <issue-id> --claim
```

- ✅ Buat issue untuk perubahan baru (refactor, module, fitur)
- 🔄 Lanjutkan issue yang sudah ada jika relevan
- ⏭️ Skip untuk typo, rename kecil, atau jika user minta langsung

---

## ⚠️ CODING-RULES.md: Baca Manual!

`CODING-RULES.md` **tidak auto-read** oleh AI tools. Agent WAJIB membaca file ini secara manual karena berisi:

- **YAGNI/KISS/DRY** — prinsip desain utama
- **Max 300 baris per file** — aturan batas ukuran file
- **Aturan keamanan** — validasi input, JWT, SQL
- **Checklist sebelum commit** — testing, blast radius, compliance

> Baca: [CODING-RULES.md](./CODING-RULES.md) — jangan skip!

---

## Ringkasan Tools

| Tool | Fungsi | Urutan |
|------|--------|--------|
| **Graphify** | Pahami arsitektur codebase | #1 Eksplorasi |
| **Context7** | Dokumentasi library eksternal | #1 Dokumentasi |
| **GitNexus** | Impact analysis sebelum edit | #2 Sebelum edit |
| **Beads** | Issue tracking | Sebelum mulai kerja |

> **Detail lengkap:** `AGENTS.md` (workflow, exception, tabel) dan `CODING-RULES.md` (YAGNI/KISS/DRY, coding standards).
