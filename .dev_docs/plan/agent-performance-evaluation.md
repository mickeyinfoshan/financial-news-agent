# Agent Performance Evaluation Framework

## Distinction: Self-Evaluation vs Agent Performance Evaluation

### Self-Evaluation (Already Implemented)
- **Scope**: Single response quality check
- **Timing**: Real-time, during response generation
- **Purpose**: Ensure individual response meets quality threshold
- **Metrics**: Accuracy, Relevance, Coherence, Reasonableness (1-10 scale)
- **Action**: Triggers automatic retry/fix for low-quality responses
- **Automation**: Fully automated, LLM-based scoring

### Agent Performance Evaluation (This Document)
- **Scope**: Overall system performance across multiple queries
- **Timing**: Offline, periodic assessment
- **Purpose**: Measure system effectiveness, identify improvement areas
- **Metrics**: Success rate, user satisfaction, cost efficiency, latency
- **Action**: Guides system improvements and optimizations
- **Automation**: Mix of automated metrics and human evaluation

---

## Agent Performance Evaluation Dimensions

### 1. Task Success Metrics

#### 1.1 Query Handling Success Rate
- **Definition**: Percentage of queries that produce acceptable responses
- **Measurement**:
  - Track queries that pass self-evaluation on first attempt
  - Track queries that require retry/fix
  - Track queries that fail after max retries
- **Target**: >90% success rate (pass self-evaluation within retry limit)

#### 1.2 Source Coverage Quality
- **Definition**: How well the agent finds relevant news sources
- **Measurement**:
  - Average number of sources cited per response
  - Percentage of responses with 0 sources (failure case)
  - Source diversity (how many different news providers used)
- **Target**: 
  - Average ≥3 sources per response
  - <5% responses with 0 sources
  - Use all available providers when relevant

#### 1.3 Traceability Completeness
- **Definition**: How well responses link claims to sources
- **Measurement**:
  - Percentage of claims with citations
  - Citation accuracy (cited sources actually support the claim)
  - Audit trail completeness (all tool calls logged)
- **Target**: 
  - ≥80% of factual claims have citations
  - 100% citation accuracy (no hallucinated citations)

### 2. Response Quality Metrics

#### 2.1 Factual Accuracy (Human Evaluation)
- **Definition**: Correctness of information in responses
- **Measurement**:
  - Sample 20-50 responses monthly
  - Human reviewers verify facts against sources
  - Score: Correct / Partially Correct / Incorrect
- **Target**: >95% correct or partially correct

#### 2.2 Storyline Coherence (Human Evaluation)
- **Definition**: Logical flow and narrative quality
- **Measurement**:
  - Human reviewers rate storyline quality (1-5 scale)
  - Check if events are presented in logical order
  - Assess if causal relationships are clear
- **Target**: Average score ≥4.0/5.0

#### 2.3 Future Impact Analysis Quality (Human Evaluation)
- **Definition**: Reasonableness and depth of forward-looking insights
- **Measurement**:
  - Human reviewers assess if analysis is:
    - Grounded in presented evidence
    - Considers multiple scenarios
    - Avoids overconfident predictions
  - Score: Strong / Adequate / Weak
- **Target**: >80% Strong or Adequate

### 3. Efficiency Metrics

#### 3.1 Response Latency
- **Definition**: Time from query to final response
- **Measurement**:
  - Track end-to-end latency per query
  - Break down by: API calls, LLM calls, retry attempts
- **Target**: 
  - P50 latency <15 seconds
  - P95 latency <45 seconds

#### 3.2 Token Cost Efficiency
- **Definition**: Token usage per query
- **Measurement**:
  - Track total tokens (input + output) per query
  - Track cost per query (based on OpenAI pricing)
  - Monitor retry overhead (tokens used in retries)
- **Target**:
  - Average cost <$0.50 per query
  - Retry overhead <30% of total tokens

#### 3.3 API Call Efficiency
- **Definition**: Number of external API calls per query
- **Measurement**:
  - Track news API calls per query
  - Track LLM API calls per query
  - Monitor failed/redundant calls
- **Target**:
  - Average ≤5 news API calls per query
  - Average ≤3 LLM calls per query (including retries)

### 4. Robustness Metrics

#### 4.1 Error Handling
- **Definition**: How well the agent handles edge cases
- **Measurement**:
  - Track queries with API failures
  - Track queries with no news found
  - Track queries with ambiguous company names
  - Measure graceful degradation (partial results vs complete failure)
- **Target**: 
  - <5% complete failures
  - >90% graceful degradation for partial failures

#### 4.2 Retry Effectiveness
- **Definition**: How often retry/fix improves response quality
- **Measurement**:
  - Compare self-evaluation scores before/after retry
  - Track which retry strategy (FIX vs REDO) was used
  - Measure success rate of each strategy
- **Target**:
  - >70% of retries improve overall score by ≥1.0 point
  - FIX strategy success rate >80%
  - REDO strategy success rate >60%

---

## Evaluation Methods

### Automated Evaluation (Continuous)

**Implementation**: Log all queries and responses to structured storage

```python
# Evaluation log schema
{
    "query_id": "uuid",
    "timestamp": "ISO8601",
    "query": "user question",
    "response": "agent response",
    "self_eval_scores": {
        "accuracy": 8.0,
        "relevance": 9.0,
        "coherence": 7.5,
        "reasonableness": 8.0,
        "overall": 8.1
    },
    "sources_count": 5,
    "retry_attempts": 1,
    "retry_strategy": "FIX",
    "latency_seconds": 12.3,
    "tokens_used": 4500,
    "cost_usd": 0.23,
    "api_calls": {
        "newsapi": 1,
        "finnhub": 2,
        "llm": 2
    },
    "success": true
}
```

**Automated Metrics Dashboard**:
- Success rate over time
- Average latency and cost trends
- Source coverage distribution
- Retry rate and effectiveness
- Error rate by category

### Human Evaluation (Periodic)

**Frequency**: Monthly or bi-weekly

**Sample Selection**:
- Random sample of 20-50 queries
- Stratified by: success/failure, retry/no-retry, query type
- Include edge cases and failures

**Evaluation Protocol**:
1. **Factual Accuracy Check**:
   - Reviewer reads response and cited sources
   - Verifies each factual claim against sources
   - Flags hallucinations or misinterpretations

2. **Storyline Quality Assessment**:
   - Rate logical flow (1-5)
   - Check temporal ordering
   - Assess causal reasoning

3. **Impact Analysis Quality**:
   - Rate depth and reasonableness (Strong/Adequate/Weak)
   - Check if grounded in evidence
   - Assess balance (not overconfident)

4. **Traceability Audit**:
   - Verify all citations are valid
   - Check if major claims have citations
   - Review audit trail completeness

**Output**: Human evaluation report with scores and improvement recommendations

### Benchmark Evaluation (Quarterly)

**Purpose**: Compare against baseline and track improvement

**Benchmark Dataset**:
- Curate 50-100 representative queries covering:
  - Company-specific questions (e.g., "What's happening with Tesla?")
  - Industry questions (e.g., "What's the outlook for semiconductor industry?")
  - Event-driven questions (e.g., "Why did bank stocks drop today?")
  - Ambiguous queries (e.g., "Tell me about Apple" - fruit or company?)

**Evaluation Process**:
1. Run all benchmark queries through current system
2. Collect automated metrics
3. Human evaluation on all responses
4. Compare against previous benchmark results
5. Identify regressions and improvements

**Baseline**: Establish baseline scores in first benchmark run

---

## Evaluation Implementation Plan

### Phase 1: Logging Infrastructure (Week 1)
- [ ] Add structured logging to agent.py
- [ ] Log all queries, responses, and metadata
- [ ] Store logs in JSON format (file or database)
- [ ] Include self-evaluation scores and performance metrics

### Phase 2: Automated Metrics (Week 2)
- [ ] Build metrics aggregation script
- [ ] Calculate success rate, latency, cost, source coverage
- [ ] Generate automated metrics report
- [ ] Set up periodic reporting (daily/weekly)

### Phase 3: Human Evaluation Process (Week 3)
- [ ] Create evaluation guidelines document
- [ ] Build sample selection tool
- [ ] Design evaluation form/spreadsheet
- [ ] Conduct first human evaluation round

### Phase 4: Benchmark Dataset (Week 4)
- [ ] Curate 50-100 benchmark queries
- [ ] Document expected characteristics for each query
- [ ] Run baseline benchmark evaluation
- [ ] Establish target scores for each metric

### Phase 5: Continuous Improvement (Ongoing)
- [ ] Monthly human evaluation
- [ ] Quarterly benchmark evaluation
- [ ] Track metrics trends over time
- [ ] Use insights to guide system improvements

---

## Success Criteria

The agent system is performing well when:

1. **High Success Rate**: >90% of queries produce acceptable responses
2. **Good Source Coverage**: Average ≥3 sources per response, <5% with 0 sources
3. **High Accuracy**: >95% factual accuracy in human evaluation
4. **Efficient**: P50 latency <15s, average cost <$0.50 per query
5. **Robust**: <5% complete failures, >90% graceful degradation
6. **Effective Retry**: >70% of retries improve quality by ≥1.0 point

---

## Key Differences Summary

| Aspect | Self-Evaluation | Agent Performance Evaluation |
|--------|----------------|------------------------------|
| **When** | Real-time, per response | Offline, periodic |
| **What** | Single response quality | System-wide performance |
| **Who** | Automated (LLM) | Automated + Human |
| **Purpose** | Quality gate | System improvement |
| **Metrics** | 4 dimensions (1-10 scale) | 15+ metrics across 4 categories |
| **Action** | Trigger retry/fix | Guide development priorities |
| **Scope** | Response-level | System-level |
