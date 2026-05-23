# .dev_process

Temporary validation and test scripts for development.

## Purpose

Ad-hoc scripts for quick testing, validation, and debugging during development.

## Ownership

Throwaway development scripts. These are temporary and can be deleted after use.

## What Goes Here

- Quick validation scripts (e.g., `test_finnhub.py`)
- Manual testing scripts (e.g., `test_manual_context.py`)
- Setup verification scripts (e.g., `check_setup.py`)
- One-off debugging scripts

## What Doesn't Go Here

- Formal unit tests (use `tests/` instead)
- Committed test infrastructure (use `tests/` instead)
- Documentation (use `docs/` or `.dev_docs/` instead)

## Important

These scripts are NOT formal tests. They are temporary helpers for development and can be deleted once they've served their purpose.

## Reference

See `.claude/rules/development-scripts.md` for the full development scripts policy.
