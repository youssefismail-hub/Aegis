# Architecture Overview

## 1. System Diagram

```text
┌─────────────────────────────────────────────────────────────────────┐
│                            VEHICLE                                 │
│                 OBD-II Port — ISO 15765-4 CAN                     │
│                           500 kbps                                  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ CAN
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ZONE CONTROLLER                                 │
│                    Real-Time Domain                                │
│                                                                     │
│  Target: STM32G431KB + TJA1051T/3 (ADR 0001)                     │
│  Status: SIL-validated in software; real hardware pending          │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ CAN HAL — hal/can_hal.h                                       │  │
│  │              │                                                │  │
│  │              ▼                                                │  │
│  │ PID Decode / DTC Decode — pid_decode.c                        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Validation: 10/10 unit tests passing against known-good values    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ Planned:
                                │ authenticated UART/SPI
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         HPC NODE                                   │
│                    Software-Centric Domain                         │
│                                                                     │
│  Target: Raspberry Pi CM4 (stand-in — see Section 5)              │
│                                                                     │
│  ┌──────────────────────┐       ┌──────────────────────┐           │
│  │   telemetry-api      │       │      sovd-api        │           │
│  │      FastAPI         │       │       FastAPI        │           │
│  │      :8000           │       │       :8001           │           │
│  │                      │       │                      │           │
│  │ GET /telemetry       │       │ GET /data-items      │           │
│  │ GET /dtc             │       │ GET /faults          │           │
│  │                      │       │ POST /faults/clear   │           │
│  │                      │       │       (JWT)           │           │
│  └──────────┬───────────┘       └──────────┬───────────┘           │
│             │                              │                       │
│             └──────────────┬───────────────┘                       │
│                            ▼                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                         TimescaleDB                            │  │
│  │                                                               │  │
│  │  vehicles │ devices │ telemetry │ dtc_events                  │  │
│  │                         ADR 0003                               │  │
│  └───────────────────────────▲───────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────┴───────────────────────────────────┐  │
│  │ connectivity/subscriber.py                                   │  │
│  │ MQTT → DB bridge                                             │  │
│  └───────────────────────────▲───────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────┴───────────────────────────────────┐  │
│  │ connectivity/publisher.py                                    │  │
│  │ Device → MQTT                                                │  │
│  └───────────────────────────▲───────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────┴───────────────────────────────────┐  │
│  │                    Mosquitto                                 │  │
│  │                    Local :1883                               │  │
│  │                    ADR 0005                                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ ota-agent                                                     │  │
│  │ Deploy / Commit / Rollback State Machine                      │  │
│  │ Status: SIMULATED                                             │  │
│  │                                                               │  │
│  │ Real A/B partitions via Mender planned once hardware exists   │  │
│  │ ADR 0006                                                       │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ Planned:
                                │ TLS + certificate authentication
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS IoT Core                               │
│                            Planned                                │
└─────────────────────────────────────────────────────────────────────┘
```

> **Legend**
>
> * **Implemented:** verified in the current software/SIL environment.
> * **Simulated:** behavior is implemented and tested, but real hardware/infrastructure is not yet integrated.
> * **Planned:** architectural target, not currently implemented.

---

## 2. Why the Zone Controller / HPC Split?

The architecture deliberately separates the **real-time CAN domain** from the **software-centric HPC domain**.

The Zone Controller has a deliberately narrow responsibility:

* Read CAN frames correctly.
* Decode supported OBD-II data.
* Avoid unintended writes to the CAN bus.
* Remain small, deterministic, and easy to validate.

The HPC node handles the components with higher complexity and faster iteration cycles:

* REST APIs
* Database access
* MQTT connectivity
* Telemetry processing
* SOVD services
* OTA orchestration
* Future cellular/cloud connectivity

This separation creates distinct failure domains. A failure in a Linux service, database, API, MQTT broker, or OTA component should not directly compromise the CAN-reading path.

The project therefore follows a **zonal + HPC architectural pattern**, with the hardware boundary reinforcing the software separation.

### Repository-level isolation

The intended dependency direction is:

```text
zone-controller-firmware/
        │
        │  Planned authenticated link
        ▼
hpc-node/
```

The two domains remain independently buildable:

* `zone-controller-firmware/` does **not** import or depend on `hpc-node/`.
* `hpc-node/` does **not** depend on Zone Controller implementation details.
* The planned integration point is a single authenticated communication interface.

---

## 3. Data Flow — Implemented and Verified

### 3.1 CAN frame acquisition and decoding

The Zone Controller reads a CAN frame and decodes either:

* **Mode 01** — OBD-II live data / PID response
* **Mode 03** — Stored Diagnostic Trouble Codes (DTCs)

The decoder has been validated with:

* **10/10 unit tests passing**
* Known-good CAN byte sequences
* SIL testing using a virtual CAN interface (`vcan0`)

```text
CAN Frame
   │
   ▼
CAN HAL
   │
   ▼
PID / DTC Decoder
   │
   ▼
Decoded Vehicle Data
```

### 3.2 Telemetry publication

> **Current status:** simulated through `publisher.py`; real Zone Controller → HPC integration is pending.

A decoded reading is represented as JSON and published to:

```text
devices/{device_id}/telemetry
```

using MQTT with:

```text
QoS 1
```

### 3.3 MQTT → Database

`subscriber.py` receives the MQTT message and:

1. Reads the device identifier (`device_uid`).
2. Resolves the corresponding device UUID.
3. Inserts the telemetry record into the TimescaleDB `telemetry` hypertable.

This path has been verified end-to-end with real published values, including:

```text
RPM:           1726
Vehicle speed: 62
Coolant temp:  91
```

The values were correctly persisted in the database.

### 3.4 API → Database

The two FastAPI services independently query the same database:

#### `telemetry-api`

Provides time-range telemetry history.

```text
GET /telemetry
```

#### `sovd-api`

Provides latest-value snapshots and fault information.

Examples:

```text
GET /data-items
GET /faults
GET /dtc
```

Latest values are retrieved using `DISTINCT ON` queries.

Both APIs have been verified against the same underlying database rows.

### 3.5 DTC lifecycle

DTCs follow a dedicated path through the `dtc_events` table.

```text
CAN DTC Response
       │
       ▼
 DTC Decoder
       │
       ▼
   MQTT / DB
       │
       ▼
  dtc_events
       │
       ▼
   sovd-api
       │
       ▼
POST /faults/{code}/clear
```

The fault-clearing endpoint is protected by JWT authentication.

Verified behavior:

* Unauthenticated requests → `401 Unauthorized`
* Authenticated requests → `cleared_at` is updated
* Updated fault state is immediately reflected by the APIs

---

## 4. Trust Boundaries

### 4.1 Zone Controller ↔ HPC Node

**Status: Planned**

The future Zone Controller ↔ HPC communication link is intended to use authenticated communication backed by a secure element.

Candidate secure elements from the original hardware specification:

* NXP SE050
* ATECC608A

The goal is to prevent an unauthenticated or compromised HPC-side component from issuing commands to the real-time domain.

> **Current status:** the physical link has not yet been implemented because the target hardware integration is still pending.

---

### 4.2 SOVD API Write Endpoint

The main vehicle-relevant state-changing operation is:

```http
POST /faults/{code}/clear
```

This endpoint is protected by JWT authentication through `auth.py`.

Current verification:

```text
Unauthenticated request
        │
        ▼
      401

Authenticated request
        │
        ▼
   Fault cleared
        │
        ▼
   cleared_at updated
```

The current implementation is explicitly **development-scoped**:

* Hardcoded development JWT secret
* Authentication pattern demonstrated
* Not intended for production deployment
* Production secret management is not yet implemented

---

### 4.3 MQTT Broker

The current development environment uses a local Mosquitto broker:

```text
Host: localhost
Port: 1883
Authentication: allow_anonymous true
```

This configuration is intentionally limited to local development.

It is **not a production security configuration**.

The planned production migration is toward AWS IoT Core with certificate-based device authentication, as documented in **ADR 0005**.

---

## 5. Simplifications Compared with a Production System

The project intentionally uses simplified components to validate the architecture and software behavior before introducing the complexity and cost of production hardware.

### 5.1 Raspberry Pi CM4 as HPC stand-in

The current HPC target is a **Raspberry Pi CM4**.

It represents the software-centric side of the architecture but is not equivalent to a production automotive HPC.

A production automotive HPC may involve:

* Multi-core automotive-grade SoCs
* Hypervisors
* Hardware isolation
* Automotive Ethernet/CAN interfaces
* Safety/security mechanisms
* ASIL-oriented partitioning and validation

The project demonstrates the **architectural separation**, rather than claiming to implement a production automotive HPC.

---

### 5.2 Zone Controller: SIL before hardware

The Zone Controller software has been validated in the SIL environment.

Target hardware:

```text
STM32G431KB
      +
TJA1051T/3
```

The real STM32 hardware has not yet been integrated.

Therefore:

```text
Software validation:  Implemented
SIL validation:       Implemented
Real hardware:        Pending
```

---

### 5.3 OTA: state-machine simulation

The OTA agent currently implements the deployment lifecycle as a software state machine:

```text
Deploy
  │
  ▼
Commit
  │
  ▼
Rollback
```

The state transitions are tested in software.

Actual A/B partition management using **Mender** is planned once the target hardware is available.

See **ADR 0006**.

---

### 5.4 MQTT: local development broker

The current MQTT infrastructure uses a local Mosquitto instance.

```text
Current:
Application → Mosquitto :1883

Planned:
Application → TLS → AWS IoT Core
```

The current broker configuration prioritizes development speed and local testing.

Certificate-based authentication and TLS are part of the planned AWS IoT Core migration described in **ADR 0005**.

---

### 5.5 Authentication: development scope

JWT authentication is currently used to demonstrate the security boundary around write operations.

Current implementation:

```text
JWT authentication
        +
Hardcoded development secret
```

Production implementation would require, at minimum:

* Secure secret storage
* Secret rotation
* Proper key management
* TLS
* Production identity management
* Certificate/device authentication where appropriate

The current implementation should therefore be considered a **security-pattern demonstration**, not production authentication infrastructure.

---

## 6. Design Philosophy

The project follows a **SIL-first, hardware-later** development strategy.

The sequence is intentional:

```text
┌──────────────────────┐
│ Define architecture  │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Implement software   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Unit testing         │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ SIL / virtual CAN    │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ End-to-end services  │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Hardware integration │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Production security  │
│ and infrastructure   │
└──────────────────────┘
```

This approach allows the core logic and interfaces to be validated before introducing hardware-specific constraints.

The current project therefore makes a clear distinction between:

| Area                             | Current Status                                 |
| -------------------------------- | ---------------------------------------------- |
| CAN decoding                     | **Implemented & tested**                       |
| PID decoding                     | **Implemented & tested**                       |
| DTC decoding                     | **Implemented & tested**                       |
| SIL / `vcan0`                    | **Implemented & tested**                       |
| MQTT telemetry flow              | **Implemented & verified**                     |
| TimescaleDB persistence          | **Implemented & verified**                     |
| Telemetry API                    | **Implemented & verified**                     |
| SOVD API                         | **Implemented & verified**                     |
| JWT write protection             | **Implemented & verified — development scope** |
| Zone Controller hardware         | **Pending**                                    |
| Zone ↔ HPC authenticated link    | **Planned**                                    |
| AWS IoT Core                     | **Planned**                                    |
| TLS / certificate authentication | **Planned**                                    |
| Mender A/B OTA                   | **Planned**                                    |
| Production secret management     | **Planned**                                    |

The objective is not to claim production readiness at the current stage, but to establish a validated architectural foundation that can progressively move from **software simulation → hardware integration → production-grade security and deployment**.
