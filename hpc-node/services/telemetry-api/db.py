"""
Database connection handling for telemetry-api.
Uses psycopg (v3) with a simple connection-per-request pattern for now —
fine at this project's scale; a connection pool (psycopg_pool) is the
natural upgrade if this ever needs to handle concurrent load.
"""

import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


def get_connection():
    """Returns a new database connection. Caller is responsible for closing it."""
    return psycopg.connect(DATABASE_URL)