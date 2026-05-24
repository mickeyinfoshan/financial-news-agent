"""CLI entry point for the financial news agent."""

from .agent import run_agent_with_retry, create_conversation
from .utils import extract_citations
from .types import AgentResult, MessageDict, EvaluationResult, RetryAttempt


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
