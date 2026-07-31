# Graph Report - .  (2026-07-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 795 nodes · 1910 edges · 64 communities (44 shown, 20 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 160 edges (avg confidence: 0.77)
- Token cost: 1,818 input · 687 output

## Graph Freshness
- Built from commit: `e0b79059`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- User Management Tests
- User Auth Endpoints
- Database Configuration
- Pagination and Sorting
- Test Fixtures and Seeding
- Inspection API Endpoints
- Analytics Endpoint Tests
- Security and Password Hashing
- devDependencies
- Data Table Components
- Background Job Services
- Inspection Workflow Tests
- Master Data Schemas
- Database Schema Context
- Auth Database Context
- Master Data Context
- Docker Entrypoint Script
- User Entity
- User Entity
- User Entity
- Date Utilities
- User Entity
- Base Model Schema
- Date Utilities
- User Entity
- User Entity
- Async Test Client
- Inspection Submission Schema
- Server Root
- File Upload Handling
- User Session Entity
- Dashboard UI Components
- Frontend TypeScript Config
- Vite and Node Config
- API Client Utilities
- Modal UI Component
- TypeScript Project References
- FastAPI Backend Framework
- TanStack Query Library
- TanStack Router Library

## God Nodes (most connected - your core abstractions)
1. `create_user()` - 93 edges
2. `User` - 76 edges
3. `create_user()` - 24 edges
4. `auth_header()` - 23 edges
5. `assign_user_to_room()` - 22 edges
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

## Communities (64 total, 20 thin omitted)

### Community 0 - "User Management Tests"
Cohesion: 0.06
Nodes (98): create_user(), AsyncClient, AsyncSession, Admin can list all users., Admin creates a new inspector., Duplicate username → 409., Non-admin cannot create users., Admin can change a user's role. (+90 more)

### Community 1 - "User Auth Endpoints"
Cohesion: 0.10
Nodes (60): admin_reset_password_endpoint(), assign_room_to_user_endpoint(), assign_user_to_room_endpoint(), change_password_endpoint(), create_user_endpoint(), delete_user_endpoint(), get_my_rooms(), get_room_users() (+52 more)

### Community 2 - "Database Configuration"
Cohesion: 0.05
Nodes (62): do_run_migrations(), run_async_migrations(), run_migrations_online(), Settings, Base, get_db(), get_current_user(), AsyncSession (+54 more)

### Community 3 - "Pagination and Sorting"
Cohesion: 0.10
Nodes (48): paginate(), PaginatedResponse, BaseModel, apply_sorting(), Select, Apply ORDER BY to query if sort_by is a valid column for the model., assign_item_to_room_endpoint(), assign_room_to_item_endpoint() (+40 more)

### Community 4 - "Test Fixtures and Seeding"
Cohesion: 0.18
Nodes (42): create_access_token(), RoomItem, assign_item_to_room(), assign_user_to_room(), auth_header(), client(), create_user(), db_session() (+34 more)

### Community 5 - "Inspection API Endpoints"
Cohesion: 0.14
Nodes (28): approve_inspection_endpoint(), create_inspection(), get_inspection_by_id(), get_inspections(), AsyncSession, InspectionSubmit, reject_inspection_endpoint(), DetailOut (+20 more)

### Community 6 - "Analytics Endpoint Tests"
Cohesion: 0.13
Nodes (35): date, AsyncClient, AsyncSession, Tests for analytics endpoints.  Covers: - GET /api/analytics/lowest-rooms (basic, admin_ppi also has dashboard access per PRD., No analytics data → empty array., Filter by YYYY-MM returns only that month's data., Respects limit parameter. (+27 more)

### Community 7 - "Security and Password Hashing"
Cohesion: 0.11
Nodes (27): upgrade(), hash_password(), verify_password(), seed_admin(), Tests for password hashing functions (app.core.security)., Hash is a string (not bytes)., Correct password returns True., Wrong password returns False. (+19 more)

### Community 8 - "devDependencies"
Cohesion: 0.05
Nodes (37): autoprefixer, dependencies, react, react-dom, @tanstack/react-query, @tanstack/react-query-devtools, @tanstack/react-router, @tanstack/react-table (+29 more)

### Community 9 - "Data Table Components"
Cohesion: 0.07
Nodes (51): DataTable(), DataTableProps, generatePageNumbers(), PaginatedResult, ChevronLeftIcon(), ChevronRightIcon(), SortAscIcon(), SortDescIcon() (+43 more)

### Community 10 - "Background Job Services"
Cohesion: 0.22
Nodes (16): create_job(), fetch_pending_jobs(), _generate_thumbnail(), mark_job(), process_one_job(), AsyncSession, Generate a thumbnail for an inspection photo using Pillow., Process a single job. Returns True if successful, False otherwise.      ponytail (+8 more)

### Community 11 - "Inspection Workflow Tests"
Cohesion: 0.41
Nodes (16): assign_user_to_room(), assign_item_to_room(), AsyncClient, AsyncSession, Helper: build a valid inspection submit body., _submit_body(), test_approve_already_approved(), test_approve_inspection() (+8 more)

### Community 12 - "Master Data Schemas"
Cohesion: 0.33
Nodes (10): ItemCreate, ItemOut, ItemUpdate, BaseModel, RoomCreate, RoomItemAssign, RoomItemOut, RoomOut (+2 more)

### Community 13 - "Database Schema Context"
Cohesion: 0.36
Nodes (9): issue_frequency_stats, room_monthly_stats, Analytics Context, Background Jobs Context, Inspection Context, Media & Upload Context, background_jobs, inspection_photos (+1 more)

### Community 22 - "Auth Database Context"
Cohesion: 0.67
Nodes (3): Auth & Authz Context, user_sessions, users

### Community 23 - "Master Data Context"
Cohesion: 0.67
Nodes (3): Master Data Context, inspection_items, rooms

### Community 49 - "Dashboard UI Components"
Cohesion: 0.05
Nodes (60): Layout(), navItems, PwModal(), currentWeekMonth(), DashboardAll, DashboardSummary, IssueFrequency, RoomScore (+52 more)

### Community 50 - "Frontend TypeScript Config"
Cohesion: 0.08
Nodes (23): DOM, DOM.Iterable, ES2020, src, compilerOptions, allowImportingTsExtensions, esModuleInterop, isolatedModules (+15 more)

### Community 51 - "Vite and Node Config"
Cohesion: 0.11
Nodes (18): ES2023, vite.config.ts, compilerOptions, allowImportingTsExtensions, isolatedModules, lib, module, moduleDetection (+10 more)

### Community 52 - "API Client Utilities"
Cohesion: 0.53
Nodes (4): accessToken, apiRequest(), setAccessToken(), tryRefresh()

## Knowledge Gaps
- **95 isolated node(s):** `docker-entrypoint.sh script`, `background_jobs`, `users`, `user_sessions`, `rooms` (+90 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User Auth Endpoints` to `User Management Tests`, `Database Configuration`, `Pagination and Sorting`, `Test Fixtures and Seeding`, `Inspection API Endpoints`, `Security and Password Hashing`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `create_user()` connect `User Management Tests` to `User Auth Endpoints`, `Inspection Workflow Tests`, `Analytics Endpoint Tests`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `hash_password()` connect `Security and Password Hashing` to `Test Fixtures and Seeding`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `create_user()` (e.g. with `test_admin_reset_password_by_supervisor_forbidden()` and `test_admin_reset_password_forbidden_non_admin()`) actually correct?**
  _`create_user()` has 88 INFERRED edges - model-reasoned connections that need verification._
- **What connects `docker-entrypoint.sh script`, `background_jobs`, `users` to the rest of the system?**
  _95 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `User Management Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.05801980198019802 - nodes in this community are weakly interconnected._
- **Should `User Auth Endpoints` be split into smaller, more focused modules?**
  _Cohesion score 0.1001984126984127 - nodes in this community are weakly interconnected._