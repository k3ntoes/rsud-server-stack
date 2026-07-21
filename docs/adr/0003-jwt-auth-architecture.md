# ADR-0003: JWT Layered Auth dengan httpOnly Refresh Cookie

**Status**: Accepted

Sistem autentikasi menggunakan **JWT dua lapis**: Access Token (15 menit) dan Refresh Token (7 hari). Refresh Token divalidasi silang dengan tabel whitelist `user_sessions` dan dikirim sebagai **httpOnly cookie**, bukan localStorage.

Keputusan ini diambil untuk menyeimbangkan keamanan dan kemudahan integrasi antara backend FastAPI dan frontend React.

**Pertimbangan yang ditolak:**
- **Refresh Token di localStorage** — rentan XSS, token bisa dicuri oleh injected script
- **Session-based auth (server-side session)** — membutuhkan state di server, tidak cocok untuk load balancing
- **Pure stateless JWT** — tidak bisa di-revoke oleh Admin PPI (fitur kill switch)

**Konsekuensi:**
- httpOnly cookie mencegah XSS token theft
- Whitelist `user_sessions` memungkinkan Admin PPI me-revoke session
- Frontend dan backend harus di domain yang sama (cocok dengan setup docker-compose + reverse proxy)
- CSRF protection perlu diperhatikan (menggunakan `SameSite=Strict` atau CSRF token)
