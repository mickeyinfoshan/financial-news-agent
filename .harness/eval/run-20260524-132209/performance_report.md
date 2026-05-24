# Agent Performance Evaluation Report

**Run Date**: 2026-05-24 13:27:26
**Test Cases**: 6
**Run Directory**: /Users/mac/code/agent/financial-news-agent-2/.harness/eval/run-20260524-132209

## Overall Statistics

- **Average Overall Score**: 7.00/10
- **Average Accuracy**: 6.33/10
- **Average Relevance**: 7.00/10
- **Average Coherence**: 7.83/10
- **Average Reasonableness**: 6.83/10
- **Total Retries**: 1
- **Retry Rate**: 16.7%
- **Average Duration**: 7516ms (7.5s)
- **Average Sources per Query**: 76.2

## Detailed Results

| ID | Category | Query | Overall | Acc | Rel | Coh | Rea | Sources | Time(s) | Retry |
|----|----------|-------|---------|-----|-----|-----|-----|---------|---------|-------|
| 1 | simple | What's the latest news about Apple? | 8.5 | 8 | 9 | 9 | 8 | 40 | 7.1 |  |
| 2 | simple | What's happening in the semiconductor in... | 1.2 | 1 | 1 | 2 | 1 | 121 | 4.7 | ✓ |
| 3 | complex | Compare Tesla and Rivian's recent develo... | 8.0 | 7 | 8 | 9 | 8 | 60 | 9.1 |  |
| 4 | complex | What are the major trends in AI chip dev... | 8.0 | 7 | 8 | 9 | 8 | 116 | 8.5 |  |
| 5 | edge_case | What's the news about NVDA? | 8.0 | 7 | 8 | 9 | 8 | 60 | 6.7 |  |
| 6 | edge_case | Tell me about Meta's recent announcement... | 8.2 | 8 | 8 | 9 | 8 | 60 | 9.0 |  |

## Performance by Category

### Simple
- **Average Score**: 4.88/10
- **Average Time**: 5.9s
- **Test Cases**: 2

### Complex
- **Average Score**: 8.00/10
- **Average Time**: 8.8s
- **Test Cases**: 2

### Edge Case
- **Average Score**: 8.12/10
- **Average Time**: 7.9s
- **Test Cases**: 2

## Timing Breakdown

- **Total Execution Time**: 45.1s
- **LLM Time**: 45.1s (100.0%)
- **API Time**: 0.0s (0.0%)

## Quality Insights

⚠️ **1 test case(s) scored below 6.0:**
- Test 2: What's happening in the semiconductor industry?... (Score: 1.2)

✓ **5 test case(s) scored 8.0 or above**