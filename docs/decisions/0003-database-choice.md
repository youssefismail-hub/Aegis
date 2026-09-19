# 0003. Telemetry storage: PostgreSQL + TimescaleDB (single database)

**Status:** Accepted

**Date:** 2026-09-17

## Context

Telemetry data (RPM, speed, coolant temp, etc.) is fundamentally
time-series: high write volume, queries mostly scoped by time range.
Relational data (vehicles, devices, DTC events) is a better fit for a
normal relational schema with foreign keys and constraints. A common
pattern at fleet scale splits these into two separate database systems
(e.g. InfluxDB for time-series + PostgreSQL for relational data).

## Options considered

- **Separate InfluxDB + PostgreSQL** — each system optimized for its own
  workload, but means running, backing up, and securing two different
  database engines, two connection pools, two sets of ops knowledge, for
  a solo project with a single device.
- **PostgreSQL + TimescaleDB extension** — TimescaleDB adds automatic
  time-based partitioning ("hypertables"), compression, and continuous
  aggregates on top of regular PostgreSQL. One database engine, one
  connection pool, standard SQL throughout, and telemetry-api only needs
  one client library.
- **Plain PostgreSQL, no extension** — simplest option, but large time
  range queries over millions of rows would need hand-rolled
  partitioning to stay fast, which TimescaleDB gives for free.

## Decision

Use PostgreSQL with the TimescaleDB extension, in one database, for both
relational and time-series data.

## Consequences

- Gains: one system to run/back up/secure instead of two; standard SQL
  everywhere including for the telemetry table; automatic hypertable
  partitioning gives real time-series query performance without
  reinventing it; foreign keys can reference across "relational" and
  "time-series" tables directly (e.g. telemetry.device_id -> devices.id),
  which is awkward or impossible across two separate database systems.
- Gives up: some of InfluxDB's time-series-specific query language
  conveniences — not a real loss, since TimescaleDB's SQL-based approach
  is arguably more transferable knowledge (most engineering teams already
  know SQL).
- Revisit if: telemetry write volume grows far beyond what a single
  Postgres instance can handle (i.e. real fleet scale, not a
  single-device project) — at that point, the ingestion pipeline
  (Kafka/ClickHouse) named in the project spec's scaling section becomes
  the actual next step, not a database swap.