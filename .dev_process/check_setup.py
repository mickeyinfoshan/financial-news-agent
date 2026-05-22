"""Quick setup verification script."""

import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def check_setup():
    """Verify the setup is correct."""
    print("Checking setup...\n")

    issues = []

    # Check environment variables
    if not os.getenv("OPENAI_API_KEY"):
        issues.append("❌ OPENAI_API_KEY not set in .env")
    else:
        print("✓ OPENAI_API_KEY is set")

    if not os.getenv("OPENAI_BASE_URL"):
        issues.append("❌ OPENAI_BASE_URL not set in .env")
    else:
        print("✓ OPENAI_BASE_URL is set")

    if not os.getenv("NEWS_API_KEY"):
        issues.append("❌ NEWS_API_KEY not set in .env")
    else:
        print("✓ NEWS_API_KEY is set")

    # Check imports
    try:
        import openai
        print("✓ openai package installed")
    except ImportError:
        issues.append("❌ openai package not installed (run: uv sync)")

    try:
        import requests
        print("✓ requests package installed")
    except ImportError:
        issues.append("❌ requests package not installed (run: uv sync)")

    # Check module structure
    try:
        from financial_news_agent import agent, news_tool, evaluator, traceability
        print("✓ All modules can be imported")
    except ImportError as e:
        issues.append(f"❌ Module import failed: {e}")

    print()

    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  {issue}")
        print("\nPlease fix these issues:")
        print("  1. Copy .env.example to .env")
        print("  2. Edit .env and add your NEWS_API_KEY")
        return False
    else:
        print("✅ Setup looks good! You can run the agent with:")
        print("   uv run python -m financial_news_agent")
        return True


if __name__ == "__main__":
    success = check_setup()
    sys.exit(0 if success else 1)
