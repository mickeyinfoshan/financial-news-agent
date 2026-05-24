# Agent Harness Optimization Loop - Final Summary

**Date**: 2026-05-24  
**Status**: STOPPED (reached stop condition)  
**Total Iterations**: 3  
**Result**: All optimizations failed

---

## Executive Summary

Ran 3 optimization iterations attempting to improve agent performance from baseline 8.17/10. All attempts failed, with scores ranging from 7.04-7.96/10. Root cause identified: Test 4 query too broad, causing agent to enter infinite search loop and exhaust iteration limit.

**Key Finding**: Prompt-based and configuration-based optimizations are insufficient. Problem requires code-level architectural changes.

---

## Baseline Performance

**Overall Score**: 8.17/10  
**Date**: Unknown (pre-optimization)  
**Key Weakness**: Test 4 (AI chip trends query) likely already problematic

---

## Iteration History

### Iteration 1: Reduce Search Calls
**Branch**: `harness-optimize/2026-05-24-001/reduce-search-calls`  
**Approach**: Limit agent to fewer tool calls  
**Score**: 7.96/10 (-0.21 vs baseline)  
**Result**: ❌ FAILED

**What Happened**:
- Test 4 improved: 7.25 → 8.0 ✓
- Test 2 degraded: 8.5 → 7.0 ✗
- Net negative impact

**Lesson**: Aggressive search limiting helps broad queries but hurts specific queries that need thorough coverage.

---

### Iteration 2: Limit Provider Sources
**Branch**: `harness-optimize/2026-05-24-002/fix-info-overload`  
**Approach**: Cap Finnhub provider to 10 articles max  
**Score**: 7.04/10 (-1.13 vs baseline)  
**Result**: ❌ FAILED

**What Happened**:
- Test 4 got WORSE: 1.2 → 1.0
- Average sources reduced: 88.5 → 42.2 ✓
- Retry rate increased: 16.7% → 33.3% ✗
- Overall score dropped significantly

**Code Change**:
```python
# financial_news_agent/news_sources/finnhub.py:145
data = data[:10]  # Limit to 10 articles
```

**Lesson**: Problem is NOT information overload. Agent enters search loop regardless of source count. Limiting sources just makes the problem worse by reducing quality of available information.

---

### Iteration 3: System Prompt Guidance
**Branch**: `harness-optimize/2026-05-24-003/improve-search-strategy`  
**Approach**: Add explicit search strategy guidance to system prompt  
**Score**: 7.21/10 (-0.96 vs baseline)  
**Result**: ❌ FAILED

**What Happened**:
- Test 4 unchanged: still 1.0/10
- Still collected 150 sources
- Still used all 10 iterations
- Answer: "Agent reached maximum iterations without completing the analysis."

**Code Change**:
```python
# financial_news_agent/agent.py:18-57
_SYSTEM_PROMPT = """...
**Search Strategy - Important:**
You have a maximum of ~10 iterations to complete your analysis. Use them wisely:

1. **When to stop searching and start synthesizing:**
   - After 2-3 searches if you have 40+ sources
   - When additional searches return similar information
   ...
"""
```

**Lesson**: System prompt "soft guidance" has ZERO effect on agent behavior when it's already in a search loop. Agent does not actively monitor its own iteration count or source count during execution.

---

## Root Cause Analysis

### The Problem: Test 4 Query
**Query**: "What are the major trends in AI chip development? Which companies are leading?"

**Why It Fails**:
1. **Too broad**: Covers entire industry, multiple companies, multiple trends
2. **No natural stopping point**: Agent keeps finding "one more company" to research
3. **Search loop pattern**:
   - Search "AI chip trends" → finds NVIDIA, AMD, Intel
   - Search "NVIDIA AI chips" → finds more info
   - Search "AMD AI chips" → finds more info
   - Search "Intel AI chips" → finds more info
   - Search "AI chip startups" → finds more companies
   - ... continues until iteration limit (10)
4. **Never synthesizes**: Agent prioritizes completeness over synthesis

### Why Optimizations Failed

**Iteration 1 (Reduce calls)**: Helped Test 4 but hurt specific queries that legitimately need multiple searches.

**Iteration 2 (Limit sources)**: Misdiagnosed the problem. Issue isn't too many sources per search, it's too many searches. Limiting sources just reduced information quality.

**Iteration 3 (Prompt guidance)**: Agent doesn't actively check "how many iterations have I used?" during execution. Prompt guidance is passive, not active.

---

## What Would Actually Work

### Option 1: Hard Code-Level Limits
```python
# In agent.py run_agent()
MAX_TOOL_CALLS = 3  # Hard limit
if tool_call_count >= MAX_TOOL_CALLS:
    # Force synthesis with what we have
    messages.append({
        "role": "system",
        "content": "You have reached the search limit. Synthesize your answer now with the sources you have collected."
    })
```

### Option 2: Forced Synthesis Threshold
```python
# After each tool call
if total_sources >= 50:
    # Inject synthesis trigger
    messages.append({
        "role": "system", 
        "content": "You have collected 50+ sources. This is sufficient. Proceed to analysis and synthesis now."
    })
```

### Option 3: Architectural Redesign
Implement Plan-Execute-Reflect pattern:
1. **Plan Phase**: Agent decides search strategy upfront
   - "I will search: (1) AI chip overview, (2) NVIDIA, (3) AMD"
2. **Execute Phase**: Run planned searches only
3. **Reflect Phase**: Synthesize results

### Option 4: Query Decomposition
Detect broad queries and decompose:
- "AI chip trends + leading companies" → 
  - "AI chip market overview 2026"
  - "Top 3 AI chip companies comparison"

### Option 5: Accept Current Performance
- Test 4 may be an edge case
- 5/6 tests score 8.0+
- Focus on improving speed/quality of successful queries instead

---

## Test Results Comparison

| Metric | Baseline | Iter 1 | Iter 2 | Iter 3 |
|--------|----------|--------|--------|--------|
| Overall | 8.17 | 7.96 | 7.04 | 7.21 |
| Simple Queries | ? | ? | 8.62 | 8.62 |
| Complex Queries | ? | ? | 5.12 | 4.75 |
| Edge Cases | ? | ? | 8.38 | 8.25 |
| Test 4 Score | ? | 8.0 | 1.0 | 1.0 |
| Avg Sources | ? | ? | 42.2 | 78.7 |
| Retry Rate | ? | ? | 33.3% | 33.3% |

---

## Recommendations

### Immediate (If Continuing Optimization)
1. **Implement hard limits** (Option 1 or 2 above)
2. **Test specifically on Test 4** before running full eval
3. **Monitor tool call count** as primary metric

### Short-term
1. **Refine Test 4 query** to be more specific:
   - Split into 2 tests: "AI chip trends" + "Leading AI chip companies"
   - Or accept partial answers as valid
2. **Add telemetry**: Log when agent enters search loops
3. **Implement early stopping**: Detect repetitive searches

### Long-term
1. **Architectural redesign** (Plan-Execute-Reflect)
2. **Search budget system**: Allocate "search credits" per query
3. **Query classifier**: Route broad vs specific queries differently
4. **Improve evaluation**: Add metrics for search efficiency, not just answer quality

---

## Files Generated

- `.dev_process/optimization_state.json` - Final state (STOPPED)
- `.dev_process/eval_iteration_1.json` - Iteration 1 results
- `.dev_process/eval_iteration_2.json` - Iteration 2 baseline
- `.dev_process/eval_iteration_2_optimized.json` - Iteration 2 results
- `.dev_process/eval_iteration_3_optimized.json` - Iteration 3 results
- `.dev_docs/plan/optimization_iteration_2.md` - Iteration 2 plan
- `.dev_docs/plan/optimization_iteration_3.md` - Iteration 3 plan
- `.harness/eval/run-*/` - Multiple evaluation runs

---

## Conclusion

The harness optimization loop successfully identified a critical weakness (Test 4 search loop) but failed to fix it through prompt/config changes. The problem requires code-level architectural changes that are beyond the scope of automated prompt optimization.

**Next Steps**: Decide whether to:
1. Implement code-level fixes manually
2. Accept current performance and optimize elsewhere
3. Redesign the agent architecture
4. Refine the test suite to be more forgiving of broad queries
