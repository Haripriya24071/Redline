"""E6: Hospital Matcher with two-stage filtering, ETA, trust, freshness, and explainable scores."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two coordinates."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_staleness_minutes(last_updated: str, now: datetime | None = None) -> float:
    """Compute minutes since last facility update."""
    ref = now or datetime.now(timezone.utc)
    try:
        ts = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return max(0.0, (ref - ts).total_seconds() / 60.0)
    except ValueError:
        return 60.0


def compute_match_score(
    eta_min: float,
    trust: float,
    staleness_min: float,
    incoming_load: int,
    max_eta: float = 45.0,
    max_stale: float = 60.0,
    max_load: float = 10.0,
) -> dict[str, Any]:
    """Compute explainable match score (lower is better):
    Score = 0.50 * ETA_norm + 0.20 * (1 - trust) + 0.15 * staleness_norm + 0.15 * load_norm
    """
    eta_norm = min(1.0, max(0.0, eta_min / max_eta))
    trust_penalty = min(1.0, max(0.0, 1.0 - trust))
    stale_norm = min(1.0, max(0.0, staleness_min / max_stale))
    load_norm = min(1.0, max(0.0, incoming_load / max_load))

    score = (
        0.50 * eta_norm
        + 0.20 * trust_penalty
        + 0.15 * stale_norm
        + 0.15 * load_norm
    )
    return {
        "score": round(score, 4),
        "factors": {
            "eta_min": round(eta_min, 1),
            "eta_norm": round(eta_norm, 3),
            "trust": round(trust, 2),
            "trust_penalty": round(trust_penalty, 3),
            "staleness_min": round(staleness_min, 1),
            "staleness_norm": round(stale_norm, 3),
            "incoming_load": incoming_load,
            "load_norm": round(load_norm, 3),
        },
        "weights": {"eta": 0.50, "trust": 0.20, "freshness": 0.15, "load": 0.15},
    }


def match_hospitals(
    from_hospital: dict[str, Any],
    hospitals: list[dict[str, Any]],
    facilities_by_hospital: dict[str, dict[str, dict[str, Any]]],
    required_facilities: list[str],
    surge_mode: bool = False,
    stale_threshold_min: float = 30.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Two-stage matching:
    Stage 1: Filter out referring hospital and hospitals lacking required free units.
    Stage 2: Rank eligible hospitals with explainable score (and load-balance in surge mode).
    """
    eligible: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for hosp in hospitals:
        hid = hosp["hospital_id"]
        if hid == from_hospital["hospital_id"]:
            continue

        facs = facilities_by_hospital.get(hid, {})
        missing = []
        min_free = 999
        worst_stale = 0.0
        for req_fac in required_facilities:
            rec = facs.get(req_fac)
            if not rec or rec["free_units"] <= 0:
                missing.append(req_fac)
            else:
                min_free = min(min_free, rec["free_units"])
                worst_stale = max(worst_stale, compute_staleness_minutes(rec["last_updated"], now))

        if missing:
            excluded.append(
                {
                    "hospital_id": hid,
                    "name": hosp["name"],
                    "reason": f"Insufficient {', '.join(missing)}",
                }
            )
            continue

        is_stale = worst_stale >= stale_threshold_min
        if surge_mode and is_stale:
            excluded.append(
                {
                    "hospital_id": hid,
                    "name": hosp["name"],
                    "reason": f"Skipped in surge mode (stale {int(worst_stale)}m)",
                }
            )
            continue

        dist_km = haversine_km(
            from_hospital["lat"], from_hospital["lng"], hosp["lat"], hosp["lng"]
        )
        eta_min = max(4.0, (dist_km / 38.0) * 60.0)
        load_for_score = hosp.get("incoming_load", 0)
        if surge_mode and min_free <= 1:
            load_for_score += 8  # Deprioritize hospitals down to their last unit during surge

        scoring = compute_match_score(
            eta_min=eta_min,
            trust=hosp.get("trust_score", 0.85),
            staleness_min=worst_stale,
            incoming_load=load_for_score,
        )

        eligible.append(
            {
                "hospital_id": hid,
                "name": hosp["name"],
                "address": hosp["address"],
                "distance_km": round(dist_km, 1),
                "eta_min": scoring["factors"]["eta_min"],
                "trust_score": hosp.get("trust_score", 0.85),
                "staleness_min": scoring["factors"]["staleness_min"],
                "is_stale": is_stale,
                "incoming_load": hosp.get("incoming_load", 0),
                "score": scoring["score"],
                "explanation": scoring,
                "facilities": {
                    f: {
                        "free_units": facs[f]["free_units"],
                        "total_units": facs[f]["total_units"],
                        "version": facs[f]["version"],
                    }
                    for f in required_facilities
                    if f in facs
                },
            }
        )

    eligible.sort(key=lambda item: (item["is_stale"], item["score"], item["staleness_min"]))
    return {
        "eligible": eligible,
        "excluded": excluded,
        "required_facilities": required_facilities,
        "surge_mode": surge_mode,
    }

