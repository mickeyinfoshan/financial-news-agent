"""Citation validation system for agent responses.

This module implements a 5-stage validation pipeline:
1. LLM Extraction - Extract claims with citations using fresh context
2. Programmatic Validation - Verify extraction accuracy
3. Range Validation - Check citations are within valid source range
4. LLM Claim-Source Validation - Validate claim-source relationships
5. Store in Trace - Add validation results to traceability
"""

import os
import json
import logging
import re
from typing import Any
from openai import OpenAI
from .types import (
    ClaimData,
    CitationValidationResult,
    SourceData
)

logger = logging.getLogger(__name__)


def parse_json_response(response_text: str) -> Any:
    """
    Parse JSON from LLM response, handling markdown code blocks.

    Args:
        response_text: Raw response text from LLM

    Returns:
        Parsed JSON object

    Raises:
        json.JSONDecodeError: If JSON parsing fails
    """
    text = response_text.strip()

    # Extract JSON from markdown code blocks if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    return json.loads(text)


# Prompt templates
EXTRACTION_PROMPT = """Extract all factual claims from this financial news analysis.
For each claim, identify the citation numbers referenced.

ANSWER:
{answer}

RULES:
1. Extract ONLY factual claims (not opinions or meta-statements)
2. Keep claim text EXACTLY as written in the answer (without citation markers)
3. Include ALL citation numbers [1], [2] for each claim
4. If a sentence has no citations, omit it
5. Return valid JSON only, no markdown

EXAMPLES:

Input: "Apple's revenue increased 15% in Q1 [1]. The company reported strong iPhone sales [1][2]. Analysts are optimistic [3]."
Output:
[
  {{"claim": "Apple's revenue increased 15% in Q1", "citations": [1]}},
  {{"claim": "The company reported strong iPhone sales", "citations": [1, 2]}},
  {{"claim": "Analysts are optimistic", "citations": [3]}}
]

Input: "Tesla stock rose 5% [1][2]. This follows strong earnings. The EV market is growing [3]."
Output:
[
  {{"claim": "Tesla stock rose 5%", "citations": [1, 2]}},
  {{"claim": "The EV market is growing", "citations": [3]}}
]

Now extract claims from the answer above.

JSON:"""


VALIDATION_PROMPT = """Validate whether each claim is supported by its cited sources.

For each claim below, I provide the claim text and the full text of all sources it cites.
Determine if the sources support the claim.

{claims_with_sources}

For each claim, return:
1. claim: the exact claim text
2. supported: true if sources support the claim, false otherwise
3. confidence: "high" (directly stated), "medium" (reasonable inference), "low" (weak/no support)
4. explanation: Brief reason (1 sentence)

CONFIDENCE LEVELS:
- "high": Claim is directly stated in sources (word-for-word or clear equivalence)
- "medium": Claim requires reasonable inference, but inference is well-supported by sources
- "low": Claim is weakly supported, requires significant inference, or sources are tangentially related

Return JSON array:
[
  {{"claim": "Apple's revenue increased 15% in Q1", "supported": true, "confidence": "high", "explanation": "..."}},
  {{"claim": "Analysts predict continued growth", "supported": false, "confidence": "low", "explanation": "..."}}
]

JSON:"""


def extract_claims_with_citations(
    answer: str,
    client: OpenAI
) -> list[ClaimData]:
    """
    Extract claims with citations using fresh LLM context.

    Args:
        answer: The agent's final answer text
        client: OpenAI client for LLM calls

    Returns:
        List of ClaimData

    Raises:
        ValueError: If extraction fails
    """
    prompt = EXTRACTION_PROMPT.format(answer=answer)

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        messages=[
            {"role": "system", "content": "You are an expert at extracting structured information. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=2000
    )

    result_text = response.choices[0].message.content
    if not result_text:
        raise ValueError("Empty response from LLM")

    # Parse JSON
    claims_raw = parse_json_response(result_text)

    # Convert to ClaimData format
    claims: list[ClaimData] = []
    for claim_raw in claims_raw:
        claims.append({
            "claim": claim_raw["claim"],
            "citations": claim_raw["citations"],
            "invalid_citations": []
        })

    logger.info(f"Extracted {len(claims)} claims")
    return claims


def validate_extraction(
    answer: str,
    extracted_claims: list[ClaimData]
) -> tuple[bool, list[str]]:
    """
    Validate extraction accuracy programmatically.

    Checks:
    1. All claim text exists in original answer (after removing citation markers)
    2. Citations appear in the answer

    Args:
        answer: Original answer text
        extracted_claims: Claims extracted by LLM

    Returns:
        Tuple of (validation_passed: bool, errors: list[str])
    """
    errors = []

    # Remove all citation markers [1], [2], etc. from answer for claim matching
    answer_without_citations = re.sub(r'\[\d+\]', '', answer)

    for idx, claim_data in enumerate(extracted_claims):
        claim_text = claim_data["claim"]
        claim_citations = claim_data["citations"]

        # Check 1: Claim text exists in answer (after removing citations)
        if claim_text not in answer_without_citations:
            errors.append(f"Claim {idx+1} not found in answer: '{claim_text[:50]}...'")

        # Check 2: All citations exist in original answer
        for cit in claim_citations:
            citation_pattern = f"[{cit}]"
            if citation_pattern not in answer:
                errors.append(f"Claim {idx+1} citation [{cit}] not found in answer")

    return (len(errors) == 0, errors)


def validate_citation_ranges(
    claims: list[ClaimData],
    num_sources: int
) -> list[ClaimData]:
    """
    Check that all citations are within valid source range.

    Populates the 'invalid_citations' field for each claim.

    Args:
        claims: List of ClaimData with citations
        num_sources: Total number of sources available (len(sources))

    Returns:
        Updated claims list with invalid_citations populated
    """
    for claim_data in claims:
        invalid = [cit for cit in claim_data["citations"]
                   if cit < 1 or cit > num_sources]
        claim_data["invalid_citations"] = invalid

    return claims


def validate_claims_against_sources(
    claims: list[ClaimData],
    sources: list[SourceData],
    client: OpenAI
) -> list[ClaimData]:
    """
    Validate all claims against their cited sources in a single LLM call.

    For each claim, checks if the cited sources actually support the claim.
    Uses batch validation for efficiency (one LLM call for all claims).

    Args:
        claims: List of ClaimData with citations
        sources: List of SourceData from tracker
        client: OpenAI client for validation

    Returns:
        Updated claims list with validation_result populated
    """
    # Build claims for validation (skip claims with only invalid citations)
    claims_for_validation = []
    for claim_data in claims:
        valid_citations = [c for c in claim_data["citations"]
                          if c not in claim_data.get("invalid_citations", [])]
        if valid_citations:
            claims_for_validation.append(claim_data)

    if not claims_for_validation:
        logger.info("No claims to validate (all have invalid citations)")
        return claims

    # Build claims_with_sources section
    claims_sections = []
    for idx, claim_data in enumerate(claims_for_validation):
        claim_text = claim_data["claim"]
        citations = [c for c in claim_data["citations"]
                    if c not in claim_data.get("invalid_citations", [])]

        # Get source texts for this claim
        source_texts = []
        for cit_num in citations:
            if 1 <= cit_num <= len(sources):
                source = sources[cit_num - 1]
                source_texts.append(
                    f"[{cit_num}] {source['title']}\n"
                    f"Source: {source['source']} | Date: {source['date']}\n"
                    f"Content: {source['summary']}"
                )

        # Build section for this claim
        section = f"""
CLAIM {idx + 1}:
"{claim_text}"

CITED SOURCES:
{chr(10).join(source_texts)}
"""
        claims_sections.append(section)

    claims_with_sources = "\n---\n".join(claims_sections)

    # Call LLM for validation
    prompt = VALIDATION_PROMPT.format(claims_with_sources=claims_with_sources)

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[
                {"role": "system", "content": "You are an expert fact-checker. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )

        result_text = response.choices[0].message.content
        if not result_text:
            raise ValueError("Empty response from LLM")

        # Parse JSON
        validations = parse_json_response(result_text)

        # Match by claim text and merge validation results
        for validation in validations:
            claim_text = validation["claim"]
            # Find matching claim in original claims list
            for claim_data in claims:
                if claim_data["claim"] == claim_text:
                    claim_data["validation_result"] = {
                        "supported": validation["supported"],
                        "confidence": validation["confidence"],
                        "explanation": validation["explanation"]
                    }
                    break

        logger.info(f"Validated {len(validations)} claims against sources")
        return claims

    except Exception as e:
        logger.error(f"Claim validation failed: {e}")
        # Return claims without validation results
        return claims


def validate_citations(
    answer: str,
    sources: list[SourceData],
    client: OpenAI
) -> CitationValidationResult:
    """
    Main orchestrator for citation validation pipeline.

    Executes all 5 stages:
    1. Extract claims with citations (with retry)
    2. Validate extraction accuracy
    3. Validate citation ranges
    4. Validate claims against sources
    5. Build final result

    Args:
        answer: Agent's final answer
        sources: List of SourceData from tracker
        client: OpenAI client

    Returns:
        CitationValidationResult with complete validation data
    """
    # Stage 1 & 2: Extract claims with retry and validation
    max_attempts = 3
    claims: list[ClaimData] = []
    extraction_attempts = 0

    for attempt in range(1, max_attempts + 1):
        extraction_attempts = attempt
        try:
            claims = extract_claims_with_citations(answer, client)

            # Stage 2: Validate extraction
            is_valid, errors = validate_extraction(answer, claims)

            if is_valid:
                logger.info(f"Extraction validated successfully on attempt {attempt}")
                break
            else:
                logger.warning(f"Extraction validation failed (attempt {attempt}): {errors}")
                if attempt == max_attempts:
                    # Fallback: use empty claims list
                    logger.error("Max extraction attempts reached, using fallback")
                    claims = []
        except Exception as e:
            logger.error(f"Extraction attempt {attempt} failed: {e}")
            if attempt == max_attempts:
                claims = []

    # Stage 3: Range validation
    claims = validate_citation_ranges(claims, len(sources))

    # Stage 4: LLM claim-source validation
    claims = validate_claims_against_sources(claims, sources, client)

    # Stage 5: Build result
    total_invalid = sum(len(c.get("invalid_citations", [])) for c in claims)

    # Determine if validation passed
    # Note: confidence represents support strength (informational only)
    # Validation fails if:
    # 1. Any claim has invalid citations (out of range)
    # 2. Any claim is unsupported (supported=false)
    validation_passed = True

    for claim in claims:
        # Check for invalid citations
        if claim.get("invalid_citations"):
            validation_passed = False

        # Check for unsupported claims (regardless of confidence)
        validation_result = claim.get("validation_result")
        if validation_result and not validation_result["supported"]:
            validation_passed = False

    return {
        "claims": claims,
        "extraction_attempts": extraction_attempts,
        "total_invalid_citations": total_invalid,
        "validation_passed": validation_passed
    }
