# PRODUCT REQUIREMENTS DOCUMENT (PRD) - SERVER STACK
**Proyek:** Sistem Inspeksi Kebersihan Harian - Backend & Web Admin
**Klien:** RSUD Ajibarang

## 1. Objektif Repositori
Menyediakan RESTful API yang tangguh untuk melayani aplikasi klien, mengelola logika bisnis dan validasi data secara terpusat, serta menyediakan antarmuka Web Dashboard untuk Supervisor dan Admin PPI.

## 2. Peran & Hak Akses Web
*   **Supervisor:** Hanya dapat melihat daftar inspeksi berstatus `PENDING`, melihat foto original via rute token sementara, dan mengeksekusi aksi `APPROVE` atau `REJECT`.
*   **Admin PPI:** Memiliki akses ke Dashboard Analitik, mengelola Master Data (Ruangan, Item Inspeksi) via Soft-Delete, dan mencabut akses sesi (*Kill Switch* Revoke JWT) perangkat petugas.

## 3. Spesifikasi Fitur Backend (API)
*   **Autentikasi:** Menerapkan otorisasi JWT stateless berlapis (Access & Refresh Token). Refresh Token divalidasi silang dengan tabel `user_sessions` (Whitelist).
*   **Two-Step Upload:** Endpoint penerimaan gambar terpisah dari JSON. Mengembalikan nama file unik untuk disisipkan oleh klien ke dalam JSON inspeksi.
*   **Idempotency API:** Endpoint submit laporan wajib menolak duplikasi menggunakan kombinasi `(room_id, local_timestamp, inspector_id)`.
*   **Timezone & Agregasi:** Menarik `business_date` dari waktu UTC mutlak untuk mencegah data meleset dari shift.

## 4. Spesifikasi Fitur Web Admin (Frontend)
*   **Approval Workflow:** UI tabel persetujuan data laporan. Menampilkan thumbnail gambar secara *lazy load*.
*   **Dashboard Analitik CQRS:** UI grafik yang HANYA menarik data dari tabel ringkasan (`room_monthly_stats`, `issue_frequency_stats`).
    *   Metrik Utama 1: 3 ruangan dengan persentase skor terendah.
    *   Metrik Utama 2: Item inspeksi yang paling sering mendapat skor 0.

## 5. Background Tasks (Pekerja Latar Belakang)
*   Sistem menggunakan Outbox Pattern (tabel `background_jobs`).
    - **Dev:** SQLite (file-based, via aiosqlite)
    - **Prod:** PostgreSQL (via asyncpg)
*   Tugas 1: Membuat file thumbnail secara asinkron setelah fase upload gambar selesai.
*   Tugas 2: Menghitung persentase skor dan meng-UPSERT tabel analitik setiap kali status laporan berubah menjadi `APPROVED`.
