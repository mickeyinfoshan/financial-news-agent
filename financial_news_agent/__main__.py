"""CLI entry point for the financial news agent."""

from typing import Any

from .agent import run_agent_with_retry, create_conversation
from .utils import extract_citations
from .types import AgentResult, MessageDict, EvaluationResult, RetryAttempt, CitationValidationResult


def truncate_text(text: str, max_length: int = 80) -> str:
    """Truncate text to max_length characters, adding '...' if truncated."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def display_citation_validation(citation_validation: CitationValidationResult) -> None:
    """Display citation validation results in the CLI."""
    print("=" * 60)
    print("CITATION VALIDATION")
    print("=" * 60)

    validation_passed = citation_validation.get("validation_passed", False)
    claims = citation_validation.get("claims", [])
    total_invalid = citation_validation.get("total_invalid_citations", 0)
    extraction_attempts = citation_validation.get("extraction_attempts", 1)

    # Display status
    status_symbol = "✓" if validation_passed else "✗"
    status_text = "PASSED" if validation_passed else "FAILED"
    print(f"Status: {status_symbol} {status_text}")

    # Handle edge case: no claims extracted
    if not claims:
        print("No claims could be extracted from the answer.")
        if extraction_attempts > 1:
            print(f"Extraction Attempts: {extraction_attempts}")
        print()
        return

    # Display summary statistics
    print(f"Claims Validated: {len(claims)} | Invalid Citations: {total_invalid} | Extraction Attempts: {extraction_attempts}")

    # If validation passed, show compact format
    if validation_passed:
        print()
        return

    # If validation failed, show detailed issues
    print()
    print("ISSUES FOUND:")
    print()

    # Group issues by type
    invalid_citation_claims: list[dict[str, Any]] = []
    unsupported_claims: list[dict[str, Any]] = []

    for claim_data in claims:
        claim_text = claim_data.get("claim", "")
        citations = claim_data.get("citations", [])
        invalid_citations = claim_data.get("invalid_citations", [])
        validation_result = claim_data.get("validation_result")

        # Check for invalid citations (out of range)
        if invalid_citations:
            invalid_citation_claims.append({
                "claim": claim_text,
                "citations": citations,
                "invalid": invalid_citations
            })

        # Check for unsupported claims
        if validation_result and not validation_result.get("supported", True):
            unsupported_claims.append({
                "claim": claim_text,
                "citations": citations,
                "confidence": validation_result.get("confidence", "unknown"),
                "explanation": validation_result.get("explanation", "No explanation provided")
            })

    # Display invalid citations
    if invalid_citation_claims:
        print("[Invalid Citations - Out of Range]")
        for item in invalid_citation_claims:
            print(f"  Claim: \"{truncate_text(item['claim'])}\"")
            print(f"  Citations Used: {item['citations']}")
            print(f"  Invalid: {item['invalid']}")
            print()

    # Display unsupported claims
    if unsupported_claims:
        print("[Unsupported Claims]")
        for item in unsupported_claims:
            print(f"  Claim: \"{truncate_text(item['claim'])}\"")
            print(f"  Citations Used: {item['citations']}")
            print(f"  Confidence: {item['confidence']}")
            print(f"  Reason: {truncate_text(item['explanation'], max_length=120)}")
            print()


def main() -> None:
    """Main CLI interface with multi-turn conversation support."""
    print("=" * 60)
    print("Financial News Agent")
    print("=" * 60)
    print("Type 'quit', 'exit', or 'q' to end the conversation.")
    print("=" * 60)
    print()

    # Initialize conversation
    messages: list[MessageDict] = create_conversation()

    # Conversation loop
    try:
        while True:
            query: str = input("\nYour question: ").strip()

            # Check for exit commands
            if query.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break

            if not query:
                print("Please enter a question.")
                continue

            print("\nAnalyzing... (this may take a moment)\n")

            # Run the agent with conversation history
            result: AgentResult
            result, messages = run_agent_with_retry(query, messages)

            # Display results
            print("=" * 60)
            print("ANSWER")
            print("=" * 60)
            print(result["answer"])
            print()

            # Extract citations from answer
            cited_indices: list[int] = extract_citations(result["answer"])

            # Display only cited sources
            print("=" * 60)
            if cited_indices:
                print(f"CITED SOURCES ({len(cited_indices)} articles)")
            else:
                print(f"SOURCES ({len(result['sources'])} articles)")
            print("=" * 60)

            if cited_indices:
                # Show only sources that were cited
                for idx in cited_indices:
                    if 1 <= idx <= len(result['sources']):
                        source = result['sources'][idx - 1]
                        print(f"[{idx}] {source['title']}")
                        print(f"    Source: {source['source']} | Date: {source['date']}")
                        print(f"    URL: {source['url']}")
                        print()
            else:
                # Fallback: show first 10 if no citations found
                for i, source in enumerate(result["sources"][:10], 1):
                    print(f"[{i}] {source['title']}")
                    print(f"    Source: {source['source']} | Date: {source['date']}")
                    print(f"    URL: {source['url']}")
                    print()

            # Display citation validation if available
            if "citation_validation" in result and result["citation_validation"]:
                display_citation_validation(result["citation_validation"])

            print("=" * 60)
            print("EVALUATION")
            print("=" * 60)
            eval_data: EvaluationResult = result["evaluation"]
            print(f"Overall Score: {eval_data['overall']}/10.0")
            print(f"  - Accuracy: {eval_data.get('accuracy', 'N/A')}/10")
            print(f"  - Relevance: {eval_data.get('relevance', 'N/A')}/10")
            print(f"  - Coherence: {eval_data.get('coherence', 'N/A')}/10")
            print(f"  - Reasonableness: {eval_data.get('reasonableness', 'N/A')}/10")
            print(f"\nFeedback: {eval_data.get('feedback', 'N/A')}")
            print()

            # Display retry history if available
            if "retry_history" in result and result["retry_history"]:
                print("=" * 60)
                print("RETRY HISTORY")
                print("=" * 60)
                retry_history: list[RetryAttempt] = result["retry_history"]
                for attempt_data in retry_history:
                    print(f"\nAttempt {attempt_data['attempt']}:")
                    attempt_eval: EvaluationResult = attempt_data['evaluation']
                    print(f"  Overall: {attempt_eval['overall']}/10")
                    print(f"  Accuracy: {attempt_eval.get('accuracy', 0)}/10")
                    print(f"  Relevance: {attempt_eval.get('relevance', 0)}/10")
                    print(f"  Coherence: {attempt_eval.get('coherence', 0)}/10")
                    print(f"  Reasonableness: {attempt_eval.get('reasonableness', 0)}/10")
                    print(f"  Answer Preview: {attempt_data['answer'][:150]}...")
                print()

    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
