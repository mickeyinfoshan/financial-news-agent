# .claude/rules

Development rules and project conventions.

## Purpose

Project-specific guidelines that Claude Code must follow when working with this codebase.

## Ownership

Project conventions and development policies.

## Contents

- [dependency-management.md](dependency-management.md) - **Package Management**: Always use `uv`, never `pip`. Covers adding dependencies and syncing from lock files.
- [documentation-organization.md](documentation-organization.md) - **Documentation Structure**: Plans go in `.dev_docs/plan/`, summaries in `.dev_docs/summary/`. Prevents clutter in project root.
- [development-scripts.md](development-scripts.md) - **Temporary Scripts**: All temporary test/validation scripts go in `.dev_process/`, not project root. Formal tests go in `tests/`.

## Usage

These rules are automatically loaded by Claude Code and override default behavior. They ensure consistency across all development work.

## Quick Reference

- **Adding a dependency**: `uv add <package>` (never `pip install`)
- **Creating a plan**: Save to `.dev_docs/plan/`
- **Writing a summary**: Save to `.dev_docs/summary/`
- **Quick test script**: Save to `.dev_process/`
- **Formal test**: Save to `tests/`

## Related Documentation

See [CLAUDE.md](../../CLAUDE.md) for project overview and architecture.
