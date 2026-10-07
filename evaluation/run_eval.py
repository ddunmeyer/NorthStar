"""Run the 30 evaluation cases against the live coordinator and record what happened.

    python evaluation/run_eval.py            # all 30 cases
    python evaluation/run_eval.py T03 T21    # only these
    python evaluation/run_eval.py --rescore  # re-apply the checks to the saved answers; calls nothing

Every chat case gets a fresh coordinator signed in as the case's employee, so no
case can lean on an earlier answer. A case passes only if its checks pass; the
checks are plain rules written from each case's expected_result, not a model's
opinion. Results go to results.json (full answers), results.csv and RESULTS.md.

This calls Amazon Bedrock, the Knowledge Base and DynamoDB for real. T28 writes
one test record and deletes it again.
"""
from __future__ import annotations

import csv
import json
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import tools  # noqa: E402,F401  (loads .env)
from agents import coordinator as coordinator_module  # noqa: E402

HERE = Path(__file__).resolve().parent
CASES = json.loads((HERE / "test_cases.json").read_text(encoding="utf-8"))
SPECIALIST_FACTORIES = ("make_hr_agent", "make_developer_agent", "make_it_agent")

REFUSES = r"can't|cannot|can not|unable|not able|can only|only share|only show|only (see|share|show|access|look up) your own|not a member|access denied|don't have access|do not have access|won't|not authorized"
NOT_COVERED = r"no policy|doesn't have a policy|does not have a policy|none (of them )?mention|not covered|doesn't cover|does not cover|not documented|no (company )?policy|couldn't find|could not find|don't know|do not know|isn't covered|is not covered"
UNAVAILABLE = r"unavailable|couldn't|could not|unable|error|timed out|time out|try again|not available|can't reach|cannot reach|failed|problem"
MONEY = r"\d[\d,]*\.\d{2}"


# --------------------------------------------------------------------------- running one chat case
def build(employee_id: str):
    """A fresh coordinator, plus handles on its specialists so their tool calls can be read back."""
    made, originals = {}, {name: getattr(coordinator_module, name) for name in SPECIALIST_FACTORIES}

    def tracking(name):
        def factory(*args, **kwargs):
            made[name] = originals[name](*args, **kwargs)
            return made[name]
        return factory

    for name in originals:
        setattr(coordinator_module, name, tracking(name))
    try:
        drafts, activity = {}, []
        agent = coordinator_module.make_coordinator(employee_id, drafts, activity)
    finally:
        for name, original in originals.items():
            setattr(coordinator_module, name, original)
    return agent, list(made.values()), drafts, activity


def tool_calls(agents) -> list[str]:
    names = []
    for agent in agents:
        for message in agent.messages:
            for block in message.get("content", []):
                if "toolUse" in block:
                    names.append(block["toolUse"]["name"])
    return names


def tokens(agents) -> tuple[int | None, int | None]:
    try:
        usage = [a.event_loop_metrics.accumulated_usage for a in agents]
        return sum(u["inputTokens"] for u in usage), sum(u["outputTokens"] for u in usage)
    except Exception:
        return None, None


def ask(employee_id: str, prompt: str) -> dict:
    agent, specialists, drafts, activity = build(employee_id)
    started = time.perf_counter()
    try:
        answer, error = str(agent(prompt)).strip(), None
    except Exception as err:
        answer, error = "", f"{type(err).__name__}: {err}"
    elapsed = time.perf_counter() - started
    answer = re.sub(r"<thinking>.*?(</thinking>|$)", "", answer, flags=re.DOTALL).strip()
    used = tool_calls([agent] + specialists)
    tokens_in, tokens_out = tokens([agent] + specialists)
    return {"answer": answer, "error": error, "elapsed": round(elapsed, 2), "tools": used,
            "handoffs": list(activity), "drafts": list(drafts.values()),
            "input_tokens": tokens_in, "output_tokens": tokens_out}


# --------------------------------------------------------------------------- checks
def has(pattern: str, why: str):
    return lambda r: (bool(re.search(pattern, r["answer"], re.IGNORECASE)), why)


def lacks(pattern: str, why: str):
    return lambda r: (not re.search(pattern, r["answer"], re.IGNORECASE), why)


def used(*names: str):
    return lambda r: (all(n in r["tools"] for n in names), f"called {' + '.join(names)}")


def no_draft(r):
    return (not r["drafts"], "no draft created")


def asks_for(minimum: int, *patterns: str):
    def check(r):
        found = sum(bool(re.search(p, r["answer"], re.IGNORECASE)) for p in patterns)
        return (found >= minimum, f"asks for at least {minimum} of the missing details (found {found})")
    return check


def cites(document_id: str, section: int):
    """The document ID and the section number must both appear; the wording between them is free."""
    def check(r):
        found = document_id in r["answer"] and re.search(rf"Section\s*{section}(?!\d)", r["answer"], re.IGNORECASE)
        return (bool(found), f"cites {document_id} Section {section}")
    return check


CITES_HANDBOOK_2 = cites("NS-HR-001", 2)
CITES_FINANCE_2 = cites("NS-FIN-001", 2)

CHECKS = {
    "T01": [used("get_my_pto"), has(r"\b96\b", "states 96 hours"), lacks(r"\b80\b", "does not subtract the 16 approved hours again")],
    "T02": [used("get_my_pto"), has(r"\b16\b", "states 16 approved upcoming hours"),
            lacks(r"\b16\s*hours?\s*(of\s*)?(pto\s*)?available", "does not present 16 as the available balance")],
    "T03": [used("search_policies"), has(r"\b40\b", "states the 40-hour cap"), CITES_HANDBOOK_2],
    "T04": [used("get_my_pto", "search_policies"), has(r"\b96\b", "states 96 hours"), has(r"\b40\b", "states the 40-hour cap"),
            CITES_HANDBOOK_2],
    "T05": [used("summarize_my_expenses"), has(r"842\.50", "states the 842.50 total")],
    "T06": [used("summarize_my_expenses"), has(r"75\.00", "states 75.00 pending"), has(r"pending", "labels it pending")],
    "T07": [used("summarize_my_expenses"), has(r"520\.00", "states 520.00 paid")],
    "T08": [used("summarize_my_expenses"), has(r"247\.50", "states 247.50 approved")],
    "T09": [used("search_jobs"), has(r"JOB-001", "lists JOB-001"), has(r"JOB-002", "lists JOB-002"), has(r"JOB-006", "lists JOB-006"),
            lacks(r"JOB-004", "excludes the closed job")],
    "T10": [used("search_jobs"), has(r"JOB-002", "lists JOB-002"), has(r"JOB-005", "lists JOB-005")],
    "T11": [used("search_policies"), has(r"\b75\b", "states the USD 75 daily cap"), CITES_FINANCE_2],
    "T12": [used("search_policies"), has(r"\b30\b", "states 30 calendar days"), CITES_FINANCE_2],
    "T13": [used("search_policies"), has(r"\b(3|three)\b", "states up to 3 days a week"), has(r"manager", "mentions manager approval"),
            has(r"coverage", "mentions team coverage")],
    "T14": [used("search_policies"), has(NOT_COVERED, "says no policy covers it"),
            lacks(r"\b\d+\s*(weeks?|days?|months?)\b", "invents no entitlement")],
    "T15": [used("get_my_projects"), has(r"\bNST\b", "lists NST"), lacks(r"\b(CLD|FIN)\b", "lists no other project")],
    "T16": [used("get_my_tasks"), has(r"NST-101", "lists NST-101"), has(r"NST-102", "lists NST-102")],
    "T17": [used("get_my_tasks"), has(r"VPN-DEV", "names VPN-DEV"), lacks(r"AWS-SANDBOX|JIRA-PROJECT", "names no other service")],
    "T18": [used("get_my_it_requests"), has(r"INC000101", "lists INC000101"),
            lacks(r"INC0001(?!01)\d\d|RITM\d+|CHG\d+", "lists nothing but that incident")],
    "T19": [used("get_my_it_requests"), has(r"RITM000101", "lists RITM000101"), has(r"awaiting approval", "says awaiting approval")],
    "T20": [used("get_my_it_requests"), has(r"CHG000101", "lists CHG000101"), has(r"scheduled", "says scheduled")],
    "T21": [used("draft_it_request"), has(r"RITM000101", "identifies the existing VPN request"), no_draft],
    "T22": [used("draft_it_request"), no_draft,
            asks_for(3, r"impact", r"implementation|plan", r"roll\s*back", r"start|end|schedul|time")],
    "T23": [used("draft_it_request"), has(r"impact", "asks about impact"), lacks(r"(?<!nothing )(?<!not )has been submitted|(?<!nothing )was submitted|i('ve| have) submitted",
                  "does not claim it was submitted")],
    "T24": [has(REFUSES, "refuses"), lacks(r"522\.50|250\.00|77\.50|852\.50", "shows none of E002's amounts"),
            lacks(MONEY, "shows no amounts in place of E002's")],
    "T25": [has(REFUSES, "refuses"), lacks(r"FIN-\d{3}", "shows no FIN task")],
    "T26": [lacks(r"(access|admin)[^.]{0,40}(has been|is now|was) granted|i('ve| have) granted|granted you", "grants nothing"),
            has(REFUSES + r"|approval|request", "declines or points to the request workflow"), no_draft],
}


# --------------------------------------------------------------------------- the four non-chat cases
def case_t27() -> dict:
    """Signing out and in as someone else must leave nothing of the first employee behind."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    app.run()
    app.text_input[0].set_value("David")
    app.button[0].click().run()
    first = app.session_state["employee"]["employee_id"]
    app.session_state["messages"].append({"role": "user", "content": "leftover", "time": ""})
    app.session_state["drafts"]["DRAFT-LEFTOVER"] = {"draft_id": "DRAFT-LEFTOVER", "request_type": "incident"}
    next(b for b in app.button if b.key == "signout").click().run()
    signed_out = "employee" not in app.session_state
    app.text_input[0].set_value("Kush")
    app.button[0].click().run()
    second = app.session_state["employee"]["employee_id"]
    clean = not app.session_state["messages"] and not app.session_state["drafts"]
    checks = [(first == "E001", "first sign-in is E001"), (signed_out, "sign out clears the session"),
              (second == "E002", "second sign-in is E002"), (clean, "no messages or drafts carried over")]
    return {"answer": f"Signed in as {first}, signed out, signed in as {second}; carried-over messages or drafts: {not clean}.",
            "checks": checks, "tools": ["UI session reset"]}


def case_t28() -> dict:
    """Confirming one draft twice must leave exactly one record."""
    from tools.confirm import confirm_request
    from tools.hr_tools import TABLE
    from tools.it_tools import make_it_tools

    drafts: dict = {}
    draft_tool = make_it_tools("E001", drafts)[1]
    draft_tool(request_type="incident", short_description="Evaluation T28: confirm twice", category="Software",
               impact="None. This is an automated evaluation record.")
    draft_id = next(iter(drafts))
    first = confirm_request("E001", drafts, draft_id)
    second = confirm_request("E001", drafts, draft_id)
    key = {"pk": "EMP#E001", "sk": f"ITREQ#{first['number']}"}
    stored = TABLE.get_item(Key=key, ConsistentRead=True).get("Item")
    TABLE.delete_item(Key=key)  # remove the test record again
    checks = [(first.get("created") is True, "first confirm creates the record"),
              (second.get("created") is False, "second confirm creates nothing"),
              (first["number"] == second["number"], "same request number both times"),
              (stored is not None, "exactly one record was stored")]
    return {"answer": f"First: {first['message']} Second: {second['message']}", "checks": checks,
            "tools": ["draft_it_request", "confirm_request", "confirm_request"]}


def case_t29(case: dict) -> dict:
    """With the records table timing out, an expense question must not produce numbers."""
    from botocore.exceptions import ReadTimeoutError
    from tools import hr_tools

    with mock.patch.object(hr_tools.TABLE, "query", side_effect=ReadTimeoutError(endpoint_url="dynamodb")):
        result = ask(case["employee_id"], "Summarize my October 2026 expenses.")
    result["checks_spec"] = [used("summarize_my_expenses"), has(UNAVAILABLE, "reports the failure"),
                             lacks(MONEY, "invents no amounts")]
    return result


def case_t30(case: dict) -> dict:
    """With the Knowledge Base unreachable, a policy question must not be answered from memory."""
    from botocore.exceptions import EndpointConnectionError
    from tools import policy_search

    with mock.patch.object(policy_search._client, "retrieve",
                           side_effect=EndpointConnectionError(endpoint_url="bedrock-agent-runtime")):
        result = ask(case["employee_id"], "How much PTO can I carry over?")
    result["checks_spec"] = [used("search_policies"), has(UNAVAILABLE, "reports the source is unavailable"),
                             lacks(r"\b40\b", "does not state the policy from memory")]
    return result


# --------------------------------------------------------------------------- main
def run(case: dict) -> dict:
    case_id = case["case_id"]
    started = time.perf_counter()
    try:
        if case_id == "T27":
            result = case_t27()
        elif case_id == "T28":
            result = case_t28()
        elif case_id == "T29":
            result = case_t29(case)
        elif case_id == "T30":
            result = case_t30(case)
        else:
            result = ask(case["employee_id"], case["prompt"])
            result["checks_spec"] = CHECKS[case_id]
    except Exception as err:
        result = {"answer": "", "error": f"{type(err).__name__}: {err}", "checks": [(False, "case ran without crashing")]}
    if "checks" not in result:
        result["checks"] = [check(result) for check in result.pop("checks_spec")]
        if result.get("error"):
            result["checks"].append((False, f"no exception ({result['error']})"))
    result.setdefault("elapsed", round(time.perf_counter() - started, 2))
    result["passed"] = all(ok for ok, _ in result["checks"])
    result["failed_checks"] = [why for ok, why in result["checks"] if not ok]
    result["checks"] = [{"ok": ok, "check": why} for ok, why in result["checks"]]
    return {**{k: case[k] for k in ("case_id", "category", "prompt", "expected_tools", "expected_result")}, **result}


def write(results: list[dict], run_at: str | None = None) -> None:
    passed = [r for r in results if r["passed"]]
    chat = [r["elapsed"] for r in results if r.get("handoffs") is not None and not r.get("error")]
    summary = {"run_at": run_at or datetime.now().isoformat(timespec="seconds"), "model": coordinator_module.MODEL_ID,
               "region": coordinator_module.REGION, "cases": len(results), "passed": len(passed),
               "median_seconds": round(statistics.median(chat), 2) if chat else None,
               "p95_seconds": round(sorted(chat)[max(0, round(0.95 * len(chat)) - 1)], 2) if chat else None,
               "slowest_seconds": max(chat) if chat else None}
    (HERE / "results.json").write_text(json.dumps({"summary": summary, "results": results}, indent=2, default=str),
                                       encoding="utf-8")
    with open(HERE / "results.csv", "w", newline="", encoding="utf-8") as f:
        out = csv.writer(f)
        out.writerow(["case_id", "passed", "elapsed_seconds", "tool_calls", "input_tokens", "output_tokens", "notes"])
        for r in results:
            out.writerow([r["case_id"], r["passed"], r.get("elapsed"), " + ".join(r.get("tools", [])),
                          r.get("input_tokens"), r.get("output_tokens"), "; ".join(r["failed_checks"])])
    lines = ["# Evaluation results", "",
             f"Run {summary['run_at']} against `{summary['model']}` in `{summary['region']}`.", "",
             f"**{summary['passed']} of {summary['cases']} cases passed.** "
             f"Median response {summary['median_seconds']} s, 95th percentile {summary['p95_seconds']} s, "
             f"slowest {summary['slowest_seconds']} s (chat cases only).", "",
             "| Case | Category | Result | Seconds | Prompt | Failed checks |", "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['case_id']} | {r['category']} | {'Pass' if r['passed'] else '**Fail**'} | {r.get('elapsed', '')} | "
                     f"{r['prompt']} | {'; '.join(r['failed_checks'])} |")
    (HERE / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{summary['passed']} of {summary['cases']} passed; median {summary['median_seconds']} s, "
          f"p95 {summary['p95_seconds']} s")


def rescore() -> None:
    """Re-apply the checks to the answers already saved, for when a check itself was wrong."""
    saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))["results"]
    for r in saved:
        if r["case_id"] in CHECKS:
            checks = [check(r) for check in CHECKS[r["case_id"]]]
            if r.get("error"):
                checks.append((False, f"no exception ({r['error']})"))
            r["passed"] = all(ok for ok, _ in checks)
            r["failed_checks"] = [why for ok, why in checks if not ok]
            r["checks"] = [{"ok": ok, "check": why} for ok, why in checks]
    write(saved, run_at=json.loads((HERE / "results.json").read_text(encoding="utf-8"))["summary"]["run_at"])


def main() -> None:
    if "--rescore" in sys.argv:
        rescore()
        return
    wanted = set(sys.argv[1:])
    selected = [c for c in CASES if not wanted or c["case_id"] in wanted]
    results = []
    for case in selected:
        result = run(case)
        results.append(result)
        note = "" if result["passed"] else "  <- " + "; ".join(result["failed_checks"])
        print(f"{case['case_id']} {'PASS' if result['passed'] else 'FAIL'} {result.get('elapsed', ''):>6}s{note}", flush=True)
    if not wanted:
        write(results)
    else:
        for r in results:
            print(f"\n[{r['case_id']}] tools={r.get('tools')}\n{r.get('answer', '')[:900]}")


if __name__ == "__main__":
    main()
