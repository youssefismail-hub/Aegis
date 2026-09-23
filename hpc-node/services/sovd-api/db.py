"""
Database connection handling for sovd-api.
Same pattern as telemetry-api/db.py — both services share the same
TimescaleDB instance but remain independently deployable services.
"""

import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


def get_connection():
    return psycopg.connect(DATABASE_URL)