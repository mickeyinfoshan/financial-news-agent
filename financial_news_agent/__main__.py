"""CLI entry point for the financial news agent."""

from .agent import run_agent_with_retry
from .utils import extract_citations


def main():
    """Main CLI interface with multi-turn conversation support."""
    print("=" * 60)
    print("Financial News Agent")
    print("=" * 60)
    print("Type 'quit', 'exit', or 'q' to end the conversation.")
    print("=" * 60)
    print()

    # Initialize conversation with system message
    system_message = {
        "role": "system",
        "content": """You are a financial news analyst AI agent. Your job is to:
1. Search for recent financial news about the company or industry the user asks about
2. Analyze the news to create a coherent storyline of what has been happening
3. Provide future impact analysis based on the trends you observe
4. **Cite your sources using numbered references [1], [2], [3] etc.**

When using the search_financial_news tool:
- Use the 'query' parameter for your full search query with keywords
- Use the 'company_name' parameter to specify the company name (e.g., 'Tesla', 'Goldman Sachs') for accurate ticker lookup
- IMPORTANT: Only provide company_name when searching for a SINGLE specific company
- For multiple companies or industry queries, leave company_name empty and use descriptive query text
- For competitor analysis, make SEPARATE tool calls for each company with their respective company_name

Examples:
- Single company: query="Tesla earnings Q1 2026", company_name="Tesla"
- Multiple companies: query="BYD sales China", company_name="BYD" (separate call)
- Industry: query="EV industry trends", company_name=None

**IMPORTANT - Source Citations:**
When you receive news articles from the tool, they will be numbered (id: 1, 2, 3, etc.).
You MUST cite these sources in your answer using the format [1], [2], [3] whenever you reference information from them.

Example citation style:
"Apple's stock rose 5% following strong earnings [1]. Analysts predict continued growth in the AI sector [2][3]."

Always use the search_financial_news tool to gather information before answering.
Be thorough - you can call the tool multiple times with different queries if needed.
Base your analysis strictly on the sources you find and cite them appropriately."""
    }

    messages = [system_message]

    # Conversation loop
    try:
        while True:
            query = input("\nYour question: ").strip()

            # Check for exit commands
            if query.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break

            if not query:
                print("Please enter a question.")
                continue

            print("\nAnalyzing... (this may take a moment)\n")

            # Run the agent with conversation history
            result, messages = run_agent_with_retry(query, messages)

            # Display results
            print("=" * 60)
            print("ANSWER")
            print("=" * 60)
            print(result["answer"])
            print()

            # Extract citations from answer
            cited_indices = extract_citations(result["answer"])

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
            eval_data = result["evaluation"]
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
                for attempt_data in result["retry_history"]:
                    print(f"\nAttempt {attempt_data['attempt']}:")
                    eval_data = attempt_data['evaluation']
                    print(f"  Overall: {eval_data['overall']}/10")
                    print(f"  Accuracy: {eval_data.get('accuracy', 0)}/10")
                    print(f"  Relevance: {eval_data.get('relevance', 0)}/10")
                    print(f"  Coherence: {eval_data.get('coherence', 0)}/10")
                    print(f"  Reasonableness: {eval_data.get('reasonableness', 0)}/10")
                    print(f"  Answer Preview: {attempt_data['answer'][:150]}...")
                print()

    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
