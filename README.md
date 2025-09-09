
# LangChain QA Challenge

A small, production-ready chain that takes a user's **question** and a **context paragraph** and returns an answer using a language model (OpenAI via `langchain-openai`).

## Features

- Modern **LangChain Expression Language** pipeline: `preprocess → prompt → llm → StrOutputParser`.
- Clean public function: `answer_question(question, context, config)`.
- Minimal input preprocessing (whitespace + smart quotes) and safe **context clipping**.
- Prompt instructs the model to use **only the provided context**, otherwise answer *"I don't know based on the provided context."*

---

## Quickstart

### Setup

```bash
# Create and activate virtual environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set up your API key (choose one option):

# Option 1: Create a .env file (recommended)
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Option 2: Export directly
export OPENAI_API_KEY=sk-...
```

### Running the CLI

```bash
# Simple CLI demo
python -m examples.run --question "What is the capital of France?" --context "Paris is the capital of France."
```

### Programmatic usage

```python
from qa_chain import answer_question, QAConfig

answer = answer_question(
    question="Who wrote the novel?",
    context="The novel '1984' was written by George Orwell.",
    config=QAConfig(model="gpt-4o-mini", temperature=0.2)
)
print(answer)  # -> "George Orwell."
```

---

## Project layout

```
src/qa_chain/
  ├─ __init__.py
  ├─ chain.py
  ├─ prompts.py
  └─ config.py
examples/
  └─ run.py
tests/
  └─ test_chain.py
requirements.txt
README.md
```

---

## Docker Support

Run the application without managing Python environments:

```bash
export OPENAI_API_KEY=sk-...
./docker-run.sh --question "What is the capital of France?" --context "Paris is the capital of France."
```

See [DOCKER.md](DOCKER.md) for detailed Docker instructions.

---

## Notes

- **Models**: defaults to `gpt-4o-mini`. Override via `QAConfig(model=...)` or `OPENAI_MODEL` env var.
- **Streaming**: This minimal version returns a single string. It's easy to extend to streaming by swapping in a streaming-friendly runner.
- **Azure OpenAI**: You can point `langchain-openai` at Azure by setting the corresponding environment variables (`AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, etc.).
- **Safety**: The prompt is constrained to the provided context; the chain will admit uncertainty if the answer isn't in the context.
```
