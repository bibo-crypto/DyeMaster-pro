# Phase 1 Audit Baseline

Date: 2026-11-19
Branch: `work/commercial-hardening`

## Actions completed

- Created a full original-source backup outside the worktree at `/home/ubuntu/backup/DyeMaster-pro-main-original`.
- Imported the supplied archive into `/home/ubuntu/work/DyeMaster-pro-main`.
- Initialized a local Git repository and created the independent branch `work/commercial-hardening`.
- Inventory completed for Python modules, UI modules, build files, updater, database, authentication, exports, and existing test-like code.
- Ran `python tools/audit.py` and `python -m compileall -q main.py app ui` against the untouched source.
- Ran an isolated real SQLite smoke test covering schema creation, color/recipe persistence, chemicals, backup, restore, and database isolation.

## Baseline findings

1. Source compilation succeeds, but there is no `tests/` suite and pytest collection initially fails because pytest is not installed in the development environment.
2. `app/tester.py` is a GUI/manual smoke-test harness, not a pytest suite. It catches many errors and must not be treated as coverage or a CI test result.
3. The audit tool reports 120 warnings, mostly broad `except Exception` handlers. These must be reduced carefully; domain/data errors must not be hidden.
4. Several source files begin with a UTF-8 BOM. Python runs them, but AST-based tooling fails unless it uses `utf-8-sig`.
5. Database schema setup is implicit and idempotent but uses repeated `ALTER TABLE ... ADD COLUMN` calls with ignored `OperationalError` exceptions. There is no explicit schema version/migration table or tested migration chain.
6. Existing recipe editing changes only recipe code/name. It does not provide the requested add/delete/replace color editor, transactional snapshot/version history, or audit trail for recipe changes.
7. The updater validates GitHub asset SHA-256 when GitHub provides a digest, but ZIP extraction uses `extractall` without path-traversal validation. The release contract and Windows executable flow still require Windows execution tests.
8. Linux validation cannot prove Tkinter UI behavior or Windows EXE/install/update behavior. Those checks remain explicitly unexecuted until a Windows runner/host is available.

## Baseline test status

The new pytest suite under `tests/` is intended to be run after installing `requirements-dev.txt`. No result is recorded here until it has actually been executed.

## Not claimed

This report does not claim Windows build success, EXE startup success, GitHub release update success, UI automation success, coverage percentage, or commercial readiness. Those require actual executions and will be reported separately.
