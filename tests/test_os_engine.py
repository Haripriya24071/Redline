"""OS Engine unit, concurrency, and acceptance tests (T1–T6, T8, T12)."""

import threading
from datetime import datetime, timedelta, timezone

import pytest

from os_engine.banker import default_hospital_b_banker
from os_engine.deadlock import ResourceAllocationGraph, sort_facilities_for_acquisition
from os_engine.matcher import match_hospitals
from os_engine.reservation import ConflictError, ReservationEngine
from os_engine.scheduler import Process, ProcessState, Scheduler, SchedulerPolicy, run_benchmark_suite
from os_engine.simulator import ScenarioSimulator
from os_engine.workers import BackgroundWorkers


def test_t1_no_double_booking_concurrent():
    """T1: Two threads reserve the last ICU bed simultaneously; exactly one succeeds."""
    for _ in range(100):
        engine = ReservationEngine()
        engine.register_facility("HOSP-B", "ICU", total_units=2, free_units=1)
        results = []

        def try_reserve(req_id: str) -> None:
            hold = engine.prepare_hold(req_id, "HOSP-B", ["ICU"])
            results.append(hold is not None)

        t1 = threading.Thread(target=try_reserve, args=("REQ-1",))
        t2 = threading.Thread(target=try_reserve, args=("REQ-2",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        assert results.count(True) == 1
        assert engine.semaphores["HOSP-B"]["ICU"].free_units == 0


def test_t2_priority_preemption():
    """T2: P1 preempts running P7; P7 returns to READY."""
    sched = Scheduler(policy=SchedulerPolicy.PREEMPTIVE_PRIORITY)
    p7 = Process("P7", "Planned transfer", 0, 7, 5)
    sched.admit(p7)
    sched.step()
    assert sched.running_pid == "P7"

    p1 = Process("P1", "Cardiac arrest", 1, 1, 2)
    sched.admit(p1)
    assert p7.state == ProcessState.READY
    sched.step()
    assert sched.running_pid == "P1"


def test_t3_aging_prevents_starvation():
    """T3: Continuous P1 stream with aging still dispatches P8."""
    res = ScenarioSimulator.run_aging_starvation_demo()
    assert res["with_aging_first_dispatch"] is not None
    assert res["with_aging_first_dispatch"] <= 80


def test_t4_hold_timeout_and_escalation():
    """T4: Expired hold releases semaphore and escalates to next hospital."""
    engine = ReservationEngine(hold_ttl_seconds=1)
    engine.register_facility("HOSP-B", "ICU", 2, 1)
    engine.register_facility("HOSP-C", "ICU", 2, 2)
    workers = BackgroundWorkers(engine)

    holds = workers.send_parallel_referral("REQ-X", ["HOSP-B"], ["ICU"], batch_size=1, ttl_seconds=1)
    assert len(holds) == 1
    assert engine.semaphores["HOSP-B"]["ICU"].free_units == 0

    future = datetime.now(timezone.utc) + timedelta(seconds=10)
    sweep = workers.sweep_expired_and_escalate(
        fallback_candidates_by_request={"REQ-X": ["HOSP-B", "HOSP-C"]},
        facilities_by_request={"REQ-X": ["ICU"]},
        now=future,
    )
    assert sweep["expired_count"] == 1
    assert engine.semaphores["HOSP-B"]["ICU"].free_units == 1
    assert len(sweep["escalated"]) == 1
    assert sweep["escalated"][0]["escalated_to"] == "HOSP-C"


def test_t5_parallel_referral_first_accept_wins():
    """T5: Parallel referral to 3 hospitals; first accept commits and releases other 2 holds."""
    engine = ReservationEngine()
    for hid in ("H1", "H2", "H3"):
        engine.register_facility(hid, "ICU", 2, 1)
    workers = BackgroundWorkers(engine)

    holds = workers.send_parallel_referral("REQ-P", ["H1", "H2", "H3"], ["ICU"], batch_size=3)
    assert len(holds) == 3

    committed = engine.commit_hold(holds[1].hold_id)
    assert committed.phase == "COMMITTED"
    assert engine.semaphores["H1"]["ICU"].free_units == 1
    assert engine.semaphores["H2"]["ICU"].free_units == 0
    assert engine.semaphores["H3"]["ICU"].free_units == 1


def test_t6_bankers_safe_state_check():
    """T6: Hospital B worked example — Req-B ventilator granted, Req-C ventilator denied."""
    banker = default_hospital_b_banker()
    assert banker.is_safe_state().safe is True

    res_b = banker.request_resources("Req-B", [0, 1, 0])
    assert res_b.safe is True

    banker2 = default_hospital_b_banker()
    res_c = banker2.request_resources("Req-C", [0, 1, 0])
    assert res_c.safe is False


def test_deadlock_rag_and_resource_ordering():
    """Deadlock cycle detection + victim selection + resource ordering."""
    assert sort_facilities_for_acquisition(["VENTILATOR", "ICU"]) == ["ICU", "VENTILATOR"]

    rag = ResourceAllocationGraph()
    rag.add_hold("Req-X", "R1:ICU", priority=2)
    rag.add_hold("Req-Y", "R2:Vent", priority=5)
    rag.add_wait("Req-X", "R2:Vent", priority=2)
    rag.add_wait("Req-Y", "R1:ICU", priority=5)
    recovery = rag.recover_if_deadlocked()
    assert recovery["deadlocked"] is True
    assert recovery["victim"] == "Req-Y"
    assert rag.detect_cycle() is None


def test_t8_stale_data_ranked_lower():
    """T8: Stale hospital (40m old) is flagged stale and ranked below fresh hospital."""
    now = datetime.now(timezone.utc)
    fresh = (now - timedelta(minutes=2)).isoformat()
    stale = (now - timedelta(minutes=40)).isoformat()

    from_h = {"hospital_id": "H0", "lat": 12.97, "lng": 77.59}
    hospitals = [
        {"hospital_id": "H1", "name": "Stale Hosp", "address": "A", "lat": 12.971, "lng": 77.591, "trust_score": 0.9, "incoming_load": 0},
        {"hospital_id": "H2", "name": "Fresh Hosp", "address": "B", "lat": 12.98, "lng": 77.60, "trust_score": 0.9, "incoming_load": 0},
    ]
    facs = {
        "H1": {"ICU": {"free_units": 2, "total_units": 4, "version": 1, "last_updated": stale}},
        "H2": {"ICU": {"free_units": 2, "total_units": 4, "version": 1, "last_updated": fresh}},
    }
    res = match_hospitals(from_h, hospitals, facs, ["ICU"], now=now)
    assert res["eligible"][0]["hospital_id"] == "H2"
    assert res["eligible"][1]["is_stale"] is True


def test_benchmark_suite_matches_case_study_numbers():
    """Verify 8-process scheduling benchmark matches Section 9 / 15.1 metrics."""
    bench = run_benchmark_suite()
    assert bench["fcfs"]["avg_waiting"] == 14.12
    assert bench["sjf"]["avg_waiting"] == 11.0
    assert bench["preemptive_priority"]["critical_avg_response"] == 0.0
    assert bench["round_robin"]["avg_waiting"] == 19.25


def test_t12_surge_mode_distribution():
    """T12: 20 Priority 1 requests distributed across hospitals in FIFO order."""
    res = ScenarioSimulator.run_surge_simulation(num_requests=20)
    assert res["fifo_order_preserved"] is True
    assert res["aging_suspended_for_p1"] is True
    assert sum(res["distribution"].values()) == 20


def test_optimistic_concurrency_conflict():
    """T7: Updating with stale version raises ConflictError."""
    engine = ReservationEngine()
    engine.register_facility("HOSP-A", "ICU", 4, 2)
    engine.update_availability("HOSP-A", "ICU", 3, expected_version=1)
    with pytest.raises(ConflictError):
        engine.update_availability("HOSP-A", "ICU", 1, expected_version=1)

