# GitHub Actions Test Coverage Integration Design

**Date:** 2026-05-24  
**Status:** Approved  
**Goal:** Add test coverage measurement and reporting to GitHub Actions CI pipeline using Codecov

## Context

The financial news agent project has a comprehensive test suite with pytest and pytest-cov already configured as dependencies. However, test coverage is not currently measured or reported in the CI pipeline. This design adds coverage measurement to GitHub Actions and integrates with Codecov for visualization and tracking, without enforcing coverage thresholds or requiring coverage improvements.

## Requirements

1. Measure test coverage during CI runs
2. Upload coverage data to Codecov for visualization and trend tracking
3. Enable automatic PR comments showing coverage changes
4. Do not enforce minimum coverage thresholds (informational only)
5. Maintain fast CI execution times
6. Use modern Codecov GitHub App authentication (no token management)

## Architecture

### High-Level Flow

```
GitHub Actions Trigger (push/PR)
  ↓
Checkout code + Setup Python + Install dependencies (existing)
  ↓
Run pytest with coverage flags (--cov=financial_news_agent --cov-report=xml)
  ↓
Generate coverage.xml (Cobertura format)
  ↓
Upload to Codecov via codecov-action@v5
  ↓
Codecov processes and displays results
  ↓
Codecov bot comments on PR with coverage diff
```

### Components

#### 1. GitHub Actions Workflow Modification

**File:** `.github/workflows/tests.yml`

**Changes:**
- Modify pytest command to include coverage flags
- Add new step to upload coverage to Codecov
- Configure Codecov action with appropriate settings

**Before:**
```yaml
- name: Run tests
  run: uv run pytest -v
```

**After:**
```yaml
- name: Run tests with coverage
  run: uv run pytest --cov=financial_news_agent --cov-report=xml --cov-report=term -v
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    NEWS_API_KEY: ${{ secrets.NEWS_API_KEY }}
    FINNHUB_API_KEY: ${{ secrets.FINNHUB_API_KEY }}

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v5
  with:
    file: ./coverage.xml
    fail_ci_if_error: false
    verbose: true
```

#### 2. Coverage Configuration

**File:** `pyproject.toml`

Add coverage configuration to specify what to measure and how to report:

```toml
[tool.coverage.run]
source = ["financial_news_agent"]
omit = [
    "*/tests/*",
    "*/.dev_process/*",
    "*/conftest.py",
]
branch = true

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false

[tool.coverage.xml]
output = "coverage.xml"
```

**Configuration rationale:**
- `source`: Only measure code in the main package
- `omit`: Exclude test files and development scripts
- `branch = true`: Track both line and branch coverage
- `precision = 2`: Show coverage percentages to 2 decimal places
- `show_missing = true`: Display which lines aren't covered in terminal output

#### 3. Codecov Setup

**One-time manual setup:**
1. Visit https://github.com/apps/codecov
2. Install Codecov GitHub App
3. Grant access to the `financial-news-agent-2` repository
4. No token configuration needed (GitHub App provides authentication)

**Codecov features enabled:**
- Coverage dashboard at codecov.io
- Historical coverage trends
- PR comments with coverage diff
- Coverage badges for README (optional)
- File-level coverage visualization

## Coverage Scope

### What Gets Measured

- **Package:** `financial_news_agent/` (all Python modules)
- **Metrics:** 
  - Line coverage: percentage of code lines executed
  - Branch coverage: percentage of conditional branches taken
- **Granularity:** File-level, function-level, and line-level coverage

### What Gets Excluded

- Test files (`tests/`)
- Development scripts (`.dev_process/`)
- Configuration files (`conftest.py`)
- Virtual environment and dependencies

### No Enforcement

Per requirements, coverage thresholds are **not enforced**:
- CI will not fail due to low coverage
- No minimum coverage percentage required
- Coverage is purely informational for developers
- `fail_ci_if_error: false` ensures Codecov issues don't block CI

## Data Flow

1. **Test Execution:** GitHub Actions runs pytest with coverage instrumentation
2. **Coverage Collection:** pytest-cov tracks which lines/branches execute during tests
3. **Report Generation:** Coverage data written to `coverage.xml` (Cobertura XML format)
4. **Terminal Display:** Coverage summary printed to CI logs via `--cov-report=term`
5. **Upload:** codecov-action reads `coverage.xml` and uploads to Codecov API
6. **Processing:** Codecov processes data and updates dashboard
7. **PR Integration:** Codecov bot posts comment on PRs showing coverage changes

## Error Handling

### Graceful Degradation

- **Codecov upload failure:** CI job continues and passes (external service issues don't block merges)
- **Coverage generation failure:** CI job fails (indicates broken test infrastructure)
- **Network issues:** Codecov action retries automatically, then gracefully fails

### Visibility

- **Console output:** Coverage summary visible in GitHub Actions logs
- **XML artifact:** `coverage.xml` available for download if manual inspection needed
- **Codecov dashboard:** Historical trends and detailed reports at codecov.io
- **PR comments:** Automatic coverage diff on every pull request

## Performance Impact

- **Coverage collection:** ~2-5 seconds added to test execution
- **Report generation:** ~1-2 seconds for XML generation
- **Upload to Codecov:** ~3-5 seconds for API upload
- **Total overhead:** ~6-12 seconds per CI run

This is negligible compared to typical test execution time and dependency installation.

## Implementation Steps

1. Add coverage configuration to `pyproject.toml`
2. Modify `.github/workflows/tests.yml` to run tests with coverage and upload to Codecov
3. Install Codecov GitHub App and grant repository access
4. Commit changes and push to trigger CI
5. Verify coverage appears on Codecov dashboard
6. (Optional) Add Codecov badge to README.md

## Future Enhancements (Out of Scope)

- Coverage thresholds and enforcement
- Coverage badges in README
- Multiple coverage formats (HTML reports as artifacts)
- Coverage comparison between branches
- Integration with other coverage services

## References

- pytest-cov documentation: https://pytest-cov.readthedocs.io/
- Codecov GitHub Action: https://github.com/codecov/codecov-action
- Codecov documentation: https://docs.codecov.com/
