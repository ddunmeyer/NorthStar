"""IT tools: the signed-in employee's IT requests, and drafting new ones.

draft_it_request never writes to the database. It validates the request and
keeps a draft in the drafts dict the app owns. Only the app's Confirm step
writes a record, after the employee clicks Confirm.
"""
import uuid
from datetime import date, datetime

from strands import tool

from tools.hr_tools import TABLE, _plain, _query_prefix

TYPES = ("access", "incident", "change")
CLOSED = {"closed", "fulfilled", "rejected", "cancelled", "resolved", "completed"}
INCIDENT_FIELDS = ["short_description", "category"]
CHANGE_FIELDS = ["short_description", "service_id", "implementation_plan", "impact",
                 "rollback_plan", "scheduled_start", "scheduled_end"]
LIST_FIELDS = ("number", "request_type", "short_description", "service_id", "status",
               "approval_status", "created_date", "start_date", "end_date", "priority",
               "category", "scheduled_start", "scheduled_end")


def _is_open(req: dict) -> bool:
    return str(req.get("status", "")).lower() not in CLOSED


def _parse_date(value: str):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: str):
    """Parse an ISO time and insist on a timezone, as the change policy requires."""
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return dt if dt.tzinfo else None


def make_it_tools(employee_id: str, drafts: dict) -> list:
    """Build the IT tools for one signed-in employee.

    drafts is a dict owned by the app; draft_it_request adds drafts to it by ID.
    """
    pk = f"EMP#{employee_id}"

    def my_requests() -> list:
        return _query_prefix(pk, "ITREQ#")

    def catalog() -> list:
        return _query_prefix("CATALOG", "SERVICE#")

    @tool
    def get_my_it_requests(request_type: str | None = None) -> dict:
        """List the signed-in employee's IT requests: incidents, access requests and changes.

        Args:
            request_type: Optional filter: access, incident or change.
        """
        requests = my_requests()
        if request_type:
            kind = request_type.strip().lower()
            if kind not in TYPES:
                return {"error": "request_type must be access, incident or change."}
            requests = [r for r in requests if r.get("request_type") == kind]
        return {"request_count": len(requests),
                "requests": [_plain({k: r[k] for k in LIST_FIELDS if k in r}) for r in requests]}

    @tool
    def draft_it_request(
        request_type: str,
        service_id: str | None = None,
        short_description: str | None = None,
        business_justification: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        category: str | None = None,
        implementation_plan: str | None = None,
        impact: str | None = None,
        rollback_plan: str | None = None,
        scheduled_start: str | None = None,
        scheduled_end: str | None = None,
    ) -> dict:
        """Prepare a DRAFT IT request for the employee to review. This never submits anything.

        If fields are missing, this returns missing_fields: ask the employee for them, then
        call again with everything. If an open request for the same access already exists,
        this returns that request instead of a draft. Only the employee can submit a draft,
        by clicking Confirm in the app.

        Args:
            request_type: access, incident or change.
            service_id: Catalog service, for example VPN-DEV or AWS-SANDBOX. Needed for access and change.
            short_description: One-line summary of the request.
            business_justification: Why the employee needs the access.
            start_date: Access start date, YYYY-MM-DD.
            end_date: Access end date, YYYY-MM-DD.
            category: Incident category, for example Network.
            implementation_plan: For a change: the steps to carry it out.
            impact: For a change: the expected impact.
            rollback_plan: For a change: how to undo it.
            scheduled_start: For a change: start time with timezone, e.g. 2026-10-10T20:00:00-05:00.
            scheduled_end: For a change: end time with timezone.
        """
        kind = (request_type or "").strip().lower()
        if kind not in TYPES:
            return {"error": "request_type must be access, incident or change."}

        given = {k: v.strip() for k, v in {
            "service_id": service_id, "short_description": short_description,
            "business_justification": business_justification, "start_date": start_date,
            "end_date": end_date, "category": category, "implementation_plan": implementation_plan,
            "impact": impact, "rollback_plan": rollback_plan,
            "scheduled_start": scheduled_start, "scheduled_end": scheduled_end,
        }.items() if v and v.strip()}

        service = None
        if kind in ("access", "change"):
            services = catalog()
            available = [s["service_id"] for s in services]
            if "service_id" not in given:
                return {"missing_fields": ["service_id"], "available_services": available}
            given["service_id"] = given["service_id"].upper()
            service = next((s for s in services if s["service_id"] == given["service_id"]), None)
            if not service:
                return {"error": f"Unknown service {given['service_id']}.", "available_services": available}

        if kind == "access":
            existing = [r for r in my_requests()
                        if r.get("request_type") == "access"
                        and r.get("service_id") == given["service_id"] and _is_open(r)]
            if existing:
                return {"existing_request": _plain({k: existing[0][k] for k in LIST_FIELDS if k in existing[0]}),
                        "message": "An open request for this access already exists. Do not draft a "
                                   "duplicate; tell the employee its number and status."}
            given.setdefault("short_description", f"{service['name']} access")
            if "end_date" in given:
                given.setdefault("start_date", date.today().isoformat())
            required = list(service.get("required_fields", []))
        elif kind == "incident":
            required = INCIDENT_FIELDS
        else:
            required = CHANGE_FIELDS

        # A justification copied from the description isn't a reason the employee gave.
        if given.get("business_justification", "").lower() == given.get("short_description", "").lower():
            given.pop("business_justification", None)

        missing = [f for f in required if f not in given]
        if missing:
            return {"missing_fields": missing,
                    "message": "Ask the employee for these before drafting. Do not make them up."}

        if kind == "access" and "start_date" in given and "end_date" in given:
            start, end = _parse_date(given["start_date"]), _parse_date(given["end_date"])
            if not start or not end:
                return {"error": "start_date and end_date must be YYYY-MM-DD."}
            if end < start:
                return {"error": "end_date can't be earlier than start_date."}
        if kind == "change":
            start, end = _parse_datetime(given["scheduled_start"]), _parse_datetime(given["scheduled_end"])
            if not start or not end:
                return {"error": "scheduled_start and scheduled_end must be ISO times with a timezone."}
            if end <= start:
                return {"error": "scheduled_end must be later than scheduled_start."}

        draft_id = f"DRAFT-{uuid.uuid4().hex[:8].upper()}"
        draft = {"draft_id": draft_id, "request_type": kind,
                 "requested_by_employee_id": employee_id, **given}
        if service is not None:
            draft["approval_required"] = bool(service.get("approval_required"))
        # Keep one open draft per request: a revised draft replaces the earlier one.
        for old_id in [d for d, v in drafts.items()
                       if v["request_type"] == kind and v.get("service_id") == given.get("service_id")]:
            del drafts[old_id]
        drafts[draft_id] = draft
        return {"draft": draft, "submitted": False,
                "next_step": "Show this draft to the employee. Nothing is submitted until they click Confirm."}

    return [get_my_it_requests, draft_it_request]