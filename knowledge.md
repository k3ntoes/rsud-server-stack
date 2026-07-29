# RSUD Ajibarang — Knowledge (auto-inject)

Prioritas absolut: **Graphify** → **Context7** → **GitNexus** → **baca file**.

```
graphify query "<pertanyaan>"     → pahami codebase (~100 token)
skill("context7-mcp") → query-docs  → dokumentasi library (~200 token)
impact({target: "..."})             → analisis dampak
read_files(...)                     → hanya file spesifik
```

❌ `grep`/`reseacher_web`/`read_subtree` tanpa graphify/context7 dulu.
❌ Baca file secara buta tanpa tahu yang dicari.

---

## Dua Mode Freebuff (Utama!)

### 1. Mode Grilling — Agent sebagai Manager

Gunakan mode ini saat perlu **analisis, desain, perencanaan** — bukan implementasi.

| Aspek | Deskripsi |
|-------|-----------|
| **Peran** | Manager/Architect — tidak perlu coding langsung |
| **Tugas** | Membuat Beads issues + file `.md` berisi checklist claim order (prioritas & dependensi) |
| **Output** | Issues terstruktur, ADR, spec docs — bukan kode |
| **Trigger** | Panggil skill: `skill("grill-me")` atau `skill("grill-with-docs")` |
| **Mirip** | `/wayfinder`, `/to-spec`, `/to-tickets` — breaking down work into plan |

> **Contoh use case**: "Analyze current auth flow and propose improvements" → mode grilling, jangan otomatis coding. Buat issues & spec dulu.

### 2. Mode Coding — Agent sebagai Developer

Gunakan mode ini saat **sudah clear apa yang harus dikerjakan** (ada issue/spec yang siap).

| Aspek | Deskripsi |
|-------|-----------|
| **Peran** | Developer — fokus implementasi |
| **Tugas** | Menulis kode sesuai spec/issue |
| **Skill wajib** | `skill("ponytail")` — paksa solusi paling minimal, YAGNI, KISS |
| **Aturan** | Ikuti `CODING-RULES.md` (YAGNI, max 300 baris/file, testing, security) |
| **Mirip** | `/implement`, `/tdd`, `/code-review` |

> **Contoh use case**: Issue `rsud-server-stack-imw`: "Hapus dead code revoke_session()" → mode coding, langsung eksekusi.

**Penting**: Mode coding WAJIB pakai skill `ponytail` + patuh `CODING-RULES.md`. Jika user minta "lazy mode" atau "simplest solution", itu pemicu ponytail.

---

## Ringkasan CLAUDE.md — Quick Reference

### 1. Graphify-First Exploration (597 nodes, 1260 edges)

```bash
graphify query "<pertanyaan>"   # ~100-500 token — pahami arsitektur
graphify path "User" "Room"     # jalur terpendek antar konsep
graphify explain "get_current_user" # detail simbol/modul
graphify gods                    # node dengan degree tertinggi
graphify surprises               # koneksi antar komunitas tak terduga
```

### 2. Context7 — Dokumentasi Library Eksternal

```python
skill("context7-mcp")                                     # load skill dulu
resolve-library-id(libraryName: "fastapi", query: "...")   # cari ID
query-docs(libraryId: "/fastapi/fastapi", query: "...")    # fetch docs (~100-500 token)
```

### 3. GitNexus — Impact Analysis Sebelum Edit

```
impact({target: "symbolName", direction: "upstream"})  # blast radius
detect_changes({scope: "compare", base_ref: "main"})    # sebelum commit
explain({target: "fileOrSymbol"})                         # security review
```

### 4. Update Graph (Monorepo)

```bash
graphify extract ./backend/ --code-only --no-viz
graphify extract ./web-admin/ --code-only --no-viz
graphify merge-graphs ./backend/graphify-out/graph.json ./web-admin/graphify-out/graph.json --out graphify-out/graph.json
```

### 5. Issue-Driven Changes (Beads CLI: `bd`)

```bash
bd create "Judul" --body "Deskripsi"    # buat issue baru
bd update <id> --claim                     # claim issue
```

### 6. Wajib: Baca CODING-RULES.md Sebelum Claim/Implement

File tidak auto-read. Agent wajib baca manual sebelum `bd update --claim` atau nulis kode.

---

## Ringkasan AGENTS.md — Detail Alur Kerja

### Workflow Eksplorasi Hemat Token

```
➊  CODING-RULES.md (WAJIB baca dulu)
➋  graphify query "<pertanyaan>"
➌  skill("context7-mcp") → query-docs
➍  impact({target: "..."}) sebelum edit
➎  Baca file spesifik (hanya yang disebut di atas)
```

### Graphify Constraints

- **Monorepo**: Wajib `extract` per proyek, lalu `merge-graphs`. Root-level `graphify .` gagal dengan `deduplicate_entities: nodes span multiple repos`.
- **No API key**: Pakai `--code-only`. Semantic extraction butuh `GEMINI_API_KEY`.
- **Output**: `extract` menempatkan `graphify-out/` di dalam direktori sub-proyek. Merge dengan `--out` ke root.

### Context7 Workflow

```
skill("context7-mcp")
  → resolve-library-id(libraryName: "...")  # cari ID library
  → query-docs(libraryId: "...", query: "") # fetch docs per konsep (pisahkan per konsep!)
```

Fallback jika server down: `researcher_docs` → `read_url` ke docs resmi.

### Agent Tools & Files

| File / Tool | Fungsi | Auto-read? |
|-------------|--------|-----------|
| `CLAUDE.md` | Quick-reference ringkas — prioritas, ✅❌ | ⚠️ Beberapa AI tools |
| `AGENTS.md` (ini) | Dokumentasi detail workflow & exception | ❌ Manual |
| `CODING-RULES.md` | Coding standards: YAGNI, KISS, max 300 baris/file | ❌ Manual |
| **Graphify** | Pahami arsitektur codebase (597 node) | Langkah #1 |
| **Context7** | Dokumentasi library eksternal (~100-500 token) | Langkah #2 |
| **GitNexus** | Impact analysis sebelum edit | Langkah #3 |
| **Beads (`bd`)** | Issue tracking di `.beads/` | — |
| **Domain docs** | `CONTEXT-MAP.md` → per-context `CONTEXT.md` | — |

### Never Do

- ❌ `grep`/`researcher_web`/`read_subtree` tanpa graphify dulu
- ❌ Baca file secara buta tanpa graphify query
- ❌ `researcher_web` untuk dokumentasi library — pakai Context7
- ❌ Gabung multiple konsep dalam satu query Context7
- ❌ Edit simbol tanpa `impact()` dulu
- ❌ Rename simbol dengan find-and-replace — pakai `rename` (via GitNexus)
- ❌ `graphify .` di root monorepo — pakai extract per subdir
- ❌ Commit tanpa `detect_changes()`
- ❌ Claim issue tanpa baca `CODING-RULES.md` dulu

> Detail lengkap: `AGENTS.md` (workflow) → `CLAUDE.md` (quick-ref) → `CODING-RULES.md` (standards). Rebuild graph: lihat `AGENTS.md` bagian Graphify.
