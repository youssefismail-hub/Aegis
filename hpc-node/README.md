# HPC Node

Runs the software-centric services: telemetry/fleet API, SOVD-style
diagnostics API, OTA agent (simulation stage), and the MQTT connectivity
bridge. See ../docs/architecture.md for the full system picture.

## Quick start (one command)

```bash
cd hpc-node
docker compose up --build
```

Brings up: TimescaleDB (with your schema applied on first run),
Mosquitto, telemetry-api (:8000), sovd-api (:8001), and the MQTT-to-DB
subscriber — all networked together automatically.

Verify:
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

## Services

| Service | Port | Purpose |
|---|---|---|
| telemetry-api | 8000 | Fleet/telemetry REST API (spec Section 7) |
| sovd-api | 8001 | SOVD-inspired diagnostics API (spec Section 2b) |
| connectivity-subscriber | — (internal) | MQTT -> TimescaleDB bridge |
| db | 5432 | TimescaleDB |
| mqtt | 1883 | Mosquitto (local dev broker, see ADR 0005) |

## Simulating a device

The connectivity service's `publisher.py` isn't part of the compose
stack — it represents what a real device would do, so it's run
separately, from outside the stack, exactly as a real device publishing
in from the vehicle would be:

```bash
cd services/connectivity
source venv/bin/activate
python3 publisher.py
```

## ota-agent

Not containerized — it's a local-only state-machine simulation, not a
real service. See `services/ota-agent/README.md`.
