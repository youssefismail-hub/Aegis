"""
telemetry-api — the fleet/telemetry REST + WebSocket API.
See project spec Section 7 and docs/decisions/0002-backend-framework-choice.md
and docs/decisions/0003-database-choice.md for why this stack was chosen.
"""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from db import get_connection

app = FastAPI(
    title="AEGIS Telemetry API",
    description="Fleet/telemetry REST + WebSocket API for the AEGIS HPC node.",
    version="0.2.0",
)


@app.get("/health")
def health_check():
    """Basic liveness check — confirms the service is up and responding."""
    return {"status": "ok", "service": "telemetry-api"}


@app.get("/api/v1/vehicles/{vehicle_id}/telemetry")
def get_telemetry(
    vehicle_id: str,
    start: Optional[datetime] = Query(None, description="ISO 8601 start time"),
    end: Optional[datetime] = Query(None, description="ISO 8601 end time"),
    pids: Optional[str] = Query(None, description="Comma-separated PID names, e.g. rpm,speed"),
):
    """
    Returns telemetry rows for a vehicle's devices within a time range,
    optionally filtered to specific PIDs.
    """
    pid_list = pids.split(",") if pids else None

    query = """
        SELECT t.time, t.pid, t.value
        FROM telemetry t
        JOIN devices d ON t.device_id = d.id
        WHERE d.vehicle_id = %s
    """
    params = [vehicle_id]

    if start:
        query += " AND t.time >= %s"
        params.append(start)
    if end:
        query += " AND t.time <= %s"
        params.append(end)
    if pid_list:
        query += " AND t.pid = ANY(%s)"
        params.append(pid_list)

    query += " ORDER BY t.time ASC"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return {
        "vehicle_id": vehicle_id,
        "count": len(rows),
        "telemetry": [
            {"time": row[0].isoformat(), "pid": row[1], "value": row[2]}
            for row in rows
        ],
    }