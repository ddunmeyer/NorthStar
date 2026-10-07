"""HR tools: the signed-in employee's PTO balance and expense summary, and open internal jobs.

The app builds these tools after sign-in with make_hr_tools(employee_id).
The employee ID is fixed inside the tools and is not a tool parameter, so the
model can never choose whose records it reads.

Money is summed here in integer cents. The model only explains the totals.
"""
import os
import re
from datetime import date
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from strands import tool

REGION = os.getenv("AWS_REGION") or "us-east-1"
TABLE = boto3.resource("dynamodb", region_name=REGION).Table(
    os.getenv("NORTHSTAR_TABLE") or "northstar"
)
MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _plain(value):
    """DynamoDB returns numbers as Decimal; convert them so results are plain JSON."""
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    return value


def _money(cents: int) -> str:
    """Format integer cents as 842.50 without ever using floating point."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100:,}.{cents % 100:02d}"


def _query_prefix(pk: str, prefix: str) -> list:
    """Query one partition for sort keys starting with prefix, following pagination."""
    items = []
    kwargs = {"KeyConditionExpression": Key("pk").eq(pk) & Key("sk").begins_with(prefix)}
    while True:
        page = TABLE.query(**kwargs)
        items.extend(page["Items"])
        if "LastEvaluatedKey" not in page:
            return items
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def _query_partition(pk: str) -> list:
    """Read every item in one partition, following pagination."""
    items = []
    kwargs = {"KeyConditionExpression": Key("pk").eq(pk)}
    while True:
        page = TABLE.query(**kwargs)
        items.extend(page["Items"])
        if "LastEvaluatedKey" not in page:
            return items
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def make_hr_tools(employee_id: str) -> list:
    """Build the HR tools for one signed-in employee."""
    pk = f"EMP#{employee_id}"

    @tool
    def get_my_pto() -> dict:
        """Get the signed-in employee's PTO balance in hours.

        available_hours already accounts for approved upcoming time off,
        so do not subtract approved_upcoming_hours again.
        """
        item = TABLE.get_item(Key={"pk": pk, "sk": "PTO"}).get("Item")
        if not item:
            return {"error": "No PTO record found for this employee."}
        keep = ["plan", "available_hours", "approved_upcoming_hours", "as_of", "unit", "note"]
        return _plain({k: item[k] for k in keep if k in item})

    @tool
    def summarize_my_expenses(month: str | None = None, status: str | None = None) -> dict:
        """Summarize the signed-in employee's expenses for one month.

        Totals are calculated in code to the cent. Report them exactly as given.

        Args:
            month: The month in YYYY-MM format, for example 2026-10. Leave it out for the current month.
            status: Optional filter, for example paid, approved or pending.
        """
        month = (month or "").strip() or date.today().strftime("%Y-%m")
        if not MONTH.match(month):
            return {"error": "month must be in YYYY-MM format, for example 2026-10."}

        expenses = _query_prefix(pk, f"EXP#{month}#")
        if status:
            expenses = [x for x in expenses if str(x.get("status", "")).lower() == status.lower()]

        totals = {}
        for x in expenses:
            cents = int(x["amount_cents"])
            cur = totals.setdefault(x.get("currency", "USD"), {"total_cents": 0, "by_status": {}})
            cur["total_cents"] += cents
            s = cur["by_status"].setdefault(x.get("status", "unknown"), {"cents": 0, "count": 0})
            s["cents"] += cents
            s["count"] += 1
        for cur in totals.values():
            cur["total"] = _money(cur["total_cents"])
            for s in cur["by_status"].values():
                s["amount"] = _money(s["cents"])

        fields = ("report_id", "submitted_date", "category", "amount_cents", "currency", "status")
        return {
            "month": month,
            "status_filter": status,
            "expense_count": len(expenses),
            # From the Travel and Expense Policy, so "approved but unpaid" is never confused with "pending".
            "status_meanings": {"pending": "awaiting review, not yet approved",
                                "approved": "approved but not yet paid",
                                "paid": "payment completed"},
            "totals_by_currency": totals,
            "expenses": [_plain({k: x[k] for k in fields if k in x}) for x in expenses],
        }

    @tool
    def search_jobs(department: str | None = None, work_mode: str | None = None,
                    title: str | None = None, location: str | None = None) -> dict:
        """Search open internal job postings. Closed postings are never returned.

        This only lists jobs. It cannot submit an application.

        Args:
            department: Optional department, for example Engineering, IT or HR.
            work_mode: Optional work mode: remote, hybrid or onsite.
            title: Optional words to look for in the job title.
            location: Optional location, for example Chicago.
        """
        wanted = {"department": department, "work_mode": work_mode, "title": title, "location": location}
        wanted = {k: v.strip().lower() for k, v in wanted.items() if v and v.strip()}
        jobs = [j for j in _query_partition("JOBS") if str(j.get("status", "")).lower() == "open"]
        for field, value in wanted.items():
            exact = field in ("department", "work_mode")
            jobs = [j for j in jobs
                    if (str(j.get(field, "")).lower() == value if exact else value in str(j.get(field, "")).lower())]
        fields = ("requisition_id", "title", "department", "location", "work_mode", "employment_type", "posted_date")
        return {"filters": wanted, "job_count": len(jobs),
                "jobs": [_plain({k: j[k] for k in fields if k in j}) for j in jobs]}

    return [get_my_pto, summarize_my_expenses, search_jobs]