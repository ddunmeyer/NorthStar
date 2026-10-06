"""Load the North Star demo data from data/ into the DynamoDB table.

Dry run by default (prints counts, writes nothing). Add --write to load.
Usage:  python scripts/load_data.py [--write]
"""
import json
import os
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

import boto3

DATA = Path(__file__).resolve().parent.parent / "data"
TABLE = os.getenv("NORTHSTAR_TABLE") or "northstar"
REGION = os.getenv("AWS_REGION") or "us-east-1"


def load(rel):
    # DynamoDB rejects Python floats, so read any decimals as Decimal.
    with open(DATA / rel) as f:
        return json.load(f, parse_float=Decimal)


def build_items():
    items = []

    def add(pk, sk, record, **extra):
        items.append({"pk": pk, "sk": sk, **record, **extra})

    for e in load("identity/employees.json"):
        add("DIRECTORY", e["name"].lower(), {"employee_id": e["employee_id"], "name": e["name"]})
        add(f"EMP#{e['employee_id']}", "PROFILE", e)
    for p in load("workday/pto_balances.json"):
        add(f"EMP#{p['employee_id']}", "PTO", p)
    for r in load("workday/time_off_requests.json"):
        add(f"EMP#{r['employee_id']}", f"LEAVE#{r['request_id']}", r)
    for x in load("workday/expenses.json"):
        month = x["submitted_date"][:7]  # e.g. 2026-10, so one month is one query
        add(f"EMP#{x['employee_id']}", f"EXP#{month}#{x['report_id']}", x)
    for j in load("workday/job_postings.json"):
        add("JOBS", j["requisition_id"], j)
    for p in load("jira/projects.json"):
        add("PROJECTS", p["project_key"], p)
    for i in load("jira/issues.json"):
        add(f"ISSUES#{i['project_key']}", i["issue_key"], i)
    for s in load("jira/sprints.json"):
        add(f"SPRINTS#{s['project_key']}", s["sprint_id"], s)
    for s in load("servicenow/service_catalog.json"):
        add("CATALOG", f"SERVICE#{s['service_id']}", s)
    for fname, kind in [("incidents", "incident"),
                        ("access_requests", "access"),
                        ("change_requests", "change")]:
        for r in load(f"servicenow/{fname}.json"):
            add(f"EMP#{r['requested_by_employee_id']}", f"ITREQ#{r['number']}", r,
                request_type=kind)
    return items


def group_name(item):
    # Employee items are grouped by sort-key prefix, everything else by partition key.
    if item["pk"].startswith("EMP#"):
        return item["sk"].split("#")[0]
    return item["pk"].split("#")[0]


def main():
    items = build_items()

    dupes = [k for k, n in Counter((i["pk"], i["sk"]) for i in items).items() if n > 1]
    if dupes:
        sys.exit(f"Duplicate keys found, nothing written: {dupes[:5]}")

    print(f"{len(items)} items")
    for name, n in sorted(Counter(group_name(i) for i in items).items()):
        print(f"  {name:10} {n}")

    if "--write" not in sys.argv:
        print("Dry run only. Add --write to load into DynamoDB.")
        return

    table = boto3.resource("dynamodb", region_name=REGION).Table(TABLE)
    with table.batch_writer() as batch:  # groups puts into batches of 25 and retries
        for item in items:
            batch.put_item(Item=item)
    print(f"Wrote {len(items)} items to {TABLE} in {REGION}.")


if __name__ == "__main__":
    main()
