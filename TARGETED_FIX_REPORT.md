# Targeted Fix Report

Base commit: `de06c2e2a4703cdf97bd6ff8f49ddb140a318fc5`
Working branch: `work/targeted-fixes`

## Packaging and versioning

PyInstaller was run locally with `DyeMasterPro.spec` after the fix. The emitted files were verified as follows:

```text
dist/DyeMasterPro/version.txt   -> 1.0.4
dist/DyeMasterPro/DyeMasterPro  -> present
dist/DyeMasterPro/_internal/version.txt -> absent after the fix
```

The spec now sets `contents_directory='.'`, so the existing CI check at `dist/DyeMasterPro/version.txt` is not bypassed or weakened. `app/config.py` retains an `_internal/version.txt` fallback for compatibility with older packages. `version.txt` and `installer.iss` both declare `1.0.4`.

## Repository cleanup

The tracked `.pytest_tmp/test_backup_and_restore_keep_e0/dyemaster-test.db.before_restore` artifact was removed. `.gitignore` now excludes pytest cache/temp folders and restore-test database artifacts. Existing `*.db` rules remain in place.

## Recipe Editor

Recipe Editor now has a dedicated Replace Color control. It retains the selected color's percentage, rejects duplicates and incompatible dye families, refreshes the normal chemical calculation preview, and records a `replace_color` history operation with old/new color codes. The database also exposes `replace_recipe_color()` for a transactional direct operation that never creates a new Recipe ID.

## Local verification

The local Linux run completed:

```text
17 passed, 2 skipped
```

The two skipped modules require Tkinter, which is not installed in this Linux sandbox. They include the UI-controller regression tests and the updater tests; the Windows CI job is configured to execute them on `windows-latest`.

The local PyInstaller build succeeded and verified the root `version.txt` location. No Windows executable was run in this sandbox, and no such run is claimed.

## GitHub Actions status

No new GitHub Actions run is claimed for this branch because the branch was not pushed from this session. The repository workflow still runs Linux pytest, Windows pytest, Windows PyInstaller, the root `version.txt` verification, and Windows artifact upload. A real Actions report requires pushing this branch or opening a pull request, then recording the resulting run URL and artifact.
