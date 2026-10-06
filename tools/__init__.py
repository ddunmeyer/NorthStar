"""Tools the specialists call. Each one is scoped to the signed-in employee.

The employee ID is supplied by the application, never by the model.
"""

from dotenv import load_dotenv

load_dotenv()  # read .env so every tool sees the NORTHSTAR_* settings
