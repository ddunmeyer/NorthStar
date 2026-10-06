"""North Star: Streamlit entry point.

Run with:  streamlit run app.py

Owns the page and the session: first-name entry, the dashboard, the chat and
the Confirm step. The signed-in employee ID is set here and handed to the
agents; it never comes from anything the model says.
"""
import streamlit as st

from ui import assistant, data, theme, views

st.set_page_config(page_title="North Star", page_icon=theme.STAR_AVATAR, layout="wide",
                   initial_sidebar_state="expanded")
# The banner is full strength on the entry screen and Overview, dimmed behind the list pages.
dim = "employee" in st.session_state and st.session_state.get("page", "Overview") != "Overview"
st.markdown(theme.css(dim_banner=dim), unsafe_allow_html=True)

if "employee" not in st.session_state:
    views.entry()
    st.stop()

profile = st.session_state.employee
employee_id = profile["employee_id"]

# One conversation, one set of drafts and one agent per signed-in employee.
# Sign out clears the whole session, so nothing carries over to the next person.
st.session_state.setdefault("page", "Overview")
st.session_state.setdefault("messages", [])
st.session_state.setdefault("drafts", {})
st.session_state.setdefault("confirmed", {})
if "agent" not in st.session_state:
    st.session_state.agent, st.session_state.agent_mode = assistant.build_agent(employee_id, st.session_state.drafts)

views.sidebar(profile, st.session_state.agent_mode)

try:
    snap = data.snapshot(employee_id, data.current_month())
except Exception as err:
    st.error("North Star can't reach your records right now. Sign in with `aws login`, then reload.")
    st.caption(f"{type(err).__name__}: {err}")
    st.stop()

PAGES = {
    "Overview": views.overview,
    "Developer projects": views.developer,
    "IT & access": views.it_access,
    "Company knowledge": views.knowledge,
}
PAGES[st.session_state.page](profile, snap)
