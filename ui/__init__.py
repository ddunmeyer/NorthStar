"""Streamlit interface for North Star."""
import os
import time

from dotenv import load_dotenv

load_dotenv()  # read .env before any module looks up NORTHSTAR_* settings

# A cloud server runs on UTC. The company is in Chicago, so "today" and the times shown in
# chat follow Central time wherever the app is hosted. (Windows has no tzset and uses its own clock.)
if hasattr(time, "tzset"):
    os.environ["TZ"] = os.getenv("NORTHSTAR_TIMEZONE") or "America/Chicago"
    time.tzset()
