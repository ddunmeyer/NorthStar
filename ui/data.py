"""Read-only lookups for the dashboard, scoped to the signed-in employee.

The tiles and list pages read DynamoDB directly so they stay fast and exact;
the chat goes through the agents. Every function takes the employee ID the
app resolved at sign-in.
"""
from __future__ import annotations

import json
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import boto3
import streamlit as st
from boto3.dynamodb.conditions import Key

REGION = os.getenv("AWS_REGION") or "us-east-1"
TABLE_NAME = os.getenv("NORTHSTAR_TABLE") or "northstar"
KB_DIR = Path(__file__).resolve().parent.parent / "kb"
CLOSED = {"closed", "fulfilled", "rejected", "cancelled", "resolved", "completed"}


@st.cache_resource
def _table():
    return boto3.resource("dynamodb", region_name=REGION).Table(TABLE_NAME)


def _plain(value):
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    return value


def _query(pk: str, prefix: str = "") -> list[dict]:
    condition = Key("pk").eq(pk)
    if prefix:
        condition &= Key("sk").begins_with(prefix)
    kwargs = {"KeyConditionExpression": condition}
    items: list[dict] = []
    while True:
        page = _table().query(**kwargs)
        items.extend(page["Items"])
        if "LastEvaluatedKey" not in page:
            return _plain(items)
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def find_employee(first_name: str) -> dict | None:
    """Resolve a first name to a profile. Case and surrounding spaces are ignored."""
    name = first_name.strip().lower()
    if not name:
        return None
    entry = _table().get_item(Key={"pk": "DIRECTORY", "sk": name}).get("Item")
    if not entry:
        return None
    profile = _table().get_item(Key={"pk": f"EMP#{entry['employee_id']}", "sk": "PROFILE"}).get("Item")
    return _plain(profile) if profile else None


@st.cache_data(ttl=20, show_spinner=False)
def snapshot(employee_id: str, month: str) -> dict:
    """Everything the dashboard shows for one employee, in a handful of queries."""
    pk = f"EMP#{employee_id}"
    pto = _table().get_item(Key={"pk": pk, "sk": "PTO"}).get("Item") or {}
    expenses = _query(pk, f"EXP#{month}#")
    projects = [p for p in _query("PROJECTS") if employee_id in p.get("member_employee_ids", [])]
    tasks = [i for p in projects for i in _query(f"ISSUES#{p['project_key']}")
             if i.get("assignee_employee_id") == employee_id]
    sprints = {s["sprint_id"]: s for p in projects for s in _query(f"SPRINTS#{p['project_key']}")}
    return {
        "pto": _plain(pto),
        "expenses": expenses,
        "expense_total_cents": sum(int(x["amount_cents"]) for x in expenses),
        "projects": projects,
        "tasks": sorted(tasks, key=lambda t: t.get("due_date", "")),
        "sprints": sprints,
        "it_requests": sorted(_query(pk, "ITREQ#"), key=lambda r: r.get("created_date", ""), reverse=True),
        "services": {s["service_id"]: s for s in _query("CATALOG", "SERVICE#")},
    }


def access_state(snap: dict, service_id: str) -> tuple[str, str]:
    """How the employee stands on one access item: (label, tone)."""
    requests = [r for r in snap["it_requests"]
                if r.get("request_type") == "access" and r.get("service_id") == service_id]
    for r in requests:
        if str(r.get("status", "")).lower() not in CLOSED:
            return f"{r['number']} · {r.get('status', 'open').lower()}", "warn"
    if any(str(r.get("status", "")).lower() == "fulfilled" for r in requests):
        return "access granted", "ok"
    return "not requested", "bad"


def money(cents: int) -> str:
    """Integer cents as 842.50, with no floating point."""
    return f"{cents // 100:,}.{cents % 100:02d}"


def current_month() -> str:
    return date.today().strftime("%Y-%m")


@st.cache_data(show_spinner=False)
def policies() -> list[dict]:
    """The policy library: the source documents the Knowledge Base indexes."""
    docs = []
    for path in sorted(KB_DIR.glob("NS-*.md")):
        meta_path = path.with_name(path.name + ".metadata.json")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))["metadataAttributes"] if meta_path.exists() else {}
        text = path.read_text(encoding="utf-8")
        body = text[text.index("## "):] if "## " in text else text
        docs.append({"document_id": meta.get("document_id", path.stem), "title": meta.get("title", path.stem),
                     "owner": meta.get("owner", ""), "effective_date": meta.get("effective_date", ""),
                     "version": meta.get("version", ""), "body": body.replace("\n## ", "\n\n#### ").replace("## ", "#### ", 1)})
    return docs
