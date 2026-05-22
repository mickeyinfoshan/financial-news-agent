"""Main agent loop with LLM and tool calling."""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from .traceability import TraceabilityTracker
from .news_tool import get_tool_schema, execute_tool
from .evaluator import evaluate_response

# Load environment variables from .env file
load_dotenv()


def run_agent(user_query: str) -> dict:
    """
    Run the financial news agent.

    Args:
        user_query: User's question about a company or industry

    Returns:
        Dict with answer, sources, evaluation, and trace
    """
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    tracker = TraceabilityTracker()

    # System prompt
    system_message = {
        "role": "system",
        "content": """You are a financial news analyst AI agent. Your job is to:
1. Search for recent financial news about the company or industry the user asks about
2. Analyze the news to create a coherent storyline of what has been happening
3. Provide future impact analysis based on the trends you observe

Always use the search_financial_news tool to gather information before answering.
Be thorough - you can call the tool multiple times with different queries if needed.
Base your analysis strictly on the sources you find."""
    }

    # Initialize conversation
    messages = [
        system_message,
        {"role": "user", "content": user_query}
    ]

    # Tool definitions
    tools = [get_tool_schema()]

    # Agent loop (max 10 iterations)
    final_answer = None
    for iteration in range(10):
        print(f"\n[Iteration {iteration + 1}]")
        try:
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.5"),
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2000
            )

            assistant_message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            print(f"Finish reason: {finish_reason}")
            print(f"Has tool calls: {bool(assistant_message.tool_calls)}")
            print(f"Content: {assistant_message.content[:100] if assistant_message.content else 'None'}...")

            # Add assistant message to conversation
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": assistant_message.tool_calls
            })

            # Track reasoning if there's text content
            if assistant_message.content:
                tracker.add_reasoning(assistant_message.content)

            # Check if we have tool calls to execute
            if assistant_message.tool_calls:
                # Execute tool calls
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    # Execute the tool
                    result = execute_tool(tool_name, tool_args)

                    # Track the tool call
                    tracker.add_tool_call(tool_name, tool_args, result)

                    # Add sources
                    for article in result:
                        tracker.add_source({
                            "title": article.get("title", ""),
                            "date": article.get("published_at", ""),
                            "source": article.get("source", ""),
                            "url": article.get("url", ""),
                            "summary": article.get("description", "")
                        })

                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
            else:
                # No tool calls, this is the final answer
                final_answer = assistant_message.content or "No answer generated."
                break

        except Exception as e:
            print(f"Error in agent loop: {e}")
            final_answer = f"Error occurred: {str(e)}"
            break

    # If no answer after max iterations
    if final_answer is None:
        final_answer = "Agent reached maximum iterations without completing the analysis."

    # Self-evaluate the response
    evaluation = evaluate_response(final_answer, tracker)

    # Return structured result
    return {
        "answer": final_answer,
        "sources": tracker.sources,
        "tool_calls": tracker.tool_calls,
        "reasoning_steps": tracker.reasoning_steps,
        "evaluation": evaluation,
        "trace": tracker.get_trace()
    }
