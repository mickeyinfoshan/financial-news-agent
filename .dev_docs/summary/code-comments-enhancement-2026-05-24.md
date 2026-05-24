# Code Comments Enhancement - 2026-05-24

## Overview

Added meaningful comments to core codebase focusing on explaining WHY (rationale, constraints, edge cases) rather than WHAT (code functionality).

## Philosophy

Following best practices:
- **Only comment when WHY is non-obvious**: Hidden constraints, subtle invariants, workarounds, surprising behavior
- **Never explain WHAT**: Well-named functions and variables already document functionality
- **No task references**: Comments explain design decisions, not implementation history
- **Focus on future maintainers**: Help readers understand non-obvious choices

## Files Enhanced

### 1. `agent.py` - Main Agent Loop

**Key comments added:**

- **Query rewriting optimization**: Why we skip rewriting on first turn and for self-contained queries (avoids unnecessary LLM calls)
- **Reasoning tracking logic**: Why we only track reasoning when tool calls are present (final answers tracked separately)
- **Final iteration forcing**: Why we disable tools on last iteration (prevents infinite loops)
- **Source numbering strategy**: Why start_id is calculated before adding sources (ensures continuous numbering across multiple tool calls)
- **Quote stripping**: Why we remove quotes from LLM output (LLMs sometimes wrap despite instructions)
- **Graceful degradation**: Why we return original query on rewriting failure (better ambiguous than broken)
- **Context window limits**: Why we limit to 6 messages and truncate to 300 chars (prevents token bloat)

### 2. `context_manager.py` - Context Window Management

**Key comments added:**

- **Summarization purpose**: Why we preserve recent messages while summarizing middle (maintains coherent multi-turn dialogue)
- **Compression strategy**: Why two-tier approach (Tier 1: remove unnecessary fields, Tier 2: limit count)
- **Truncation rationale**: Why 500 char limit on summarization input (prevents overwhelming the prompt)

### 3. `evaluator.py` - Self-Evaluation

**Key comments added:**

- **Citation validation**: Why we check for invalid citations (catches hallucinated source numbers)
- **Cited sources only**: Why we only include cited sources in evaluation (reduces tokens, focuses evaluation)
- **Markdown extraction**: Why we strip code fences (LLMs add them despite JSON-only instructions)

### 4. `retry_manager.py` - Retry/Fix Mechanism

**Key comments added:**

- **Strategy selection logic**: Detailed explanation of when to use FIX vs REDO
  - REDO: Fundamental issues (low accuracy/relevance, no sources) - needs fresh search
  - FIX: Minor issues (low coherence/reasonableness) - can improve with same sources
- **Threshold rationale**: Why specific score thresholds trigger different strategies

### 5. `news_tool.py` - News Search

**Key comments added:**

- **Timezone handling**: Why we strip timezone info (avoids comparison issues between aware/naive datetimes)
- **Article limit**: Why 20 articles (balances coverage with token efficiency)

### 6. `traceability.py` - Timing and Traceability

**Key comments added:**

- **Slow operation logging**: Why we log slow operations (helps identify performance bottlenecks)

## Comment Categories

### 1. Performance Optimizations
- Query rewriting skip conditions
- Context truncation limits
- Article count limits
- Token efficiency strategies

### 2. Edge Case Handling
- First turn query rewriting
- Empty message lists
- Failed API calls
- Missing citations

### 3. Data Integrity
- Continuous source numbering
- Citation validation
- Timezone normalization

### 4. LLM Quirks
- Quote stripping
- Markdown fence removal
- JSON extraction

### 5. Design Decisions
- FIX vs REDO strategy selection
- Two-tier compression
- Recent message preservation

## Examples of Good Comments Added

### Before (no comment):
```python
if len(messages) <= 1:
    return user_query
```

### After (explains WHY):
```python
# Skip rewriting on first turn - no prior context exists
if len(messages) <= 1:
    return user_query
```

---

### Before (obvious comment):
```python
# Calculate starting ID BEFORE adding sources (for continuous numbering)
start_id: int = len(tracker.sources) + 1
```

### After (explains the constraint):
```python
# Calculate start_id before adding sources - ensures continuous numbering across tool calls
# Example: first call adds 10 sources (1-10), second call starts at 11
start_id: int = len(tracker.sources) + 1
```

---

### Before (no comment):
```python
if accuracy < 5.0 or relevance < 4.0 or len(sources) == 0:
    return "redo"
return "fix"
```

### After (explains the logic):
```python
# REDO: Major issues requiring fresh search
# - Low accuracy: wrong information, needs better sources
# - Low relevance: answered wrong question, needs better query
# - No sources: search failed, needs to try again
if accuracy < 5.0 or relevance < 4.0 or len(sources) == 0:
    return "redo"

# FIX: Minor issues, existing sources are adequate
# - Low coherence: narrative needs improvement
# - Low reasonableness: analysis needs better logic
return "fix"
```

## Impact

### Maintainability
- Future developers can understand non-obvious design decisions
- Reduces time spent reverse-engineering logic
- Documents constraints that aren't obvious from code

### Debugging
- Comments explain expected behavior in edge cases
- Helps identify when behavior deviates from intent
- Documents performance considerations

### Onboarding
- New contributors can understand rationale faster
- Reduces need for tribal knowledge
- Self-documenting codebase

## What We Didn't Comment

Following best practices, we avoided:
- ❌ Obvious operations (e.g., "create client", "loop through messages")
- ❌ Task references (e.g., "added for issue #123", "fixes bug from yesterday")
- ❌ Redundant docstrings (function signatures already document parameters)
- ❌ Implementation details that are clear from code

## Statistics

- **Files modified**: 6 core files
- **Comments added**: ~25 meaningful comments
- **Focus areas**: Performance, edge cases, design decisions, LLM quirks
- **Average comment length**: 1-2 lines (concise and focused)

## Verification

All comments follow the principle: "If removing the comment wouldn't confuse a future reader, don't write it."

Each comment answers one of these questions:
- Why this approach instead of alternatives?
- What constraint or invariant must be maintained?
- What edge case is being handled?
- What quirk or limitation is being worked around?
