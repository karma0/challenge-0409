from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI

from .config import QAConfig
from .prompts import build_prompt
from .rate_limiter import check_rate_limit
from .security import sanitize_output, validate_config, validate_input


def _normalize_text(s: str) -> str:
    # Normalize unicode and collapse whitespace
    s = unicodedata.normalize("NFKC", s or "")
    # Replace smart quotes with ascii equivalents
    s = (
        s.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _clip_context(context: str, max_chars: int) -> str:
    if len(context) <= max_chars:
        return context
    # Try to cut on a sentence boundary near the limit
    clipped = context[:max_chars]
    # Backtrack to the last sentence terminator within the last 200 chars
    tail = clipped[-200:]
    idx = max(tail.rfind(". "), tail.rfind("! "), tail.rfind("? "))
    if idx != -1:
        clipped = clipped[: len(clipped) - (len(tail) - idx - 1)]
    return clipped


def _preprocess(inputs: Dict[str, str], config: QAConfig) -> Dict[str, str]:
    q = _normalize_text(inputs.get("question", ""))
    c = _normalize_text(inputs.get("context", ""))
    c = _clip_context(c, config.max_context_chars)
    return {"question": q, "context": c}


def build_chain(config: QAConfig) -> Any:
    preprocess = RunnableLambda(lambda d: _preprocess(d, config))
    prompt = build_prompt()
    llm = ChatOpenAI(model=config.model, temperature=config.temperature)
    return preprocess | prompt | llm | StrOutputParser()


def answer_question(question: str, context: str, config: QAConfig | None = None) -> str:
    """Answer a user's question using ONLY the provided context.

    This function implements the challenge spec requirements:
    1. Accepts two inputs: a question and context paragraph
    2. Integrates OpenAI LLM to generate answers
    3. Preprocesses inputs (normalizes whitespace, handles special chars)
    4. Returns formatted answer as a string

    Args:
        question: The user's question (string).
        context: A paragraph (or more) with the relevant context.
        config: Optional QAConfig to control model, temperature, and max_context_chars.
                If not provided, uses sensible defaults.

    Returns:
        The model's answer as a plain string. If the answer cannot be found
        in the context, returns "I don't know based on the provided context."

    Raises:
        SecurityError: If inputs or config violate security constraints.

    Example:
        >>> answer = answer_question(
        ...     "What is the capital?",
        ...     "Paris is the capital of France."
        ... )
        >>> print(answer)
        'Paris' or 'The capital is Paris.'
    """
    cfg = config or QAConfig()

    # Validate inputs and configuration
    validate_input(question, context)
    validate_config(cfg)

    # Check rate limit if enabled
    if cfg.enable_rate_limiting:
        check_rate_limit(cfg.rate_limit_identifier)

    # Build and run the chain
    chain = build_chain(cfg)
    result: str = chain.invoke({"question": question, "context": context})

    # Sanitize output before returning
    return sanitize_output(result)
