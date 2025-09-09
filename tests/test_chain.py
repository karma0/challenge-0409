import os

import pytest
from dotenv import load_dotenv

from qa_chain import QAConfig, answer_question

# Load environment variables from .env file
load_dotenv()


@pytest.mark.skipif("OPENAI_API_KEY" not in os.environ, reason="needs OPENAI_API_KEY")
def test_answer_question_smoke():
    context = "Paris is the capital of France."
    q = "What is the capital of France?"
    a = answer_question(q, context, QAConfig(temperature=0.0))
    assert "Paris" in a
