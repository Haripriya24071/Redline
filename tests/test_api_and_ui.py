"""Flask API, RBAC, duplicate detection, and UI/Accessibility smoke tests (T7, T9, T10, T11)."""

import pytest

from app import app, state


@pytest.fixture(autouse=True)
def reset_state():
    state.reset()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_all_9_screens_and_style_guide_render(client):
    """T11: Every screen renders HTTP 200 with accessible skip link and main landmark."""
    routes = [
        "/",
        "/requests/new",
        "/matches",
        "/coordination",
        "/tracker",
        "/availability",
        "/monitor",
        "/analytics",
        "/surge",
        "/style-guide",
    ]
    for route in routes:
        resp = client.get(route)
        assert resp.status_code == 200, f"{route} returned {resp.status_code}"
        html = resp.get_data(as_text=True)
        assert 'class="skip-link"' in html
        assert '<main id="main-content"' in html


def test_t7_api_version_conflict(client):
    """T7: Stale version PATCH returns 409 Conflict."""
    r1 = client.patch(
        "/api/facilities/HOSP-RRM/ICU",
        json={"free_units": 2, "version": 1, "role": "receiving"},
    )
    assert r1.status_code == 200

    r2 = client.patch(
        "/api/facilities/HOSP-RRM/ICU",
        json={"free_units": 0, "version": 1, "role": "receiving"},
    )
    assert r2.status_code == 409
    assert r2.get_json()["code"] == "VERSION_CONFLICT"


def test_t9_duplicate_patient_detection(client):
    """T9: Referring same patient_hash twice warns with 409 DUPLICATE_DETECTED."""
    r1 = client.post(
        "/api/requests",
        json={"from_hospital": "HOSP-JAIN", "case_type": "trauma", "patient_hash": "PAT-7777"},
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/requests",
        json={"from_hospital": "HOSP-DSH", "case_type": "trauma", "patient_hash": "PAT-7777"},
    )
    assert r2.status_code == 409
    assert r2.get_json()["code"] == "DUPLICATE_DETECTED"


def test_t10_rbac_auditor_readonly_and_break_glass_logged(client):
    """T10: Auditor edit is refused (403); break-glass edit is logged in audit trail."""
    r_auditor = client.patch(
        "/api/facilities/HOSP-RRM/ICU",
        json={"free_units": 0, "version": 1, "role": "auditor"},
    )
    assert r_auditor.status_code == 403

    r_bg = client.patch(
        "/api/facilities/HOSP-RRM/ICU",
        json={"free_units": 2, "version": 1, "role": "admin", "break_glass": True},
    )
    assert r_bg.status_code == 200

    mon = client.get("/api/monitor").get_json()
    assert any(entry["break_glass"] is True for entry in mon["audit_log"])


def test_api_simulator_endpoints(client):
    """Verify /api/simulator/run and /api/analytics work end-to-end."""
    for scenario in ("race_condition", "aging", "deadlock", "priority_inheritance", "surge"):
        resp = client.post("/api/simulator/run", json={"scenario": scenario})
        assert resp.status_code == 200
        assert "summary" in resp.get_json()


def test_seeded_8_hospital_processes_and_workbench_apis(client):
    """Verify 8 seeded hospital processes, custom simulation, live stepper, analytics, and CSV export."""
    reqs = client.get("/api/requests").get_json()["requests"]
    assert len(reqs) >= 8
    categories = {r["category"] for r in reqs}
    assert {"Emergency", "ICU Monitoring", "Laboratory", "OP Patient", "Pharmacy"}.issubset(categories)

    # Custom workload simulation
    sim_resp = client.post(
        "/api/monitor/simulate",
        json={
            "quantum": 2,
            "aging": 8,
            "processes": [
                {"pid": "X1", "name": "OP", "category": "OP Patient", "arrival_time": 0, "priority": 7, "burst_time": 5, "deadline": 20},
                {"pid": "X2", "name": "Cardiac", "category": "Emergency", "arrival_time": 1, "priority": 1, "burst_time": 3, "deadline": 5},
            ],
        },
    )
    assert sim_resp.status_code == 200
    sim_data = sim_resp.get_json()
    assert "edf" in sim_data["algorithms"]
    assert "srtf" in sim_data["algorithms"]
    assert len(sim_data["quantum_sweep"]) == 8

    # Live kernel stepper & policy change
    ctrl = client.post("/api/scheduler/control", json={"action": "step", "policy": "edf"})
    assert ctrl.status_code == 200
    assert ctrl.get_json()["scheduler"]["policy"] == "edf"

    # Extended analytics & CSV export
    ana = client.get("/api/analytics?workload=hospital10").get_json()
    assert "extended_benchmark" in ana
    assert "quantum_sweep" in ana

    csv_resp = client.get("/api/export/csv?workload=case_study")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.content_type
    assert "preemptive_priority" in csv_resp.get_data(as_text=True)


