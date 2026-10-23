# AI Customer Support Agent

A runnable demo for freelance client showcases. Features:
- Chat interface using Streamlit
- LangGraph agent with Groq (optional; local demo mode works without a key)
- FAQ retrieval using Chroma + LangChain when documents are indexed
- Order lookup tool using sample data
- Support ticket creation in SQLite
- Human escalation for unresolved issues

## Requirements
- Python 3.11+
- `uv`
- A Groq API key for LLM-powered responses (optional; without it, a simple demo fallback is used)

## Setup

```bash
uv sync
```

Copy `.env.example` to `.env` and add your key if you have one:

```env
GROQ_API_KEY=your_groq_api_key
```

## Run the app

In terminal 1:

```bash
uv run uvicorn app.api:app --reload
```

In terminal 2:

```bash
uv run streamlit run app/ui.py
```

Open the Streamlit URL shown in the terminal (usually http://localhost:8501).

## Example prompts
- "Where is order ORD-1001?"
- "What is your return policy?"
- "My payment was charged twice and I need help."
- "The product arrived damaged. Please create a ticket."
- "I want to speak to a human."

## Notes
- This is a demo with synthetic customer/order data. Do not use real customer information without appropriate security and privacy controls.
- Order lookup is a mock tool. Replace it with a verified, authenticated integration for a real client.
- Ticket creation is a local SQLite write.
- If `GROQ_API_KEY` is missing, the app uses deterministic demo responses so you can test the workflow.
