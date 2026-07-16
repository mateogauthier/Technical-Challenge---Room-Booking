import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from src.tools import make_tools

load_dotenv()

_SYSTEM_PROMPT = """You are a helpful room booking assistant for the Cubo Itaú office.
The office has five meeting rooms: A (capacity 4), B (capacity 6), C (capacity 8), D (capacity 10), and E (capacity 20).
Bookings are made in 30-minute slots; a single booking can last up to 3 hours.
No two bookings may overlap in the same room.

Always confirm with the user before cancelling a booking unless they have already confirmed.
When creating a booking, make sure you have room, title, attendees, start time, and end time before calling the tool.
If any information is missing, ask for it first.
"""


def build_agent(current_user: str):
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0,
    )
    tools = make_tools(current_user)
    system_prompt = _SYSTEM_PROMPT + f"\nThe user currently logged in is: {current_user}"
    return create_react_agent(llm, tools, prompt=system_prompt)


def run_agent(graph, user_message: str, chat_history: list[dict], current_user: str) -> str:
    messages = []
    for msg in chat_history[-10:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    today = datetime.now().strftime("%Y-%m-%d (%A)")
    messages.append(HumanMessage(content=f"[Today is {today}] {user_message}"))

    result = graph.invoke({"messages": messages})
    return result["messages"][-1].content
