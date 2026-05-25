# Citation Validation System - Implementation Summary

**Date:** 2026-05-26  
**Status:** ✅ Completed

## Overview

Implemented a comprehensive 5-stage citation validation pipeline that validates the quality of citations in agent responses. The system extracts claims with their citations, validates them programmatically and with LLM, and stores detailed results in the trace.

## What Was Implemented

### 1. New Data Structures (types.py)

Added 3 new TypedDict definitions:

- **ClaimData**: Represents a single claim with citations and validation status
  - `claim`: The claim text
  - `citations`: List of citation numbers [1, 2, 3]
  - `invalid_citations`: Citations out of valid range
  - `validation_result`: LLM validation result (optional)

- **ClaimSourceValidation**: LLM validation result for claim-source relationship
  - `supported`: Whether sources support the claim
  - `confidence`: "high" (directly stated), "medium" (inference), "low" (weak)
  - `explanation`: Brief explanation

- **CitationValidationResult**: Complete validation output
  - `claims`: All claims with validation
  - `extraction_attempts`: Number of extraction retries
  - `total_invalid_citations`: Count of out-of-range citations
  - `validation_passed`: Overall validation status

Updated `TraceData` to include `citation_validation` field.

### 2. Citation Validator Module (citation_validator.py)

New module implementing 5-stage validation pipeline:

#### Stage 1: LLM Extraction
- Extracts claims with citations using fresh LLM context
- Uses structured prompt with clear JSON format
- Returns list of ClaimData with claim text and citation numbers

#### Stage 2: Programmatic Validation
- Validates extraction accuracy:
  - Claims exist in original answer (no hallucination)
  - Citations exist in original answer
  - Citation positions match claim positions (within 200 chars)
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

#### Stage 5: Orchestration
- Coordinates all stages
- Handles extraction retry (max 3 attempts)
- Builds final CitationValidationResult
- Determines overall validation_passed status

### 3. Integration (agent/shared.py)

Integrated validation into `build_final_result()`:
- Runs after query rewriting, before evaluation
- Calls `validate_citations()` with answer, sources, and client
- Stores results in trace
- Logs validation statistics
- Graceful error handling (continues if validation fails)

## Key Design Decisions

### 1. Confidence Levels
- **"high"**: Claim directly stated in sources (word-for-word or clear equivalence)
- **"medium"**: Reasonable inference well-supported by sources
- **"low"**: Weak support, significant inference required, or tangential relation

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

### 3. Validation Status Logic
`validation_passed = False` if:
- Any claim has invalid citations (out of range)
- Any claim has `supported=False` with confidence "high" or "medium"

### 4. Error Handling
- Extraction failures: Retry up to 3 times, fallback to empty claims list
- Validation failures: Log error, continue without validation results
- LLM errors: Graceful degradation, don't block agent execution

## Testing

### Unit Tests (.dev_process/test_citation_validator.py)
- ✅ Citation extraction from text
- ✅ Extraction validation (valid cases)
- ✅ Hallucination detection
- ✅ Citation range validation

### End-to-End Test (.dev_process/test_citation_e2e.py)
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
- **With retry**: +500 tokens per extraction retry attempt

## Files Modified

1. `financial_news_agent/types.py` - Added 3 TypedDicts, updated TraceData
2. `financial_news_agent/citation_validator.py` - NEW FILE (~350 lines)
3. `financial_news_agent/agent/shared.py` - Integrated validation call
4. `.dev_process/test_citation_validator.py` - Unit tests
5. `.dev_process/test_citation_e2e.py` - End-to-end test

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

## Future Enhancements (Not in This Phase)

- Integration with retry mechanism (trigger retry based on validation results)
- Frontend display of validation results
- Configurable validation thresholds
- Performance optimization for large answers

## Success Criteria

✅ Citation validation pipeline executes successfully  
✅ Claims extracted with correct citations  
✅ Invalid citations detected and recorded  
✅ Claim-source relationships validated  
✅ Validation results stored in trace  
✅ All tests pass  
✅ Token usage increase < 25%  
✅ Type checking passes

## Conclusion

The citation validation system is fully implemented and tested. It provides comprehensive validation of citation quality, detecting invalid citations, hallucinated claims, and unsupported claims. All validation results are stored in the trace for transparency and debugging.
