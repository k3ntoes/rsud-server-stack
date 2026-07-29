# Context: Web Admin Frontend

## Responsibility

Provide a responsive web dashboard for Admin PPI and Supervisor roles to manage master data, review inspections, and view analytics. Built as a pure SPA — no SSR, backend is FastAPI.

## Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Framework | React 18 | UI components |
| Build | Vite 6 | Dev server + production build |
| Routing | TanStack Router | Type-safe routes, preload |
| Data Fetching | TanStack Query | Caching, auto-refetch, mutations |
| Styling | Tailwind CSS 3 + Planograph Theme | Design system |
| Components | Custom (Modal via native `<dialog>`), DataTable via `@tanstack/react-table` | Minimal dependensi eksternal |

## Language

**API Client** (`lib/api.ts`):
Custom fetch wrapper that handles: auto-inject `Authorization: Bearer` header, auto-refresh on 401, redirect to login on session expiry. Token disimpan di **sessionStorage** (bukan localStorage) — hilang saat tab ditutup.

**Access Token**:
JWT short-lived (15 menit) disimpan di `sessionStorage("auth_token")`. Dikirim via `Authorization: Bearer` header oleh API Client.

**Auto-Refresh**:
Saat API Client menerima 401, ia otomatis memanggil `POST /api/auth/refresh` (mengirim httpOnly cookie). Jika berhasil, token baru disimpan dan request original diulang. Jika gagal, redirect ke `/login`.

**Auth Context** (`hooks/useAuth.tsx`):
React Context (`AuthProvider`) yang menyediakan `user`, `isLoading`, `isAuthenticated`, dan fungsi `login`/`logout` ke seluruh aplikasi. Mengecek `/api/auth/me` saat mount untuk restore session.

**TanStack Query Mutation Pattern**:
Setiap mutation hook (create/update/delete) mengikuti pola: `useMutation({ mutationFn, onSuccess: () => queryClient.invalidateQueries([key]) })`. Konsisten di semua hooks.

**DataTable** (`components/DataTable.tsx`):
Komponen tabel generik berbasis `@tanstack/react-table` yang mendukung: pagination (client-side), sorting multi-kolom, global search, selection, column visibility. Digunakan oleh halaman rooms, items, users, inspectors.

**MasterDataPage** (`components/MasterDataPage.tsx`):
Komponen generic untuk CRUD halaman master data (rooms, items) yang menggunakan DataTable di dalamnya. Menerima props: `useList`, `useCreate`, `useUpdate`, `useDelete` hooks + `renderActions` + `renderBadges`.

**renderBadges**:
Prop opsional pada MasterDataPage untuk menampilkan badge di setiap row — digunakan di halaman rooms (badge item names), items (badge room names), dan bisa di-extend untuk halaman lain.

**useDebounce** (`hooks/useDebounce.ts`):
Hook untuk debounce input pencarian — digunakan bersama DataTable untuk mengurangi frekuensi fetch saat user mengetik.

**Data fetching hooks**:
- `useMasterData.ts` — `useRoomsAll()`, `useItemsAll()`, `useAllRoomItems()` + CRUD mutations
- `useUsers.ts` — `useUsers()`, `useAllUserRooms()` + CRUD + password reset
- `useInspections.ts` — list/detail/approve/reject
- `useAnalytics.ts` — `useDashboardData()` (1 hook menggantikan 3 hook), `useDashboardSummary()`, `useLowestRooms()`, `useTopIssues()`, `useInspectorPerformance()`

**Page Route**:
Halaman didefinisikan sebagai TanStack Router route dengan `createRoute()`, dipasang ke route tree di `main.tsx`.

**Protected Route** (`_protected.tsx`):
Route layout (`id: "protected"`) yang membungkus semua halaman yang membutuhkan autentikasi. Component-nya adalah `Layout.tsx` yang mengecek auth dan redirect ke `/login` jika tidak terautentikasi.

**Planograph Theme**:
Design system kustom dengan palet warna: Canvas (latar, 60%), Navy (sidebar/header, 30%), Teal (tombol/aksi, 10%). Ciri khas: shadow planograph (bayangan + border outline 1px).

**Native Modal**:
Komponen `Modal` menggunakan elemen HTML `<dialog>` native — tidak perlu library modal eksternal.

**React Query DevTools**:
Diaktifkan hanya di mode development (`import.meta.env.DEV`) — floating button 🔥 di pojok kiri bawah halaman. Berguna untuk debugging query cache, status loading/fresh/stale, invalidasi. Tidak ditampilkan di production.

## Pages

| Route | Page | Auth | Description |
|-------|------|------|-------------|
| `/` | `index.tsx` | — | Redirect ke `/login` atau `/dashboard` |
| `/login` | `login.tsx` | Public | Form login dengan validasi client-side |
| `/dashboard` | `dashboard.tsx` | Protected | Stat cards: pending count, rooms, month inspections, avg score (1 endpoint) |
| `/rooms` | `rooms.tsx` | Protected | CRUD table (DataTable + MasterDataPage) dengan badge items per room + search + pagination |
| `/items` | `items.tsx` | Protected | CRUD table (DataTable + MasterDataPage) dengan badge rooms per item + search + pagination |
| `/inspections` | `inspections.tsx` | Protected | List dengan tab filter (Semua/Menunggu/Disetujui/Ditolak) paginated |
| `/inspections/$id` | `inspection-detail.tsx` | Protected | Detail inspeksi + approve/reject |
| `/inspectors` | `inspectors.tsx` | Protected | Kinerja inspector + badge rooms per inspector |
| `/users` | `users.tsx` | Protected | CRUD pengguna + admin reset password per baris + room_ids badges |
| `/analytics` | `analytics.tsx` | Protected | Bar chart: ruangan terendah + item bermasalah |

### Feature: Change Password

Button "Ganti Password" di header Layout — membuka modal native `<dialog>` untuk mengubah password sendiri.

## Key Decisions

- **sessionStorage over localStorage**: Token hilang saat tab ditutup — mengurangi risiko token stale
- **Custom `apiRequest` instead of TanStack Query's fetch**: Kontrol penuh atas refresh flow — retry request original setelah refresh berhasil, bukan sekedar refetch
- **Auto-refresh via httpOnly cookie**: Seamless — user tidak perlu login ulang selama refresh cookie masih valid
- **TanStack Router not React Router**: Type-safe route params, built-in preload, loading state
- **Native `<dialog>` for Modal**: Tidak perlu dependensi eksternal — browser support sudah mature
- **No shadcn/ui**: Semua komponen dikustom dengan Tailwind — konsisten dengan Planograph theme, tidak perlu tambahan dependensi
- **SPA not SSR**: Dashboard internal — SEO tidak relevan, FastAPI sudah handle server logic
- **Vite proxy `/api` to backend during dev**: CORS dihindari — frontend dan backend di domain yang sama di production (via nginx)
- **QueryClient retry: 1, refetchOnWindowFocus: false**: Dashboard internal — data cukup di-refresh manual atau via mutation invalidation

## Cross-module relationships

| Modul | Dependency | Dihubungkan via |
|-------|-----------|-----------------|
| `lib/api.ts` | — | Digunakan oleh semua hooks |
| `hooks/useAuth.tsx` | `lib/api.ts` | AuthContext menyediakan user state ke seluruh app |
| `hooks/useMasterData.ts` | `lib/api.ts` | Rooms + Items CRUD + useRoomsAll + useAllRoomItems |
| `hooks/useUsers.ts` | `lib/api.ts` | Users CRUD + password reset + useAllUserRooms |
| `hooks/useInspections.ts` | `lib/api.ts` | Inspection list/detail/approve/reject |
| `hooks/useAnalytics.ts` | `lib/api.ts` | Dashboard + analytics data |
| `hooks/useDebounce.ts` | — | Debounce input pencarian, digunakan oleh MasterDataPage |
| `components/Layout.tsx` | `hooks/useAuth.tsx` | Redirect ke login jika tidak terautentikasi |
| `components/Modal.tsx` | — | Native `<dialog>` wrapper |
| `components/DataTable.tsx` | `@tanstack/react-table` | Tabel generik dengan sorting, pagination, search |
| `components/MasterDataPage.tsx` | `DataTable`, hooks | Generic CRUD page untuk master data |
| `components/Icons.tsx` | — | SVG icons reusable |

## ADRs

See `docs/adr/` for frontend-specific decisions:
- ADR-0001: React + Vite + TanStack sebagai Frontend Stack
- ADR-0007: Frontend Auth Pattern — SessionStorage + Auto-Refresh Token
