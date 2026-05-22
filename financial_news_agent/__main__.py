"""CLI entry point for the financial news agent."""

from .agent import run_agent


def main():
    """Main CLI interface."""
    print("=" * 60)
    print("Financial News Agent")
    print("=" * 60)
    print()

    query = input("Ask about a company or industry: ")

    if not query.strip():
        print("No query provided. Exiting.")
        return

    print("\nAnalyzing... (this may take a moment)\n")

    # Run the agent
    result = run_agent(query)

    # Display results
    print("=" * 60)
    print("ANSWER")
    print("=" * 60)
    print(result["answer"])
    print()

    print("=" * 60)
    print(f"SOURCES ({len(result['sources'])} articles)")
    print("=" * 60)
    for i, source in enumerate(result["sources"][:10], 1):
        print(f"{i}. {source['title']}")
        print(f"   Source: {source['source']} | Date: {source['date']}")
        print(f"   URL: {source['url']}")
        print()

    print("=" * 60)
    print("EVALUATION")
    print("=" * 60)
    eval_data = result["evaluation"]
    print(f"Overall Score: {eval_data['overall']}/5.0")
    print(f"  - Accuracy: {eval_data.get('accuracy', 'N/A')}/5")
    print(f"  - Relevance: {eval_data.get('relevance', 'N/A')}/5")
    print(f"  - Coherence: {eval_data.get('coherence', 'N/A')}/5")
    print(f"  - Reasonableness: {eval_data.get('reasonableness', 'N/A')}/5")
    print(f"\nFeedback: {eval_data.get('feedback', 'N/A')}")
    print()


if __name__ == "__main__":
    main()
