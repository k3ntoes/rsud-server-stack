# Graph Report - .  (2026-07-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 842 nodes · 1983 edges · 66 communities (53 shown, 13 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 98 edges (avg confidence: 0.75)
- Token cost: 2,394 input · 723 output

## Graph Freshness
- Built from commit: `35f888bc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Inspection UI Components
- Inspection Management API
- Authentication Tests
- Pagination and Analytics
- User Management API
- Frontend Dependencies
- Test Fixtures and Seeding
- Analytics Integration Tests
- Security and Password Hashing
- Inspection Submission Tests
- Background Jobs and Workers
- Authentication Schemas
- Master Data Schemas
- Inspection Data Schemas
- Database Schema Context
- Auth Database Tables
- Master Data Tables
- Docker Entrypoint
- User Entity
- Date Utilities
- Date Type
- Base Schema Model
- Date Helper
- User Model
- User Reference
- Async Test Client
- Inspection Submission Schema
- Server Root
- File Upload Type
- Master Data Hooks
- User and Admin Hooks
- TypeScript Application Config
- Frontend Routing and State
- Vite and Node Config
- Database Models and Migrations
- Database and Auth Core
- Auth Dependencies and Errors
- Analytics Dashboard UI
- Data Table Components
- Database Migration Script
- Auth Context and Provider
- Layout and Modal Components
- TypeScript Project References

## God Nodes (most connected - your core abstractions)
1. `create_user()` - 57 edges
2. `User` - 42 edges
3. `apiRequest()` - 42 edges
4. `create_user()` - 24 edges
5. `auth_header()` - 23 edges
6. `hash_password()` - 18 edges
7. `seed_room()` - 18 edges
8. `seed_item()` - 18 edges
9. `compilerOptions` - 18 edges
10. `Base` - 15 edges

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

## Communities (66 total, 13 thin omitted)

### Community 0 - "Inspection UI Components"
Cohesion: 0.17
Nodes (17): InspectionDetail, InspectionListItem, InspectionOut, InspectionPhoto, ListParams, useApproveInspection(), useInspection(), useInspections() (+9 more)

### Community 1 - "Inspection Management API"
Cohesion: 0.13
Nodes (34): approve_inspection_endpoint(), create_inspection(), get_inspection_by_id(), get_inspections(), AsyncSession, InspectionSubmit, UploadFile, User (+26 more)

### Community 2 - "Authentication Tests"
Cohesion: 0.07
Nodes (58): AsyncClient, AsyncSession, Malformed token → 401 with code TOKEN_INVALID (Android auto-refresh trigger)., Expired access token → 401 with code TOKEN_EXPIRED., Refresh token used as access → 401 with code TOKEN_INVALID., Admin can list all users., Admin creates a new inspector., Duplicate username → 409. (+50 more)

### Community 3 - "Pagination and Analytics"
Cohesion: 0.07
Nodes (77): paginate(), PaginatedResponse, BaseModel, apply_sorting(), Select, Apply ORDER BY to query if sort_by is a valid column for the model., dashboard_data(), dashboard_summary() (+69 more)

### Community 4 - "User Management API"
Cohesion: 0.06
Nodes (97): AdminResetPasswordRequest, admin_reset_password_endpoint(), assign_room_to_user_endpoint(), assign_user_to_room_endpoint(), change_password_endpoint(), create_user_endpoint(), delete_user_endpoint(), get_my_rooms() (+89 more)

### Community 5 - "Frontend Dependencies"
Cohesion: 0.05
Nodes (37): autoprefixer, dependencies, react, react-dom, @tanstack/react-query, @tanstack/react-query-devtools, @tanstack/react-router, @tanstack/react-table (+29 more)

### Community 6 - "Test Fixtures and Seeding"
Cohesion: 0.18
Nodes (42): create_access_token(), RoomItem, assign_item_to_room(), assign_user_to_room(), auth_header(), client(), create_user(), db_session() (+34 more)

### Community 7 - "Analytics Integration Tests"
Cohesion: 0.13
Nodes (35): date, AsyncClient, AsyncSession, Tests for analytics endpoints.  Covers: - GET /api/analytics/lowest-rooms (basic, admin_ppi also has dashboard access per PRD., No analytics data → empty array., Filter by YYYY-MM returns only that month's data., Respects limit parameter. (+27 more)

### Community 8 - "Security and Password Hashing"
Cohesion: 0.11
Nodes (27): upgrade(), hash_password(), verify_password(), seed_admin(), Tests for password hashing functions (app.core.security)., Hash is a string (not bytes)., Correct password returns True., Wrong password returns False. (+19 more)

### Community 9 - "Inspection Submission Tests"
Cohesion: 0.17
Nodes (30): AsyncClient, AsyncSession, Helper: build a valid inspection submit body., Submit body with a photo on the first item (file_name is a stub)., Create inspection with one photo; returns (auth_headers, created_json)., Owner replaces a photo: 200, new file name, sort_order unchanged, old file remov, Supervisor can replace a photo of an inspection owned by someone else., Another inspector (not owner) cannot replace → 403 FORBIDDEN. (+22 more)

### Community 10 - "Background Jobs and Workers"
Cohesion: 0.24
Nodes (15): create_job(), fetch_pending_jobs(), _generate_thumbnail(), mark_job(), process_one_job(), AsyncSession, Generate a thumbnail for an inspection photo using Pillow., Process a single job. Returns True if successful, False otherwise.      ponytail (+7 more)

### Community 11 - "Authentication Schemas"
Cohesion: 0.28
Nodes (12): AdminResetPasswordRequest, ChangePasswordRequest, LoginRequest, BaseModel, RefreshRequest, TokenResponse, UserCreate, UserListOut (+4 more)

### Community 12 - "Master Data Schemas"
Cohesion: 0.33
Nodes (10): ItemCreate, ItemOut, ItemUpdate, BaseModel, RoomCreate, RoomItemAssign, RoomItemOut, RoomOut (+2 more)

### Community 13 - "Inspection Data Schemas"
Cohesion: 0.36
Nodes (9): DetailOut, DetailSubmit, InspectionListItem, InspectionOut, InspectionSubmit, PhotoOut, PhotoSubmit, RejectRequest (+1 more)

### Community 14 - "Database Schema Context"
Cohesion: 0.36
Nodes (9): issue_frequency_stats, room_monthly_stats, Analytics Context, Background Jobs Context, Inspection Context, Media & Upload Context, background_jobs, inspection_photos (+1 more)

### Community 24 - "Auth Database Tables"
Cohesion: 0.67
Nodes (3): Auth & Authz Context, user_sessions, users

### Community 25 - "Master Data Tables"
Cohesion: 0.67
Nodes (3): Master Data Context, inspection_items, rooms

### Community 48 - "Master Data Hooks"
Cohesion: 0.18
Nodes (26): Item, Room, RoomItem, SyncResponse, useAllRoomItems(), useAssignItemToRoom(), useAssignRoomToItem(), useCreateItem() (+18 more)

### Community 49 - "User and Admin Hooks"
Cohesion: 0.17
Nodes (22): useRoomsAll(), ROLES, SyncResponse, useAdminResetPassword(), useAllUserRooms(), useAssignUserToRoom(), useCreateUser(), useDeleteUser() (+14 more)

### Community 50 - "TypeScript Application Config"
Cohesion: 0.08
Nodes (23): DOM, DOM.Iterable, ES2020, src, compilerOptions, allowImportingTsExtensions, esModuleInterop, isolatedModules (+15 more)

### Community 51 - "Frontend Routing and State"
Cohesion: 0.14
Nodes (18): useDashboardData(), useAuth(), queryClient, Register, router, routeTree, @tanstack/react-router, DashboardPage() (+10 more)

### Community 52 - "Vite and Node Config"
Cohesion: 0.11
Nodes (18): ES2023, vite.config.ts, compilerOptions, allowImportingTsExtensions, isolatedModules, lib, module, moduleDetection (+10 more)

### Community 53 - "Database Models and Migrations"
Cohesion: 0.24
Nodes (12): do_run_migrations(), run_async_migrations(), run_migrations_online(), Base, IssueFrequencyStats, RoomMonthlyStats, Inspection, InspectionDetail (+4 more)

### Community 54 - "Database and Auth Core"
Cohesion: 0.19
Nodes (7): get_db(), UserRoom, UserSession, BackgroundJob, Comprehensive seed data for end-to-end demo.  Usage: uv run python -m app.seed, Base, datetime

### Community 55 - "Auth Dependencies and Errors"
Cohesion: 0.11
Nodes (18): Settings, AuthError, get_current_user(), AsyncSession, Exception, User, Raised by auth dependencies to produce a 401 with a machine-readable code., error_response() (+10 more)

### Community 56 - "Analytics Dashboard UI"
Cohesion: 0.24
Nodes (10): currentWeekMonth(), DashboardAll, DashboardSummary, IssueFrequency, RoomScore, useDashboardSummary(), useLowestRooms(), useTopIssues() (+2 more)

### Community 57 - "Data Table Components"
Cohesion: 0.20
Nodes (12): DataTable(), DataTableProps, generatePageNumbers(), PaginatedResult, ChevronLeftIcon(), ChevronRightIcon(), SortAscIcon(), SortDescIcon() (+4 more)

### Community 58 - "Database Migration Script"
Cohesion: 0.29
Nodes (9): AsyncSession, _extract_all(), _import_all(), migrate(), SQLite → PostgreSQL data migration script.  Usage:     # Ensure PostgreSQL is ru, Convert Python/DB types to JSON-safe values for cross-DB transfer., Extract all data from SQLite source as dicts., Import all data into PostgreSQL, preserving FK relationships. (+1 more)

### Community 59 - "Auth Context and Provider"
Cohesion: 0.31
Nodes (8): AuthContext, AuthProvider(), AuthState, User, accessToken, setAccessToken(), setOnUnauthorized(), tryRefresh()

### Community 61 - "Layout and Modal Components"
Cohesion: 0.32
Nodes (6): Layout(), navItems, PwModal(), Modal(), ModalProps, useChangePassword()

## Knowledge Gaps
- **89 isolated node(s):** `docker-entrypoint.sh script`, `background_jobs`, `users`, `user_sessions`, `rooms` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Pagination and Analytics` to `Test Fixtures and Seeding`, `Security and Password Hashing`, `Database Models and Migrations`, `Database and Auth Core`, `Auth Dependencies and Errors`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `create_user()` connect `User Management API` to `Analytics Integration Tests`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `hash_password()` connect `Security and Password Hashing` to `Database and Auth Core`, `Test Fixtures and Seeding`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 52 inferred relationships involving `create_user()` (e.g. with `test_inspector_performance_as_inspector_forbidden()` and `test_inspector_performance_empty_month()`) actually correct?**
  _`create_user()` has 52 INFERRED edges - model-reasoned connections that need verification._
- **What connects `docker-entrypoint.sh script`, `background_jobs`, `users` to the rest of the system?**
  _89 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Inspection Management API` be split into smaller, more focused modules?**
  _Cohesion score 0.1253968253968254 - nodes in this community are weakly interconnected._
- **Should `Authentication Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.07130333138515488 - nodes in this community are weakly interconnected._