"""E8: Banker's Algorithm for multi-resource deadlock avoidance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SafeStateResult:
    safe: bool
    safe_sequence: list[str]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "safe": self.safe,
            "safe_sequence": self.safe_sequence,
            "reason": self.reason,
        }


class BankersAlgorithm:
    """Deadlock avoidance for multi-resource hospital reservations (ICU, Vent, Specialist)."""

    def __init__(
        self,
        available: list[int],
        allocations: dict[str, list[int]],
        max_need: dict[str, list[int]],
    ) -> None:
        self.available = list(available)
        self.allocations = {k: list(v) for k, v in allocations.items()}
        self.max_need = {k: list(v) for k, v in max_need.items()}

    def is_safe_state(
        self,
        available: list[int] | None = None,
        allocations: dict[str, list[int]] | None = None,
    ) -> SafeStateResult:
        """Check whether at least one safe completion sequence exists."""
        avail = list(available if available is not None else self.available)
        alloc = {k: list(v) for k, v in (allocations if allocations is not None else self.allocations).items()}
        num_res = len(avail)
        need = {
            pid: [self.max_need[pid][j] - alloc[pid][j] for j in range(num_res)]
            for pid in alloc
        }

        work = list(avail)
        finish = {pid: False for pid in alloc}
        sequence: list[str] = []

        while len(sequence) < len(alloc):
            progressed = False
            for pid in alloc:
                if not finish[pid] and all(need[pid][j] <= work[j] for j in range(num_res)):
                    for j in range(num_res):
                        work[j] += alloc[pid][j]
                    finish[pid] = True
                    sequence.append(pid)
                    progressed = True
                    break
            if not progressed:
                return SafeStateResult(
                    safe=False,
                    safe_sequence=sequence,
                    reason="No safe sequence exists; granting would risk deadlock.",
                )

        return SafeStateResult(
            safe=True,
            safe_sequence=sequence,
            reason=f"Safe sequence found: {' -> '.join(sequence)}",
        )

    def request_resources(self, pid: str, request: list[int]) -> SafeStateResult:
        """Try-allocate resources for pid; commit only if resulting state is safe."""
        if pid not in self.allocations:
            return SafeStateResult(False, [], f"Unknown request {pid}")

        num_res = len(self.available)
        need = [self.max_need[pid][j] - self.allocations[pid][j] for j in range(num_res)]
        if any(request[j] > need[j] for j in range(num_res)):
            return SafeStateResult(False, [], f"{pid} exceeded its declared maximum claim.")
        if any(request[j] > self.available[j] for j in range(num_res)):
            return SafeStateResult(False, [], f"Insufficient available resources for {pid}.")

        trial_avail = [self.available[j] - request[j] for j in range(num_res)]
        trial_alloc = {k: list(v) for k, v in self.allocations.items()}
        trial_alloc[pid] = [trial_alloc[pid][j] + request[j] for j in range(num_res)]

        result = self.is_safe_state(trial_avail, trial_alloc)
        if result.safe:
            self.available = trial_avail
            self.allocations = trial_alloc
        return result

    def snapshot(self) -> dict[str, Any]:
        state = self.is_safe_state()
        rows = []
        for pid in self.allocations:
            need = [self.max_need[pid][j] - self.allocations[pid][j] for j in range(len(self.available))]
            rows.append(
                {
                    "pid": pid,
                    "allocation": self.allocations[pid],
                    "max_need": self.max_need[pid],
                    "remaining_need": need,
                }
            )
        return {
            "available": self.available,
            "resources": ["ICU Bed", "Ventilator", "Specialist"],
            "rows": rows,
            "safe_state": state.to_dict(),
        }


def default_hospital_b_banker() -> BankersAlgorithm:
    """Worked example from Section 16.4 of the case study at Hospital B."""
    return BankersAlgorithm(
        available=[1, 1, 0],
        allocations={
            "Req-A": [1, 0, 0],
            "Req-B": [1, 1, 0],
            "Req-C": [0, 0, 1],
        },
        max_need={
            "Req-A": [1, 0, 0],
            "Req-B": [1, 2, 0],
            "Req-C": [1, 2, 1],
        },
    )

