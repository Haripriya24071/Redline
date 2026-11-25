"""E5: CPU Scheduler for HEMS-Link transfer requests.

Models transfer requests as OS processes with five states (NEW, READY, RUNNING,
WAITING, TERMINATED) and supports Preemptive Priority with aging, MLFQ, FCFS,
non-preemptive SJF, Round Robin, and Surge FIFO (Priority 1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProcessState(str, Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    TERMINATED = "TERMINATED"


class SchedulerPolicy(str, Enum):
    PREEMPTIVE_PRIORITY = "preemptive_priority"
    NON_PREEMPTIVE_PRIORITY = "non_preemptive_priority"
    MLFQ = "mlfq"
    FCFS = "fcfs"
    SJF = "sjf"
    SRTF = "srtf"
    ROUND_ROBIN = "round_robin"
    EDF = "edf"


CASE_PRIORITY_MAP: dict[str, int] = {
    "cardiac_arrest": 1,
    "trauma": 2,
    "icu_monitoring": 2,
    "stroke": 3,
    "stat_lab_test": 3,
    "availability_sync": 4,
    "pharmacy_stat": 4,
    "record_share": 5,
    "op_triage": 5,
    "specialist_enquiry": 6,
    "planned_transfer": 7,
    "pharmacy_refill": 7,
    "discharge_back": 8,
}

CASE_CATEGORY_MAP: dict[str, str] = {
    "cardiac_arrest": "Emergency",
    "trauma": "Emergency",
    "icu_monitoring": "ICU Monitoring",
    "stroke": "Emergency",
    "stat_lab_test": "Laboratory",
    "availability_sync": "Transfer",
    "pharmacy_stat": "Pharmacy",
    "record_share": "Laboratory",
    "op_triage": "OP Patient",
    "specialist_enquiry": "OP Patient",
    "planned_transfer": "Transfer",
    "pharmacy_refill": "Pharmacy",
    "discharge_back": "OP Patient",
}


@dataclass
class Process:
    """Process Control Block (PCB) for a hospital activity or transfer request."""

    pid: str
    name: str
    arrival_time: int
    priority: int  # 1 = highest, 8 = lowest
    burst_time: int
    case_type: str = "planned_transfer"
    category: str | None = None
    deadline: int | None = None
    state: ProcessState = ProcessState.NEW
    remaining_time: int = field(init=False)
    effective_priority: int = field(init=False)
    wait_ticks: int = 0
    mlfq_level: int = 0
    quantum_used: int = 0
    first_dispatch_time: int | None = None
    completion_time: int | None = None
    waiting_reason: str | None = None
    aged_count: int = 0

    def __post_init__(self) -> None:
        self.remaining_time = self.burst_time
        self.effective_priority = self.priority
        if self.category is None:
            self.category = CASE_CATEGORY_MAP.get(self.case_type, "Hospital Activity")
        if self.deadline is None:
            slack_by_prio = {1: 3, 2: 5, 3: 7, 4: 12, 5: 15, 6: 20, 7: 26, 8: 32}
            self.deadline = self.arrival_time + self.burst_time + slack_by_prio.get(self.priority, 20)
        if self.priority <= 2:
            self.mlfq_level = 0
        elif self.priority <= 6:
            self.mlfq_level = 1
        else:
            self.mlfq_level = 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "pid": self.pid,
            "name": self.name,
            "arrival_time": self.arrival_time,
            "priority": self.priority,
            "effective_priority": self.effective_priority,
            "burst_time": self.burst_time,
            "remaining_time": self.remaining_time,
            "case_type": self.case_type,
            "category": self.category,
            "deadline": self.deadline,
            "state": self.state.value,
            "wait_ticks": self.wait_ticks,
            "mlfq_level": self.mlfq_level,
            "first_dispatch_time": self.first_dispatch_time,
            "completion_time": self.completion_time,
            "waiting_reason": self.waiting_reason,
            "aged_count": self.aged_count,
        }


class Scheduler:
    """Stateful OS scheduler supporting Preemptive/Non-Preemptive Priority + Aging, MLFQ, FCFS, SJF, SRTF, RR, and EDF."""

    def __init__(
        self,
        policy: SchedulerPolicy = SchedulerPolicy.PREEMPTIVE_PRIORITY,
        aging_interval: int = 10,
        quantum: int = 3,
        surge_mode: bool = False,
    ) -> None:
        self.policy = policy
        self.aging_interval = aging_interval
        self.quantum = max(1, quantum)
        self.surge_mode = surge_mode
        self.clock = 0
        self.idle_ticks = 0
        self.processes: dict[str, Process] = {}
        self.ready_queue: list[str] = []
        self.waiting_queue: list[str] = []
        self.running_pid: str | None = None
        self.timeline: list[dict[str, Any]] = []
        self.decisions: list[dict[str, Any]] = []
        self.context_switches = 0

    def admit(self, proc: Process) -> None:
        """Admit a NEW process into the READY queue (and pre-empt if needed)."""
        proc.state = ProcessState.READY
        self.processes[proc.pid] = proc
        self.ready_queue.append(proc.pid)
        self._log_decision("ADMIT", proc.pid, f"P{proc.effective_priority} ({proc.category}) admitted to READY")
        self._maybe_preempt(proc.pid)

    def _log_decision(self, action: str, pid: str, detail: str) -> None:
        self.decisions.append(
            {
                "tick": self.clock,
                "action": action,
                "pid": pid,
                "detail": detail,
            }
        )

    def _maybe_preempt(self, candidate_pid: str) -> None:
        if self.running_pid is None or self.policy not in (
            SchedulerPolicy.PREEMPTIVE_PRIORITY,
            SchedulerPolicy.MLFQ,
            SchedulerPolicy.SRTF,
            SchedulerPolicy.EDF,
        ):
            return
        running = self.processes[self.running_pid]
        candidate = self.processes[candidate_pid]
        should_preempt = False
        reason = ""
        if self.policy == SchedulerPolicy.PREEMPTIVE_PRIORITY:
            should_preempt = candidate.effective_priority < running.effective_priority
            reason = f"P{candidate.effective_priority} < P{running.effective_priority}"
        elif self.policy == SchedulerPolicy.SRTF:
            should_preempt = candidate.remaining_time < running.remaining_time
            reason = f"RT {candidate.remaining_time} < RT {running.remaining_time}"
        elif self.policy == SchedulerPolicy.EDF:
            cand_dl = candidate.deadline if candidate.deadline is not None else 99999
            run_dl = running.deadline if running.deadline is not None else 99999
            should_preempt = cand_dl < run_dl
            reason = f"DL {cand_dl} < DL {run_dl}"
        elif self.policy == SchedulerPolicy.MLFQ:
            should_preempt = (
                candidate.mlfq_level < running.mlfq_level
                or (
                    candidate.mlfq_level == running.mlfq_level
                    and candidate.effective_priority < running.effective_priority
                )
            )
            reason = f"Q{candidate.mlfq_level}/P{candidate.effective_priority}"

        if should_preempt:
            running.state = ProcessState.READY
            running.quantum_used = 0
            self.ready_queue.append(running.pid)
            self.running_pid = None
            self.context_switches += 1
            self._log_decision(
                "PREEMPT",
                candidate.pid,
                f"Pre-empted {running.pid} for {candidate.pid} ({reason})",
            )

    def move_to_waiting(self, pid: str, reason: str) -> None:
        """Block a running or ready process in WAITING state (e.g. awaiting reply)."""
        proc = self.processes[pid]
        if self.running_pid == pid:
            self.running_pid = None
        if pid in self.ready_queue:
            self.ready_queue.remove(pid)
        proc.state = ProcessState.WAITING
        proc.waiting_reason = reason
        if pid not in self.waiting_queue:
            self.waiting_queue.append(pid)
        self._log_decision("WAIT", pid, reason)

    def wake_up(self, pid: str) -> None:
        """Move a WAITING process back to READY when reply/resource arrives."""
        proc = self.processes[pid]
        if pid in self.waiting_queue:
            self.waiting_queue.remove(pid)
        proc.state = ProcessState.READY
        proc.waiting_reason = None
        if pid not in self.ready_queue:
            self.ready_queue.append(pid)
        self._log_decision("WAKE", pid, "Returned to READY queue")
        self._maybe_preempt(pid)

    def _select_next_pid(self) -> str | None:
        if not self.ready_queue:
            return None

        if self.surge_mode:
            # In surge mode, Priority 1 requests use strict FIFO
            p1_pids = [pid for pid in self.ready_queue if self.processes[pid].priority == 1]
            if p1_pids:
                return p1_pids[0]

        if self.policy == SchedulerPolicy.FCFS:
            return self.ready_queue[0]
        if self.policy == SchedulerPolicy.SJF:
            return min(
                self.ready_queue,
                key=lambda pid: (self.processes[pid].burst_time, self.processes[pid].arrival_time),
            )
        if self.policy == SchedulerPolicy.SRTF:
            return min(
                self.ready_queue,
                key=lambda pid: (self.processes[pid].remaining_time, self.processes[pid].arrival_time),
            )
        if self.policy == SchedulerPolicy.EDF:
            return min(
                self.ready_queue,
                key=lambda pid: (
                    self.processes[pid].deadline if self.processes[pid].deadline is not None else 99999,
                    self.processes[pid].effective_priority,
                    self.processes[pid].arrival_time,
                ),
            )
        if self.policy == SchedulerPolicy.ROUND_ROBIN:
            return self.ready_queue[0]
        if self.policy == SchedulerPolicy.MLFQ:
            return min(
                self.ready_queue,
                key=lambda pid: (
                    self.processes[pid].mlfq_level,
                    self.processes[pid].effective_priority,
                    self.processes[pid].arrival_time,
                ),
            )
        # PREEMPTIVE_PRIORITY and NON_PREEMPTIVE_PRIORITY
        return min(
            self.ready_queue,
            key=lambda pid: (
                self.processes[pid].effective_priority,
                self.processes[pid].arrival_time,
            ),
        )

    def step(self) -> dict[str, Any] | None:
        """Advance the scheduler by 1 normalised time unit."""
        # 1. Apply aging to waiting READY processes
        for pid in self.ready_queue:
            proc = self.processes[pid]
            if self.surge_mode and proc.priority == 1:
                continue  # Aging suspended for P1 FIFO in surge mode
            proc.wait_ticks += 1
            if (
                self.aging_interval > 0
                and proc.wait_ticks % self.aging_interval == 0
                and proc.effective_priority > 1
            ):
                proc.effective_priority -= 1
                proc.aged_count += 1
                if proc.mlfq_level > 0:
                    proc.mlfq_level -= 1
                self._log_decision(
                    "AGING",
                    pid,
                    f"Boosted to effective priority P{proc.effective_priority}",
                )

        # 2. Check if running process needs quantum rotation (RR / MLFQ)
        if self.running_pid is not None:
            running = self.processes[self.running_pid]
            if self.policy == SchedulerPolicy.ROUND_ROBIN and running.quantum_used >= self.quantum:
                running.state = ProcessState.READY
                running.quantum_used = 0
                self.ready_queue.append(running.pid)
                self.running_pid = None
                self.context_switches += 1
            elif self.policy == SchedulerPolicy.MLFQ:
                level_quantum = 2 if running.mlfq_level == 0 else (4 if running.mlfq_level == 1 else 9999)
                if running.quantum_used >= level_quantum:
                    running.state = ProcessState.READY
                    running.quantum_used = 0
                    if running.mlfq_level < 2:
                        running.mlfq_level += 1
                    self.ready_queue.append(running.pid)
                    self.running_pid = None
                    self.context_switches += 1

        # 3. Pre-emption check before dispatch
        if self.running_pid is not None and self.ready_queue:
            best_ready = self._select_next_pid()
            if best_ready is not None:
                self._maybe_preempt(best_ready)

        # 4. Dispatch if CPU idle
        if self.running_pid is None:
            next_pid = self._select_next_pid()
            if next_pid is not None:
                self.ready_queue.remove(next_pid)
                proc = self.processes[next_pid]
                proc.state = ProcessState.RUNNING
                if proc.first_dispatch_time is None:
                    proc.first_dispatch_time = self.clock
                self.running_pid = next_pid
                self._log_decision("DISPATCH", next_pid, f"Dispatched at t={self.clock}")

        # 5. Execute 1 tick
        event: dict[str, Any] | None = None
        if self.running_pid is not None:
            proc = self.processes[self.running_pid]
            proc.remaining_time -= 1
            proc.quantum_used += 1
            event = {
                "tick": self.clock,
                "pid": proc.pid,
                "name": proc.name,
                "priority": proc.effective_priority,
            }
            if self.timeline and self.timeline[-1]["pid"] == proc.pid and self.timeline[-1]["end"] == self.clock:
                self.timeline[-1]["end"] = self.clock + 1
            else:
                self.timeline.append(
                    {
                        "pid": proc.pid,
                        "name": proc.name,
                        "start": self.clock,
                        "end": self.clock + 1,
                        "priority": proc.priority,
                        "category": proc.category,
                    }
                )

            if proc.remaining_time <= 0:
                proc.state = ProcessState.TERMINATED
                proc.completion_time = self.clock + 1
                self._log_decision("TERMINATE", proc.pid, f"Completed at t={self.clock + 1}")
                self.running_pid = None
        else:
            self.idle_ticks += 1

        self.clock += 1
        return event

    def snapshot(self) -> dict[str, Any]:
        """Return live state for /api/monitor."""
        active_ticks = max(0, self.clock - self.idle_ticks)
        cpu_util = round((active_ticks / self.clock) * 100, 1) if self.clock > 0 else 0.0
        return {
            "policy": self.policy.value,
            "quantum": self.quantum,
            "aging_interval": self.aging_interval,
            "surge_mode": self.surge_mode,
            "clock": self.clock,
            "idle_ticks": self.idle_ticks,
            "cpu_utilization_pct": cpu_util,
            "running": self.processes[self.running_pid].to_dict() if self.running_pid else None,
            "ready_queue": [self.processes[pid].to_dict() for pid in self.ready_queue],
            "waiting_queue": [self.processes[pid].to_dict() for pid in self.waiting_queue],
            "all_processes": [p.to_dict() for p in self.processes.values()],
            "timeline": self.timeline[-60:],
            "decisions": self.decisions[-30:],
            "context_switches": self.context_switches,
        }


def default_workload() -> list[Process]:
    """Return the exact 8-process workload from Section 9.1 of the case study."""
    return [
        Process("T1", "Availability sync", 0, 4, 8, "availability_sync"),
        Process("T2", "Step-down transfer", 0, 8, 3, "discharge_back"),
        Process("T3", "Specialist enquiry", 1, 6, 4, "specialist_enquiry"),
        Process("T4", "Planned dialysis transfer", 2, 7, 3, "planned_transfer"),
        Process("T5", "Record / lab sharing", 3, 5, 4, "record_share"),
        Process("T6", "Stroke neuro-unit", 4, 3, 5, "stroke"),
        Process("T7", "Road accident ICU + vent", 5, 2, 6, "trauma"),
        Process("T8", "Cardiac arrest ICU", 6, 1, 7, "cardiac_arrest"),
    ]


def hospital_10_workload() -> list[Process]:
    """Return a comprehensive 10-process Case Study 2 workload covering all 5 hospital subsystems."""
    return [
        Process("H1", "OP Walk-in Registration", 0, 6, 4, "op_triage", "OP Patient", deadline=28),
        Process("H2", "Routine Lab CBC Batch", 0, 5, 6, "record_share", "Laboratory", deadline=26),
        Process("H3", "Pharmacy Ward Refill", 1, 7, 3, "pharmacy_refill", "Pharmacy", deadline=32),
        Process("H4", "ICU Ventilator Telemetry", 2, 2, 4, "icu_monitoring", "ICU Monitoring", deadline=9),
        Process("H5", "Cardiac Arrest Code Blue", 3, 1, 6, "cardiac_arrest", "Emergency", deadline=10),
        Process("H6", "Stat ABG Blood Gas Lab", 4, 3, 3, "stat_lab_test", "Laboratory", deadline=12),
        Process("H7", "Road Trauma Multi-Organ", 5, 2, 5, "trauma", "Emergency", deadline=14),
        Process("H8", "ICU Epinephrine Stat", 6, 4, 2, "pharmacy_stat", "Pharmacy", deadline=16),
        Process("H9", "Stroke Thrombolysis Unit", 7, 3, 4, "stroke", "Emergency", deadline=18),
        Process("H10", "OP Discharge Summary", 8, 8, 3, "discharge_back", "OP Patient", deadline=38),
    ]


def clone_workload(procs: list[Process]) -> list[Process]:
    """Create fresh Process instances from an existing workload list."""
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
        for p in procs
    ]


def simulate_algorithm(
    policy: SchedulerPolicy,
    workload: list[Process] | None = None,
    quantum: int = 3,
    aging_interval: int = 0,
) -> dict[str, Any]:
    """Run a full simulation of one algorithm and return metrics + Gantt chart."""
    procs = clone_workload(workload) if workload is not None else default_workload()
    sched = Scheduler(policy=policy, aging_interval=aging_interval, quantum=quantum)
    pending = sorted(procs, key=lambda p: p.arrival_time)
    total_burst = sum(p.burst_time for p in procs)
    max_arrival = max((p.arrival_time for p in procs), default=0)

    while len([p for p in sched.processes.values() if p.state == ProcessState.TERMINATED]) < len(procs):
        arriving = [p for p in pending if p.arrival_time == sched.clock]
        for p in arriving:
            sched.admit(p)
        sched.step()
        if sched.clock > max_arrival + total_burst + 200:
            break

    rows = []
    for p in procs:
        ct = p.completion_time or 0
        tat = ct - p.arrival_time
        wt = tat - p.burst_time
        rt = (p.first_dispatch_time if p.first_dispatch_time is not None else 0) - p.arrival_time
        dl = p.deadline if p.deadline is not None else (p.arrival_time + p.burst_time + 20)
        slack = dl - ct
        rows.append(
            {
                "pid": p.pid,
                "name": p.name,
                "category": p.category,
                "arrival": p.arrival_time,
                "priority": p.priority,
                "burst": p.burst_time,
                "deadline": dl,
                "completion": ct,
                "turnaround": tat,
                "waiting": wt,
                "response": rt,
                "slack": slack,
                "deadline_met": ct <= dl,
            }
        )

    critical = [r for r in rows if r["priority"] <= 3 or r["pid"] in ("T6", "T7", "T8")]
    n = len(rows) or 1
    cn = len(critical) or 1
    total_time = max((r["completion"] for r in rows), default=1) or 1
    deadline_misses = sum(1 for r in rows if not r["deadline_met"])
    return {
        "policy": policy.value,
        "quantum": quantum,
        "rows": rows,
        "gantt": sched.timeline,
        "avg_waiting": round(sum(r["waiting"] for r in rows) / n, 2),
        "avg_turnaround": round(sum(r["turnaround"] for r in rows) / n, 2),
        "avg_response": round(sum(r["response"] for r in rows) / n, 2),
        "critical_avg_waiting": round(sum(r["waiting"] for r in critical) / cn, 2) if critical else 0.0,
        "critical_avg_response": round(sum(r["response"] for r in critical) / cn, 2) if critical else 0.0,
        "context_switches": sched.context_switches,
        "total_time": total_time,
        "cpu_utilization_pct": round((total_burst / total_time) * 100, 1),
        "throughput": round(len(rows) / total_time, 3),
        "deadline_misses": deadline_misses,
        "sla_compliance_pct": round(((len(rows) - deadline_misses) / n) * 100, 1),
    }


def run_benchmark_suite() -> dict[str, Any]:
    """Compare FCFS, SJF, Preemptive Priority, and Round Robin (Q=3) on the 8-process set."""
    return {
        "fcfs": simulate_algorithm(SchedulerPolicy.FCFS),
        "sjf": simulate_algorithm(SchedulerPolicy.SJF),
        "preemptive_priority": simulate_algorithm(SchedulerPolicy.PREEMPTIVE_PRIORITY),
        "round_robin": simulate_algorithm(SchedulerPolicy.ROUND_ROBIN, quantum=3),
    }


def run_extended_benchmark(
    workload: list[Process] | None = None,
    quantum: int = 3,
    aging_interval: int = 10,
) -> dict[str, Any]:
    """Compare all 8 scheduling algorithms including SRTF, Non-Preemptive Priority, EDF, and MLFQ."""
    base = workload if workload is not None else hospital_10_workload()
    return {
        "fcfs": simulate_algorithm(SchedulerPolicy.FCFS, workload=base),
        "sjf": simulate_algorithm(SchedulerPolicy.SJF, workload=base),
        "srtf": simulate_algorithm(SchedulerPolicy.SRTF, workload=base),
        "non_preemptive_priority": simulate_algorithm(SchedulerPolicy.NON_PREEMPTIVE_PRIORITY, workload=base, aging_interval=aging_interval),
        "preemptive_priority": simulate_algorithm(SchedulerPolicy.PREEMPTIVE_PRIORITY, workload=base, aging_interval=aging_interval),
        "round_robin": simulate_algorithm(SchedulerPolicy.ROUND_ROBIN, workload=base, quantum=quantum),
        "edf": simulate_algorithm(SchedulerPolicy.EDF, workload=base),
        "mlfq": simulate_algorithm(SchedulerPolicy.MLFQ, workload=base, aging_interval=aging_interval),
    }


def run_quantum_sweep(workload: list[Process] | None = None, max_q: int = 8) -> list[dict[str, Any]]:
    """Evaluate Round Robin across Time Quantums Q=1..max_q for sensitivity analysis."""
    base = workload if workload is not None else default_workload()
    results = []
    for q in range(1, max_q + 1):
        sim = simulate_algorithm(SchedulerPolicy.ROUND_ROBIN, workload=base, quantum=q)
        results.append(
            {
                "quantum": q,
                "avg_waiting": sim["avg_waiting"],
                "avg_turnaround": sim["avg_turnaround"],
                "avg_response": sim["avg_response"],
                "critical_avg_response": sim["critical_avg_response"],
                "context_switches": sim["context_switches"],
                "sla_compliance_pct": sim["sla_compliance_pct"],
            }
        )
    return results

