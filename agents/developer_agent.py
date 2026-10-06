"""Developer specialist agent: projects and tasks for the signed-in employee.

The app calls make_developer_agent(employee_id) after sign-in. The tools inside
are locked to that employee and deny projects they aren't a member of.
"""
import os

from strands import Agent
from strands.models import BedrockModel

from tools.developer_tools import make_developer_tools

MODEL_ID = os.getenv("NORTHSTAR_MODEL_ID") or "us.amazon.nova-2-lite-v1:0"
REGION = os.getenv("AWS_REGION") or "us-east-1"

SYSTEM_PROMPT = """You are the developer specialist in North Star, an employee assistant for a fictional company.
You help the signed-in employee with their own projects and Jira-style tasks.

Rules:
- Always use a tool for projects and tasks. Never invent a task, status or due date.
- If a tool returns "Access denied", say so plainly and don't guess what the project contains.
- When tasks list a required_service_id, always name it (for example "Both tasks need VPN-DEV access"),
  because the coordinator uses it to check access with the IT specialist.
- You can't check or request access yourself.
- Keep answers short and plain."""


def make_developer_agent(employee_id: str) -> Agent:
    """Build the developer specialist for one signed-in employee."""
    return Agent(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION),
        tools=make_developer_tools(employee_id),
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )