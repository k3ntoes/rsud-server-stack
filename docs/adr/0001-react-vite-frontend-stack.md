# ADR-0001: React + Vite + TanStack sebagai Frontend Stack

**Status**: Accepted

Web Admin Dashboard RSUD Ajibarang menggunakan **React + Vite** sebagai framework frontend, dengan **TanStack Router** untuk routing, **TanStack Query** untuk data fetching, dan **shadcn/ui** untuk komponen UI.

Keputusan ini diambil karena Web Admin bersifat internal (tidak perlu SEO/SSR) dan backend sudah menggunakan FastAPI terpisah — sehingga fitur unggulan Next.js (SSR, Server Components) tidak memberikan nilai tambah, namun menambah kompleksitas (Server/Client boundary, biaya server Node.js runtime).

**Pertimbangan yang ditolak:**
- **Next.js** — membutuhkan Node.js runtime, bundle size lebih besar (~92KB vs ~42KB), dan Server Components redundant karena FastAPI sudah menangani server-side logic

**Konsekuensi:**
- Deploy sebagai static files — biaya infrastruktur minimal
- Tidak ada SSR/SEO — tidak relevan untuk dashboard internal
- Frontend dan backend dapat di-scale secara independen
