# Context: Media & Upload

## Responsibility

Handle image upload, storage, thumbnail generation, and secure one-time access to original photos.

## Language

**Two-Step Upload**:
Images are uploaded via a separate endpoint before JSON submission. Returns unique filenames to embed in the inspection payload.

**Photo File Name**:
Unique filename (UUID-based) returned by the upload endpoint.

**Inspection Photo**:
Stored in the `inspection_photos` table. Each row links to one `inspection_detail` and contains one `photo_file_name`. Unlimited photos per item.

**Thumbnail**:
Aspect-ratio-preserved compressed version of the original photo, generated asynchronously for lazy-load in the web dashboard. Field: `thumbnail_file_name` di `inspection_photos`.

**One-Time Token**:
Temporary token route for accessing original photos. Photos are not publicly exposed.

**No Size Limit**:
Server does not enforce file size limits. The Android app compresses photos before upload without losing detail.

**Local Storage**:
Photos stored on the filesystem (`uploads/` via Docker volume). Can be migrated to MinIO/S3 later if needed.

## Key Decisions

- Two-Step Upload: image endpoint separate from JSON submission
- Protected photo endpoints (not publicly exposed)
- Original photos accessible via one-time tokenized route
- Multiple photos per item via `inspection_photos` table (normalized)
- No server-side size limit — Android handles compression
- Thumbnails: aspect ratio preserved, generated asynchronously via background jobs (task type: `generate_thumbnail`)
- Thumbnail file name stored in `inspection_photos.thumbnail_file_name` — nullable, diisi setelah background job selesai
- Local storage via Docker volume (`uploads/`), upgradeable to MinIO/S3

## ADRs

See `docs/adr/` for media-specific decisions:
- ADR-0002: Multi-Photo Schema
