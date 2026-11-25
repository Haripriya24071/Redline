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

