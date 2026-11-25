# HEMS-Link API Contract & Sample Data Spec

**Project:** Redline / HEMS-Link (Multi-Hospital Emergency Patient Transfer & Coordination System)  
**Boundary:** Presentation + OS Engine (`os_engine/`) <-> Flask API (`app.py`)

## 1. Core Data Models

### Hospital (`hospitals`)
- `hospital_id` (str): e.g. `"HOSP-A"`
- `name` (str): Human-readable name
- `address` (str)
- `lat` (float), `lng` (float)
- `trust_score` (float, 0.0–1.0)
- `incoming_load` (int)

### Facility Semaphore (`facilities`)
- `hospital_id` (str)
- `facility` (str): `"ICU"`, `"EMERGENCY"`, `"VENTILATOR"`, `"NEURO"`, `"SPECIALIST"`
- `total_units` (int)
- `free_units` (int)
- `version` (int): Optimistic concurrency token
- `last_updated` (ISO-8601 UTC string)

### Transfer Request / PCB (`requests`)
- `request_id` (str): e.g. `"REQ-1001"`
- `from_hospital` (str)
- `case_type` (str): `"cardiac_arrest"`, `"trauma"`, `"stroke"`, `"availability_sync"`, `"record_share"`, `"specialist_enquiry"`, `"planned_transfer"`, `"discharge_back"`
- `priority` (int, 1–8; 1 = highest)
- `effective_priority` (int, 1–8; updated by aging)
- `burst_time` (int)
- `remaining_time` (int)
- `facilities_needed` (list[str])
- `state` (str): `"NEW" | "READY" | "RUNNING" | "WAITING" | "TERMINATED"`
- `patient_hash` (str): Used for duplicate detection
- `consent_given` (bool)
- `created_at` (ISO-8601 UTC string)
- `wait_ticks` (int)

### Reservation / Hold (`transfers`)
- `hold_id` (str)
- `request_id` (str)
- `to_hospital` (str)
- `facilities` (list[str])
- `phase` (str): `"PREPARE" | "COMMITTED" | "ABORTED" | "EXPIRED"`
- `reserved_until` (ISO-8601 UTC string)
- `response` (str | null): `"ACCEPT" | "REJECT" | "MORE_INFO" | null`

## 2. Endpoints
- `GET /api/health` — Service status
- `GET /api/hospitals` — List hospitals and facility semaphores
- `PATCH /api/facilities/<hospital_id>/<facility>` — Optimistic concurrency update (`version` required; returns `409 Conflict` on mismatch)
- `GET /api/requests` — List all transfer requests
- `POST /api/requests` — Create request (checks duplicate `patient_hash`, assigns priority, admits to scheduler)
- `POST /api/matches` — Rank eligible hospitals with explainable score payload
- `POST /api/refer` — Parallel referral (top-N holds, first-accept-wins)
- `POST /api/transfers/<hold_id>/respond` — Receiving hospital `ACCEPT` / `REJECT` / `MORE_INFO`
- `GET /api/monitor` — Live OS state: queues, semaphores, Banker's safe-state, RAG deadlock detector, Gantt timeline, event log
- `POST /api/simulator/run` — Run scenario (`race_condition`, `aging`, `deadlock`, `priority_inheritance`, `surge`, `benchmark`)
- `POST /api/surge` — Toggle surge mode (P1 FIFO + load balancing)
- `POST /api/reset` — Reset to clean seeded demo data

