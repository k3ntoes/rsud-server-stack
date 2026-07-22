## Agent skills

### Issue tracker
Issues tracked via Beads (CLI: `bd`), stored in `.beads/` as a Dolt-backed AI-native issue tracker. See `docs/agents/issue-tracker.md`.

### Triage labels
Default triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs
Multi-context layout: `CONTEXT-MAP.md` at root points to per-context `CONTEXT.md` files under `src/`. See `docs/agents/domain.md`.

## Workflow: Issue-Driven Changes

### Always Do

- **MUST create a Beads issue before starting work on a new change.**
  - Before modifying any file, run `bd create "<title>" --body "<description>"` to create a tracking issue.
  - The issue title should clearly describe what will be changed and why.
  - The issue body should include:
    - Context: what needs to change and why
    - Files affected (estimated)
    - Dependencies: ADRs, CONTEXT.md terms, or existing issues this relates to
  - After creation, claim the issue: `bd update <issue-id> --claim`

- **Exception: already working on an issue.**
  - If an issue already exists for the work (claimed or assigned), skip creation.
  - If the user explicitly asks to continue without creating an issue, skip creation.

### Never Do

- NEVER make changes without a corresponding Beads issue, unless the change is trivial (typo, rename) or explicitly requested by the user without one.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **rsud-server-stack** (1056 symbols, 2045 relationships, 64 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/rsud-server-stack/context` | Codebase overview, check index freshness |
| `gitnexus://repo/rsud-server-stack/clusters` | All functional areas |
| `gitnexus://repo/rsud-server-stack/processes` | All execution flows |
| `gitnexus://repo/rsud-server-stack/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

<!-- graphify:start -->
# Graphify — Knowledge Graph

This project uses **graphify** (v0.9.23) to build a navigable knowledge graph from source code. The graph helps agents understand code relationships, detect communities, and trace execution paths across the monorepo.

## Monorepo Update (Correct Command)

Gunakan **`graphify extract`** (bukan `graphify .`), lalu merge dengan `--out`:

```bash
# 1. Extract per subdirectory (output di <dir>/graphify-out/graph.json)
graphify extract ./backend/ --code-only --no-viz
graphify extract ./web-admin/ --code-only --no-viz

# 2. Merge into single monorepo graph (output: graphify-out/graph.json)
graphify merge-graphs ./backend/graphify-out/graph.json ./web-admin/graphify-out/graph.json --out graphify-out/graph.json
```

## Known Constraints

- **Monorepo**: Wajib `graphify extract ./subdir/` per proyek, lalu `merge-graphs --out`. Root-level `graphify .` gagal dengan `deduplicate_entities: nodes span multiple repos`.
- **No API key**: Gunakan `--code-only`. AST extraction berfungsi tanpa API key. Semantic extraction (docs, papers, images) butuh `GEMINI_API_KEY`.
- **Output**: `graphify extract` menempatkan `graphify-out/` di **dalam** direktori yang di-scan (`backend/graphify-out/`, `web-admin/graphify-out/`). Merge dengan `--out` menulis ke root `graphify-out/graph.json`.

## Resources

| Task | Command |
|------|---------|
| Full code re-index | `graphify extract ./backend/ --code-only --no-viz && graphify extract ./web-admin/ --code-only --no-viz && graphify merge-graphs ./backend/graphify-out/graph.json ./web-admin/graphify-out/graph.json --out graphify-out/graph.json` |
| Incremental update | Same as full re-index — graphify handles caching via `extract` |
| Re-cluster only | `graphify cluster-only <dir>` |
| Query merged graph | `graphify query "<question>"` (from root, reads `graphify-out/graph.json`) |
| Shortest path | `graphify path "NodeA" "NodeB"` |
| Merge graphs | `graphify merge-graphs <g1.json> <g2.json> --out <output.json>` |

<!-- graphify:end -->
