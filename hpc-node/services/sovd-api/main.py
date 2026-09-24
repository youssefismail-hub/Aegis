"""
sovd-api — SOVD-inspired (Service-Oriented Vehicle Diagnostics) REST layer.
See docs/decisions/0004-sovd-diagnostics-approach.md.
"""

from fastapi import FastAPI

from db import get_connection

app = FastAPI(
    title="AEGIS SOVD-Inspired Diagnostics API",
    description="Service-Oriented Vehicle Diagnostics-style REST layer, simplified/inspired-by, not standards-compliant.",
    version="0.2.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "sovd-api"}


@app.get("/components/{component}/data-items")
def get_data_items(component: str, vehicle_id: str):
    """
    Returns the most recent value per PID for a vehicle — a live
    "current state" snapshot, not a time range (that's telemetry-api's
    job). `component` is currently informational (e.g. "engine") since
    this project only models one component; it's part of the endpoint
    shape so the API is structurally ready for multiple components later
    without a breaking change.
    """
    query = """
        SELECT DISTINCT ON (t.pid) t.pid, t.value, t.time
        FROM telemetry t
        JOIN devices d ON t.device_id = d.id
        WHERE d.vehicle_id = %s
        ORDER BY t.pid, t.time DESC
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, [vehicle_id])
            rows = cur.fetchall()

    return {
        "component": component,
        "vehicle_id": vehicle_id,
        "data_items": [
            {"pid": row[0], "value": row[1], "last_updated": row[2].isoformat()}
            for row in rows
        ],
    }


@app.get("/components/{component}/faults")
def get_faults(component: str, vehicle_id: str, active_only: bool = True):
    """
    Returns DTCs for a vehicle, SOVD-shaped. Deliberately similar to
    telemetry-api's /dtc endpoint but under the diagnostics-service's
    own URL structure and response shape — these are two independent
    API surfaces by design (see ADR 0004), not one endpoint duplicated.
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
        "component": component,
        "vehicle_id": vehicle_id,
        "faults": [
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