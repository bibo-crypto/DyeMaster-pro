# DyeMaster Pro Engineering Round Report

Base: `3cefd3a889491a828729e22fd968180a14d141c8`

## Implemented

- Added centralized recipe compatibility rules in `app/recipe_rules.py`, using the existing rules only:
  - no INDANTHREN + REATTIVI mixing;
  - no REATTIVI CALDI + REATTIVI FREDDI mixing.
- Applied compatibility and integrity validation at both Recipe Editor and SQLite persistence boundaries.
- Extended recipe History transactions to support detailed `add_color`, `delete_color`, `replace_color`, `update_quantity`, and `edit_recipe` events with full before/after snapshots, version IDs, actor, and operation details.
- Added transactional `update_recipe_color_percentage()` support.
- Added `schema_migrations` metadata with idempotent schema versions 1 and 2.
- Added immutable `production_records` snapshots linked to a captured recipe version. Production reads use the stored snapshot rather than the current recipe contents.
- Made schema initialization explicitly transactional so a migration failure rolls back schema changes.
- Added real SQLite integration tests for compatibility rejection, operation history, quantity updates, production snapshot stability, old-database migration, idempotent reopening, and migration rollback.

## Local verification

```text
30 passed, 0 skipped
Coverage: 14% total
```

The suite was run with SQLite temporary databases and Tkinter available. No chemistry formulas or existing calculator rules were changed.

## Not yet verified

- Windows GitHub Actions and Windows artifact have not yet been run for this new engineering-round commit; they will be required before this round is considered complete.
- GUI interaction on a real Windows desktop and launching the packaged EXE were not performed in this Linux sandbox. The CI job can verify the build and tests, but it does not launch the graphical EXE.
