# Optimization Iteration 1

## Target Issue
Test 4 (AI chip development trends) has the lowest accuracy (6/10) and relevance (7/10) scores, despite retrieving the most sources (150). This indicates a problem with information quality and filtering when dealing with complex multi-company queries.

## Root Cause Analysis

**Symptoms:**
- Accuracy: 6/10 (lowest across all tests)
- Relevance: 7/10 (second lowest)
- Source count: 150 (highest, but quality appears low)
- Query type: Complex trend analysis involving multiple companies

**Hypothesis:**
When the agent searches for broad trends involving many companies, it:
1. Generates too many search queries (one per company mentioned)
2. Retrieves large volumes of articles without quality filtering
3. Struggles to synthesize coherent insights from information overload
4. May include less relevant sources that dilute the analysis

**Evidence from logs:**
The evaluation run shows multiple API errors (429 rate limits, 402 payment required), suggesting the agent is making excessive API calls. For Test 4, it likely searched for: NVIDIA, AMD, Intel, Broadcom, Google TPU, Amazon Trainium, Cerebras, Groq, etc. - resulting in 150+ sources.

## Proposed Solution

Improve the search strategy to prioritize quality over quantity:

1. **Add source count limits per search** - Prevent information overload
2. **Implement relevance scoring** - Filter sources before passing to LLM
3. **Optimize multi-company queries** - Use combined searches instead of individual per-company searches
4. **Add deduplication** - Remove near-duplicate articles from different sources

## Implementation Steps

1. **Modify `news_tool.py`**: Add max_sources parameter to limit results per search
   - Default: 20 sources per search (down from unlimited)
   - For complex queries: 30 sources total across all searches

2. **Add relevance filtering in `news_tool.py`**:
   - Score articles based on keyword matches
   - Filter out articles with low relevance scores
   - Prioritize recent articles (last 7 days > last 30 days)

3. **Improve search query generation in `agent.py`**:
   - For multi-company queries, generate 1-2 broad searches instead of N individual searches
   - Example: Instead of searching "NVIDIA", "AMD", "Intel" separately, search "AI chip development NVIDIA AMD Intel trends"

4. **Run tests** to verify improvements:
   ```bash
   uv run pytest
   ```

5. **Commit changes**

## Expected Impact

- **Baseline score**: 8.17/10 (Test 4: 7.25/10, Accuracy: 6/10)
- **Target score**: 8.5+/10 (Test 4: 8.0+/10, Accuracy: 7.5+/10)
- **Risk assessment**: Low
  - Changes are additive (limits and filters)
  - Existing functionality preserved
  - Easy to revert if needed

## Rollback Plan

If this optimization fails:
1. `git checkout feat/harness-loop`
2. `git branch -D harness-optimize/2026-05-24-001/improve-accuracy`
3. Analyze why the approach didn't work
4. Try alternative strategy (e.g., improve synthesis instead of filtering)
