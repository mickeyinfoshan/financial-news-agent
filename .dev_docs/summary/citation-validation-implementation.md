# Citation Validation System - Implementation Summary

**Date:** 2026-05-26  
**Status:** ✅ Completed and Fully Integrated

## Overview

Implemented a comprehensive 5-stage citation validation pipeline that validates the quality of citations in agent responses. The system extracts claims with their citations, validates them programmatically and with LLM, and stores detailed results accessible through AgentResult, API responses, and session storage.

## What Was Implemented

### 1. Core Validation Pipeline (citation_validator.py)

New module implementing 5-stage validation:

#### Stage 1: LLM Extraction
- Extracts claims with citations using fresh LLM context
- Uses structured prompt with concrete examples
- Returns list of ClaimData with claim text and citation numbers

**Prompt Features:**
- Clear JSON schema with examples
- Demonstrates handling of multiple citations per claim
- Shows how to skip sentences without citations
- Clarifies that claim text should not include citation markers

#### Stage 2: Programmatic Validation
- Validates extraction accuracy:
  - Claims exist in original answer (after removing citation markers)
  - Citations exist in original answer
- Uses regex to remove `[1]`, `[2]` markers before matching
- Returns validation status and error list

#### Stage 3: Range Validation
- Checks citations are within valid source range (1 to N)
- Populates `invalid_citations` field for each claim
- Simple programmatic check

#### Stage 4: LLM Claim-Source Validation
- Validates claim-source relationships using LLM
- **Key design**: Pairs each claim with its cited source texts (1-to-N structure)
- Prompt includes full source content for each claim
- Returns supported status, confidence level, and explanation
- Batch validation (one LLM call for all claims)

**Confidence Levels:**
- **"high"**: Claim directly stated in sources (word-for-word or clear equivalence)
- **"medium"**: Reasonable inference well-supported by sources
- **"low"**: Weak support, significant inference required, or tangential relation

#### Stage 5: Orchestration
- Coordinates all stages with retry logic (max 3 attempts)
- Handles extraction failures gracefully
- Builds final CitationValidationResult
- Determines overall validation_passed status

### 2. Data Structures (types.py)

Added 3 new TypedDict definitions:

**ClaimData**: Represents a single claim with citations and validation status
```python
{
    "claim": str,                    # Claim text (without citation markers)
    "citations": list[int],          # Citation numbers [1, 2, 3]
    "invalid_citations": list[int],  # Citations out of valid range
    "validation_result": {           # LLM validation (optional)
        "supported": bool,
        "confidence": str,
        "explanation": str
    }
}
```

**CitationValidationResult**: Complete validation output
```python
{
    "claims": list[ClaimData],
    "extraction_attempts": int,
    "total_invalid_citations": int,
    "validation_passed": bool
}
```

**Updated AgentResult**: Added citation_validation as top-level field
```python
{
    "answer": str,
    "sources": list[SourceData],
    "evaluation": EvaluationResult,
    "trace": TraceData,
    "citation_validation": CitationValidationResult  # NEW
}
```

**Updated MessageDict**: Added citation_validation for session storage
```python
{
    "role": str,
    "content": str,
    "sources": list[SourceData],
    "evaluation": EvaluationResult,
    "citation_validation": CitationValidationResult  # NEW
}
```

### 3. Integration Points

#### Agent Integration (agent/shared.py)
- Integrated into `build_final_result()` function
- Runs after query rewriting, before evaluation
- Calls `validate_citations()` with answer, sources, and client
- Stores results directly in AgentResult (top-level field)
- Logs validation statistics
- Graceful error handling (continues if validation fails)

#### API Integration (api/models.py + api/routes.py)
- Added `citation_validation` field to response models:
  - `CreateSessionWithResultResponse`
  - `QueryResponse`
- Updated route handlers to include validation in responses
- Results exposed through REST API

#### Session Storage (api/session_manager.py)
- Updated `update_session()` to embed citation_validation
- Stored in assistant messages alongside other metadata
- Persisted across session lifecycle
- Available when retrieving conversation history

## Key Design Decisions

### 1. Storage Location
**Decision**: Store at AgentResult top level (not in trace)

**Rationale**:
- Easier access: `result["citation_validation"]` vs `result["trace"]["citation_validation"]`
- Aligns with other top-level fields like `evaluation` and `retry_history`
- Makes validation results first-class citizens

### 2. Prompt Structure for Stage 4
Claims and sources are paired in the prompt:
```
CLAIM 1:
"Apple's revenue increased 15%"

CITED SOURCES:
[1] Apple Reports Record Q1 Results
Source: Reuters | Date: 2024-01-15
Content: Apple Inc. reported a 15% increase...

[2] Tech Giants Post Strong Earnings
Source: Bloomberg | Date: 2024-01-16
Content: Major technology companies...
```

This 1-to-N structure allows LLM to directly see which sources support each claim.

### 3. Validation Logic
**Claim Matching**: Remove all citation markers `[1]`, `[2]` from answer before checking if claim exists
- Handles cases where citations appear in middle of sentences
- Example: "Apple's revenue [1] increased 15%" → "Apple's revenue  increased 15%"
- Claim "Apple's revenue increased 15%" matches correctly

**Citation Checking**: Verify citation markers exist in original answer
- Simple string search for `[1]`, `[2]`, etc.
- No position requirements (citations can be anywhere)

### 4. Error Handling
- Extraction failures: Retry up to 3 times, fallback to empty claims list
- Validation failures: Log error, continue without validation results
- LLM errors: Graceful degradation, don't block agent execution

### 5. Code Quality
- Extracted JSON parsing to `parse_json_response()` utility function
- Removed redundant retry logic (single retry loop in orchestrator)
- Moved all imports to module level
- Simplified validation logic (removed unnecessary `extract_citations` calls)

## Files Modified

1. **financial_news_agent/types.py** - Added 3 TypedDicts, updated AgentResult and MessageDict
2. **financial_news_agent/citation_validator.py** - NEW FILE (~350 lines)
3. **financial_news_agent/agent/shared.py** - Integrated validation call
4. **financial_news_agent/api/models.py** - Added citation_validation to response models
5. **financial_news_agent/api/routes.py** - Updated route handlers
6. **financial_news_agent/api/session_manager.py** - Added session storage support
7. **.dev_process/test_citation_validator.py** - Unit tests
8. **.dev_process/test_citation_e2e.py** - End-to-end test

## Access Patterns

### Backend (Python)
```python
from financial_news_agent import run_agent

result = run_agent(query="What's the latest news about Apple?")

# Access validation results
validation = result["citation_validation"]
print(f"Claims: {len(validation['claims'])}")
print(f"Validation passed: {validation['validation_passed']}")

# Access individual claims
for claim in validation["claims"]:
    print(f"Claim: {claim['claim']}")
    print(f"Citations: {claim['citations']}")
    print(f"Invalid: {claim['invalid_citations']}")
    if "validation_result" in claim:
        print(f"Supported: {claim['validation_result']['supported']}")
```

### API (REST)
```bash
# Query endpoint
curl -X POST http://localhost:8000/api/session/{session_id}/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the latest news about Apple?"}'

# Response includes citation_validation
{
  "answer": "...",
  "sources": [...],
  "evaluation": {...},
  "citation_validation": {
    "claims": [...],
    "extraction_attempts": 1,
    "total_invalid_citations": 0,
    "validation_passed": true
  }
}
```

### Session History
```python
# Retrieve session
session = session_manager.get_session(session_id)

# Access validation from message history
for message in session["messages"]:
    if message["role"] == "assistant" and "citation_validation" in message:
        validation = message["citation_validation"]
        # Process validation data
```

## Testing

### Unit Tests
- ✅ Citation extraction from text
- ✅ Extraction validation (valid cases)
- ✅ Hallucination detection
- ✅ Citation range validation

### End-to-End Test
- ✅ Full pipeline with real LLM calls
- ✅ 4 claims extracted correctly
- ✅ Invalid citation [4] detected (out of range)
- ✅ All valid claims validated with confidence levels
- ✅ Results stored in proper structure

### Type Checking
- ✅ mypy passes with no errors
- ✅ All TypedDict definitions correct
- ✅ Proper handling of Optional types

## Token Usage

Per validation run:
- **Extraction**: ~500 tokens (answer + prompt + response)
- **Claim-source validation**: ~1000 tokens (claims + sources + response)
- **Total**: ~1500 tokens (~10-20% increase)
- **With retry**: +500 tokens per extraction retry attempt (max 3 attempts)

## Performance Impact

- **Latency**: +1-2 seconds for LLM calls (extraction + validation)
- **Token cost**: ~1500 tokens per validation
- **Success rate**: High (extraction succeeds on first attempt in most cases)

## Example Output

```json
{
  "claims": [
    {
      "claim": "Apple's revenue increased 15% in Q1 2024",
      "citations": [1],
      "invalid_citations": [],
      "validation_result": {
        "supported": true,
        "confidence": "high",
        "explanation": "Source [1] directly states this fact"
      }
    },
    {
      "claim": "The company reported strong iPhone sales",
      "citations": [1, 2],
      "invalid_citations": [],
      "validation_result": {
        "supported": true,
        "confidence": "high",
        "explanation": "Both sources confirm strong iPhone sales"
      }
    },
    {
      "claim": "The tech sector shows resilience",
      "citations": [4],
      "invalid_citations": [4]
    }
  ],
  "extraction_attempts": 1,
  "total_invalid_citations": 1,
  "validation_passed": false
}
```

## Commit History

1. **e5413bd** - feat: implement citation validation system
2. **5ea22f1** - chore: remove unused imports in citation_validator
3. **ac32123** - refactor: move re import to module level
4. **e118fd1** - improve: add examples to extraction prompt
5. **3621c39** - refactor: move citation_validation to AgentResult top level
6. **d6d207d** - feat: add citation_validation to API response models
7. **d3af60f** - feat: add citation_validation to session storage

## Success Criteria

✅ Citation validation pipeline executes successfully  
✅ Claims extracted with correct citations  
✅ Invalid citations detected and recorded  
✅ Claim-source relationships validated  
✅ Validation results stored in AgentResult (top-level)  
✅ Results exposed through API  
✅ Results persisted in session storage  
✅ All tests pass  
✅ Token usage increase < 25%  
✅ Latency increase < 3 seconds  
✅ Type checking passes  
✅ Code quality optimized (no redundant logic, clean imports)

## Conclusion

The citation validation system is fully implemented, optimized, and integrated across the entire stack (core → agent → API → session storage). It provides comprehensive validation of citation quality, detecting invalid citations, hallucinated claims, and unsupported claims. All validation results are easily accessible through multiple access patterns and persisted for future reference.
