#!/usr/bin/env python3
"""Example demonstrating logging and debugging features."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qa_chain import (
    DebugContext,
    QAConfig,
    answer_question,
    debug_mode,
    dump_debug_info,
    setup_logging,
)


def main():
    """Demonstrate logging and debugging features."""
    # Setup logging with JSON format
    setup_logging(level="DEBUG", format_type="json")

    print("=== QA Chain Debug Example ===\n")

    # Example 1: Basic logging
    print("1. Basic question with logging:")
    config = QAConfig(
        model="gpt-4o-mini",
        temperature=0.2,
        log_level="INFO",
        log_format="simple",  # Switch to simple for readability
    )

    question = "What is machine learning?"
    context = """Machine learning is a subset of artificial intelligence (AI)
    that enables systems to learn and improve from experience without being
    explicitly programmed. It focuses on developing computer programs that
    can access data and use it to learn for themselves."""

    answer = answer_question(question, context, config)
    print(f"Answer: {answer}\n")

    # Example 2: Debug mode
    print("2. Debug mode with detailed logging:")
    with debug_mode(True):
        debug_config = QAConfig(
            model="gpt-4o-mini",
            temperature=0.5,
            enable_debug_mode=True,
            log_level="DEBUG",
        )

        with DebugContext() as ctx:
            ctx.checkpoint("start", {"question": question[:20] + "..."})

            answer = answer_question(
                "What are the main types of ML?",
                """There are three main types of machine learning:
                1. Supervised Learning - uses labeled data
                2. Unsupervised Learning - finds patterns in unlabeled data
                3. Reinforcement Learning - learns through trial and error""",
                debug_config,
            )

            ctx.checkpoint("completed", {"answer_length": len(answer)})

    print(f"Answer: {answer}\n")

    # Example 3: Slow request logging
    print("3. Slow request detection:")
    slow_config = QAConfig(
        model="gpt-4o-mini",
        log_slow_requests=True,
        log_slow_request_threshold=0.01,  # Very low threshold to trigger
    )

    answer = answer_question(
        "What is deep learning?",
        "Deep learning is a subset of machine learning that uses neural networks with multiple layers.",
        slow_config,
    )
    print(f"Answer: {answer}\n")

    # Example 4: Debug info dump
    print("4. Debug information dump:")
    dump_config = QAConfig(enable_debug_mode=True)

    answer = answer_question(
        "What is AI?",
        "Artificial Intelligence (AI) is the simulation of human intelligence in machines.",
        dump_config,
    )

    # Dump debug info
    dump_debug_info(
        question="What is AI?",
        context="Artificial Intelligence (AI) is the simulation of human intelligence in machines.",
        answer=answer,
        config=dump_config,
        execution_time=0.5,
        filename="debug_example.json",
    )

    print(f"Answer: {answer}")
    print("Debug info saved to debug_example.json\n")

    # Show the debug file contents
    if os.path.exists("debug_example.json"):
        print("Debug file contents:")
        with open("debug_example.json") as f:
            print(f.read())


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: Please set OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    main()
