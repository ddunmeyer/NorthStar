"""North Star: Streamlit entry point.

Run with:  streamlit run app.py

Owns the page: first-name entry, dashboard tiles, chat, citations and the
Confirm step. Passes the signed-in employee ID to the coordinator agent.
"""
import streamlit as st

st.set_page_config(page_title="North Star", page_icon="✦", layout="wide")
st.title("North Star")
st.caption("Your workday. On course.")
st.info("Scaffold only. The chat experience is built in a later step.")
