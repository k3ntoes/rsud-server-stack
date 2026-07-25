# Coding Rules — RSUD Ajibarang Server Stack

Aturan ini wajib diikuti oleh **semua AI agent** yang menulis, mengubah, atau men-review kode di repository ini.

---

## 1. Prinsip Desain

### YAGNI (You Ain't Gonna Need It)
- Jangan tulis kode untuk fitur yang belum diminta.
- Jangan tambahkan abstraksi, parameter, atau fleksibilitas "untuk jaga-jaga".
- Jika fitur belum ada di PRD, jangan dibuat. Jika dibutuhkan nanti, akan ditambahkan nanti.
- Pertanyaan sebelum nambah kode: _"Apakah fitur ini dibutuhkan sekarang?"_ Jika tidak, skip.

### KISS (Keep It Simple, Stupid)
- Solusi paling sederhana yang bekerja adalah yang terbaik.
- Jangan bikin class/pattern complex kalau function biasa sudah cukup.
- Lebih suka standard library daripada custom utility.
- Lebih suka inline logic daripada abstraction layer yang tidak perlu.
- Kode yang mudah dibaca > kode yang clever.

### DRY (Don't Repeat Yourself)
- Jika pola yang sama muncul 2+ kali, extract ke function/component.
- Tapi jangan extract terlalu dini — **tunggu hingga pola ke-3**. (YAGNI > DRY)
- Duplikasi yang tidak disengaja lebih baik daripada abstraksi yang premature.

---

## 2. Aturan File

### Maksimal 300 Baris per File
- Setiap file **tidak boleh melebihi 300 baris** (termasuk imports dan comments).
- Jika sebuah file mencapai batas, refactor dengan memisahkan tanggung jawab ke file baru.
- Pengecualian: file konfigurasi, migration SQL, atau data fixture (max 500 baris).

### Satu Tanggung Jawab per File
- Setiap file harus punya **satu alasan untuk berubah** (Single Responsibility).
- Contoh yang benar:
  - `routes/auth.py` — hanya routing
  - `services/auth_service.py` — hanya logic auth
  - `models/user.py` — hanya definisi model User
- Contoh yang salah:
  - `utils.py` — tempat sampah berbagai fungsi tidak terkait
  - `models.py` — semua model dalam satu file

### Naming Convention
- **Backend (Python/FastAPI)**: `snake_case` untuk file, fungsi, variabel.
- **Frontend (React/Vite)**: `PascalCase` untuk komponen, `camelCase` untuk fungsi/variabel, `kebab-case` untuk file non-komponen.
- **Database**: `snake_case` untuk tabel dan kolom.

---

## 3. Research & Context Gathering

### 🔷 WAJIB: Gunakan Graphify Sebelum Membaca File Apapun
Sebelum membaca file atau membuat perubahan, AI agent **WAJIB** menggunakan Graphify knowledge graph sebagai langkah pertama:

1. `graphify query "Bagaimana arsitektur <konsep>?"` — pahami alur dan relasi kode
2. `graphify path "<A>" "<B>"` — cari jalur antara 2 konsep (jika perlu)
3. `graphify explain "<simbol>"` — detail suatu simbol/modul (jika perlu)
4. **Setelah graphify memberi jawaban**, baru baca file spesifik yang disebutkan

> **Mengapa?** Graphify sudah memiliki knowledge graph dengan 442 node dan 1,013 edges. Query ke graphify hanya memakan ~100-500 token, sedangkan membaca file langsung bisa ribuan token.

> **Fallback**: Jika `graphify-out/graph.json` tidak ada atau rusak, rebuild dulu dengan `graphify extract` (lihat `AGENTS.md` bagian Graphify).

### Wajib: Gunakan GitNexus untuk Impact Analysis
Setelah memahami arsitektur via Graphify, gunakan GitNexus untuk analisis dampak sebelum mengedit kode:

1. `gitnexus://repo/rsud-server-stack/context` — cek index freshness  
2. Jika index stale, jalankan `node .gitnexus/run.cjs analyze`
3. Sebelum mengedit symbol: **`impact({target: "symbolName", direction: "upstream"})`** dan report blast radius
4. Gunakan `query()` untuk execution flow detail
5. Gunakan `context()` untuk 360-degree view
6. Gunakan `detect_changes()` sebelum commit

### Difference: Graphify vs GitNexus

| Graphify | GitNexus |
|----------|----------|
| 🎯 Arsitektur tingkat tinggi & relasi konsep | 🎯 Impact analysis per symbol |
| 💬 Query bahasa alami ("Bagaimana alur login?") | 💬 Query symbol spesifik |
| 🗺️ Shortest path antar konsep | 🛡️ Blast radius / call graph |
| 🔍 Penjelasan node/simbol | 🔄 Rename refactoring |
| ✅ **Langkah #1** — untuk memahami | ✅ **Langkah #2** — untuk mengubah |

### Wajib: Update Graphify Graph Setelah Perubahan Besar
Setelah perubahan kode yang signifikan (refactor, module baru, restrukturisasi), update knowledge graph:

```bash
# 1. Extract per subdirectory (code-only, no API key needed)
graphify extract ./backend/ --code-only --no-viz
graphify extract ./web-admin/ --code-only --no-viz

# 2. Merge into single monorepo graph
graphify merge-graphs ./backend/graphify-out/graph.json ./web-admin/graphify-out/graph.json --out graphify-out/graph.json
```

Lihat `AGENTS.md` (bagian Graphify) untuk perintah query, cluster-only, dan troubleshooting.

> **Catatan**: Gunakan `graphify extract ./subdir/` (bukan `graphify .`). Root-level `graphify .` gagal dengan `deduplicate_entities: nodes span multiple repos`. `extract` menempatkan `graphify-out/` di dalam direktori yang di-scan, bukan di root.

### 🔷 WAJIB: Gunakan Context7 untuk Dokumentasi Library (Bukan Web Fetch)

**Context7 MCP** sudah terkonfigurasi dan harus menjadi pilihan PERTAMA untuk dokumentasi library/framework. Jangan pakai `researcher_web` atau `read_url` untuk ini.

#### Kenapa Context7 Lebih Baik?

| Metode | Biaya Token | Akurasi | Kecepatan |
|--------|-------------|---------|-----------|
| ✅ **Context7** `query-docs` | ~100-500 token | Tinggi (dokumentasi resmi) | Cepat (API langsung) |
| ❌ `researcher_web` + `read_url` | ~2,000-5,000+ token | Rendah (scrape HTML, iklan, noise) | Lambat (buka web, baca HTML) |
| ❌ `skill("find-docs")` | ~1,000-2,000 token | Sedang (campuran) | Sedang |

#### Always Do

Sebelum menulis kode yang melibatkan library/framework, AI agent **WAJIB**:

1. **Load skill dulu**: `skill("context7-mcp")`
2. **Resolve library ID**: panggil `resolve-library-id` dengan nama library
3. **Query docs**: panggil `query-docs` dengan `libraryId` + pertanyaan spesifik
4. **Satu konsep per query** — jangan gabung multiple konsep dalam satu `query-docs`

> Template perintah:
> ```
> skill("context7-mcp")  →  resolve-library-id(libraryName: "next.js", query: "...")  →  query-docs(libraryId: "/vercel/next.js", query: "...")
> ```

#### Never Do

- **JANGAN** gunakan `researcher_web` + `read_url` untuk dokumentasi library — ini boros token 5-10x lipat dan hasilnya kurang akurat.
- **JANGAN** andalkan training data untuk API signatures — dokumentasi library berubah cepat, selalu pakai Context7.
- **JANGAN** gabung multiple konsep dalam satu `query-docs` — hasilnya dangkal untuk setiap topik.

#### Exception

- Jika Context7 MCP tidak tersedia (server down atau API key expired), fallback ke `researcher_docs` agent, lalu ke `read_url` langsung ke situs dokumentasi resmi.
- Untuk pertanyaan tentang ekosistem (bukan dokumentasi teknis), misalnya "Apa perbedaan antara ORM populer?", `researcher_web` lebih cocok.

> Skill Context7 terinstall di `.agents/skills/context7-mcp/`.
> MCP Server: `https://mcp.context7.com/mcp`

### Baca Domain Docs Terkait
- Baca `CONTEXT-MAP.md` untuk menemukan context yang relevan
- Baca `src/<context>/CONTEXT.md` untuk glossary dan key decisions
- Baca `docs/adr/` untuk keputusan arsitektural yang sudah dibuat

---

## 4. Code Quality

### Error Handling
- Semua error di backend harus punya **HTTP status code yang tepat** (4xx untuk client error, 5xx untuk server error).
- Jangan swallow exceptions tanpa log.
- Gunakan validation (Pydantic) di layer API, bukan di daleman service.

### Testing
- Unit test untuk semua business logic.
- Integration test untuk endpoint kritis (auth, submission).
- Nama test harus deskriptif: `test_submit_inspection_duplicate_idempotency`.

### Keamanan
- Input dari client **tidak pernah trusted** — selalu validasi.
- SQLAlchemy ORM — jangan raw SQL concatenation.
- Semua file upload divalidasi (ekstensi, content type).
- JWT secret, DB password, API keys — hanya di environment variables.

---

## 5. Proses Development

### Urutan Implementasi (sesuai ADR)
1. **Auth** — autentikasi & otorisasi
2. **Master Data** — rooms & inspection items
3. **Inspection + Media** — core workflow & upload (parallel)
4. **Analytics + Background Jobs** — dashboard & async processing (parallel)

### Checklist Sebelum Commit
- [ ] Semua test passing
- [ ] Tidak ada debug code / console.log
- [ ] Tidak ada commented-out code
- [ ] Tidak ada file > 300 baris (kecuali pengecualian)
- [ ] Tidak ada duplikasi yang tidak perlu
- [ ] Blast radius sudah di-check via GitNexus `detect_changes()`
- [ ] PRD/ADR compliance — apakah perubahan sesuai dengan dokumen yang sudah disepakati?
