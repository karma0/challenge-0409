import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure 'src' is on the path for local execution
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from qa_chain import QAConfig, answer_question  # noqa: E402


def main():
    # Pre-flight check for API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_API_KEY"):
        print("Error: No API key found.")
        print("Please set one of the following:")
        print("  - OPENAI_API_KEY in your .env file or environment")
        print("  - AZURE_OPENAI_API_KEY (with related Azure settings)")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="LangChain QA Chain demo")
    parser.add_argument("--question", required=True, help="User's question")
    parser.add_argument("--context", required=True, help="Context paragraph")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-context-chars", type=int, default=6000)
    args = parser.parse_args()

    config = QAConfig(
        model=args.model,
        temperature=args.temperature,
        max_context_chars=args.max_context_chars,
    )

    answer = answer_question(args.question, args.context, config=config)
    print(answer)


if __name__ == "__main__":
    main()
