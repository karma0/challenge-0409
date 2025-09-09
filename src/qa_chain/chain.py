from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI

from .config import QAConfig
from .prompts import build_prompt


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

    Args:
        question: The user's question (string).
        context: A paragraph (or more) with the relevant context.
        config: Optional QAConfig to control model, temperature, and max_context_chars.

    Returns:
        The model's answer as a plain string.
    """
    cfg = config or QAConfig()
    chain = build_chain(cfg)
    result: str = chain.invoke({"question": question, "context": context})
    return result
