# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A conversational room booking chatbot for the Cubo Itaú office, built as a Promtior technical challenge. Users authenticate and chat with a LangChain ReAct agent backed by Groq (Llama 3.3) to create, list, and cancel meeting room bookings. The full spec is in [docs/Challenge-Guide.pdf](docs/Challenge-Guide.pdf).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in your Groq API key
cp .env.example .env

# Run locally
streamlit run app.py
```

## Architecture

```
app.py (Streamlit entry point)
  └─ src/auth.py              # authenticate(username, password) — hardcoded users
  └─ src/agent.py             # build_agent_executor(user) / run_agent(executor, msg, history, user)
       └─ src/tools.py        # make_tools(current_user) → list of @tool closures
            └─ src/booking_store.py   # SQLite logic + all business-rule validation
```

**Data flow:** The Streamlit UI handles login via `src.auth`, then creates a per-session `AgentExecutor` (LangChain ReAct agent + Groq LLM). Each user message is passed to `run_agent()`, which prepends recent history as text and calls the executor. The agent reasons over available tools and calls them; the tools are closures that capture `current_user` so the LLM cannot impersonate another user.

**Key invariant:** All business rule validation happens in `src/booking_store.py`, not in the LLM prompt. The tools return `{"success": False, "error": "..."}` for any constraint violation — the LLM then relays the error naturally to the user.

## Domain Rules

- **Rooms:** A (cap 4), B (cap 6), C (cap 8), D (cap 10), E (cap 20)
- **Slots:** 30-minute increments, start times must be on a 30-min boundary
- **Max duration:** 3 hours per booking
- **No overlaps:** one booking per room per slot
- **Users:** `User1` and `User2`, password `TechnicalChallengePromptior`
- **Every booking requires:** room, title, attendee count, start datetime, end datetime

## Key Files

| File | Purpose |
|---|---|
| [app.py](app.py) | Streamlit UI — login screen + chat interface (entry point) |
| [src/agent.py](src/agent.py) | LangChain ReAct agent wired to Groq |
| [src/tools.py](src/tools.py) | `make_tools(current_user)` — five `@tool` closures |
| [src/booking_store.py](src/booking_store.py) | SQLite CRUD + `_validate_booking()` enforcing all rules |
| [src/auth.py](src/auth.py) | `authenticate(username, password)` |
| [docs/overview.md](docs/overview.md) | Project write-up and component diagram |
| [notebook.ipynb](notebook.ipynb) | Required Jupyter notebook with tech walkthrough |

## Deployment (Railway)

Push to GitHub, connect repo in Railway, set `GROQ_API_KEY` as an env var. The `railway.toml` points to `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`. SQLite file (`bookings.db`) is ephemeral on Railway's free tier — state resets on redeploy.
