"""E7/E9: Background expiry worker and parallel referral / escalation ladder."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from os_engine.reservation import HoldRecord, ReservationEngine


class BackgroundWorkers:
    """Coordinates parallel first-accept-wins referrals, hold expiry, and escalation."""

    def __init__(self, reservation_engine: ReservationEngine) -> None:
        self.engine = reservation_engine
        self.escalation_log: list[dict[str, Any]] = []

    def send_parallel_referral(
        self,
        request_id: str,
        candidate_hospital_ids: list[str],
        facilities: list[str],
        batch_size: int = 3,
        ttl_seconds: int = 120,
    ) -> list[HoldRecord]:
        """Send referral to top-N hospitals in parallel with tentative holds."""
        created_holds: list[HoldRecord] = []
        for hid in candidate_hospital_ids[:batch_size]:
            hold = self.engine.prepare_hold(
                request_id=request_id,
                hospital_id=hid,
                facilities=facilities,
                ttl_seconds=ttl_seconds,
            )
            if hold is not None:
                created_holds.append(hold)
        return created_holds

    def sweep_expired_and_escalate(
        self,
        fallback_candidates_by_request: dict[str, list[str]] | None = None,
        facilities_by_request: dict[str, list[str]] | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Expire timed-out holds and escalate to next candidate if none remain."""
        expired = self.engine.expire_stale_holds(now=now)
        escalated: list[dict[str, Any]] = []
        fallback_candidates_by_request = fallback_candidates_by_request or {}
        facilities_by_request = facilities_by_request or {}

        for hold in expired:
            req_id = hold.request_id
            active = [
                h
                for h in self.engine.holds.values()
                if h.request_id == req_id and h.phase in ("PREPARE", "COMMITTED")
            ]
            if not active:
                tried = {h.to_hospital for h in self.engine.holds.values() if h.request_id == req_id}
                remaining = [c for c in fallback_candidates_by_request.get(req_id, []) if c not in tried]
                if remaining:
                    next_hid = remaining[0]
                    new_hold = self.engine.prepare_hold(
                        request_id=req_id,
                        hospital_id=next_hid,
                        facilities=facilities_by_request.get(req_id, hold.facilities),
                    )
                    if new_hold:
                        entry = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "request_id": req_id,
                            "from_expired": hold.to_hospital,
                            "escalated_to": next_hid,
                            "hold_id": new_hold.hold_id,
                        }
                        self.escalation_log.append(entry)
                        escalated.append(entry)

        return {
            "expired_count": len(expired),
            "expired_holds": [h.to_dict() for h in expired],
            "escalated": escalated,
        }

