"""Coordinator agent: routes each request to the HR, developer or IT specialist.

The specialists are exposed to the coordinator as tools (the agents-as-tools
pattern). The coordinator never touches DynamoDB; it only reads the
specialists' answers. Each hand-off is appended to `activity` so the app can
show it.
"""
import os

from strands import Agent, tool
from strands.models import BedrockModel

from agents.developer_agent import make_developer_agent
from agents.hr_agent import make_hr_agent
from agents.it_agent import make_it_agent

MODEL_ID = os.getenv("NORTHSTAR_MODEL_ID") or "us.amazon.nova-2-lite-v1:0"
REGION = os.getenv("AWS_REGION") or "us-east-1"

SYSTEM_PROMPT = """You are the coordinator of North Star, an employee assistant for a fictional company.
You can't see any records yourself. Send each request to the right specialist:
- ask_hr: PTO, time off, expenses, open internal jobs, and company policies.
- ask_developer: projects and Jira-style tasks.
- ask_it: IT incidents, access requests, changes, and drafting new IT requests.

You are the only one who talks to the specialists. Never tell the employee to contact a
specialist; ask the specialist yourself. Whenever the employee asks to get, request or
need access, ALWAYS call ask_it, even if the conversation already mentions related requests.
Never answer a question about the employee's records or requests without calling a specialist.

Rules:
- Give the specialist the request in clear, complete words, including any details from
  earlier in the conversation that it needs.
- One request can need more than one specialist. If the developer specialist says tasks need
  an access service (such as VPN-DEV), ask the IT specialist whether the employee already has
  a request for that access.
- Report the specialists' facts and numbers exactly. Never add your own numbers, policies,
  request numbers or statuses.
- If no specialist covers the question, say you don't know. Don't answer from general knowledge.
- The specialists only see the signed-in employee's own records. If the request is for someone else's
  records, by name or by an employee ID such as E002, say you can only share the employee's own records.
  Don't show the employee's own records in their place.
- Never add portals, forms, contacts or next steps that a specialist didn't mention.
- When a specialist cites a policy, keep the citation exactly as given, with the document ID and section,
  for example "Employee Handbook (NS-HR-001), Section 2". Never shorten it to just the document name.
- A draft is not submitted. Never say a request was submitted; tell the employee to click Confirm.
- Your final answer must cover every part of the employee's request, combining what each
  specialist said. Never drop details: if the developer specialist lists tasks, your answer
  must list every task key with its summary and status, and then give the access status.
- When listing jobs, keep each requisition ID (for example JOB-002).
- Keep it short and plain."""


def make_coordinator(employee_id: str, drafts: dict, activity: list | None = None) -> Agent:
    """Build the coordinator and its three specialists for one signed-in employee."""
    activity = activity if activity is not None else []
    hr = make_hr_agent(employee_id)
    developer = make_developer_agent(employee_id)
    it = make_it_agent(employee_id, drafts)

    def _ask(name: str, specialist: Agent, request: str) -> str:
        activity.append(f"Coordinator → {name}: {request}")
        return str(specialist(request))

    @tool
    def ask_hr(request: str) -> str:
        """Ask the HR specialist about the employee's PTO, time off, expenses or company policies.

        Args:
            request: The question in complete words, for example "What is my PTO balance?".
        """
        return _ask("HR", hr, request)

    @tool
    def ask_developer(request: str) -> str:
        """Ask the developer specialist about the employee's projects and Jira-style tasks.

        Args:
            request: The question in complete words, for example "List my tasks and the access they need.".
        """
        return _ask("Developer", developer, request)

    @tool
    def ask_it(request: str) -> str:
        """Ask the IT specialist about the employee's IT requests, or to draft a new one.

        Args:
            request: The request in complete words, for example "Do I have an open request for VPN-DEV?".
        """
        return _ask("IT", it, request)

    return Agent(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION),
        tools=[ask_hr, ask_developer, ask_it],
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )