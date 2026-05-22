# Dependency Management

**ALWAYS use `uv` for package management. NEVER use `pip`.**

## Commands

```bash
# Add dependency
uv add <package>

# Add dev dependency
uv add --dev <package>

# Sync from pyproject.toml/uv.lock
uv sync
```

## Rules

- ✅ `uv add` / `uv sync`
- ❌ `pip install`
- ✅ Commit both `pyproject.toml` and `uv.lock`
- ❌ Manual edits to `uv.lock`
