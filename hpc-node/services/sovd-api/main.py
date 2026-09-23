"""
sovd-api — SOVD-inspired (Service-Oriented Vehicle Diagnostics) REST layer.
See docs/decisions/0004-sovd-diagnostics-approach.md for why this exists
as a separate service from telemetry-api.

Endpoint shape follows SOVD's component-based pattern:
  /components/{component}/data-items
  /components/{component}/faults

Kept minimal and explicitly not standards-compliant — see the ADR.
"""

from fastapi import FastAPI

from db import get_connection

app = FastAPI(
    title="AEGIS SOVD-Inspired Diagnostics API",
    description="Service-Oriented Vehicle Diagnostics-style REST layer, simplified/inspired-by, not standards-compliant.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "sovd-api"}