# ADR-0002: Multi-Photo Schema — Tabel `inspection_photos` Terpisah

**Status**: Accepted

Setiap item inspeksi dapat memiliki banyak foto (tidak terbatas). Oleh karena itu, foto dipisahkan ke tabel `inspection_photos` sendiri, bukan menggunakan kolom `photo_file_name` tunggal di `inspection_details`.

**Pertimbangan yang ditolak:**
- **JSONB array** (`photo_file_names TEXT[]`) — lebih simpel tanpa join, tetapi menyulitkan query individual, sorting, dan tidak scalable untuk jumlah foto besar
- **Single column** — tidak memenuhi kebutuhan multi-foto

**Konsekuensi:**
- Normalized, flexible, query foto per-item mudah
- Memudahkan async thumbnail generation (cukup update `thumbnail_file_name` per row)
- Sort order memungkinkan urutan foto yang konsisten
