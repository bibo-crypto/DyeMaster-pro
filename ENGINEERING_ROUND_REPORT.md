# DyeMaster Pro Engineering Round Report

Base: `3cefd3a889491a828729e22fd968180a14d141c8`

Final merged commit: [`9bbf707fe46f11f9105943a2c09c71fbaa8e89e5`](https://github.com/bibo-crypto/DyeMaster-pro/commit/9bbf707fe46f11f9105943a2c09c71fbaa8e89e5)
Pull request: [#1](https://github.com/bibo-crypto/DyeMaster-pro/pull/1)

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
python3 -m compileall -q main.py app ui tests: passed
git diff --check: passed
```

The suite was run with SQLite temporary databases and Tkinter available. No chemistry formulas or existing calculator rules were changed.

## GitHub Actions verification

Main-branch CI run: [44847244248](https://github.com/bibo-crypto/DyeMaster-pro/actions/runs/44847244248)

- Linux pytest: passed.
- Windows pytest: passed.
- PyInstaller on Windows: passed.
- Verify packaged files: passed.
- Windows artifact upload: passed.

Downloaded artifact `windows-dyemaster-build` was inspected successfully:

- `DyeMasterPro.exe` present.
- `version.txt` present beside the executable and contains `1.0.4`.

The run emitted only a GitHub Actions Node.js 20 deprecation annotation for existing action versions; it did not fail any job.

## Explicit limitation

The packaged graphical EXE was not launched interactively in this Linux sandbox. CI built and inspected the Windows package and ran the Windows test/build workflow, but this is not a claim of manual EXE launch verification.

No GitHub Release was created or modified.
