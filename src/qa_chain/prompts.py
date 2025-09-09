from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT = (
    "You are a careful assistant. Use ONLY the provided context to answer the user's question. "
    "If the answer cannot be determined from the context, reply exactly: "
    "'I don't know based on the provided context.'"
)

HUMAN_TEMPLATE = (
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Answer concisely and directly:"
)


def build_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_TEMPLATE),
        ]
    )
