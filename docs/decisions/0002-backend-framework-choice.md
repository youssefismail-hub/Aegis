# 0002. Telemetry/SOVD API framework: FastAPI

**Status:** Accepted

**Date:** 2026-09-15

## Context

The HPC node needs to host two independent REST/WebSocket services
(telemetry-api and sovd-api, per project spec Sections 7 and 2b). Both
need JSON APIs, JWT auth, and a WebSocket endpoint for live telemetry
push. Framework choice needed to balance: development speed, portfolio
value (auto-generated docs are a concrete, visible deliverable), and fit
with the rest of the stack (Python is already used for DBC tooling via
`cantools`, so staying in one language across HPC-node services reduces
context-switching).

## Options considered

- **FastAPI (Python)** — async by default, built-in Pydantic request/response
  validation, auto-generates interactive OpenAPI/Swagger docs at `/docs`
  with zero extra work. Same language as the DBC tooling already planned.
- **Express (Node.js)** — mature, huge ecosystem, but no built-in schema
  validation or API docs generation without adding extra libraries
  (e.g. Zod + swagger-jsdoc), meaning more manual setup for the same
  end result.
- **Flask (Python)** — simpler than FastAPI but no async support or
  built-in validation/docs out of the box; would need the same extra
  libraries as Express to reach FastAPI's baseline.

## Decision

Use FastAPI for both telemetry-api and sovd-api.

## Consequences

- Gains: auto-generated interactive API docs (`/docs`) with no extra
  work — a genuinely clickable portfolio artifact for free. Built-in
  request/response validation via Pydantic catches malformed requests
  before they reach business logic. Native async support matters once
  the WebSocket live-telemetry endpoint is built. Same language (Python)
  as the DBC decode tooling, reducing context-switching.
- Gives up: Node's larger general ecosystem — not a real loss here since
  nothing HPC-node-specific needs a Node-only library.
- Revisit if: a specific library only exists in the Node ecosystem and
  becomes a hard requirement later.