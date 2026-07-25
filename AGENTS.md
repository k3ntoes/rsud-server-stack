## 📖 Cara Membaca Dokumen Ini

| File | Fungsi | Dibaca Otomatis? |
|------|--------|------------------|
| **`CLAUDE.md`** | Quick-reference ringkas — prioritas ekplorasi ✅❌ | ⚠️ Beberapa AI tools (Claude Code, dll) |
| **`AGENTS.md`** (ini) | Dokumentasi detail — semua workflow, exception, tabel | ❌ Tidak, harus dibaca manual |
| **`CODING-RULES.md`** | Coding standards — YAGNI, KISS, 300 baris/file | ❌ Tidak, harus dibaca manual |

> **Mulailah dengan `CLAUDE.md`** jika Anda AI agent yang mendukung auto-read. Jika tidak, baca `AGENTS.md` ini untuk panduan lengkap.

---

## 🧭 Graphify-First Exploration

Sebelum membaca file APAPUN, AI agent **WAJIB** menggunakan `graphify` untuk memahami codebase terlebih dahulu. Ini menghemat ribuan token dengan menghindari pembacaan file secara buta.

### Always Do

- **WAJIB: Gunakan `graphify query` sebelum membaca file.** Untuk memahami bagaimana suatu fitur bekerja, jalankan:
  ```bash
  graphify query "Bagaimana alur <fitur>?"
  ```
  Ini akan mengembalikan node-node relevan dari knowledge graph tanpa perlu membaca file secara langsung.

- **WAJIB: Gunakan `graphify path` untuk mencari jalur antar 2 konsep.**
  ```bash
  graphify path "User" "Room"
  ```

- **WAJIB: Gunakan `graphify explain` untuk penjelasan detail suatu simbol/modul.**
  ```bash
  graphify explain "get_current_user"
  ```

- **WAJIB: Cek god nodes dan surprising connections** untuk mendapatkan gambaran besar codebase:
  ```bash
  graphify query "Apa god nodes di codebase ini?"
  graphify query "Apa surprising connections?"
  ```

- **Setelah graphify memberi gambaran, baru baca file spesifik** yang diperlukan — bukan seluruh folder.

### Never Do

- **JANGAN langsung membaca file** (via `read_files`, `grep`, atau `code-searcher`) tanpa `graphify query` terlebih dahulu.
- **JANGAN membaca seluruh folder** (`read_subtree` dengan maxTokens besar) tanpa tahu persis apa yang dicari.
- **JANGAN menggunakan `grep`/`ripgrep` untuk mencari konsep tingkat tinggi** — gunakan `graphify query` yang sudah memahami relasi antar kode.

### Exception

- Jika `graphify-out/graph.json` tidak ada atau rusak, rebuild dulu (lihat bagian bawah) atau fallback ke GitNexus.
- Untuk perubahan kecil/typo yang sudah jelas lokasinya, graphify query bisa dilewati.
- Query spesifik yang butuh implementasi detail (bukan arsitektur) boleh langsung ke file setelah konfirmasi user.

---

## Agent skills

### Issue tracker
Issues tracked via Beads (CLI: `bd`), stored in `.beads/` as a Dolt-backed AI-native issue tracker. See `docs/agents/issue-tracker.md`.

### Triage labels
Default triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs
Multi-context layout: `CONTEXT-MAP.md` at root points to per-context `CONTEXT.md` files under `src/`. See `docs/agents/domain.md`.

## Workflow: Issue-Driven Changes

### Always Do

- **MUST create a Beads issue before starting work on a new change.**
  - Before modifying any file, run `bd create "<title>" --body "<description>"` to create a tracking issue.
  - The issue title should clearly describe what will be changed and why.
  - The issue body should include:
    - Context: what needs to change and why
    - Files affected (estimated)
    - Dependencies: ADRs, CONTEXT.md terms, or existing issues this relates to
  - After creation, claim the issue: `bd update <issue-id> --claim`

- **Exception: already working on an issue.**
  - If an issue already exists for the work (claimed or assigned), skip creation.
  - If the user explicitly asks to continue without creating an issue, skip creation.

### Never Do

- NEVER make changes without a corresponding Beads issue, unless the change is trivial (typo, rename) or explicitly requested by the user without one.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **rsud-server-stack** (v1.6.9, 1191 symbols, 2296 relationships, 78 execution flows, 25 communities). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `gitnexus analyze` from the project root (globally installed at `/home/kentoes/.nvm/versions/node/v24.18.0/bin/gitnexus`). Alternate: `node .gitnexus/run.cjs analyze`.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/rsud-server-stack/context` | Codebase overview, check index freshness |
| `gitnexus://repo/rsud-server-stack/clusters` | All functional areas |
| `gitnexus://repo/rsud-server-stack/processes` | All execution flows |
| `gitnexus://repo/rsud-server-stack/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

<!-- context7:start -->
# Context7 — Dokumentasi Library/Framework Eksternal

> **Pembagian tugas:** Graphify → memahami **codebase internal** (backend, frontend). Context7 → dokumentasi **library/framework eksternal** (React, FastAPI, SQLAlchemy, Next.js, dll).

Context7 MCP memberikan akses ke dokumentasi library/framework terkini tanpa perlu scraping web. **Selalu gunakan ini dulu sebelum `researcher_web` atau `read_url` untuk dokumentasi teknis.**

## Always: Load Skill First

Context7 MCP tidak otomatis terlihat sebagai tool. Agent harus **load skill dulu**:

```python
skill("context7-mcp")
```

Setelah itu MCP tools `resolve-library-id` dan `query-docs` tersedia.

## Always Do

- **WAJIB: Load skill `skill("context7-mcp")`** sebelum menulis kode yang melibatkan library/framework.
- **WAJIB: Gunakan `resolve-library-id`** untuk menemukan ID library yang tepat.
- **WAJIB: Gunakan `query-docs`** untuk dokumentasi spesifik — lebih hemat token 5-10x dari web fetch.
- **WAJIB: Pisahkan query per konsep** — jangan gabung routing + auth + caching dalam satu query.
- **WAJIB: Verifikasi API signatures** — jangan andalkan training data yang mungkin usang.

## Never Do

- **JANGAN gunakan `researcher_web` + `read_url` untuk dokumentasi library** — biaya token 2,000-5,000 vs hanya ~100-500 via Context7.
- **JANGAN gunakan `skill("find-docs")` sebagai pengganti** — Context7 lebih akurat karena langsung ke dokumentasi resmi.
- **JANGAN gabung multiple konsep dalam satu `query-docs`** — hasilnya dangkal untuk setiap topik.

## Perbandingan Biaya Token

| Metode | Token | Akurasi |
|--------|-------|---------|
| ✅ **Context7** `query-docs` | ~100-500 | ✅ Tinggi |
| ❌ `researcher_web` + `read_url` | ~2,000-5,000+ | ❌ Rendah |
| ⚠️ `skill("find-docs")` | ~1,000-2,000 | ⚠️ Sedang |

## Workflow (Hemat Token)

```
skill("context7-mcp")                       # load skill
  → resolve-library-id(libraryName: "...")   # cari ID library
  → query-docs(libraryId: "...", query: "") # fetch docs per konsep
```

## Exception

- Jika Context7 MCP server down atau API key expired, fallback ke `researcher_docs` agent, lalu `read_url` ke situs dokumentasi resmi.
- Untuk pertanyaan tentang ekosistem (bukan dokumentasi teknis), misalnya "Apa perbedaan ORM populer?", `researcher_web` lebih cocok.

<!-- context7:end -->

<!-- graphify:start -->
# Graphify — Knowledge Graph

This project uses **graphify** (v0.9.23, installed at `/home/kentoes/.local/bin/graphify`) to build a navigable knowledge graph from source code. The graph helps agents understand code relationships, detect communities, and trace execution paths across the monorepo.

## Always Do

- **WAJIB: Gunakan `graphify query` sebagai langkah PERTAMA** sebelum membaca file apapun (lihat bagian "Graphify-First Exploration" di atas).
- **WAJIB: Update graph setelah perubahan kode besar** (refactor, module baru, restrukturisasi).
- **WAJIB: Cek index freshness** — pastikan `graphify-out/graph.json` masih relevan dengan kode terbaru.

## Never Do

- **JANGAN membaca file secara buta** tanpa graphify query terlebih dahulu (boros token).
- **JANGAN gunakan `graphify .` di root monorepo** — gagal dengan `deduplicate_entities: nodes span multiple repos`. Gunakan `graphify extract ./subdir/` per proyek.
- **JANGAN gunakan grep/ripgrep untuk eksplorasi arsitektur tingkat tinggi** — itu tugas graphify.

## Current Graph Stats

| Scope | Nodes | Links | Communities |
|-------|-------|-------|-------------|
| `backend/` | 396 | 988 | 36 |
| `web-admin/` | 201 | 272 | 15 |
| **Merged** (`graphify-out/graph.json`) | **597** | **1260** | — (per-project) |

## Monorepo Update (Correct Command)

Gunakan **`graphify extract`** (bukan `graphify .`), lalu merge dengan `--out`:

```bash
# 1. Extract per subdirectory (output di <dir>/graphify-out/graph.json)
graphify extract ./backend/ --code-only --no-viz
graphify extract ./web-admin/ --code-only --no-viz

# 2. Merge into single monorepo graph (output: graphify-out/graph.json)
graphify merge-graphs ./backend/graphify-out/graph.json ./web-admin/graphify-out/graph.json --out graphify-out/graph.json
```

## Known Constraints

- **Monorepo**: Wajib `graphify extract ./subdir/` per proyek, lalu `merge-graphs --out`. Root-level `graphify .` gagal dengan `deduplicate_entities: nodes span multiple repos`.
- **No API key**: Gunakan `--code-only`. AST extraction berfungsi tanpa API key. Semantic extraction (docs, papers, images) butuh `GEMINI_API_KEY`.
- **Output**: `graphify extract` menempatkan `graphify-out/` di **dalam** direktori yang di-scan (`backend/graphify-out/`, `web-admin/graphify-out/`). Merge dengan `--out` menulis ke root `graphify-out/graph.json`.

## Query Workflow (Hemat Token)

Urutan yang benar untuk memahami kode:

```
1. graphify query "Bagaimana arsitektur <fitur>?"
2. graphify path "<KonsepA>" "<KonsepB>"  (jika perlu hubungan)
3. graphify explain "<simbol>"              (jika perlu detail simbol)
4. Baca file spesifik yang disebut graphify  (hanya file yang diperlukan)
```

### Contoh

```bash
# INI HEMAT TOKEN ✅
graphify query "Bagaimana alur login?"
# Output: menyebutkan file login.tsx, useAuth.tsx, auth/api.py, auth/schemas.py
# Baru baca file-file itu saja

# INI BOROS TOKEN ❌
grep -r "login" src/  # membaca banyak file yang mungkin tidak relevan
read_subtree src/      # membaca semua file tanpa tahu yang dicari
```

## Resources

| Task | Command |
|------|---------|
| Full code re-index | `graphify extract ./backend/ --code-only --no-viz && graphify extract ./web-admin/ --code-only --no-viz && graphify merge-graphs ./backend/graphify-out/graph.json ./web-admin/graphify-out/graph.json --out graphify-out/graph.json` |
| Incremental update | Same as full re-index — graphify handles caching via `extract` |
| Query merged graph | `graphify query "<question>"` (from root, reads `graphify-out/graph.json`) |
| Shortest path | `graphify path "<NodeA>" "<NodeB>"` (e.g. `graphify path "User" "Room"`) |
| Show god nodes | `graphify gods` — nodes with highest degree centrality (hubs) |
| Show surprises | `graphify surprises` — unexpected cross-community connections |
| Merge graphs | `graphify merge-graphs <g1.json> <g2.json> --out <output.json>` |

<!-- graphify:end -->
