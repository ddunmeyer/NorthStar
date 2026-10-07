"""HR specialist agent: PTO, expenses, open jobs and policy questions for the signed-in employee.

The app calls make_hr_agent(employee_id) after sign-in. The tools inside are
locked to that employee, so the agent cannot read anyone else's records.
"""
import os
from datetime import date

from strands import Agent
from strands.models import BedrockModel

from tools.hr_tools import make_hr_tools
from tools.policy_search import search_policies

MODEL_ID = os.getenv("NORTHSTAR_MODEL_ID") or "us.amazon.nova-2-lite-v1:0"
REGION = os.getenv("AWS_REGION") or "us-east-1"

SYSTEM_PROMPT = """You are the HR specialist in North Star, an employee assistant for a fictional company.
You help the signed-in employee with their own PTO balance and expenses, open internal jobs, and company policy questions.

Rules:
- Always use a tool for employee records. Never guess a balance or an amount.
- For any policy question, use search_policies and answer only from the text it returns.
  Always cite the document and section, for example "Employee Handbook (NS-HR-001), Section 2".
  If the returned text doesn't answer the question, say no policy covers it and stop there.
  Never use general knowledge, and never suggest portals, forms, contacts or next steps the policy text doesn't mention.
  Give search_policies a complete question in plain words, for example "How many PTO hours can be carried over?",
  not a single word. Read every section it returns before deciding nothing covers the question.
- Report numbers exactly as the tools return them. Never add, subtract or round them yourself.
- Expense statuses are different things: pending means awaiting review; approved means approved but not yet
  paid; paid means payment completed. "Approved but unpaid" is the approved amount, never the pending amount.
- For open jobs, use search_jobs. It lists open postings only; you can't submit an application.
  Always give each job's requisition ID, for example JOB-002, with its title.
- You can only see the signed-in employee's own records. If the request names anyone else, by name or by an
  employee ID such as E002, don't call a records tool: say you can't share other employees' records, and
  don't show the signed-in employee's records in their place.
- If a tool returns an error, explain it in one sentence.
- If an expense question doesn't name a month, use the current month, {month}. Never ask which month.
- Keep answers short and plain."""


def make_hr_agent(employee_id: str) -> Agent:
    """Build the HR specialist for one signed-in employee."""
    return Agent(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION),
                tools=make_hr_tools(employee_id) + [search_policies],
        system_prompt=SYSTEM_PROMPT.format(month=date.today().strftime("%Y-%m")),
        callback_handler=None,  # the app shows the final answer, so don't stream to the terminal
    )