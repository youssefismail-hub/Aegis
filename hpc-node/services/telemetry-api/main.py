"""
telemetry-api — the fleet/telemetry REST + WebSocket API.
See project spec Section 7 and docs/decisions/0002-backend-framework-choice.md
for why FastAPI was chosen.

This is currently a scaffold: a real, runnable app with a health check.
Real endpoints (telemetry query, DTC, trips, live WebSocket) get added
incrementally from here.
"""

from fastapi import FastAPI

app = FastAPI(
    title="AEGIS Telemetry API",
    description="Fleet/telemetry REST + WebSocket API for the AEGIS HPC node.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Basic liveness check — confirms the service is up and responding."""
    return {"status": "ok", "service": "telemetry-api"}