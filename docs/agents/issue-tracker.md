# Issue tracker: Beads

Issues and specs for this repo live in a **Beads** database (`.beads/`). Beads is an AI-native issue tracking tool that uses a Dolt-backed database stored directly in the repository.

## Prerequisites

Ensure the `bd` CLI is installed. If not:

```bash
curl -sSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
```

## Conventions

- **Create an issue**: `bd create "<title>" --body "<description>"`
- **List issues**: `bd list`
- **View an issue**: `bd show <issue-id>`
- **Update issue status**: `bd update <issue-id> --claim` (claim) / `bd update <issue-id> --status done` (resolve)
- **Add comments**: `bd update <issue-id> --comment "<comment>"`
- **Sync with remote**: `bd dolt push` / `bd dolt pull`

Issues are:
- **Git-native**: Stored in Dolt database with version control and branching
- **Branch-aware**: Issues can follow your branch workflow
- **Sync-ready**: Uses Dolt remotes for backup and team sharing

## When a skill says "publish to the issue tracker"

Run `bd create` with the appropriate title and body.

## When a skill says "fetch the relevant ticket"

Run `bd show <issue-id>` to view the issue details.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a Beads issue that groups related child tickets.

- **Map**: A Beads issue that holds the Notes / Decisions-so-far / Fog body.
- **Child ticket**: A Beads issue linked to the map issue via its description.
- **Blocking**: Recorded in the issue body as a `Blocked by: <issue-id>, <issue-id>` line.
- **Frontier**: Scan open, unblocked, and unclaimed issues via `bd list`.
- **Claim**: `bd update <issue-id> --claim`
- **Resolve**: `bd update <issue-id> --status done`, then append a context pointer to the map.
