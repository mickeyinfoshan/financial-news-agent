---
name: agent-performance-evaluation
description: Measure and benchmark the financial news agent's performance across multiple test queries. Use this skill when the user wants to test the agent, measure performance, run benchmarks, evaluate quality, check agent metrics, or assess how well the agent is working. Also trigger when they mention evaluation scores, response quality, timing analysis, or want to compare performance over time.
---

# Agent Performance Evaluation

This skill runs a comprehensive performance evaluation of the financial news agent by executing a predefined test suite and generating a detailed performance report.

## What This Skill Does

1. **Runs Test Queries**: Executes 6 curated test queries covering different scenarios (simple lookups, complex analysis, edge cases)
2. **Collects Metrics**: Gathers evaluation scores, timing data, token usage, retry rates, and source counts
3. **Tracks History**: Saves results with timestamps for comparison against previous runs
4. **Generates Report**: Automatically creates a markdown report with tables, statistics, and insights

## When to Use This Skill

Use this skill when the user wants to:
- Test the agent's performance
- Measure response quality
- Benchmark the system
- Check if recent changes improved or degraded performance
- Understand timing and cost characteristics
- Validate the agent is working correctly

## Test Suite

The skill includes a predefined test suite with queries covering:

### Simple Queries (baseline performance)
- Recent news about a major company (e.g., "What's the latest news about Apple?")
- Industry overview (e.g., "What's happening in the semiconductor industry?")

### Complex Queries (multi-step reasoning)
- Comparative analysis (e.g., "Compare Tesla and Rivian's recent developments")
- Trend analysis (e.g., "What are the major trends in AI chip development?")

### Edge Cases (robustness testing)
- Ambiguous company names (e.g., "What's the news about Meta?" - could be Meta Platforms or metaphorical)
- Queries requiring ticker resolution (e.g., "News about NVDA")
- Time-sensitive queries (e.g., "Breaking news about tech stocks today")

## Execution Workflow

Simply run the evaluation script - it handles everything automatically:

```bash
cd /Users/mac/code/agent/financial-news-agent-2
uv run python ~/.claude/skills/agent-performance-evaluation/scripts/run_evaluation.py
```

This script will:
- Create a timestamped directory in `.harness/eval/run-YYYYMMDD-HHMMSS/`
- Run all 6 test queries with fresh conversations
- Collect all metrics (evaluation scores, timing, sources, retries)
- Save raw results to `results.json` and `test_queries.json`
- **Automatically generate the performance report** as `performance_report.md`
- Display progress and final summary

## Output

The skill produces three files in `.harness/eval/run-YYYYMMDD-HHMMSS/`:

1. **`results.json`**: Raw metrics for all test cases
2. **`test_queries.json`**: The test queries that were executed
3. **`performance_report.md`**: Human-readable report with:
   - Overall statistics (average scores, retry rate, timing)
   - Detailed results table for each test
   - Performance breakdown by category
   - Timing analysis (LLM vs API time)
   - Quality insights (low scores, high performers)
   - Historical comparison (if previous runs exist)

## Tips for Effective Evaluation

- **Run regularly**: Establish a baseline, then run after significant changes
- **Track trends**: Compare multiple runs to identify improvements or regressions
- **Investigate failures**: When scores drop, examine the full results to understand why
- **Consider context**: Simple queries should be fast with high scores; complex queries may take longer but should still score well

## Troubleshooting

**Import errors**: Ensure the financial news agent is installed and the path in the script is correct

**API rate limits**: If tests fail due to rate limits, add delays between queries or reduce the test suite size

**Missing timing data**: Older agent versions may not include timing information; focus on evaluation scores instead

**Inconsistent results**: Run the test suite multiple times to account for API variability and LLM non-determinism
