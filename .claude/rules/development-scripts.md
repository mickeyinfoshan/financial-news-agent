# Development Process Scripts

**All temporary validation and test scripts MUST be placed in `.dev_process/` directory.**

## Rules

- ✅ Temporary test scripts → `.dev_process/`
- ✅ Validation scripts → `.dev_process/`
- ✅ Quick verification scripts → `.dev_process/`
- ❌ Do NOT create `test_*.py`, `verify_*.py`, `check_*.py` in project root
- ✅ Scripts in `.dev_process/` are temporary and can be deleted after use

## Examples

```bash
# Correct
.dev_process/test_llm_client.py
.dev_process/verify_mcp_connection.py
.dev_process/check_database.py

# Wrong
test_something.py
verify_api.py
quick_check.sh
```

## Note

These are NOT formal unit tests (use `tests/` for those). These are quick, throwaway scripts for development and debugging.
