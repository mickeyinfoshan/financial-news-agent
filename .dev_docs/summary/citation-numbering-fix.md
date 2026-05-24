# Source Citation Numbering Fix - Summary

## Problem

The agent was generating citations that didn't match the provided source list. When making multiple tool calls in a single session, each compressed tool result restarted numbering from 1, causing citation ambiguity.

**Example of the bug:**
- Tool call 1: Returns 3 articles → sent to LLM as IDs [1, 2, 3]
- Tool call 2: Returns 2 articles → sent to LLM as IDs [1, 2] ❌ (should be [4, 5])
- When LLM cited [1], it was ambiguous - could mean article 1 from first call OR article 1 from second call

## Root Cause

In `context_manager.py`, the `compress_tool_result()` function always started numbering from 1:
```python
for idx, article in enumerate(articles, 1):  # Always starts at 1
```

## Solution

### 1. Added `start_id` parameter to `compress_tool_result()`
**File:** `financial_news_agent/context_manager.py`

```python
def compress_tool_result(articles: list, aggressive: bool = False, start_id: int = 1) -> list:
    for idx, article in enumerate(articles, start_id):  # Now uses start_id
        compressed.append({"id": idx, ...})
```

### 2. Calculate correct `start_id` in agent loop
**File:** `financial_news_agent/agent.py`

In both `run_agent()` and `run_agent_stream()`:
```python
# Calculate starting ID BEFORE adding sources
start_id = len(tracker.sources) + 1

# Add sources to tracker
for article in result:
    tracker.add_source({...})

# Compress with correct offset
compressed_articles = compress_tool_result(result, aggressive=aggressive, start_id=start_id)
```

### 3. Enhanced system prompt with explicit prohibitions
Made it explicit that IDs are cumulative across tool calls AND added strict rules:

**Added "CRITICAL - Source Citations Rules" section with:**

YOU MUST:
- ONLY cite sources that were returned by the search_financial_news tool
- Use the exact IDs provided in the tool response: [1], [2], [3], etc.
- Base ALL claims strictly on the retrieved articles

YOU MUST NEVER:
- Cite sources from your training data or general knowledge
- Invent or hallucinate article titles, sources, or citations
- Reference articles that were not returned by the tool
- Create your own source list or numbering

This prevents the LLM from generating its own sources or citing from training data.

### 4. Added citation validation
**File:** `financial_news_agent/evaluator.py`

```python
invalid_citations = [idx for idx in cited_indices if idx < 1 or idx > len(tracker.sources)]
if invalid_citations:
    logger.warning(f"Invalid citations detected: {invalid_citations}")
```

## Verification

### Test Results
✅ All 15 context/citation tests passed
✅ Custom test verified continuous numbering across multiple tool calls
✅ No regressions in existing functionality

### Example Output (After Fix)
```
[Tool Call 1] Searching for 'Tesla news'...
  Sent to LLM with IDs: [1, 2, 3]

[Tool Call 2] Searching for 'BYD competitor news'...
  Sent to LLM with IDs: [4, 5]  ✅ Correct!

Total sources: 5
IDs sent to LLM: [1, 2, 3, 4, 5]  ✅ No duplicates, continuous numbering
```

## Impact

**Before:**
- Citation ambiguity when multiple tool calls were made
- LLM could cite wrong sources or hallucinate sources
- Evaluator correctly detected mismatches but couldn't prevent them

**After:**
- Each citation [N] maps to exactly one source
- No ambiguity across multiple tool calls
- LLM receives clear, continuous numbering
- Evaluator can validate citations accurately

## Files Modified

1. `financial_news_agent/context_manager.py` - Added `start_id` parameter
2. `financial_news_agent/agent.py` - Pass correct `start_id` in both sync and async functions
3. `financial_news_agent/evaluator.py` - Added citation validation
4. `.dev_process/test_citation_fix.py` - Comprehensive test for the fix

## Date
2026-05-24
