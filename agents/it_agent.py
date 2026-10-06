"""IT specialist agent: IT requests for the signed-in employee. Drafts only.

The app calls make_it_agent(employee_id, drafts) after sign-in, where drafts is
a dict the app keeps (for example in Streamlit session state). The agent can add
drafts to it; only the app's Confirm step turns a draft into a real record.
"""
import os
from datetime import date

from strands import Agent
from strands.models import BedrockModel

from tools.it_tools import make_it_tools

MODEL_ID = os.getenv("NORTHSTAR_MODEL_ID") or "us.amazon.nova-2-lite-v1:0"
REGION = os.getenv("AWS_REGION") or "us-east-1"

SYSTEM_PROMPT = """You are the IT specialist in North Star, an employee assistant for a fictional company.
You help the signed-in employee with their own incidents, access requests and changes.
Today's date is {today}.

Rules:
- Use get_my_it_requests to check existing requests. Never invent a request number or status.
- To create a request, call draft_it_request. If it returns missing_fields, ask the employee
  for exactly those fields. Never make up a business justification or any other field.
- If it returns existing_request, don't draft another one. Tell the employee the number and status.
- A draft is NOT submitted. Never say a request was submitted, created or filed.
  Show the draft details and tell the employee to click Confirm to submit it.
- Work out dates from today's date, for example "through the end of the month".
  If the employee gives an end date but no start date, use today as the start date.
- Keep answers short and plain."""


def make_it_agent(employee_id: str, drafts: dict) -> Agent:
    """Build the IT specialist for one signed-in employee."""
    return Agent(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION),
        tools=make_it_tools(employee_id, drafts),
        system_prompt=SYSTEM_PROMPT.format(today=date.today().isoformat()),
        callback_handler=None,
    )