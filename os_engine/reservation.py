"""E7: Atomic Reservation Engine (Counting Semaphores + Mutex + Two-Phase Hold + Optimistic Concurrency)."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from os_engine.deadlock import sort_facilities_for_acquisition


class ConflictError(Exception):
    """Raised on optimistic concurrency version mismatch (HTTP 409)."""


class HoldExpiredError(Exception):
    """Raised when committing an expired or already aborted hold."""


@dataclass
class FacilitySemaphore:
    """Counting semaphore for a single hospital resource type."""

    hospital_id: str
    facility: str
    total_units: int
    free_units: int
    version: int = 1
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "hospital_id": self.hospital_id,
            "facility": self.facility,
            "total_units": self.total_units,
            "free_units": self.free_units,
            "version": self.version,
            "last_updated": self.last_updated,
        }


@dataclass
class HoldRecord:
    """Two-phase reservation hold record."""

    hold_id: str
    request_id: str
    to_hospital: str
    facilities: list[str]
    phase: str  # PREPARE | COMMITTED | ABORTED | EXPIRED
    reserved_until: datetime
    response: str | None = None
    responded_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "hold_id": self.hold_id,
            "request_id": self.request_id,
            "to_hospital": self.to_hospital,
            "facilities": self.facilities,
            "phase": self.phase,
            "reserved_until": self.reserved_until.isoformat(),
            "response": self.response,
            "responded_at": self.responded_at,
        }


class ReservationEngine:
    """Thread-safe atomic reservation engine protecting facility critical sections."""

    def __init__(self, hold_ttl_seconds: int = 120) -> None:
        self._mutex = threading.Lock()
        self.hold_ttl_seconds = hold_ttl_seconds
        self.semaphores: dict[str, dict[str, FacilitySemaphore]] = {}
        self.holds: dict[str, HoldRecord] = {}
        self.event_log: list[dict[str, Any]] = []

    def register_facility(
        self,
        hospital_id: str,
        facility: str,
        total_units: int,
        free_units: int,
        last_updated: str | None = None,
    ) -> None:
        with self._mutex:
            self.semaphores.setdefault(hospital_id, {})[facility] = FacilitySemaphore(
                hospital_id=hospital_id,
                facility=facility,
                total_units=total_units,
                free_units=free_units,
                last_updated=last_updated or datetime.now(timezone.utc).isoformat(),
            )

    def _log(self, event_type: str, detail: str) -> None:
        self.event_log.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                "detail": detail,
            }
        )

    def update_availability(
        self,
        hospital_id: str,
        facility: str,
        free_units: int,
        expected_version: int,
    ) -> FacilitySemaphore:
        """Optimistic concurrency update (compare-and-swap on version)."""
        with self._mutex:
            sem = self.semaphores[hospital_id][facility]
            if sem.version != expected_version:
                raise ConflictError(
                    f"Version conflict on {hospital_id}/{facility}: expected v{expected_version}, current v{sem.version}"
                )
            sem.free_units = max(0, min(sem.total_units, free_units))
            sem.version += 1
            sem.last_updated = datetime.now(timezone.utc).isoformat()
            self._log("AVAILABILITY_UPDATE", f"{hospital_id}/{facility} -> {sem.free_units} (v{sem.version})")
            return sem

    def prepare_hold(
        self,
        request_id: str,
        hospital_id: str,
        facilities: list[str],
        ttl_seconds: int | None = None,
    ) -> HoldRecord | None:
        """Phase 1 (Prepare): Atomically decrement semaphores in resource order."""
        ordered = sort_facilities_for_acquisition(facilities)
        ttl = ttl_seconds if ttl_seconds is not None else self.hold_ttl_seconds
        with self._mutex:
            hosp_facs = self.semaphores.get(hospital_id, {})
            for fac in ordered:
                sem = hosp_facs.get(fac)
                if not sem or sem.free_units <= 0:
                    return None

            # All-or-nothing wait(S) inside mutex critical section
            for fac in ordered:
                sem = hosp_facs[fac]
                sem.free_units -= 1
                sem.version += 1
                sem.last_updated = datetime.now(timezone.utc).isoformat()

            hold = HoldRecord(
                hold_id=f"HOLD-{uuid.uuid4().hex[:8].upper()}",
                request_id=request_id,
                to_hospital=hospital_id,
                facilities=ordered,
                phase="PREPARE",
                reserved_until=datetime.now(timezone.utc) + timedelta(seconds=ttl),
            )
            self.holds[hold.hold_id] = hold
            self._log("PREPARE_HOLD", f"{hold.hold_id} for {request_id} at {hospital_id} ({', '.join(ordered)})")
            return hold

    def commit_hold(self, hold_id: str) -> HoldRecord:
        """Phase 2a (Commit): Receiving hospital accepts; also aborts sibling parallel holds."""
        with self._mutex:
            hold = self.holds[hold_id]
            if hold.phase != "PREPARE":
                raise HoldExpiredError(f"Hold {hold_id} is {hold.phase}, cannot commit.")
            if datetime.now(timezone.utc) > hold.reserved_until:
                self._release_locked(hold, "EXPIRED")
                raise HoldExpiredError(f"Hold {hold_id} expired before commit.")

            hold.phase = "COMMITTED"
            hold.response = "ACCEPT"
            hold.responded_at = datetime.now(timezone.utc).isoformat()
            self._log("COMMIT_HOLD", f"{hold.hold_id} ACCEPTED by {hold.to_hospital}")

            # First-accept-wins: release all other PREPARE holds for the same request
            for other in self.holds.values():
                if other.request_id == hold.request_id and other.hold_id != hold_id and other.phase == "PREPARE":
                    self._release_locked(other, "ABORTED", response="SUPERSEDED")

            return hold

    def abort_hold(self, hold_id: str, reason: str = "REJECT") -> HoldRecord:
        """Phase 2b (Abort): Receiving hospital rejects or caller cancels -> signal(S)."""
        with self._mutex:
            hold = self.holds[hold_id]
            if hold.phase == "PREPARE":
                self._release_locked(hold, "ABORTED", response=reason)
            return hold

    def _release_locked(self, hold: HoldRecord, new_phase: str, response: str | None = None) -> None:
        for fac in hold.facilities:
            sem = self.semaphores[hold.to_hospital][fac]
            sem.free_units = min(sem.total_units, sem.free_units + 1)
            sem.version += 1
            sem.last_updated = datetime.now(timezone.utc).isoformat()
        hold.phase = new_phase
        if response:
            hold.response = response
        hold.responded_at = datetime.now(timezone.utc).isoformat()
        self._log("RELEASE_HOLD", f"{hold.hold_id} -> {new_phase} (signal restored {hold.to_hospital})")

    def expire_stale_holds(self, now: datetime | None = None) -> list[HoldRecord]:
        """Release any PREPARE holds past reserved_until."""
        ref = now or datetime.now(timezone.utc)
        expired: list[HoldRecord] = []
        with self._mutex:
            for hold in self.holds.values():
                if hold.phase == "PREPARE" and ref > hold.reserved_until:
                    self._release_locked(hold, "EXPIRED", response="TIMEOUT")
                    expired.append(hold)
        return expired

    def snapshot_semaphores(self) -> dict[str, dict[str, Any]]:
        with self._mutex:
            return {
                hid: {fac: sem.to_dict() for fac, sem in facs.items()}
                for hid, facs in self.semaphores.items()
            }

