# Linux Test Report

Date: 2026-11-19
Command:

```bash
python -m pytest -q --cov=app --cov=ui --cov-report=term-missing --cov-report=xml:coverage.xml
```

## Result

- Passed: 12
- Failed: 0
- Skipped: 1
- Total collected/executed: 13 test outcomes
- Total measured coverage: 9% (9,707 statements; 882 covered)
- Coverage XML: `coverage.xml` generated locally and ignored by Git

The skipped test module is the updater test because this Linux sandbox does not provide the `tkinter` module. This is an explicit environment limitation, not a pass claim. Windows CI is configured to run the updater tests where Tkinter is available.

## Covered areas

- Input validation and recipe validation
- Chemical and cost calculations
- SQLite schema creation
- Color and recipe persistence
- Transaction rollback when a recipe references a missing color
- PBKDF2 password hashing and login permissions
- Backup and restore of a real SQLite database
- Recipe rename/code update persistence
- Transactional add/replace recipe contents and immutable edit history

## Not validated by this report

- Tkinter UI behavior
- Windows EXE build or startup
- Inno Setup installation
- Update replacement on Windows
- GitHub Release download and deployment
- Performance under production-sized datasets
- Full database migration compatibility across historical releases

No coverage target was imposed and no code was excluded to inflate the result.
