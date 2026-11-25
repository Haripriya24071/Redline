"""HEMS-Link (Redline) Flask Application & API."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from flask import Flask, Response, jsonify, render_template, request

from os_engine.banker import default_hospital_b_banker
from os_engine.deadlock import ResourceAllocationGraph
from os_engine.matcher import match_hospitals
from os_engine.reservation import ConflictError, HoldExpiredError, ReservationEngine
from os_engine.scheduler import (
    CASE_CATEGORY_MAP,
    CASE_PRIORITY_MAP,
    Process,
    ProcessState,
    Scheduler,
    SchedulerPolicy,
    default_workload,
    hospital_10_workload,
    run_benchmark_suite,
    run_extended_benchmark,
    run_quantum_sweep,
    simulate_algorithm,
)
from os_engine.simulator import ScenarioSimulator
from os_engine.workers import BackgroundWorkers

app = Flask(__name__)


class HEMSState:
    """In-memory state store backed by OS Engine modules and seeded sample data."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        now = datetime.now(timezone.utc)
        fresh = (now - timedelta(minutes=2)).isoformat()
        recent = (now - timedelta(minutes=6)).isoformat()
        stale = (now - timedelta(minutes=42)).isoformat()

        self.hospitals: list[dict[str, Any]] = [
            {
                "hospital_id": "HOSP-JAIN",
                "name": "Jain Univ. Health Centre",
                "address": "Jakkasandra, Kanakapura Rd (Origin)",
                "lat": 12.6418,
                "lng": 77.4404,
                "trust_score": 0.95,
                "incoming_load": 0,
            },
            {
                "hospital_id": "HOSP-DSH",
                "name": "Dayananda Sagar Hospital",
                "address": "Kanakapura Rd, Harohalli",
                "lat": 12.6685,
                "lng": 77.4512,
                "trust_score": 0.96,
                "incoming_load": 1,
            },
            {
                "hospital_id": "HOSP-RRM",
                "name": "Rajarajeswari Medical College",
                "address": "Mysore Rd, Kambipura",
                "lat": 12.8858,
                "lng": 77.4608,
                "trust_score": 0.92,
                "incoming_load": 2,
            },
            {
                "hospital_id": "HOSP-BGS",
                "name": "BGS Gleneagles Global",
                "address": "Uttarahalli Main Rd, Kengeri",
                "lat": 12.9012,
                "lng": 77.4956,
                "trust_score": 0.95,
                "incoming_load": 2,
            },
            {
                "hospital_id": "HOSP-APL",
                "name": "Apollo Hospital",
                "address": "Bannerghatta Rd, Bengaluru",
                "lat": 12.8962,
                "lng": 77.5988,
                "trust_score": 0.93,
                "incoming_load": 3,
            },
            {
                "hospital_id": "HOSP-SGR",
                "name": "Sagar Hospital",
                "address": "Tilak Nagar, Jayanagar",
                "lat": 12.9288,
                "lng": 77.5994,
                "trust_score": 0.88,
                "incoming_load": 1,
            },
            {
                "hospital_id": "HOSP-KNG",
                "name": "Kanakapura Taluk General",
                "address": "Kanakapura Town, Ramanagara",
                "lat": 12.5462,
                "lng": 77.4199,
                "trust_score": 0.86,
                "incoming_load": 1,
            },
            {
                "hospital_id": "HOSP-NAR",
                "name": "Narayana Health City",
                "address": "Bommasandra, Hosur Rd",
                "lat": 12.8105,
                "lng": 77.6948,
                "trust_score": 0.95,
                "incoming_load": 2,
            },
            {
                "hospital_id": "HOSP-MNI",
                "name": "Manipal Hospital",
                "address": "Jayanagar 9th Block, Bengaluru",
                "lat": 12.9178,
                "lng": 77.5912,
                "trust_score": 0.94,
                "incoming_load": 2,
            },
            {
                "hospital_id": "HOSP-STJ",
                "name": "St. John's Medical College",
                "address": "Koramangala, Bengaluru",
                "lat": 12.9293,
                "lng": 77.6209,
                "trust_score": 0.93,
                "incoming_load": 3,
            },
        ]

        self.reservation = ReservationEngine(hold_ttl_seconds=180)
        seed_facs = {
            "HOSP-JAIN": [("ICU", 2, 0, fresh), ("EMERGENCY", 4, 2, fresh), ("VENTILATOR", 1, 0, fresh), ("NEURO", 1, 0, fresh), ("SPECIALIST", 2, 1, fresh)],
            "HOSP-DSH": [("ICU", 6, 2, fresh), ("EMERGENCY", 8, 4, fresh), ("VENTILATOR", 4, 2, fresh), ("NEURO", 2, 1, fresh), ("SPECIALIST", 3, 2, fresh)],
            "HOSP-RRM": [("ICU", 8, 3, recent), ("EMERGENCY", 10, 5, recent), ("VENTILATOR", 5, 2, recent), ("NEURO", 3, 2, recent), ("SPECIALIST", 4, 2, recent)],
            "HOSP-BGS": [("ICU", 10, 4, fresh), ("EMERGENCY", 8, 4, fresh), ("VENTILATOR", 6, 3, fresh), ("NEURO", 4, 3, fresh), ("SPECIALIST", 5, 3, fresh)],
            "HOSP-APL": [("ICU", 8, 3, recent), ("EMERGENCY", 6, 3, recent), ("VENTILATOR", 5, 2, recent), ("NEURO", 3, 2, recent), ("SPECIALIST", 4, 2, recent)],
            "HOSP-SGR": [("ICU", 5, 2, stale), ("EMERGENCY", 5, 2, stale), ("VENTILATOR", 3, 1, stale), ("NEURO", 2, 1, stale), ("SPECIALIST", 2, 1, stale)],
            "HOSP-KNG": [("ICU", 4, 2, fresh), ("EMERGENCY", 6, 4, fresh), ("VENTILATOR", 2, 1, fresh), ("NEURO", 1, 0, fresh), ("SPECIALIST", 2, 1, fresh)],
            "HOSP-NAR": [("ICU", 12, 5, fresh), ("EMERGENCY", 10, 5, fresh), ("VENTILATOR", 8, 4, fresh), ("NEURO", 4, 2, fresh), ("SPECIALIST", 6, 4, fresh)],
            "HOSP-MNI": [("ICU", 8, 3, fresh), ("EMERGENCY", 8, 4, fresh), ("VENTILATOR", 5, 3, fresh), ("NEURO", 3, 2, fresh), ("SPECIALIST", 4, 3, fresh)],
            "HOSP-STJ": [("ICU", 10, 4, recent), ("EMERGENCY", 10, 5, recent), ("VENTILATOR", 6, 3, recent), ("NEURO", 4, 2, recent), ("SPECIALIST", 5, 3, recent)],
        }
        for hid, items in seed_facs.items():
            for fac, total, free, ts in items:
                self.reservation.register_facility(hid, fac, total, free, last_updated=ts)

        self.workers = BackgroundWorkers(self.reservation)
        self.scheduler = Scheduler(policy=SchedulerPolicy.PREEMPTIVE_PRIORITY, aging_interval=10)
        self.banker = default_hospital_b_banker()
        self.rag = ResourceAllocationGraph()

        self.requests: dict[str, dict[str, Any]] = {}
        self.audit_log: list[dict[str, Any]] = []
        self.surge_mode = False

        # Seed 8 hospital activity processes covering Emergency, ICU Monitoring, Lab, OP, Pharmacy & Transfers
        self._seed_sample_requests()

    def _seed_sample_requests(self) -> None:
        samples = [
            ("REQ-1001", "HOSP-JAIN", "op_triage", ["EMERGENCY"], "PAT-1102", True, 0, 4, "OP Patient", "OP Walk-in Triage"),
            ("REQ-1002", "HOSP-JAIN", "planned_transfer", ["EMERGENCY"], "PAT-1109", True, 0, 3, "Transfer", "Planned Dialysis Transfer"),
            ("REQ-1003", "HOSP-JAIN", "pharmacy_stat", ["SPECIALIST"], "PAT-3304", True, 1, 2, "Pharmacy", "ICU Epinephrine Stat"),
            ("REQ-1004", "HOSP-JAIN", "icu_monitoring", ["ICU"], "PAT-5501", True, 1, 4, "ICU Monitoring", "ICU Ventilator Telemetry"),
            ("REQ-1005", "HOSP-JAIN", "stat_lab_test", ["EMERGENCY"], "PAT-6620", True, 2, 3, "Laboratory", "Stat ABG Blood Gas Lab"),
            ("REQ-1006", "HOSP-JAIN", "stroke", ["ICU", "NEURO"], "PAT-4410", True, 3, 5, "Emergency", "Stroke Neuro-Unit"),
            ("REQ-1007", "HOSP-JAIN", "trauma", ["ICU", "VENTILATOR"], "PAT-7218", True, 4, 6, "Emergency", "Road Trauma ICU + Vent"),
            ("REQ-1008", "HOSP-JAIN", "cardiac_arrest", ["ICU", "VENTILATOR"], "PAT-8821", True, 5, 7, "Emergency", "Cardiac Arrest Code Blue"),
        ]
        for rid, from_h, ctype, facs, phash, consent, arr_t, burst_t, cat, label in samples:
            prio = CASE_PRIORITY_MAP.get(ctype, 5)
            proc = Process(
                pid=rid,
                name=f"{label} ({from_h})",
                arrival_time=arr_t,
                priority=prio,
                burst_time=burst_t,
                case_type=ctype,
                category=cat,
            )
            self.scheduler.admit(proc)
            if rid in ("REQ-1001", "REQ-1003", "REQ-1005"):
                self.scheduler.step()
            self.requests[rid] = {
                "request_id": rid,
                "from_hospital": from_h,
                "case_type": ctype,
                "category": cat,
                "priority": prio,
                "burst_time": burst_t,
                "arrival_time": arr_t,
                "deadline": proc.deadline,
                "facilities_needed": facs,
                "patient_hash": phash,
                "consent_given": consent,
                "state": proc.state.value,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "timeline": [
                    {"state": "NEW", "at": datetime.now(timezone.utc).isoformat(), "note": f"{cat} task submitted"},
                    {"state": "READY", "at": datetime.now(timezone.utc).isoformat(), "note": f"Assigned Priority {prio}"},
                ],
                "hold_ids": [],
                "accepted_by": None,
                "ambulance_eta_min": None,
            }

        # Create one active parallel referral for REQ-1008 so Coordination & Tracker have live holds
        holds = self.workers.send_parallel_referral("REQ-1008", ["HOSP-DSH", "HOSP-BGS"], ["ICU", "VENTILATOR"], batch_size=2)
        self.requests["REQ-1008"]["hold_ids"] = [h.hold_id for h in holds]
        self.requests["REQ-1008"]["state"] = "WAITING"
        self.scheduler.move_to_waiting("REQ-1008", "Waiting for parallel referral reply")

    def log_audit(self, actor_role: str, action: str, detail: str, break_glass: bool = False) -> None:
        self.audit_log.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "role": actor_role,
                "action": action,
                "detail": detail,
                "break_glass": break_glass,
            }
        )


state = HEMSState()


# ---------------------------------------------------------------------------
# Page Routes (9 Screens + Style Guide)
# ---------------------------------------------------------------------------
@app.route("/")
def screen_dashboard() -> str:
    return render_template("dashboard.html", active_page="dashboard")


@app.route("/requests/new")
def screen_new_request() -> str:
    return render_template("new_request.html", active_page="new_request")


@app.route("/matches")
def screen_matches() -> str:
    return render_template("matches.html", active_page="matches")


@app.route("/coordination")
def screen_coordination() -> str:
    return render_template("coordination.html", active_page="coordination")


@app.route("/tracker")
def screen_tracker() -> str:
    return render_template("tracker.html", active_page="tracker")


@app.route("/availability")
def screen_availability() -> str:
    return render_template("availability.html", active_page="availability")


@app.route("/monitor")
def screen_monitor() -> str:
    return render_template("monitor.html", active_page="monitor")


@app.route("/analytics")
def screen_analytics() -> str:
    return render_template("analytics.html", active_page="analytics")


@app.route("/surge")
def screen_surge() -> str:
    return render_template("surge.html", active_page="surge")


@app.route("/style-guide")
def screen_style_guide() -> str:
    return render_template("style_guide.html", active_page="style_guide")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "service": "hems-link", "simulated_data": True})


@app.route("/api/hospitals")
def api_hospitals():
    sems = state.reservation.snapshot_semaphores()
    enriched = []
    for h in state.hospitals:
        hid = h["hospital_id"]
        enriched.append({**h, "facilities": sems.get(hid, {})})
    return jsonify({"hospitals": enriched, "surge_mode": state.surge_mode})


@app.route("/api/facilities/<hospital_id>/<facility>", methods=["PATCH"])
def api_update_facility(hospital_id: str, facility: str):
    data = request.get_json(silent=True) or {}
    role = data.get("role") or request.headers.get("X-Role", "receiving")
    break_glass = bool(data.get("break_glass", False))

    if role == "auditor":
        state.log_audit(role, "FORBIDDEN_EDIT", f"Denied edit on {hospital_id}/{facility}")
        return jsonify({"error": "Auditor role is read-only."}), 403

    if "free_units" not in data or "version" not in data:
        return jsonify({"error": "free_units and version are required."}), 400

    try:
        updated = state.reservation.update_availability(
            hospital_id=hospital_id,
            facility=facility.upper(),
            free_units=int(data["free_units"]),
            expected_version=int(data["version"]),
        )
        state.log_audit(
            role,
            "UPDATE_AVAILABILITY",
            f"{hospital_id}/{facility} -> {updated.free_units} (v{updated.version})",
            break_glass=break_glass,
        )
        return jsonify({"facility": updated.to_dict()})
    except ConflictError as exc:
        return jsonify({"error": str(exc), "code": "VERSION_CONFLICT"}), 409
    except KeyError:
        return jsonify({"error": "Hospital or facility not found."}), 404


@app.route("/api/requests", methods=["GET", "POST"])
def api_requests():
    if request.method == "GET":
        return jsonify({"requests": list(state.requests.values()), "surge_mode": state.surge_mode})

    data = request.get_json(silent=True) or {}
    role = data.get("role") or request.headers.get("X-Role", "referring")
    if role == "auditor":
        return jsonify({"error": "Auditor role is read-only."}), 403

    from_hospital = data.get("from_hospital", "HOSP-A")
    case_type = data.get("case_type", "cardiac_arrest")
    facilities_needed = data.get("facilities_needed") or ["ICU"]
    patient_hash = data.get("patient_hash", f"PAT-{uuid.uuid4().hex[:4].upper()}")
    consent_given = bool(data.get("consent_given", True))
    force_duplicate = bool(data.get("force_duplicate", False))

    # Duplicate detection (T9)
    duplicate = next(
        (
            r["request_id"]
            for r in state.requests.values()
            if r["patient_hash"] == patient_hash and r["state"] != "TERMINATED"
        ),
        None,
    )
    if duplicate and not force_duplicate:
        return jsonify(
            {
                "warning": f"Duplicate active referral detected for patient {patient_hash} ({duplicate}).",
                "duplicate_request_id": duplicate,
                "code": "DUPLICATE_DETECTED",
            }
        ), 409

    rid = f"REQ-{1000 + len(state.requests) + 1}"
    prio = int(data.get("priority", CASE_PRIORITY_MAP.get(case_type, 5)))
    prio = max(1, min(8, prio))
    category = data.get("category") or CASE_CATEGORY_MAP.get(case_type, "Hospital Activity")
    arrival_t = int(data.get("arrival_time", state.scheduler.clock))
    burst_t = max(1, int(data.get("burst_time", 5)))
    deadline_val = data.get("deadline")
    deadline_int = int(deadline_val) if deadline_val not in (None, "") else None
    proc_name = data.get("name") or f"{case_type.replace('_', ' ').title()} ({from_hospital})"

    proc = Process(
        pid=rid,
        name=proc_name,
        arrival_time=arrival_t,
        priority=prio,
        burst_time=burst_t,
        case_type=case_type,
        category=category,
        deadline=deadline_int,
    )
    state.scheduler.admit(proc)
    state.scheduler.step()

    req_record = {
        "request_id": rid,
        "from_hospital": from_hospital,
        "case_type": case_type,
        "category": category,
        "priority": prio,
        "burst_time": burst_t,
        "arrival_time": arrival_t,
        "deadline": proc.deadline,
        "facilities_needed": facilities_needed,
        "patient_hash": patient_hash,
        "consent_given": consent_given,
        "state": proc.state.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "timeline": [
            {"state": "NEW", "at": datetime.now(timezone.utc).isoformat(), "note": f"{category} request created"},
            {"state": "READY", "at": datetime.now(timezone.utc).isoformat(), "note": f"Priority {prio} assigned"},
        ],
        "hold_ids": [],
        "accepted_by": None,
        "ambulance_eta_min": None,
    }
    state.requests[rid] = req_record
    state.log_audit(role, "CREATE_REQUEST", f"Created {rid} ({case_type}, P{prio})")
    return jsonify({"request": req_record}), 201


@app.route("/api/matches", methods=["POST"])
def api_matches():
    data = request.get_json(silent=True) or {}
    from_id = data.get("from_hospital", "HOSP-A")
    facilities = data.get("facilities_needed") or ["ICU"]
    from_hosp = next((h for h in state.hospitals if h["hospital_id"] == from_id), state.hospitals[0])
    sems = state.reservation.snapshot_semaphores()
    result = match_hospitals(
        from_hospital=from_hosp,
        hospitals=state.hospitals,
        facilities_by_hospital=sems,
        required_facilities=facilities,
        surge_mode=state.surge_mode,
    )
    return jsonify(result)


@app.route("/api/refer", methods=["POST"])
def api_refer():
    data = request.get_json(silent=True) or {}
    req_id = data.get("request_id")
    hospital_ids = data.get("hospital_ids") or []
    batch_size = int(data.get("batch_size", 3))
    if not req_id or req_id not in state.requests:
        return jsonify({"error": "Valid request_id required."}), 404

    req_rec = state.requests[req_id]
    holds = state.workers.send_parallel_referral(
        request_id=req_id,
        candidate_hospital_ids=hospital_ids,
        facilities=req_rec["facilities_needed"],
        batch_size=batch_size,
    )
    if not holds:
        return jsonify({"error": "No candidate hospitals had free units to hold."}), 409

    req_rec["hold_ids"].extend([h.hold_id for h in holds])
    req_rec["state"] = "WAITING"
    req_rec["timeline"].append(
        {
            "state": "WAITING",
            "at": datetime.now(timezone.utc).isoformat(),
            "note": f"Parallel holds placed at {', '.join(h.to_hospital for h in holds)}",
        }
    )
    if req_id in state.scheduler.processes:
        state.scheduler.move_to_waiting(req_id, f"Parallel referral to {len(holds)} hospitals")

    return jsonify({"holds": [h.to_dict() for h in holds]}), 201


@app.route("/api/transfers", methods=["GET"])
def api_list_transfers():
    holds = [h.to_dict() for h in state.reservation.holds.values()]
    return jsonify({"holds": holds, "requests": state.requests})


@app.route("/api/transfers/<hold_id>/respond", methods=["POST"])
def api_respond_transfer(hold_id: str):
    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").upper()
    role = data.get("role") or request.headers.get("X-Role", "receiving")
    if role == "auditor":
        return jsonify({"error": "Auditor role is read-only."}), 403
    if hold_id not in state.reservation.holds:
        return jsonify({"error": "Hold not found."}), 404

    try:
        if action == "ACCEPT":
            hold = state.reservation.commit_hold(hold_id)
            req_rec = state.requests.get(hold.request_id)
            if req_rec:
                req_rec["state"] = "TERMINATED"
                req_rec["accepted_by"] = hold.to_hospital
                req_rec["ambulance_eta_min"] = 14
                req_rec["timeline"].append(
                    {
                        "state": "TERMINATED",
                        "at": datetime.now(timezone.utc).isoformat(),
                        "note": f"Accepted by {hold.to_hospital}; sibling holds released",
                    }
                )
            if hold.request_id in state.scheduler.processes:
                proc = state.scheduler.processes[hold.request_id]
                proc.state = ProcessState.TERMINATED
            state.log_audit(role, "ACCEPT_TRANSFER", f"{hold_id} accepted by {hold.to_hospital}")
            return jsonify({"hold": hold.to_dict()})

        if action == "REJECT":
            hold = state.reservation.abort_hold(hold_id, reason="REJECT")
            state.log_audit(role, "REJECT_TRANSFER", f"{hold_id} rejected by {hold.to_hospital}")
            return jsonify({"hold": hold.to_dict()})

        if action == "MORE_INFO":
            hold = state.reservation.holds[hold_id]
            hold.response = "MORE_INFO"
            state.log_audit(role, "MORE_INFO", f"{hold_id} requested additional clinical info")
            return jsonify({"hold": hold.to_dict()})

        return jsonify({"error": "Action must be ACCEPT, REJECT, or MORE_INFO."}), 400
    except HoldExpiredError as exc:
        return jsonify({"error": str(exc)}), 410


def _resolve_workload(workload_name: str) -> list[Process]:
    if workload_name == "case_study":
        return default_workload()
    if workload_name == "hospital10":
        return hospital_10_workload()
    live_procs = list(state.scheduler.processes.values())
    if not live_procs:
        return default_workload()
    return [
        Process(
            pid=p.pid,
            name=p.name,
            arrival_time=p.arrival_time,
            priority=p.priority,
            burst_time=p.burst_time,
            case_type=p.case_type,
            category=p.category,
            deadline=p.deadline,
        )
        for p in live_procs
    ]


@app.route("/api/monitor")
def api_monitor():
    state.workers.sweep_expired_and_escalate()

    quantum = max(1, min(10, int(request.args.get("quantum", 3))))
    aging = max(0, min(30, int(request.args.get("aging", 10))))
    workload_name = request.args.get("workload", "live")
    selected_procs = _resolve_workload(workload_name)

    live_algorithms = run_extended_benchmark(
        workload=selected_procs,
        quantum=quantum,
        aging_interval=aging,
    )
    quantum_sweep = run_quantum_sweep(workload=selected_procs, max_q=8)

    category_breakdown: dict[str, dict[str, int]] = {}
    for p in selected_procs:
        cat = p.category or "Hospital Activity"
        entry = category_breakdown.setdefault(cat, {"count": 0, "total_burst": 0})
        entry["count"] += 1
        entry["total_burst"] += p.burst_time

    return jsonify(
        {
            "scheduler": state.scheduler.snapshot(),
            "workload_name": workload_name,
            "workload_processes": [p.to_dict() for p in selected_procs],
            "live_algorithms": live_algorithms,
            "quantum_sweep": quantum_sweep,
            "category_breakdown": category_breakdown,
            "semaphores": state.reservation.snapshot_semaphores(),
            "holds": [h.to_dict() for h in state.reservation.holds.values()],
            "banker": state.banker.snapshot(),
            "deadlock": state.rag.snapshot(),
            "events": state.reservation.event_log[-20:],
            "audit_log": state.audit_log[-15:],
            "surge_mode": state.surge_mode,
            "test_cases": ScenarioSimulator.run_5_algorithm_test_cases(),
        }
    )


@app.route("/api/monitor/simulate", methods=["POST"])
def api_monitor_simulate_custom():
    """Run all 8 scheduling algorithms on a user-supplied list of hospital activity processes."""
    data = request.get_json(silent=True) or {}
    raw_procs = data.get("processes") or []
    quantum = max(1, min(10, int(data.get("quantum", 3))))
    aging = max(0, min(30, int(data.get("aging", 10))))

    if not raw_procs:
        return jsonify({"error": "At least one process is required."}), 400

    procs: list[Process] = []
    for idx, item in enumerate(raw_procs):
        ctype = str(item.get("case_type", "planned_transfer"))
        prio = max(1, min(8, int(item.get("priority", CASE_PRIORITY_MAP.get(ctype, 5)))))
        arr = max(0, int(item.get("arrival_time", 0)))
        burst = max(1, min(50, int(item.get("burst_time", 4))))
        dl_raw = item.get("deadline")
        dl = int(dl_raw) if dl_raw not in (None, "") else None
        procs.append(
            Process(
                pid=str(item.get("pid") or f"P{idx + 1}"),
                name=str(item.get("name") or f"Activity {idx + 1}"),
                arrival_time=arr,
                priority=prio,
                burst_time=burst,
                case_type=ctype,
                category=str(item.get("category") or CASE_CATEGORY_MAP.get(ctype, "Hospital Activity")),
                deadline=dl,
            )
        )

    algorithms = run_extended_benchmark(workload=procs, quantum=quantum, aging_interval=aging)
    sweep = run_quantum_sweep(workload=procs, max_q=8)
    return jsonify(
        {
            "processes": [p.to_dict() for p in procs],
            "algorithms": algorithms,
            "quantum_sweep": sweep,
        }
    )


@app.route("/api/scheduler/control", methods=["POST"])
def api_scheduler_control():
    """Interactive live kernel control: step, run_5, set_policy."""
    data = request.get_json(silent=True) or {}
    action = data.get("action", "step")

    if "policy" in data:
        try:
            state.scheduler.policy = SchedulerPolicy(data["policy"])
        except ValueError:
            return jsonify({"error": f"Unsupported policy {data['policy']}"}), 400
    if "quantum" in data:
        state.scheduler.quantum = max(1, min(10, int(data["quantum"])))
    if "aging_interval" in data:
        state.scheduler.aging_interval = max(0, min(30, int(data["aging_interval"])))

    events = []
    if action == "step":
        ev = state.scheduler.step()
        if ev:
            events.append(ev)
    elif action == "run_5":
        for _ in range(5):
            ev = state.scheduler.step()
            if ev:
                events.append(ev)
    elif action == "set_policy":
        state.log_audit("coordinator", "POLICY_CHANGE", f"Kernel policy -> {state.scheduler.policy.value}")

    # Sync request states with PCB states
    for rid, proc in state.scheduler.processes.items():
        if rid in state.requests:
            state.requests[rid]["state"] = proc.state.value

    return jsonify({"events": events, "scheduler": state.scheduler.snapshot()})


@app.route("/api/analytics")
def api_analytics():
    quantum = max(1, min(10, int(request.args.get("quantum", 3))))
    aging = max(0, min(30, int(request.args.get("aging", 10))))
    workload_name = request.args.get("workload", "case_study")
    selected = _resolve_workload(workload_name)
    return jsonify(
        {
            "benchmark": run_benchmark_suite(),
            "extended_benchmark": run_extended_benchmark(workload=selected, quantum=quantum, aging_interval=aging),
            "hospital10_benchmark": run_extended_benchmark(workload=hospital_10_workload(), quantum=quantum, aging_interval=aging),
            "quantum_sweep": run_quantum_sweep(workload=selected, max_q=8),
            "workload_name": workload_name,
            "requests_count": len(state.requests),
            "hospitals_count": len(state.hospitals),
        }
    )


@app.route("/api/export/csv")
def api_export_csv():
    """Export scheduling benchmark table as downloadable CSV."""
    workload_name = request.args.get("workload", "live")
    quantum = max(1, min(10, int(request.args.get("quantum", 3))))
    aging = max(0, min(30, int(request.args.get("aging", 10))))
    selected = _resolve_workload(workload_name)
    results = run_extended_benchmark(workload=selected, quantum=quantum, aging_interval=aging)

    lines = [
        "Algorithm,Avg_Waiting,Avg_Turnaround,Avg_Response,Critical_Avg_Wait,Critical_Avg_Response,Context_Switches,CPU_Util_Pct,Throughput,Deadline_Misses,SLA_Compliance_Pct"
    ]
    for key, res in results.items():
        lines.append(
            f"{key},{res['avg_waiting']},{res['avg_turnaround']},{res['avg_response']},"
            f"{res['critical_avg_waiting']},{res['critical_avg_response']},{res['context_switches']},"
            f"{res['cpu_utilization_pct']},{res['throughput']},{res['deadline_misses']},{res['sla_compliance_pct']}"
        )
    csv_body = "\n".join(lines) + "\n"
    return Response(
        csv_body,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=redline_{workload_name}_scheduling_report.csv"},
    )


@app.route("/api/simulator/run", methods=["POST"])
def api_simulator_run():
    data = request.get_json(silent=True) or {}
    scenario = data.get("scenario", "race_condition")
    if scenario == "race_condition":
        return jsonify(ScenarioSimulator.run_race_condition_demo(trials=int(data.get("trials", 200))))
    if scenario == "aging":
        return jsonify(ScenarioSimulator.run_aging_starvation_demo())
    if scenario == "deadlock":
        return jsonify(ScenarioSimulator.run_deadlock_demo())
    if scenario == "priority_inheritance":
        return jsonify(ScenarioSimulator.run_priority_inheritance_demo())
    if scenario == "surge":
        return jsonify(ScenarioSimulator.run_surge_simulation(num_requests=int(data.get("count", 20))))
    if scenario == "benchmark":
        return jsonify(run_benchmark_suite())
    if scenario == "step_scheduler":
        ev = state.scheduler.step()
        return jsonify({"step": ev, "scheduler": state.scheduler.snapshot()})
    return jsonify({"error": f"Unknown scenario {scenario}"}), 400


@app.route("/api/surge", methods=["POST"])
def api_surge():
    data = request.get_json(silent=True) or {}
    enabled = bool(data.get("enabled", not state.surge_mode))
    state.surge_mode = enabled
    state.scheduler.surge_mode = enabled
    state.log_audit("coordinator", "SURGE_MODE", f"Surge mode {'ENABLED' if enabled else 'DISABLED'}")
    return jsonify({"surge_mode": state.surge_mode})


@app.route("/api/reset", methods=["POST"])
def api_reset():
    state.reset()
    return jsonify({"status": "reset", "simulated_data": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

