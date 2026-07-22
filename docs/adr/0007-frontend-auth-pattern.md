# ADR-0007: Frontend Auth Pattern — SessionStorage + Auto-Refresh Token

**Status**: Accepted

Frontend web-admin menyimpan **Access Token di sessionStorage** dan melakukan **auto-refresh via httpOnly cookie** saat menerima HTTP 401 dari backend.

## Context

JWT auth di backend menggunakan dual-token pattern (ADR-0003): Access Token (15 menit) + Refresh Token (7 hari, httpOnly cookie). Frontend perlu menyimpan Access Token di sisi klien dan secara otomatis merefreshnya tanpa interupsi user.

## Keputusan

### 1. sessionStorage (bukan localStorage)

| Storage | Kelebihan | Kekurangan |
|---------|-----------|------------|
| **sessionStorage** | Token hilang saat tab ditutup — bersih otomatis | Session tidak survive tab baru / browser restart |
| localStorage | Session survive browser restart | Token bisa stale, perlu cleanup manual |

Keputusan: **sessionStorage**. Dashboard internal — tidak ada session sharing antar tab. Keamanan lebih baik karena token tidak bertahan setelah tab ditutup.

### 2. Auto-Refresh via httpOnly Cookie

Saat API request mendapat HTTP 401:
1. API client (`lib/api.ts`) tidak langsung mengembalikan error
2. Panggil `POST /api/auth/refresh` — httpOnly cookie dikirim otomatis oleh browser
3. Jika sukses: simpan Access Token baru di sessionStorage, ulangi request original
4. Jika gagal: bersihkan token, redirect ke `/login`

```typescript
// Pattern di lib/api.ts
if (res.status === 401 && accessToken) {
  const newToken = await tryRefresh();
  if (newToken) {
    headers["Authorization"] = `Bearer ${newToken}`;
    res = await fetch(url, { ...options, headers });  // retry original request
  } else {
    setAccessToken(null);
    onUnauthorized?.();  // redirect to /login
    throw new Error("Session expired");
  }
}
```

### 3. Retry Original Request

Ketika refresh berhasil, API client mengulangi **request original yang gagal** (bukan hanya refetch dari cache). Ini memastikan data yang diminta user tetap sampai — TanStack Query menerima response sukses, bukan error yang perlu di-refetch manual.

### 4. On-Mount Session Check

`AuthProvider` memanggil `GET /api/auth/me` saat mount untuk me-restore session:
- Jika cookie masih valid → backend mengembalikan user → aplikasi masuk ke dashboard
- Jika cookie expired → 401 → redirect ke `/login`

## Konsekuensi

- Frontend dan backend harus di domain yang sama (httpOnly cookie tidak bisa跨域) — dipenuhi via Vite proxy (dev) dan nginx (prod)
- CSR risk: httpOnly cookie tidak bisa dibaca JavaScript, tapi sudah di-handle oleh SameSite=Strict (lihat ADR-0003)
- Auto-refresh seamless — user tidak pernah melihat login page selama cookie masih hidup
- Token tidak persist setelah tab ditutup — cocok untuk dashboard internal
- Jika cookie expired saat user sedang aktif, redirect ke `/login` terjadi di request berikutnya (lazy expiry)

## Referensi

- Lihat `web-admin/src/lib/api.ts` untuk implementasi API client
- Lihat `web-admin/src/hooks/useAuth.tsx` untuk implementasi AuthContext
- ADR-0003: JWT Layered Auth dengan httpOnly Refresh Cookie
