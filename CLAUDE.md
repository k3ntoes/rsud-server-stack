# RSUD Ajibarang — Quick Reference for AI Agents

> **CLAUDE.md ini dibaca otomatis oleh AI tools tertentu (Claude Code, Cursor via CLAUDE.md).** Ringkasan cepat di bawah. Detail lengkap: `AGENTS.md` dan `CODING-RULES.md`.

---

## 🎯 Prioritas Eksplorasi Codebase (Hemat Token)

Gunakan urutan ini — jangan langsung baca file:

```
➊ BACA CODING-RULES.md              → prinsip desain, aturan file, keamanan
➋ graphify query "<pertanyaan>"    → pahami arsitektur & relasi kode internal
➌ skill("context7-mcp") → query-docs  → dokumentasi library eksternal
➍ impact({target: "symbolName"})   → analisis dampak sebelum edit
➎ Baca file spesifik               → hanya file yang disebut di atas
```

> ⚠️ **WAJIB BACA `CODING-RULES.md` sebelum claim issue / implement kode!**
> File itu **tidak auto-read** oleh AI tools — agent harus membaca manual.

---

## ➊ Graphify — Pahami Codebase Internal

Graphify (v0.9.23) — **597 node, 1,260 edges**. Gunakan sebelum membaca file:

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
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **rsud-server-stack** (1476 symbols, 3138 relationships, 105 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

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

---

## ➎ CODING-RULES.md: WAJIB Dibaca Sebelum Claim / Implement!

`CODING-RULES.md` **tidak auto-read** oleh AI tools. Agent WAJIB membaca file ini **sebelum claim issue atau mengimplementasi kode** karena berisi:

- **YAGNI/KISS/DRY** — prinsip desain utama
- **Max 300 baris per file** — aturan batas ukuran file
- **Aturan keamanan** — validasi input, JWT, SQL
- **Checklist sebelum commit** — testing, blast radius, compliance
- **Research & Context Gathering** — Graphify, GitNexus, Context7 workflow

> **Aturan:** Setiap agent WAJIB membaca `CODING-RULES.md` sebagai langkah pertama sebelum claim issue (`bd update --claim`) atau sebelum memulai implementasi kode.
> Baca: [CODING-RULES.md](./CODING-RULES.md) — jangan skip!

---

## ➏ Issue-Driven Changes

Sebelum modifikasi (kecuali trivial/typo):

```bash
# 1. Baca CODING-RULES.md dulu (langkah ➎)
# 2. Lalu:
bd create "Judul" --body "Deskripsi perubahan"
bd update <issue-id> --claim
```

- ✅ Buat issue untuk perubahan baru (refactor, module, fitur)
- 🔄 Lanjutkan issue yang sudah ada jika relevan
- ⏭️ Skip untuk typo, rename kecil, atau jika user minta langsung

---

## Ringkasan Tools

| Tool | Fungsi | Urutan |
|------|--------|--------|
| **CODING-RULES.md** | **WAJIB baca sebelum claim/implement** | **#0 Sebelum apapun** |
| **Graphify** | Pahami arsitektur codebase | #1 Eksplorasi |
| **Context7** | Dokumentasi library eksternal | #2 Dokumentasi |
| **GitNexus** | Impact analysis sebelum edit | #3 Sebelum edit |
| **Beads** | Issue tracking | Setelah baca rules |

> **Detail lengkap:** `AGENTS.md` (workflow, exception, tabel).
> **WAJIB baca** `CODING-RULES.md` sebagai LANGKAH PERTAMA sebelum claim/implement!
