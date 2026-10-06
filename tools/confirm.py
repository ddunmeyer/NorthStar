"""Confirm step: turn a draft into a real IT request record.

This is application code, not an agent tool: only the app calls it, after the
employee clicks Confirm. The record's number comes from the draft ID and is
written with attribute_not_exists(pk), so confirming the same draft twice
creates exactly one record. DynamoDB guarantees that, not the model.
"""
from datetime import date

from botocore.exceptions import ClientError

from tools.hr_tools import TABLE

PREFIX = {"access": "RITM", "incident": "INC", "change": "CHG"}


def confirm_request(employee_id: str, drafts: dict, draft_id: str) -> dict:
    """Write the draft as one IT request record for the signed-in employee."""
    draft = drafts.get(draft_id)
    if not draft:
        return {"ok": False, "error": "That draft doesn't exist. Ask the assistant to draft it again."}
    if draft.get("requested_by_employee_id") != employee_id:
        return {"ok": False, "error": "You can only confirm your own drafts."}

    number = f"{PREFIX[draft['request_type']]}{draft_id.removeprefix('DRAFT-')}"
    needs_approval = bool(draft.get("approval_required"))
    item = {
        **draft,
        "pk": f"EMP#{employee_id}",
        "sk": f"ITREQ#{number}",
        "number": number,
        "status": "Awaiting approval" if needs_approval else "New",
        "created_date": date.today().isoformat(),
        "mock": True,
    }
    if needs_approval:
        item["approval_status"] = "pending"

    try:
        TABLE.put_item(Item=item, ConditionExpression="attribute_not_exists(pk)")
    except ClientError as error:
        if error.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
        existing = TABLE.get_item(Key={"pk": item["pk"], "sk": item["sk"]}).get("Item", {})
        return {"ok": True, "created": False, "number": number, "status": existing.get("status"),
                "message": f"{number} was already submitted. No duplicate was created."}

    return {"ok": True, "created": True, "number": number, "status": item["status"],
            "message": f"Submitted {number}. Status: {item['status']}."}