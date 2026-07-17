# Room Booking Chatbot

A conversational AI chatbot that lets users book meeting rooms at the Cubo Itaú office through natural language. Built as a Promtior technical challenge.

**Live demo:** *(add your Railway URL here)*

---

## What it does

Users log in and chat with an AI assistant to manage meeting room bookings. Instead of filling out forms, they just describe what they need:

> *"Book Room B for a team sync with 4 people tomorrow from 10:00 to 11:00"*

The assistant understands the request, validates it against all business rules, and confirms or explains why it can't be done.

## Features

- **Create bookings** — specify room, title, attendees, date and time range
- **List available rooms** — find which rooms are free for a given time and group size
- **Room schedule** — see all slots for a specific room on a given day (available vs. occupied)
- **Cancel bookings** — cancel your own bookings by name or ID
- **User authentication** — login required; users can only cancel their own bookings
- **Constraint enforcement** — all rules validated server-side, not by the LLM:
  - Rooms A–E with capacities 4 / 6 / 8 / 10 / 20
  - Bookings in 30-minute slots, start times on 30-min boundaries
  - Maximum 3 hours per booking
  - No overlapping bookings in the same room

## Stack

| Layer | Technology |
|---|---|
| LLM | Groq — `llama-3.3-70b-versatile` (free tier) |
| Agent | LangChain + LangGraph ReAct agent |
| UI | Streamlit |
| Storage | SQLite |
| Deployment | Railway |

## Running locally

```bash
# Install dependencies
pip install -r requirements.txt

# Add your Groq API key (get one free at console.groq.com)
cp .env.example .env
# Edit .env and set GROQ_API_KEY=your_key_here

# Start the app
streamlit run app.py
```

Login with `User1` or `User2`, password: `TechnicalChallengePromtior`

## Project structure

```
app.py                  # Streamlit UI — login screen + chat interface
src/
  auth.py               # User authentication
  agent.py              # LangGraph ReAct agent wired to Groq
  tools.py              # LangChain @tool definitions (one per booking action)
  booking_store.py      # SQLite CRUD + all business rule validation
docs/
  overview.md           # Architecture write-up and component diagram
  diagram.svg           # Component diagram (Excalidraw)
notebook.ipynb          # Technology walkthrough with runnable examples
scripts/
  reset_db.py           # Wipe and recreate the database (useful before demos)
```

## Manual test checklist

| # | Test | Expected result |
|---|---|---|
| 1 | Log in with wrong password | Error message shown, access denied |
| 2 | Log in as User1 with correct password | Chat interface appears |
| 3 | "What rooms are available tomorrow from 10:00 to 11:00 for 3 people?" | Lists rooms with enough capacity that are free |
| 4 | "Book Room B for Team Sync with 3 attendees tomorrow from 14:00 to 15:00" | Booking confirmed |
| 5 | "Book Room B for Another Meeting with 2 attendees tomorrow from 14:30 to 15:30" | Rejected — overlap with existing booking |
| 6 | "Book Room A for Big Meeting with 10 attendees tomorrow from 16:00 to 17:00" | Rejected — Room A capacity is 4 |
| 7 | "Book Room C for All Day with 5 attendees tomorrow from 09:00 to 16:00" | Rejected — exceeds 3-hour maximum |
| 8 | "Show me the schedule for Room B tomorrow" | Shows Team Sync slot as occupied |
| 9 | "Show me my bookings" | Lists Team Sync booking |
| 10 | "Cancel my Team Sync booking" → confirm | Booking cancelled successfully |
| 11 | Log out → log in as User2 → try to cancel User1's booking | Rejected — can only cancel own bookings |

All 11 tests pass on the live deployment.
