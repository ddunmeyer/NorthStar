"""The pages of North Star: entry, sidebar, overview chat and the three list pages."""
from __future__ import annotations

from datetime import date, datetime
from html import escape

import streamlit as st

from ui import assistant, data, theme

PAGES = [
    ("Overview", ":material/home:"),
    ("Developer projects", ":material/code:"),
    ("IT & access", ":material/laptop_mac:"),
    ("Company knowledge", ":material/menu_book:"),
]

ICONS = {
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "card": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20M16 15h2"/>',
    "check": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    "doc": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
    "user": '<circle cx="12" cy="8" r="4" fill="currentColor"/><path d="M4 21a8 8 0 0 1 16 0z" fill="currentColor"/>',
}

TONES = {
    "ok": {"approved", "fulfilled", "resolved", "completed", "done", "paid", "closed"},
    "warn": {"awaiting approval", "pending", "pending approval", "in review", "scheduled", "new"},
    "info": {"in progress", "open"},
    "bad": {"rejected", "blocked", "cancelled"},
}


def html(markup: str) -> None:
    """Render trusted, app-built markup. st.html strips inline SVG, so this goes through markdown."""
    st.markdown(markup, unsafe_allow_html=True)


def html_in(target, markup: str) -> None:
    target.markdown(markup, unsafe_allow_html=True)


def icon(name: str, size: int = 28) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def pill(text: str, tone: str | None = None) -> str:
    if tone is None:
        tone = next((t for t, words in TONES.items() if str(text).lower() in words), "")
    return f'<span class="ns-pill {tone}">{escape(str(text))}</span>'


def nice_date(value: str) -> str:
    try:
        d = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return str(value or "")
    stamp = f"{d:%a, %b} {d.day}"
    return f"{stamp}, {d:%I:%M %p}".replace(", 0", ", ") if "T" in str(value) else stamp


def clock() -> str:
    return datetime.now().strftime("%I:%M %p").lstrip("0")


def md_safe(text: str) -> str:
    """Streamlit reads $...$ as maths; amounts must stay as written."""
    return text.replace("$", "\\$")


# ------------------------------------------------------------------ entry
def entry() -> None:
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        html(
            '<div class="ns-entry">'
            f'<div class="ns-entry-brand"><div class="ns-emblem">{theme.star_svg(30)}</div>'
            '<div><div class="ns-wordmark">NORTH STAR</div><div class="ns-tagline">Your workday. On course.</div></div></div>'
            '<h1>Find your direction.</h1><p>Enter your first name to open your dashboard.</p></div>'
        )
        with st.form("entry", border=False):
            name = st.text_input("Username", placeholder="Your first name")
            submitted = st.form_submit_button("Enter North Star", use_container_width=True)
        if submitted:
            try:
                profile = data.find_employee(name)
            except Exception as err:
                st.error("North Star can't reach AWS right now. Sign in with `aws login` and try again.")
                st.caption(f"{type(err).__name__}: {err}")
                return
            if profile:
                st.session_state.clear()
                st.session_state.employee = profile
                st.rerun()
            st.error("That first name isn't recognized. Check the spelling and try again.")
        html('<div class="ns-foot" style="text-align:center">Classroom demo &middot; All records are fictional &middot; '
                'First-name entry is not secure sign-in</div>')


# ---------------------------------------------------------------- sidebar
def sidebar(profile: dict, mode: str) -> None:
    with st.sidebar:
        html(
            f'<div class="ns-brand"><div class="ns-emblem">{theme.star_svg(30)}</div>'
            '<div><div class="ns-wordmark">NORTH STAR</div><div class="ns-tagline">Your workday. On course.</div></div></div>'
            f'<div class="ns-profile"><div class="ns-avatar">{icon("user", 26)}</div>'
            f'<div><div class="ns-profile-name">{escape(profile["name"])}</div>'
            f'<div class="ns-profile-meta">{escape(profile.get("department", ""))}</div></div></div>'
        )
        for label, material in PAGES:
            active = st.session_state.page == label
            if st.button(label, icon=material, key=f"nav_{label}", type="primary" if active else "secondary",
                         use_container_width=True) and not active:
                st.session_state.page = label
                st.rerun()
        if st.button("Sign out", icon=":material/logout:", key="signout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        if mode == "coordinator":
            status = '<span class="ns-dot"></span>Coordinator and specialists online'
        else:
            status = '<span class="ns-dot warn"></span>Specialist tools online &middot; coordinator pending'
        html(f'<div class="ns-side-note">{status}<br>{escape(assistant.MODEL_ID)} &middot; {escape(assistant.REGION)}</div>')


# ----------------------------------------------------------------- drafts
DRAFT_LABELS = [
    ("service_id", "Service"), ("short_description", "Summary"), ("category", "Category"),
    ("business_justification", "Business reason"), ("start_date", "Start"), ("end_date", "End"),
    ("impact", "Impact"), ("implementation_plan", "Implementation"), ("rollback_plan", "Rollback"),
    ("scheduled_start", "Scheduled start"), ("scheduled_end", "Scheduled end"),
]


def _confirm_function():
    """tools.confirm.confirm_request(employee_id, drafts, draft_id) -> {"ok", "number", ...}."""
    try:
        from tools import confirm
        return getattr(confirm, "confirm_request", None)
    except Exception:
        return None


def draft_card(draft_id: str, where: str) -> None:
    done = st.session_state.confirmed.get(draft_id)
    draft = done["draft"] if done else st.session_state.drafts.get(draft_id)
    if not draft:
        return
    rows = "".join(f"<dt>{label}</dt><dd>{escape(nice_date(draft[key]) if 'date' in key or 'scheduled' in key else str(draft[key]))}</dd>"
                   for key, label in DRAFT_LABELS if draft.get(key))
    if draft.get("approval_required"):
        rows += "<dt>Approval</dt><dd>Manager approval required after submission</dd>"
    state = pill(f"Submitted as {done['number']}", "ok") if done else pill("Draft · not submitted", "warn")
    html(f'<div class="ns-draft"><div class="ns-draft-head">{icon("doc", 22)}'
            f'{escape(draft["request_type"].title())} request {state}</div><dl>{rows}</dl></div>')
    if done:
        return
    confirm = _confirm_function()
    with st.container(key=f"draftbar_{where}_{draft_id}"):
        left, right, _ = st.columns([1.3, 1, 2])
        if left.button("Confirm request", key=f"confirm_{where}_{draft_id}", type="primary", disabled=confirm is None,
                       help=None if confirm else "The Confirm step (tools/confirm.py) isn't built yet.",
                       use_container_width=True):
            try:
                result = confirm(st.session_state.employee["employee_id"], st.session_state.drafts, draft_id)
            except Exception as err:
                st.error(f"The request was not submitted. {type(err).__name__}: {err}")
                return
            if not result.get("ok"):
                st.error(result.get("error", "The request was not submitted."))
                return
            st.session_state.confirmed[draft_id] = {"number": result["number"], "draft": draft}
            st.session_state.drafts.pop(draft_id, None)
            data.snapshot.clear()
            st.rerun()
        if right.button("Discard", key=f"discard_{where}_{draft_id}", use_container_width=True):
            st.session_state.drafts.pop(draft_id, None)
            st.rerun()


# --------------------------------------------------------------- overview
def _tile(key: str, icon_name: str, label: str, value: str, unit: str, foot: str, action: str) -> bool:
    with st.container(key=f"tile_{key}"):
        html(
            f'<div class="ns-tile"><div class="ns-tile-icon">{icon(icon_name)}</div><div>'
            f'<div class="ns-tile-label">{escape(label)}</div>'
            f'<div class="ns-tile-value">{escape(value)}<small>{escape(unit)}</small></div>'
            f'<div class="ns-tile-foot">{escape(foot)}</div></div><div class="ns-chevron">&rsaquo;</div></div>'
        )
        return st.button(action, key=f"tilebtn_{key}")


def _user_message(msg: dict) -> None:
    html(f'<div class="ns-user"><div class="ns-user-bubble">{escape(msg["content"])}</div>'
            f'<div class="ns-user-avatar">{icon("user", 22)}</div></div>'
            f'<div class="ns-time ns-user-time">{msg["time"]}</div>')


def _sources_html(sources: list[dict]) -> str:
    chips = []
    for s in sources:
        title = s.get("title") or s.get("document_id") or "Policy"
        section = s.get("section")
        name = f"{title} · Section {section}" if section else title
        if s.get("section_title"):
            name += f": {s['section_title']}"
        chips.append(f'<div class="ns-source">{icon("doc", 20)}<span>{escape(str(name))}</span>'
                     f'<small>{escape(str(s.get("document_id", "")))}</small></div>')
    return f'<div class="ns-sources">{"".join(chips)}</div>' if chips else ""


def _assistant_message(msg: dict, index: int) -> None:
    with st.chat_message("assistant", avatar=theme.STAR_AVATAR):
        html('<div class="ns-from">NORTH STAR</div>')
        st.markdown(md_safe(msg["content"]))
        if msg.get("sources"):
            html(_sources_html(msg["sources"]))
    if msg.get("error"):
        lead = '<span class="ns-check bad">!</span>Request failed &middot; no data shown'
    elif msg.get("steps"):
        lead = '<span class="ns-check">&#10003;</span>Used ' + "".join(
            f'<span class="ns-step">{escape(s)}</span>' for s in msg["steps"])
        if msg.get("sources"):
            lead += "<span>Policy cited</span>"
    else:
        lead = '<span class="ns-check">&#10003;</span>Answered without a record lookup'
    html(f'<div class="ns-activity">{lead}<span>&middot; {msg.get("elapsed", 0):.1f} s</span>'
            f'<span class="ns-time">{msg["time"]}</span></div>')
    if msg.get("error"):
        with st.expander("Technical detail"):
            st.code(msg["error"])
    elif msg.get("handoffs"):
        count = len(msg["handoffs"])
        with st.expander(f"How North Star answered · {count} hand-off{'s' if count != 1 else ''}"):
            for step, line in enumerate(msg["handoffs"], start=1):
                who, _, request = line.partition(": ")
                html(f'<div class="ns-handoff"><span class="ns-step">{step}</span><b>{escape(who)}</b>'
                     f'<span>{escape(request)}</span></div>')
    for draft_id in msg.get("draft_ids", []):
        draft_card(draft_id, f"chat{index}")


def overview(profile: dict, snap: dict) -> None:
    month_name = date.today().strftime("%B")
    month_long = date.today().strftime("%B %Y")
    html(f'<div class="ns-hero"><h1>Welcome back, {escape(profile["name"])}.</h1>'
            '<p>Everything you need. One clear direction.</p></div>')

    prompt = st.session_state.pop("queued", None)
    pto = snap["pto"]
    open_tasks = [t for t in snap["tasks"] if str(t.get("status", "")).lower() != "done"]
    c1, c2, c3 = st.columns(3)
    with c1:
        if _tile("pto", "calendar", "Available PTO", str(pto.get("available_hours", "0")), "hours",
                 f'{pto.get("approved_upcoming_hours", 0)} upcoming hours already counted', "Ask about my PTO"):
            prompt = "How much PTO do I have, and what can I carry over?"
    with c2:
        pending = sum(int(x["amount_cents"]) for x in snap["expenses"] if x.get("status") == "pending")
        if _tile("exp", "card", f"{month_name} expenses", "$" + data.money(snap["expense_total_cents"]), "",
                 f'{len(snap["expenses"])} reports · ${data.money(pending)} pending', "Summarize my expenses"):
            prompt = f"Summarize my {month_long} expenses."
    with c3:
        need = sorted({t["required_service_id"] for t in open_tasks if t.get("required_service_id")})
        if _tile("tasks", "check", "Assigned tasks", str(len(open_tasks)), "",
                 ("Needs " + ", ".join(need)) if need else "No access needed", "Show my tasks"):
            prompt = "Show my Jira tasks and help me get the access I need."

    quick = [
        ("pto", "My PTO balance", ":material/calendar_month:", "How much PTO do I have?"),
        ("exp", "Expense summary", ":material/bar_chart:", f"Summarize my {month_long} expenses."),
        ("jobs", "Open roles", ":material/group:", "What roles are open right now?"),
        ("it", "Track my IT requests", ":material/confirmation_number:", "What's the status of my IT requests?"),
    ]
    for col, (key, label, material, text) in zip(st.columns(4), quick):
        if col.button(label, icon=material, key=f"quick_{key}", use_container_width=True):
            prompt = text

    with st.container(key="chat_panel"):
        box = st.container(height=440, key="chat_scroll", border=False)
        typed = st.chat_input("Ask North Star about your workday...")
    prompt = typed or prompt

    with box:
        if not st.session_state.messages and not prompt:
            html(f'<div class="ns-empty">{theme.star_svg(44)}<h3>Where would you like to start?</h3>'
                    'Ask about your time off, expenses, tasks or IT requests. '
                    'North Star checks your records and shows where each answer came from.</div>')
        for index, msg in enumerate(st.session_state.messages):
            (_user_message if msg["role"] == "user" else _assistant_message)(*([msg] if msg["role"] == "user" else [msg, index]))
        if prompt:
            _run_turn(prompt)
    html('<div class="ns-foot">Classroom demo &middot; All records are fictional.</div>')


def _run_turn(prompt: str) -> None:
    user = {"role": "user", "content": prompt, "time": clock()}
    st.session_state.messages.append(user)
    _user_message(user)
    reply = assistant.Reply(text="")
    with st.chat_message("assistant", avatar=theme.STAR_AVATAR):
        html('<div class="ns-from">NORTH STAR</div>')
        slot = st.empty()
        html_in(slot, '<div class="ns-working"><span class="ns-pulse"></span>Charting your course</div>')
        for kind, value in assistant.ask(st.session_state.agent, prompt, st.session_state.drafts,
                                         st.session_state.activity, data.policies()):
            if kind == "working":
                html_in(slot, f'<div class="ns-working"><span class="ns-pulse"></span>{escape(str(value))}</div>')
            elif kind == "text":
                slot.markdown(md_safe(str(value)))
            else:
                reply = value
    st.session_state.messages.append({
        "role": "assistant", "content": reply.text, "time": clock(), "steps": reply.steps,
        "sources": reply.sources, "draft_ids": reply.draft_ids, "elapsed": reply.elapsed, "error": reply.error, "handoffs": reply.handoffs,
    })
    st.rerun()


def _ask_from_page(label: str, prompt: str, key: str) -> None:
    if st.button(label, icon=":material/auto_awesome:", key=key):
        st.session_state.page = "Overview"
        st.session_state.queued = prompt
        st.rerun()


# ------------------------------------------------------------- list pages
def developer(profile: dict, snap: dict) -> None:
    html('<h1 class="ns-page-title">Developer projects</h1>'
            '<p class="ns-page-sub">The projects you belong to and the work assigned to you.</p>')
    if not snap["projects"]:
        st.info("You aren't a member of any project in this snapshot.")
        return
    for col, project in zip(st.columns(max(len(snap["projects"]), 3)), snap["projects"]):
        mine = [t for t in snap["tasks"] if t["project_key"] == project["project_key"]]
        sprint = next((s for s in snap["sprints"].values()
                       if s["project_key"] == project["project_key"] and s.get("state") == "active"), None)
        sprint_line = f'{escape(sprint["name"])} · ends {nice_date(sprint["end_date"])}' if sprint else "No active sprint"
        html_in(col, f'<div class="ns-card"><span class="ns-key">{escape(project["project_key"])}</span>'
                 f'<h4>{escape(project["name"])}</h4><div class="ns-muted">{sprint_line}</div>'
                 f'<div class="ns-muted">{len(mine)} assigned to you · {len(project.get("member_employee_ids", []))} members</div></div>')

    html('<div class="ns-section">Assigned to you</div>')
    if not snap["tasks"]:
        st.info("Nothing is assigned to you right now.")
    for task in snap["tasks"]:
        meta = [f'{escape(task.get("priority", ""))} priority', f'due {nice_date(task.get("due_date", ""))}']
        done = str(task.get("status", "")).lower() == "done"
        if not done and task.get("due_date", "9999") < date.today().isoformat():
            meta[1] = f'<span style="color:var(--ns-bad)">overdue since {nice_date(task["due_date"])}</span>'
        access = ""
        if task.get("required_service_id"):
            label, tone = data.access_state(snap, task["required_service_id"])
            access = pill(f'{task["required_service_id"]} · {label}', tone)
        html(f'<div class="ns-row"><span class="ns-key">{escape(task["issue_key"])}</span>'
                f'<div><div class="ns-row-title">{escape(task["summary"])}</div>'
                f'<div class="ns-row-meta">{" · ".join(meta)}</div></div>'
                f'<div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end">{access}{pill(task.get("status", ""))}</div></div>')
    _ask_from_page("Ask North Star about the access I need",
                   "Show my Jira tasks and help me get the access I need.", "ask_dev")


def it_access(profile: dict, snap: dict) -> None:
    html('<h1 class="ns-page-title">IT &amp; access</h1>'
            '<p class="ns-page-sub">Your incidents, access requests and changes. New requests are drafted in chat and submitted only when you confirm.</p>')
    if st.session_state.drafts:
        html('<div class="ns-section">Drafts waiting for you</div>')
        for draft_id in list(st.session_state.drafts):
            draft_card(draft_id, "it")

    groups = [("access", "Access"), ("incident", "Incidents"), ("change", "Changes")]
    by_type = {kind: [r for r in snap["it_requests"] if r.get("request_type") == kind] for kind, _ in groups}
    for tab, (kind, label) in zip(st.tabs([f"{label} ({len(by_type[kind])})" for kind, label in groups]), groups):
        with tab:
            if not by_type[kind]:
                st.info(f"No {label.lower()} on record.")
            for r in by_type[kind]:
                meta = [f'opened {nice_date(r.get("created_date", ""))}']
                if r.get("service_id"):
                    meta.insert(0, escape(snap["services"].get(r["service_id"], {}).get("name", r["service_id"])))
                if r.get("start_date"):
                    meta.append(f'{nice_date(r["start_date"])} to {nice_date(r.get("end_date", ""))}')
                if r.get("scheduled_start"):
                    meta.append(f'scheduled {nice_date(r["scheduled_start"])}')
                if r.get("category"):
                    meta.append(escape(str(r["category"])))
                html(f'<div class="ns-row"><span class="ns-key">{escape(r["number"])}</span>'
                        f'<div><div class="ns-row-title">{escape(r.get("short_description", ""))}</div>'
                        f'<div class="ns-row-meta">{" · ".join(meta)}</div></div>{pill(r.get("status", ""))}</div>')
    _ask_from_page("Ask North Star to draft a request", "I need to request access. What can I request?", "ask_it")


def knowledge(profile: dict, snap: dict) -> None:
    html('<h1 class="ns-page-title">Company knowledge</h1>'
            '<p class="ns-page-sub">The six policy documents North Star answers from. All content is fictional.</p>')
    query = st.text_input("Search policies", placeholder="Try carryover, hotel, VPN or rollback",
                          label_visibility="collapsed").strip().lower()
    docs = [d for d in data.policies() if not query or query in d["title"].lower() or query in d["body"].lower()]
    if not docs:
        st.info("No policy mentions that. North Star will say so too, and won't guess.")
    for doc in docs:
        with st.expander(f'{doc["document_id"]}  ·  {doc["title"]}', expanded=bool(query)):
            html(f'<div class="ns-muted">Owner: {escape(doc["owner"])} &middot; Effective {nice_date(doc["effective_date"])} '
                    f'&middot; Version {escape(str(doc["version"]))}</div>')
            st.markdown(md_safe(doc["body"]))
