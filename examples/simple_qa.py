#!/usr/bin/env python3
"""
Simple example demonstrating the core challenge spec requirements.

This shows the basic usage of answer_question() with just two inputs:
1. A user's question
2. A context paragraph
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qa_chain import answer_question


def main():
    """Demonstrate basic question-answering as per challenge spec."""
    # Example 1: Simple factual question
    question = "What is the capital of France?"
    context = "Paris is the capital of France. It is known for the Eiffel Tower."

    print("Question:", question)
    print("Context:", context)
    print("Answer:", answer_question(question, context))
    print()

    # Example 2: Question not in context
    question2 = "What is the population of France?"
    context2 = "France is a country in Western Europe. Its capital is Paris."

    print("Question:", question2)
    print("Context:", context2)
    print("Answer:", answer_question(question2, context2))


if __name__ == "__main__":
    # Note: Requires OPENAI_API_KEY environment variable
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        sys.exit(1)

    main()
