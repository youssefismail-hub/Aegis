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
@app.get("/api/v1/vehicles/{vehicle_id}/dtc")
def get_dtc(vehicle_id: str, active_only: bool = Query(True, description="If true, exclude cleared DTCs")):
    """
    Returns DTC (Diagnostic Trouble Code) history for a vehicle's devices.
    By default, only returns active (uncleared) codes — pass
    active_only=false to see the full history including cleared codes.
    """
    query = """
        SELECT e.code, e.description, e.severity, e.detected_at, e.cleared_at
        FROM dtc_events e
        JOIN devices d ON e.device_id = d.id
        WHERE d.vehicle_id = %s
    """
    params = [vehicle_id]

    if active_only:
        query += " AND e.cleared_at IS NULL"

    query += " ORDER BY e.detected_at DESC"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return {
        "vehicle_id": vehicle_id,
        "count": len(rows),
        "dtcs": [
            {
                "code": row[0],
                "description": row[1],
                "severity": row[2],
                "detected_at": row[3].isoformat(),
                "cleared_at": row[4].isoformat() if row[4] else None,
            }
            for row in rows
        ],
    }