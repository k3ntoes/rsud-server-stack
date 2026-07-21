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

### Wajib: Gunakan GitNexus Sebelum Menulis Kode
Sebelum membuat atau mengubah file apapun, AI agent **WAJIB** melakukan:

1. `gitnexus://repo/rsud-server-stack/context` — cek index freshness
2. Jika index stale (kedaluwarsa), jalankan `node .gitnexus/run.cjs analyze`
3. Sebelum mengedit symbol apa pun: jalankan **`impact({target: "symbolName", direction: "upstream"})`** dan report blast radius ke user
4. Gunakan `query()` untuk memahami execution flow
5. Gunakan `context()` untuk 360-degree view suatu symbol
6. Gunakan `detect_changes()` sebelum commit

> **Fallback**: Jika tools GitNexus MCP tidak tersedia, gunakan `code-searcher` + `read_files` + `read_subtree` sebagai alternatif untuk memahami codebase.
> Lihat `.claude/skills/gitnexus/` untuk panduan lengkap.

### Wajib: Gunakan Context7 untuk Best Practices & Docs
Sebelum menulis kode yang melibatkan library/framework tertentu, AI agent **WAJIB**:

1. Cek dokumentasi terbaru library via **Context7 MCP**
2. Verifikasi API signatures, konfigurasi, dan best practices — jangan andalkan training data saja
3. Untuk multi-konsep, panggil `query-docs` per konsep (jangan digabung)

> Skill Context7 sudah terinstall di `.agents/skills/context7-mcp/`.

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
