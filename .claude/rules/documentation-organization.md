# Documentation Organization

**All planning and summary documents MUST be placed in `.dev_docs/` directory.**

## Directory Structure

```
.dev_docs/
├── plan/       # Implementation plans, design docs
└── summary/    # Summaries, retrospectives, notes
```

## Rules

- ✅ Plans → `.dev_docs/plan/`
- ✅ Summaries → `.dev_docs/summary/`
- ❌ Do NOT create `*_PLAN.md`, `*_SUMMARY.md` in project root
- ✅ Use descriptive filenames with dates when relevant
- ✅ Every directory MUST have a `README.md` explaining its purpose and ownership boundary
- ✅ Parent directory READMEs should link to child directory READMEs
- ✅ Keep parent READMEs concise and avoid duplicating child-level details

## Examples

```bash
# Correct
.dev_docs/plan/llm-refactoring.md
.dev_docs/plan/2026-03-17-api-changes.md
.dev_docs/summary/agent-workflow.md

# Wrong
REFACTORING_PLAN.md
API_SUMMARY.md
implementation-notes.md
```
