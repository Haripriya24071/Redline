# HEMS-Link (Redline) — Hospital Emergency Management OS Prototype

**Case Study 2: Hospital Emergency Management System & Multi-Hospital Coordination**  
Operating Systems — III Semester, CSE (AI), Jain (Deemed-to-be) University.

> **Disclaimer:** Academic prototype using simulated hospital availability and synthetic patient data for decision support only. It does not replace clinical judgement.

---

## 1. Case Study Objectives & Student Tasks Coverage

| Requirement | Implementation in Redline |
| :--- | :--- |
| **Model hospital activities as processes** | Every hospital activity is modeled as a Process Control Block (`Process` in `os_engine/scheduler.py`) with 5 states (`NEW → READY → RUNNING → WAITING → TERMINATED`), Priority (`1–8`), Burst Time, Arrival Time, Remaining Time, Category, and Real-Time SLA Deadline. |
| **At least 8 processes across all hospital subsystems** | Live system seeds **8 processes** (`REQ-1001`–`REQ-1008`) plus a **10-process Full Hospital Mix** (`hospital_10_workload()`) and the **8-process Case Study Baseline** (`T1`–`T8`) covering **Emergency Patients**, **ICU Monitoring**, **Laboratory Tests**, **OP Patients**, **Pharmacy Requests**, and **Inter-Hospital Transfers**. |
| **Core CPU Scheduling Algorithms** | **FCFS**, **SJF (Non-Preemptive)**, **Preemptive Priority (+ Aging)**, and **Round Robin (configurable Quantum Q=1..8)**. |
| **Real-Time & Advanced Scheduling** | **EDF (Earliest Deadline First)** with SLA compliance & slack tracking, **SRTF (Shortest Remaining Time First)**, **Non-Preemptive Priority**, **MLFQ (3-level feedback queue)**, and **Surge FIFO**. |
| **CPU Scheduling Criteria Analysis** | Computes **Completion Time (CT)**, **Turnaround Time (TAT = CT − AT)**, **Waiting Time (WT = TAT − BT)**, **Response Time (RT)**, **Critical P1–P3 Response**, **CPU Utilization %**, **Throughput**, **Context Switches**, and **Real-Time Deadline Miss Rate / SLA %**. |

---

## 2. Implemented Features & Visuals

### Interactive Scheduling & OS Kernel Workbench (`/monitor`)
- **Live Kernel Debugger & Stepper:** Step tick-by-tick (`Step +1`, `Run +5`, `Auto-Play`), switch the live kernel policy on the fly, and inspect Ready/Waiting queues, CPU utilization, and real-time kernel decision logs (`ADMIT`, `DISPATCH`, `PREEMPT`, `AGING`, `WAIT`, `TERMINATE`).
- **8-Algorithm Scheduling Workbench:** Compare FCFS, SJF, SRTF, Non-Preemptive Priority, Preemptive Priority + Aging, Round Robin, EDF, and MLFQ side-by-side or individually.
- **Interactive Gantt Charts with Time Rulers:** Color-coded execution segments with `IDLE` detection, tick rulers, and hover tooltips.
- **Custom Hospital Process Builder:** Add custom Emergency, ICU Monitoring, Lab, OP, or Pharmacy tasks with custom Arrival, Burst, Priority, and Deadline, then simulate all 8 algorithms immediately via `POST /api/monitor/simulate`.
- **Configurable Sliders & CSV Export:** Live sliders for Round Robin **Time Quantum (`Q = 1..8`)** and **Aging Interval (`0..20`)**, plus one-click **CSV report export** (`/api/export/csv`).
- **Synchronization & Deadlock Proofs:**
  - **Counting Semaphores & Optimistic Concurrency** (`version` token conflict handling with `409 Conflict`).
  - **Mutex Critical Section Proof** (200 concurrent thread trials: 0 double-bookings with mutex vs race failures without).
  - **Banker's Algorithm Safe-State Matrix** (`Allocation`, `Max Need`, `Remaining Need`, `Available`, Safe Sequence).
  - **Interactive SVG Resource Allocation Graph (RAG)** showing circular wait (`Req-X ↔ Req-Y`) and lowest-priority victim recovery.
  - **Real-Time Priority Inheritance Timeline** & **Aging Starvation Boost Curve** (SVG).

### CPU Scheduling Criteria & Quantum Lab (`/analytics`)
- **8-Algorithm Criteria Matrix** across `Case Study 2 (T1–T8)`, `Full Hospital Mix (H1–H10)`, and `Live Queue`.
- **Round Robin Quantum Sensitivity SVG Chart (`Q = 1..8`):** Visualizes the trade-off between Average Waiting Time and Context Switch overhead.
- **Subsystem Workload Breakdown** & Critical First-Response comparison bars.

### Live Emergency Dispatch & Route Map (`/`)
- **KPI Telemetry Strip:** Active OS processes, Critical P1–P3 queue count, Network free ICU/Ventilator beds, and Kernel safety status.
- **Hospital Activity Intake:** Supports Cardiac Arrest, Trauma, ICU Ventilator Telemetry, Stroke, Stat ABG Lab, Pharmacy Stat/Refill, OP Triage, Specialist Enquiry, and Planned Transfer with customizable CPU burst & SLA deadline.
- **Kanakapura → Bengaluru SVG Route Map:** Concentric distance rings, animated origin/assigned hospital pins, and live bed dots across 10 simulated Bengaluru/Kanakapura hospitals.

### Additional Screens
- **Bed Board (`/availability`):** Direct Counting Semaphore adjustments (`+1`/`-1`) with optimistic version conflict banners and RBAC enforcement.
- **Surge Mode (`/surge`):** Mass-casualty Priority-1 FIFO queue (aging suspended for P1) with visual capacity-balanced distribution across hospitals.
- **Tracker (`/tracker`), Coordination (`/coordination`), Matches (`/matches`), New Request (`/requests/new`), Style Guide (`/style-guide`):** Complete transfer lifecycle, parallel top-N referral holds, Light/Dark Liquid Glass UI, and **EN / HI / KN** internationalization.

---

## 3. Recommended Additional Features (Roadmap & Extensions)

The following additional OS and clinical-systems enhancements are recommended for future iterations of Redline / HEMS-Link:

1. **Multi-Core SMP Hospital CPU Scheduling & Processor Affinity:** Extend `os_engine/scheduler.py` from single-CPU to $N$-core symmetric multiprocessing (e.g., separate cores for Emergency Triage, ICU Telemetry, and Lab Processing) with load balancing and core-affinity pinning.
2. **Rate Monotonic Scheduling (RMS) for Periodic ICU Vitals:** Model continuous ICU monitoring (ECG, SpO₂, ventilator telemetry) as periodic real-time tasks $(C_i, T_i)$ with Liu–Layland schedulability utilization bound checks ($U \le n(2^{1/n} - 1)$).
3. **Persistent SQLite (WAL Mode) + Server-Sent Events (SSE):** Replace in-memory `HEMSState` with SQLite `WAL` mode (`busy_timeout`) for multi-worker persistence and add `/api/stream` SSE push updates across open dispatch consoles instead of manual refresh.
4. **Live Road-Network Ambulance Routing & Traffic Weights:** Upgrade Haversine distance ETA in `os_engine/matcher.py` to graph-based Dijkstra/A* routing with time-of-day Bengaluru traffic multipliers.
5. **Real-Time EDF Admission Control:** Reject or auto-shed non-critical OP/Pharmacy tasks when admitting a new critical task would push total CPU utilization above 100% or cause a P1–P3 deadline miss.
6. **Authenticated RBAC & HL7/FHIR Interoperability Stubs:** Add session-backed authentication for Coordinator, Referring, Receiving, and Auditor roles and standardized FHIR `ServiceRequest` / `Location` JSON payloads.

---

## 4. Project Structure
- `os_engine/` — Core OS Engine (`scheduler.py`, `matcher.py`, `reservation.py`, `banker.py`, `deadlock.py`, `workers.py`, `simulator.py`)
- `app.py` — Flask server, 9 UI screen routes + Style Guide, and REST API endpoints
- `templates/` & `static/` — Liquid Glass UI, SVG charts/maps, tactile keycaps, Light/Dark themes, and EN/HI/KN i18n
- `tests/` — Automated pytest suite (`test_os_engine.py`, `test_api_and_ui.py`)
- `contract.md` — Frozen API contract & data model specification
- `docs/` — Accessibility report (`a11y_report.md`), generator scripts (`generate_figures.py`, `build_report.py`), color diagrams (`figures_color/`), and updated Case Study 2 Reports (`Redline_OS_Case_Study_Report.pdf` / `.docx`)

## 5. Run Instructions
```bash
py -3 -m pip install -r requirements.txt
py -3 app.py
```
Open `http://127.0.0.1:5000` in your browser.

## 6. Run Tests
```bash
py -3 -m pytest -v
```
