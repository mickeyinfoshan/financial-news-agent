# Agent Performance Evaluation Report

**Run Date**: 2026-05-24 14:23:55
**Test Cases**: 6
**Run Directory**: /Users/mac/code/agent/financial-news-agent-2/.harness/eval/run-20260524-141627

## Overall Statistics

- **Average Overall Score**: 7.21/10
- **Average Accuracy**: 6.83/10
- **Average Relevance**: 7.33/10
- **Average Coherence**: 7.67/10
- **Average Reasonableness**: 7.00/10
- **Total Retries**: 2
- **Retry Rate**: 33.3%
- **Average Duration**: 9611ms (9.6s)
- **Average Sources per Query**: 78.7

## Detailed Results

| ID | Category | Query | Overall | Acc | Rel | Coh | Rea | Sources | Time(s) | Retry |
|----|----------|-------|---------|-----|-----|-----|-----|---------|---------|-------|
| 1 | simple | What's the latest news about Apple? | 8.5 | 8 | 9 | 9 | 8 | 40 | 6.6 |  |
| 2 | simple | What's happening in the semiconductor in... | 8.8 | 8 | 9 | 9 | 9 | 62 | 6.8 | ✓ |
| 3 | complex | Compare Tesla and Rivian's recent develo... | 8.5 | 8 | 9 | 9 | 8 | 80 | 8.1 |  |
| 4 | complex | What are the major trends in AI chip dev... | 1.0 | 1 | 1 | 1 | 1 | 150 | 7.7 | ✓ |
| 5 | edge_case | What's the news about NVDA? | 8.2 | 8 | 8 | 9 | 8 | 60 | 8.9 |  |
| 6 | edge_case | Tell me about Meta's recent announcement... | 8.2 | 8 | 8 | 9 | 8 | 80 | 19.5 |  |

## Performance by Category

### Simple
- **Average Score**: 8.62/10
- **Average Time**: 6.7s
- **Test Cases**: 2

### Complex
- **Average Score**: 4.75/10
- **Average Time**: 7.9s
- **Test Cases**: 2

### Edge Case
- **Average Score**: 8.25/10
- **Average Time**: 14.2s
- **Test Cases**: 2

## Timing Breakdown

- **Total Execution Time**: 57.7s
- **LLM Time**: 57.7s (100.0%)
- **API Time**: 0.0s (0.0%)

## Quality Insights

⚠️ **1 test case(s) scored below 6.0:**
- Test 4: What are the major trends in AI chip development? Which comp... (Score: 1.0)

✓ **5 test case(s) scored 8.0 or above**

## Historical Comparison

- **Previous run average**: 7.04/10
- **Current run average**: 7.21/10
- **Change**: ↑ 0.17 points