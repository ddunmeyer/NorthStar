"""The bridge between the chat page and the agents.

The page asks for one agent per signed-in employee and streams its replies.
If agents/coordinator.py provides make_coordinator, that is used. Until then
a single agent holding every available specialist tool stands in, so the page
works end to end while the coordinator is being built.

Coordinator contract the page relies on:
    make_coordinator(employee_id)            or
    make_coordinator(employee_id, drafts)    -> a Strands Agent
where drafts is the dict the app owns for unconfirmed IT requests.
"""
from __future__ import annotations

import inspect
import json
import os
import queue
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Iterator

MODEL_ID = os.getenv("NORTHSTAR_MODEL_ID") or "us.amazon.nova-2-lite-v1:0"
REGION = os.getenv("AWS_REGION") or "us-east-1"

# What the activity line calls each tool or specialist.
STEP_LABELS = {
    "get_my_pto": "PTO balance", "summarize_my_expenses": "Expense totals", "search_jobs": "Open roles",
    "search_policies": "Policy search", "get_my_projects": "Projects", "get_my_tasks": "Jira tasks",
    "get_my_it_requests": "IT requests", "draft_it_request": "Request drafting",
    "hr_specialist": "HR specialist", "developer_specialist": "Developer specialist", "it_specialist": "IT specialist",
}
WORKING = {
    "get_my_pto": "Checking your PTO balance", "summarize_my_expenses": "Adding up your expenses",
    "search_policies": "Searching company policies", "get_my_projects": "Looking up your projects",
    "get_my_tasks": "Pulling your Jira tasks", "get_my_it_requests": "Checking your IT requests",
    "draft_it_request": "Preparing a draft", "hr_specialist": "Asking the HR specialist",
    "developer_specialist": "Asking the developer specialist", "it_specialist": "Asking the IT specialist",
}

STAND_IN_PROMPT = """You are North Star, an employee assistant for a fictional company. Today is {today}.
You help the signed-in employee with their own PTO, expenses, projects, tasks and IT requests.

Rules:
- Always use a tool for records. Never guess a balance, amount, task or status.
- Report numbers exactly as the tools return them. Never add, subtract or round them yourself.
- You can only see the signed-in employee's own records. If asked about another person, say you can't share other employees' records.
- When tasks need an access item, check the employee's IT requests for it before suggesting a new request.
- draft_it_request only prepares a draft. Never say a request was submitted; the employee confirms it on screen.
- You have no policy search tool yet. For any policy question (carryover, caps, limits, approval rules), say that
  policy lookup isn't connected yet and state no rule or number. A note inside a tool result is not a policy.
- If you don't have a tool for something, say you don't know.
- If an expense question doesn't name a month, use the current month.
- Write dates the way people say them, for example Oct 9, not 2026-10-09.
- Keep answers short and plain. Use a short list when there are several items."""

_THINKING = re.compile(r"<thinking>.*?(</thinking>|$)", re.DOTALL)


def clean(text: str) -> str:
    """Nova sometimes narrates in <thinking> tags; the page shows answers, not reasoning."""
    return _THINKING.sub("", text).strip()


@dataclass
class Reply:
    text: str = ""
    steps: list[str] = field(default_factory=list)      # friendly names of tools used, in order
    sources: list[dict] = field(default_factory=list)   # policy citations returned by tools
    draft_ids: list[str] = field(default_factory=list)  # drafts created during this turn
    elapsed: float = 0.0
    tokens: int | None = None
    error: str | None = None


def build_agent(employee_id: str, drafts: dict):
    """Return (agent, mode). mode is 'coordinator' or 'stand-in'."""
    try:
        from agents import coordinator
        factory = getattr(coordinator, "make_coordinator", None)
    except Exception:
        factory = None
    if factory:
        wants_drafts = len(inspect.signature(factory).parameters) >= 2
        return (factory(employee_id, drafts) if wants_drafts else factory(employee_id)), "coordinator"

    from strands import Agent
    from strands.models import BedrockModel

    from tools.developer_tools import make_developer_tools
    from tools.hr_tools import make_hr_tools
    from tools.it_tools import make_it_tools

    tools = make_hr_tools(employee_id) + make_developer_tools(employee_id) + make_it_tools(employee_id, drafts)
    agent = Agent(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION),
        tools=tools,
        system_prompt=STAND_IN_PROMPT.format(today=date.today().strftime("%A, %B %d, %Y")),
        callback_handler=None,
    )
    return agent, "stand-in"


def _collect(messages: list, reply: Reply) -> None:
    """Read the turn's tool calls and results back out of the conversation."""
    for message in messages:
        for block in message.get("content", []):
            if "toolUse" in block:
                label = STEP_LABELS.get(block["toolUse"]["name"], block["toolUse"]["name"].replace("_", " "))
                if label not in reply.steps:
                    reply.steps.append(label)
            for part in block.get("toolResult", {}).get("content", []):
                payload = part.get("json")
                if payload is None and "text" in part:
                    try:
                        payload = json.loads(part["text"])
                    except (TypeError, ValueError):
                        payload = None
                if isinstance(payload, dict):
                    for src in payload.get("sources") or payload.get("citations") or []:
                        if isinstance(src, dict) and src not in reply.sources:
                            reply.sources.append(src)


def ask(agent, prompt: str, drafts: dict) -> Iterator[tuple[str, object]]:
    """Run one turn. Yields ('working', label), ('text', partial answer), then ('done', Reply).

    The agent runs on a worker thread and reports through a queue, so the page
    thread is the only one that touches Streamlit.
    """
    events: queue.Queue = queue.Queue()
    seen_tools: set[str] = set()
    outcome: dict = {}
    before_messages = len(agent.messages)
    before_drafts = set(drafts)

    def on_event(**kw):
        tool_use = kw.get("current_tool_use") or {}
        if tool_use.get("toolUseId") and tool_use["toolUseId"] not in seen_tools:
            seen_tools.add(tool_use["toolUseId"])
            events.put(("tool", tool_use.get("name", "")))
        if "data" in kw:
            events.put(("data", kw["data"]))

    def run():
        try:
            outcome["result"] = agent(prompt)
        except Exception as err:  # surfaced to the user as a plain message, never as invented data
            outcome["error"] = err
        finally:
            events.put(("end", None))

    previous_handler = agent.callback_handler
    agent.callback_handler = on_event
    started = time.perf_counter()
    threading.Thread(target=run, daemon=True).start()

    partial = ""
    try:
        while True:
            kind, value = events.get()
            if kind == "end":
                break
            if kind == "tool":
                partial = ""  # anything said before a tool call was a preamble, not the answer
                yield "working", WORKING.get(value, "Working on it")
            else:
                partial += value
                shown = clean(partial)
                if shown:
                    yield "text", shown
    finally:
        agent.callback_handler = previous_handler

    reply = Reply(elapsed=time.perf_counter() - started)
    _collect(agent.messages[before_messages:], reply)
    reply.draft_ids = [d for d in drafts if d not in before_drafts]
    if "error" in outcome:
        reply.error = f"{type(outcome['error']).__name__}: {outcome['error']}"
        reply.text = ("I couldn't complete that request, so I haven't shown any data. "
                      "Nothing was changed. Please try again in a moment.")
    else:
        result = outcome["result"]
        reply.text = clean(str(result)) or "I don't have an answer for that."
        try:
            reply.tokens = int(result.metrics.accumulated_usage["totalTokens"])
        except Exception:
            reply.tokens = None
    yield "done", reply
