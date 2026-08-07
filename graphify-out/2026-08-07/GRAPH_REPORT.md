# Graph Report - .  (2026-08-07)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 898 nodes · 2100 edges · 81 communities (51 shown, 30 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 171 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ed1da654`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- create_user
- master/api.py
- User
- test_auth.py
- hash_password
- inspection/api.py
- test_user_rooms.py
- Analytics Integration Tests
- test_inspection.py
- analytics.tsx
- conftest.py
- useAuth.tsx
- process_one_job
- analytics/api.py
- Background Jobs Context
- Auth & Authz Context
- Master Data Context
- docker-entrypoint.sh
- AdminResetPasswordRequest
- User
- User
- User
- date
- BaseModel
- date
- Exception
- InspectionSubmit
- UploadFile
- User
- User
- User
- AsyncClient
- ChangePasswordRequest
- ItemCreate
- ItemUpdate
- LoginRequest
- rsud-server
- RefreshRequest
- RoomCreate
- RoomItemAssign
- RoomUpdate
- UserCreate
- UserRoom
- UserRoomAssign
- UserSession
- UserUpdate
- devDependencies
- useMasterData.ts
- apiRequest
- compilerOptions
- inspection-detail.tsx
- compilerOptions
- main.tsx
- MasterDataPage.tsx
- DataTable.tsx
- tsconfig.json

## God Nodes (most connected - your core abstractions)
1. `create_user()` - 97 edges
2. `User` - 71 edges
3. `apiRequest()` - 27 edges
4. `assign_item_to_room()` - 22 edges
5. `assign_user_to_room()` - 19 edges
6. `hash_password()` - 18 edges
7. `compilerOptions` - 18 edges
8. `compilerOptions` - 15 edges
9. `UserRoom` - 14 edges
10. `_seed_approved_inspection()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `test_lowest_rooms_ordered_by_score_asc()` --calls--> `create_user()`  [INFERRED]
  tests/test_analytics.py → app/modules/auth/services.py
- `test_lowest_rooms_as_inspector_forbidden()` --calls--> `create_user()`  [INFERRED]
  tests/test_analytics.py → app/modules/auth/services.py
- `test_lowest_rooms_as_admin_allowed()` --calls--> `create_user()`  [INFERRED]
  tests/test_analytics.py → app/modules/auth/services.py
- `test_lowest_rooms_empty()` --calls--> `create_user()`  [INFERRED]
  tests/test_analytics.py → app/modules/auth/services.py
- `test_lowest_rooms_filter_year_month()` --calls--> `create_user()`  [INFERRED]
  tests/test_analytics.py → app/modules/auth/services.py

## Import Cycles
- None detected.

## Communities (81 total, 30 thin omitted)

### Community 0 - "create_user"
Cohesion: 0.08
Nodes (74): create_user(), assign_item_to_room(), AsyncClient, AsyncSession, Regresi: baris ber-`updated_at` NULL (data lama sebelum kolom ini diisi)     har, Regresi yang sama untuk inspection-items (NULL updated_at harus ikut terkirim)., Baris dengan updated_at yang lebih baru dari since tetap terfilter dengan benar., test_create_item() (+66 more)

### Community 1 - "master/api.py"
Cohesion: 0.10
Nodes (54): assign_item_to_room_endpoint(), assign_room_to_item_endpoint(), create_item_endpoint(), create_room_endpoint(), delete_item_endpoint(), delete_room_endpoint(), get_item_by_id(), get_items() (+46 more)

### Community 2 - "User"
Cohesion: 0.09
Nodes (62): admin_reset_password_endpoint(), assign_room_to_user_endpoint(), assign_user_to_room_endpoint(), change_password_endpoint(), create_user_endpoint(), delete_user_endpoint(), get_my_rooms(), get_room_users() (+54 more)

### Community 3 - "test_auth.py"
Cohesion: 0.07
Nodes (58): AsyncClient, AsyncSession, Malformed token → 401 with code TOKEN_INVALID (Android auto-refresh trigger)., Expired access token → 401 with code TOKEN_EXPIRED., Refresh token used as access → 401 with code TOKEN_INVALID., Admin can list all users., Admin creates a new inspector., Duplicate username → 409. (+50 more)

### Community 4 - "hash_password"
Cohesion: 0.10
Nodes (27): upgrade(), hash_password(), verify_password(), seed_admin(), Tests for password hashing functions (app.core.security)., Hash is a string (not bytes)., Correct password returns True., Wrong password returns False. (+19 more)

### Community 5 - "inspection/api.py"
Cohesion: 0.05
Nodes (63): Settings, AuthError, get_current_user(), AsyncSession, Exception, User, Raised by auth dependencies to produce a 401 with a machine-readable code., error_response() (+55 more)

### Community 6 - "test_user_rooms.py"
Cohesion: 0.13
Nodes (40): assign_user_to_room(), AsyncClient, AsyncSession, Regresi: room ber-`updated_at` NULL (data lama) harus tetap terkirim saat `since, Room dengan updated_at lebih lama dari since tetap terfilter benar (NULL-safe)., Regresi: unassign user dari room kini soft-delete. Sync bulk     `/api/auth/user, Assign user ke room harus menaikkan Room.updated_at (sync /rooms ikut berubah)., Setelah unassign, /api/auth/me/rooms tidak lagi mengembalikan room tsb. (+32 more)

### Community 7 - "Analytics Integration Tests"
Cohesion: 0.13
Nodes (35): date, AsyncClient, AsyncSession, Tests for analytics endpoints.  Covers: - GET /api/analytics/lowest-rooms (basic, admin_ppi also has dashboard access per PRD., No analytics data → empty array., Filter by YYYY-MM returns only that month's data., Respects limit parameter. (+27 more)

### Community 8 - "test_inspection.py"
Cohesion: 0.17
Nodes (30): AsyncClient, AsyncSession, Helper: build a valid inspection submit body., Submit body with a photo on the first item (file_name is a stub)., Create inspection with one photo; returns (auth_headers, created_json)., Owner replaces a photo: 200, new file name, sort_order unchanged, old file remov, Supervisor can replace a photo of an inspection owned by someone else., Another inspector (not owner) cannot replace → 403 FORBIDDEN. (+22 more)

### Community 9 - "analytics.tsx"
Cohesion: 0.20
Nodes (13): currentWeekMonth(), DashboardAll, DashboardSummary, IssueFrequency, RoomScore, useDashboardData(), useDashboardSummary(), useLowestRooms() (+5 more)

### Community 10 - "conftest.py"
Cohesion: 0.07
Nodes (42): do_run_migrations(), run_async_migrations(), run_migrations_online(), Base, get_db(), create_access_token(), apply_sorting(), Select (+34 more)

### Community 11 - "useAuth.tsx"
Cohesion: 0.18
Nodes (14): Layout(), navItems, PwModal(), AuthContext, AuthProvider(), AuthState, useAuth(), User (+6 more)

### Community 12 - "process_one_job"
Cohesion: 0.24
Nodes (15): create_job(), fetch_pending_jobs(), _generate_thumbnail(), mark_job(), process_one_job(), AsyncSession, Generate a thumbnail for an inspection photo using Pillow., Process a single job. Returns True if successful, False otherwise.      ponytail (+7 more)

### Community 13 - "analytics/api.py"
Cohesion: 0.18
Nodes (23): dashboard_data(), dashboard_summary(), inspector_performance(), lowest_rooms(), AsyncSession, Single endpoint for dashboard stats — pending count, room count, monthly stats., top_issues(), DashboardOut (+15 more)

### Community 15 - "Background Jobs Context"
Cohesion: 0.36
Nodes (9): issue_frequency_stats, room_monthly_stats, Analytics Context, Background Jobs Context, Inspection Context, Media & Upload Context, background_jobs, inspection_photos (+1 more)

### Community 28 - "Auth & Authz Context"
Cohesion: 0.67
Nodes (3): Auth & Authz Context, user_sessions, users

### Community 29 - "Master Data Context"
Cohesion: 0.67
Nodes (3): Master Data Context, inspection_items, rooms

### Community 69 - "devDependencies"
Cohesion: 0.05
Nodes (37): autoprefixer, dependencies, react, react-dom, @tanstack/react-query, @tanstack/react-query-devtools, @tanstack/react-router, @tanstack/react-table (+29 more)

### Community 70 - "useMasterData.ts"
Cohesion: 0.15
Nodes (27): ADR-0013, Item, Room, RoomItem, SyncResponse, useAllRoomItems(), useAssignItemToRoom(), useAssignRoomToItem() (+19 more)

### Community 71 - "apiRequest"
Cohesion: 0.19
Nodes (23): useRoomsAll(), ROLES, SyncResponse, useAdminResetPassword(), useAllUserRooms(), useAssignUserToRoom(), useCreateUser(), useDeleteUser() (+15 more)

### Community 72 - "compilerOptions"
Cohesion: 0.08
Nodes (23): DOM, DOM.Iterable, ES2020, src, compilerOptions, allowImportingTsExtensions, esModuleInterop, isolatedModules (+15 more)

### Community 73 - "inspection-detail.tsx"
Cohesion: 0.16
Nodes (18): InspectionDetail, InspectionListItem, InspectionOut, InspectionPhoto, ListParams, useApproveInspection(), useInspection(), useInspections() (+10 more)

### Community 74 - "compilerOptions"
Cohesion: 0.11
Nodes (18): ES2023, vite.config.ts, compilerOptions, allowImportingTsExtensions, isolatedModules, lib, module, moduleDetection (+10 more)

### Community 75 - "main.tsx"
Cohesion: 0.20
Nodes (12): queryClient, Register, router, routeTree, @tanstack/react-router, Route, Route, Route (+4 more)

### Community 76 - "MasterDataPage.tsx"
Cohesion: 0.29
Nodes (7): PaginatedResult, Entity, MasterDataPage(), MasterDataPageProps, Modal(), ModalProps, useDebounce()

### Community 77 - "DataTable.tsx"
Cohesion: 0.36
Nodes (7): DataTable(), DataTableProps, generatePageNumbers(), ChevronLeftIcon(), ChevronRightIcon(), SortAscIcon(), SortDescIcon()

## Knowledge Gaps
- **90 isolated node(s):** `docker-entrypoint.sh script`, `background_jobs`, `users`, `user_sessions`, `rooms` (+85 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_user()` connect `create_user` to `User`, `test_user_rooms.py`, `Analytics Integration Tests`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `User` connect `User` to `create_user`, `master/api.py`, `hash_password`, `inspection/api.py`, `conftest.py`, `analytics/api.py`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `hash_password()` connect `hash_password` to `conftest.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 92 inferred relationships involving `create_user()` (e.g. with `test_create_item()` and `test_create_item_duplicate()`) actually correct?**
  _`create_user()` has 92 INFERRED edges - model-reasoned connections that need verification._
- **What connects `docker-entrypoint.sh script`, `background_jobs`, `users` to the rest of the system?**
  _90 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `create_user` be split into smaller, more focused modules?**
  _Cohesion score 0.0824561403508772 - nodes in this community are weakly interconnected._
- **Should `master/api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10275689223057644 - nodes in this community are weakly interconnected._