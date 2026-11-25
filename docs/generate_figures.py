"""Generate 9 high-resolution color OS diagrams and analytical charts for the Redline Case Study 2 Report."""

from __future__ import annotations

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Patch
import numpy as np

from os_engine.scheduler import default_workload, run_extended_benchmark, run_quantum_sweep
from os_engine.simulator import ScenarioSimulator

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures_color")
os.makedirs(OUT_DIR, exist_ok=True)

NAVY = "#0F2942"
TEAL = "#0D7377"
BLUE = "#2563EB"
ICE = "#EFF6FF"
SLATE = "#475569"
CORAL = "#DC2626"
CORAL_BG = "#FEE2E2"
GREEN = "#15803D"
GREEN_BG = "#DCFCE7"
AMBER = "#B45309"
AMBER_BG = "#FEF3C7"
INDIGO = "#4338CA"
INDIGO_BG = "#E0E7FF"
BORDER = "#94A3B8"

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#CBD5E1"


def draw_box(ax, x, y, w, h, title, subtitle="", fc="#F8FAFC", ec=NAVY, tc=NAVY, lw=1.6, fs=9.5, sub_fs=7.5, radius=0.018):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.010,rounding_size={radius}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3
    )
    ax.add_patch(patch)
    if subtitle:
        ax.text(x + w / 2, y + h * 0.65, title, ha="center", va="center", fontsize=fs, fontweight="bold", color=tc, zorder=4)
        ax.text(x + w / 2, y + h * 0.28, subtitle, ha="center", va="center", fontsize=sub_fs, color=SLATE, zorder=4)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=fs, fontweight="bold", color=tc, zorder=4)


def draw_arrow(ax, x1, y1, x2, y2, label="", color=NAVY, rad=0.0, lx_off=0.0, ly_off=0.0, lw=1.6, ls="-"):
    arr = FancyArrowPatch(
        (x1, y1), (x2, y2),
        connectionstyle=f"arc3,rad={rad}",
        arrowstyle="-|>,head_length=6,head_width=3.5",
        color=color, linewidth=lw, linestyle=ls, zorder=2
    )
    ax.add_patch(arr)
    if label:
        mx = (x1 + x2) / 2 + lx_off
        my = (y1 + y2) / 2 + ly_off
        ax.text(mx, my, label, ha="center", va="center", fontsize=7.8, fontweight="bold", color=color,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.90), zorder=5)


def fig1_architecture():
    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.96, "Redline (HEMS-Link) — Layered OS & Clinical Coordination Architecture",
            ha="center", va="center", fontsize=12.5, fontweight="bold", color=NAVY)

    layers = [
        (0.75, "PRESENTATION LAYER (Liquid Glass UI • Light/Dark • EN / HI / KN • RBAC Switcher)",
         "9 Operational Screens (Dispatch, OS Kernel Workbench, Analytics, Bed Board, Surge, Tracker, Matches, Coordination, New Request) + Style Guide",
         "#EFF6FF", BLUE),
        (0.53, "FLASK REST API & SECURITY LAYER (app.py)",
         "/api/requests (409 Dup)  |  /api/matches  |  /api/refer  |  /api/facilities (409 Ver)  |  /api/monitor  |  /api/scheduler/control  |  /api/export/csv",
         "#F0FDFA", TEAL),
        (0.30, "OS KERNEL & SIMULATION ENGINE (os_engine/)",
         "8-Policy Scheduler + Aging + EDF + MLFQ  |  Explainable Matcher  |  Mutex + Semaphores + 2-Phase Hold  |  Banker's  |  RAG Deadlock  |  Workers",
         "#EEF2FF", INDIGO),
        (0.08, "SIMULATED DATA, TELEMETRY & AUDIT LAYER",
         "10 Kanakapura–Bengaluru Hospitals  |  Versioned Facility Semaphores  |  8+ Seeded Hospital Processes  |  IPC Event Log & RBAC Audit Trail",
         "#F8FAFC", SLATE),
    ]

    for y, title, sub, fc, ec in layers:
        draw_box(ax, 0.03, y, 0.94, 0.15, title, sub, fc=fc, ec=ec, tc=ec, fs=9.3, sub_fs=7.0, lw=1.8)

    draw_arrow(ax, 0.5, 0.74, 0.5, 0.695, color=BLUE)
    draw_arrow(ax, 0.5, 0.52, 0.5, 0.465, color=TEAL)
    draw_arrow(ax, 0.5, 0.29, 0.5, 0.245, color=INDIGO)

    fig.savefig(os.path.join(OUT_DIR, "fig1_architecture.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig2_dispatch_flowchart():
    fig, ax = plt.subplots(figsize=(11, 7.2), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.97, "End-to-End Hospital Activity Dispatch & OS Kernel Flowchart",
            ha="center", va="center", fontsize=12.5, fontweight="bold", color=NAVY)

    # Row 1 (y=0.82)
    draw_box(ax, 0.03, 0.82, 0.20, 0.09, "1. Activity Intake", "Emerg, ICU, Lab, OP, Pharm", fc=ICE, ec=BLUE, tc=NAVY, fs=8.5, sub_fs=7.0)
    draw_box(ax, 0.28, 0.82, 0.20, 0.09, "2. Duplicate Check?", "Active patient_hash?", fc=AMBER_BG, ec=AMBER, tc=AMBER, fs=8.5, sub_fs=7.0)
    draw_box(ax, 0.54, 0.82, 0.20, 0.09, "3. Admit PCB (READY)", "Assign P1–P8, BT, SLA DL", fc=ICE, ec=TEAL, tc=NAVY, fs=8.5, sub_fs=7.0)
    draw_box(ax, 0.79, 0.82, 0.18, 0.09, "4. CPU Scheduler", "Preempt if P_new < P_run", fc=INDIGO_BG, ec=INDIGO, tc=INDIGO, fs=8.5, sub_fs=7.0)

    # Row 2 (y=0.64) — Duplicate warning branch isolated on left
    draw_box(ax, 0.28, 0.64, 0.20, 0.085, "HTTP 409 Warning", "Prompt override or abort", fc=CORAL_BG, ec=CORAL, tc=CORAL, fs=8.3, sub_fs=7.0)

    # Row 3 (y=0.45) — Matching, Mutex, Parallel Hold
    draw_box(ax, 0.73, 0.45, 0.24, 0.10, "5. Hospital Matcher", "Filter free S>0; rank ETA/Trust", fc="#F0FDFA", ec=TEAL, tc=NAVY, fs=8.5, sub_fs=7.0)
    draw_box(ax, 0.41, 0.45, 0.26, 0.10, "6. Mutex Critical Section", "Order resources; S--, v++, PREPARE", fc=INDIGO_BG, ec=INDIGO, tc=INDIGO, fs=8.5, sub_fs=7.0)
    draw_box(ax, 0.06, 0.45, 0.28, 0.10, "7. Parallel Top-N Hold", "PCB -> WAITING; await reply", fc=AMBER_BG, ec=AMBER, tc=AMBER, fs=8.5, sub_fs=7.0)

    # Row 4 (y=0.22) — Outcomes
    draw_box(ax, 0.04, 0.22, 0.26, 0.105, "8a. ACCEPT (First Wins)", "COMMITTED; sibling signal(S)", fc=GREEN_BG, ec=GREEN, tc=GREEN, fs=8.4, sub_fs=7.0)
    draw_box(ax, 0.37, 0.22, 0.26, 0.105, "8b. REJECT / EXPIRED", "signal(S) restores; Escalate", fc=CORAL_BG, ec=CORAL, tc=CORAL, fs=8.4, sub_fs=7.0)
    draw_box(ax, 0.70, 0.22, 0.26, 0.105, "8c. Banker / RAG Check", "Deadlock -> release victim", fc="#F8FAFC", ec=SLATE, tc=NAVY, fs=8.4, sub_fs=7.0)

    # Row 5 (y=0.04) — Final Termination
    draw_box(ax, 0.28, 0.04, 0.44, 0.095, "9. TERMINATED & Audit Logged", "Ambulance ETA dispatched • Audit trail updated", fc=GREEN_BG, ec=GREEN, tc=GREEN, fs=9.0, sub_fs=7.3)

    draw_arrow(ax, 0.24, 0.865, 0.27, 0.865, color=NAVY)
    draw_arrow(ax, 0.38, 0.81, 0.38, 0.735, "Yes", color=CORAL, lx_off=0.03)
    draw_arrow(ax, 0.49, 0.865, 0.53, 0.865, "No", color=GREEN, ly_off=0.025)
    draw_arrow(ax, 0.75, 0.865, 0.78, 0.865, color=NAVY)
    draw_arrow(ax, 0.88, 0.81, 0.88, 0.56, color=INDIGO)
    draw_arrow(ax, 0.72, 0.50, 0.68, 0.50, color=TEAL)
    draw_arrow(ax, 0.40, 0.50, 0.35, 0.50, color=INDIGO)
    draw_arrow(ax, 0.17, 0.44, 0.17, 0.335, "Accept", color=GREEN, lx_off=-0.045)
    draw_arrow(ax, 0.27, 0.44, 0.47, 0.335, "Timeout / Reject", color=CORAL, lx_off=0.055)
    draw_arrow(ax, 0.58, 0.44, 0.80, 0.335, "Multi-Res", color=SLATE, lx_off=0.045)
    draw_arrow(ax, 0.54, 0.335, 0.78, 0.44, "Retry Next", color=AMBER, rad=-0.18, ly_off=-0.02, ls="--")
    draw_arrow(ax, 0.17, 0.21, 0.36, 0.145, color=GREEN)
    draw_arrow(ax, 0.83, 0.21, 0.64, 0.145, color=SLATE)

    fig.savefig(os.path.join(OUT_DIR, "fig2_dispatch_flowchart.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig3_process_states():
    fig, ax = plt.subplots(figsize=(10.8, 4.6), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.94, "Five-State Process Lifecycle & PCB Structure in Redline",
            ha="center", va="center", fontsize=12.5, fontweight="bold", color=NAVY)

    draw_box(ax, 0.04, 0.56, 0.14, 0.16, "NEW", "Intake created", fc="#F1F5F9", ec=SLATE, tc=NAVY, fs=10, sub_fs=7.5)
    draw_box(ax, 0.26, 0.56, 0.16, 0.16, "READY", "Priority + Aging Q", fc=ICE, ec=BLUE, tc=BLUE, fs=10, sub_fs=7.5)
    draw_box(ax, 0.52, 0.56, 0.16, 0.16, "RUNNING", "Matching & Mutex", fc=GREEN_BG, ec=GREEN, tc=GREEN, fs=10, sub_fs=7.5)
    draw_box(ax, 0.78, 0.56, 0.18, 0.16, "TERMINATED", "Committed / Done", fc=INDIGO_BG, ec=INDIGO, tc=INDIGO, fs=10, sub_fs=7.5)
    draw_box(ax, 0.39, 0.19, 0.20, 0.16, "WAITING", "Awaiting Hold Reply", fc=AMBER_BG, ec=AMBER, tc=AMBER, fs=10, sub_fs=7.5)

    draw_arrow(ax, 0.19, 0.64, 0.25, 0.64, "admit", color=NAVY, ly_off=0.045)
    draw_arrow(ax, 0.43, 0.67, 0.51, 0.67, "dispatch", color=GREEN, ly_off=0.045)
    draw_arrow(ax, 0.51, 0.60, 0.43, 0.60, "preempt / Q", color=CORAL, ly_off=-0.05)
    draw_arrow(ax, 0.69, 0.64, 0.77, 0.64, "accept / finish", color=INDIGO, ly_off=0.045)
    draw_arrow(ax, 0.60, 0.55, 0.52, 0.36, "parallel hold / I/O", color=AMBER, lx_off=0.08)
    draw_arrow(ax, 0.46, 0.36, 0.36, 0.55, "reply / signal(S)", color=BLUE, lx_off=-0.08)

    draw_box(ax, 0.02, 0.02, 0.96, 0.09,
             "PCB Fields:  PID  |  Category  |  Arrival Time (AT)  |  Base & Effective Priority (P1–P8)  |  Burst / Remaining  |  SLA Deadline  |  Wait Ticks  |  State",
             fc="#F8FAFC", ec="#CBD5E1", tc=NAVY, fs=7.4, lw=1.2)

    fig.savefig(os.path.join(OUT_DIR, "fig3_process_states.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig4_gantt_charts():
    # Use aging_interval=0 for baseline T1-T8 static scheduling comparison
    bench = run_extended_benchmark(workload=default_workload(), quantum=3, aging_interval=0)
    algos = [
        ("FCFS", bench["fcfs"]["gantt"]),
        ("SJF (Non-Preemptive)", bench["sjf"]["gantt"]),
        ("SRTF (Preemptive SJF)", bench["srtf"]["gantt"]),
        ("Preemptive Priority", bench["preemptive_priority"]["gantt"]),
        ("Round Robin (Q = 3)", bench["round_robin"]["gantt"]),
        ("EDF (Real-Time)", bench["edf"]["gantt"]),
    ]

    pid_colors = {
        "T1": "#3B82F6",
        "T2": "#64748B",
        "T3": "#0EA5E9",
        "T4": "#0D9488",
        "T5": "#6366F1",
        "T6": "#D97706",
        "T7": "#EA580C",
        "T8": "#DC2626",
    }

    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=300)
    y_positions = np.arange(len(algos))[::-1]

    for y, (label, gantt) in zip(y_positions, algos):
        for seg in gantt:
            s, e, pid = seg["start"], seg["end"], seg["pid"]
            w = e - s
            col = pid_colors.get(pid, SLATE)
            ax.barh(y, w, left=s, height=0.58, color=col, edgecolor="white", linewidth=1.2)
            ax.text(s + w / 2, y, pid, ha="center", va="center", color="white",
                    fontsize=7.8 if w >= 2 else 6.8, fontweight="bold")

    ax.set_yticks(y_positions)
    ax.set_yticklabels([a[0] for a in algos], fontsize=9.5, fontweight="bold", color=NAVY)
    ax.set_xlim(0, 40)
    ax.set_xticks(range(0, 41, 2))
    ax.set_xlabel("Normalised CPU Time Units (0 to 40 ticks)", fontsize=9.5, fontweight="bold", color=NAVY)
    ax.set_title("Multi-Algorithm Gantt Charts on Case Study Workload (T1–T8)", fontsize=12, fontweight="bold", color=NAVY, pad=14)
    ax.grid(axis="x", linestyle="--", alpha=0.35, color="#94A3B8")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    legend_patches = [
        Patch(facecolor=pid_colors["T8"], label="T8: Cardiac Arrest (P1)"),
        Patch(facecolor=pid_colors["T7"], label="T7: Trauma ICU (P2)"),
        Patch(facecolor=pid_colors["T6"], label="T6: Stroke Unit (P3)"),
        Patch(facecolor=pid_colors["T1"], label="T1: Avail Sync (P4)"),
        Patch(facecolor=pid_colors["T5"], label="T5: Lab Share (P5)"),
        Patch(facecolor=pid_colors["T3"], label="T3: Specialist (P6)"),
        Patch(facecolor=pid_colors["T4"], label="T4: Dialysis (P7)"),
        Patch(facecolor=pid_colors["T2"], label="T2: Discharge (P8)"),
    ]
    ax.legend(handles=legend_patches, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=4, frameon=False, fontsize=8)

    fig.savefig(os.path.join(OUT_DIR, "fig4_gantt_charts.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig5_metrics_and_quantum():
    bench = run_extended_benchmark(workload=default_workload(), quantum=3, aging_interval=0)
    sweep = run_quantum_sweep(workload=default_workload(), max_q=8)

    order = [
        ("FCFS", "fcfs"),
        ("SJF", "sjf"),
        ("SRTF", "srtf"),
        ("NP-Prio", "non_preemptive_priority"),
        ("P-Prio", "preemptive_priority"),
        ("RR Q=3", "round_robin"),
        ("EDF", "edf"),
        ("MLFQ", "mlfq"),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=300)

    x = np.arange(len(order))
    w = 0.26
    wt = [bench[k]["avg_waiting"] for _, k in order]
    tat = [bench[k]["avg_turnaround"] for _, k in order]
    crit = [bench[k]["critical_avg_response"] for _, k in order]

    ax1.bar(x - w, wt, width=w, label="Avg Waiting Time", color=BLUE)
    ax1.bar(x, tat, width=w, label="Avg Turnaround Time", color=TEAL)
    ax1.bar(x + w, crit, width=w, label="Critical Response (T6–T8)", color=CORAL)
    ax1.set_xticks(x)
    ax1.set_xticklabels([lbl for lbl, _ in order], fontsize=8, rotation=20, ha="right", color=NAVY, fontweight="bold")
    ax1.set_ylabel("Normalised Time Units (ticks)", fontsize=9, fontweight="bold", color=NAVY)
    ax1.set_title("A. 8-Algorithm Scheduling Criteria Comparison", fontsize=10.5, fontweight="bold", color=NAVY)
    ax1.grid(axis="y", linestyle="--", alpha=0.35)
    ax1.legend(fontsize=7.8, frameon=False)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    qs = [d["quantum"] for d in sweep]
    q_wt = [d["avg_waiting"] for d in sweep]
    q_sw = [d["context_switches"] for d in sweep]

    l1 = ax2.plot(qs, q_wt, marker="o", linewidth=2.2, color=BLUE, label="Avg Waiting Time")
    ax2.set_xlabel("Round Robin Time Quantum (Q)", fontsize=9, fontweight="bold", color=NAVY)
    ax2.set_ylabel("Avg Waiting Time (ticks)", fontsize=9, fontweight="bold", color=BLUE)
    ax2.tick_params(axis="y", labelcolor=BLUE)
    ax2.set_xticks(qs)
    ax2.grid(True, linestyle="--", alpha=0.35)
    ax2.spines["top"].set_visible(False)

    ax2_r = ax2.twinx()
    l2 = ax2_r.plot(qs, q_sw, marker="s", linestyle="--", linewidth=2.0, color=CORAL, label="Context Switches")
    ax2_r.set_ylabel("Context Switches", fontsize=9, fontweight="bold", color=CORAL)
    ax2_r.tick_params(axis="y", labelcolor=CORAL)
    ax2_r.spines["top"].set_visible(False)

    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc="upper right", fontsize=7.8, frameon=False)
    ax2.set_title("B. Round Robin Quantum Sensitivity (Q = 1 to 8)", fontsize=10.5, fontweight="bold", color=NAVY)

    fig.tight_layout(pad=1.8)
    fig.savefig(os.path.join(OUT_DIR, "fig5_metrics_and_quantum.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig6_synchronization_two_phase():
    race = ScenarioSimulator.run_race_condition_demo(trials=1000)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.7), dpi=300, gridspec_kw={"width_ratios": [1.5, 1]})

    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.axis("off")
    ax1.set_title("A. Mutex Critical Section, Counting Semaphore & 2-Phase Hold", fontsize=10.5, fontweight="bold", color=NAVY)

    draw_box(ax1, 0.03, 0.82, 0.22, 0.11, "Req-1 (Thread A)", "Needs last ICU bed", fc=ICE, ec=BLUE, tc=BLUE, fs=8.3, sub_fs=7.0)
    draw_box(ax1, 0.39, 0.82, 0.24, 0.11, "Mutex + Semaphore", "S = 1, version = v1", fc=INDIGO_BG, ec=INDIGO, tc=INDIGO, fs=8.3, sub_fs=7.0)
    draw_box(ax1, 0.74, 0.82, 0.23, 0.11, "Req-2 (Thread B)", "Concurrent claim", fc=AMBER_BG, ec=AMBER, tc=AMBER, fs=8.3, sub_fs=7.0)

    for x in (0.14, 0.51, 0.855):
        ax1.plot([x, x], [0.16, 0.81], linestyle=":", color=BORDER, linewidth=1.3)

    draw_arrow(ax1, 0.15, 0.72, 0.49, 0.72, "1. lock() & wait(S)", color=BLUE, ly_off=0.04)
    draw_box(ax1, 0.35, 0.53, 0.32, 0.12, "CRITICAL SECTION (A)", "S: 1->0, v: 1->2, PREPARE Hold", fc=GREEN_BG, ec=GREEN, tc=GREEN, fs=7.8, sub_fs=6.8)
    draw_arrow(ax1, 0.49, 0.47, 0.15, 0.47, "2. Hold ID + unlock()", color=GREEN, ly_off=0.035)
    draw_arrow(ax1, 0.84, 0.38, 0.53, 0.38, "3. lock() & check S", color=AMBER, ly_off=0.04)
    draw_arrow(ax1, 0.53, 0.27, 0.84, 0.27, "4. S==0 -> Denied (Safe)", color=CORAL, ly_off=0.035)
    draw_box(ax1, 0.02, 0.03, 0.96, 0.12,
             "Parallel Top-N Commit (First-Accept-Wins)",
             "Winner ACCEPT -> Phase=COMMITTED  |  Sibling PREPARE Holds -> ABORTED & signal(S) restores S",
             fc="#F0FDFA", ec=TEAL, tc=NAVY, fs=7.8, sub_fs=6.8, lw=1.4)

    cats = ["Without Mutex\n(Unsafe Check-Then-Act)", "With Mutex Lock\n(Atomic Critical Section)"]
    vals = [race["without_mutex_double_bookings"], race["with_mutex_double_bookings"]]
    bars = ax2.bar(cats, vals, color=[CORAL, GREEN], width=0.48, edgecolor="white")
    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + 22, f"{v} / 1000\ndouble-bookings",
                 ha="center", va="bottom", fontsize=9, fontweight="bold", color=NAVY)
    ax2.set_ylim(0, 1180)
    ax2.set_ylabel("Double-Bookings (1,000 Trials)", fontsize=9, fontweight="bold", color=NAVY)
    ax2.set_title("B. Concurrency Race Proof (1,000 Trials)", fontsize=10.5, fontweight="bold", color=NAVY)
    ax2.grid(axis="y", linestyle="--", alpha=0.35)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout(pad=1.6)
    fig.savefig(os.path.join(OUT_DIR, "fig6_synchronization_two_phase.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig7_starvation_aging_pi():
    aging = ScenarioSimulator.run_aging_starvation_demo()
    trace = aging["aging_trace"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=300)

    ticks = [pt["tick"] for pt in trace]
    prios = [pt["effective_priority"] for pt in trace]
    ax1.step(ticks, prios, where="post", linewidth=2.5, color=GREEN, label="With Aging (-1 / 10 ticks)")
    ax1.axhline(8, linestyle="--", color=CORAL, linewidth=2.0, label="Without Aging (Starves >120)")
    ax1.scatter([aging["with_aging_first_dispatch"]], [1], color=BLUE, s=75, zorder=5)
    ax1.annotate(f"P8 Dispatched (t={aging['with_aging_first_dispatch']})",
                 xy=(aging["with_aging_first_dispatch"], 1),
                 xytext=(max(5, aging["with_aging_first_dispatch"] - 36), 2.1),
                 arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5),
                 fontsize=8.5, fontweight="bold", color=BLUE)
    ax1.invert_yaxis()
    ax1.set_yticks(range(1, 9))
    ax1.set_yticklabels([f"P{i}" for i in range(1, 9)], fontsize=8.5, fontweight="bold", color=NAVY)
    ax1.set_xlabel("Simulation Time (ticks under continuous P1 emergency stream)", fontsize=8.8, fontweight="bold", color=NAVY)
    ax1.set_ylabel("Effective Priority (P1 = highest)", fontsize=9, fontweight="bold", color=NAVY)
    ax1.set_title("A. Starvation Prevention via Priority Aging", fontsize=10.5, fontweight="bold", color=NAVY)
    ax1.grid(True, linestyle="--", alpha=0.35)
    ax1.legend(loc="lower left", fontsize=8, frameon=True, facecolor="white")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    ax2.barh(1.2, 2, left=0, height=0.38, color=SLATE, edgecolor="white")
    ax2.text(1, 1.2, "P8\n(Lock)", ha="center", va="center", color="white", fontsize=7.5, fontweight="bold")
    ax2.barh(1.2, 2, left=2, height=0.38, color=CORAL, edgecolor="white")
    ax2.text(3, 1.2, "P1\nWait", ha="center", va="center", color="white", fontsize=7.5, fontweight="bold")
    ax2.barh(1.2, 8, left=4, height=0.38, color=AMBER, edgecolor="white")
    ax2.text(8, 1.2, "P4 Preempts P8\n(Priority Inversion!)", ha="center", va="center", color="white", fontsize=7.5, fontweight="bold")
    ax2.barh(1.2, 2, left=12, height=0.38, color=SLATE, edgecolor="white")
    ax2.text(13, 1.2, "P8", ha="center", va="center", color="white", fontsize=7.5, fontweight="bold")
    ax2.barh(1.2, 3, left=14, height=0.38, color=GREEN, edgecolor="white")
    ax2.text(15.5, 1.2, "P1 Runs\n(t=14)", ha="center", va="center", color="white", fontsize=7.5, fontweight="bold")

    ax2.barh(0.3, 2, left=0, height=0.38, color=SLATE, edgecolor="white")
    ax2.text(1, 0.3, "P8\n(Lock)", ha="center", va="center", color="white", fontsize=7.5, fontweight="bold")
    ax2.barh(0.3, 2, left=2, height=0.38, color=BLUE, edgecolor="white")
    ax2.text(3, 0.3, "P8->P1", ha="center", va="center", color="white", fontsize=7.5, fontweight="bold")
    ax2.barh(0.3, 3, left=4, height=0.38, color=GREEN, edgecolor="white")
    ax2.text(5.5, 0.3, "P1 Runs\n(t=4)", ha="center", va="center", color="white", fontsize=7.5, fontweight="bold")
    ax2.barh(0.3, 8, left=7, height=0.38, color=AMBER, edgecolor="white")
    ax2.text(11, 0.3, "P4 Runs After P1", ha="center", va="center", color="white", fontsize=7.5, fontweight="bold")

    ax2.set_yticks([0.3, 1.2])
    ax2.set_yticklabels(["With Priority\nInheritance\n(Delay = 2t)", "Without\nInheritance\n(Delay = 12t)"], fontsize=8.5, fontweight="bold", color=NAVY)
    ax2.set_xlim(0, 18)
    ax2.set_xticks(range(0, 19, 2))
    ax2.set_xlabel("Ticks", fontsize=9, fontweight="bold", color=NAVY)
    ax2.set_title("B. Priority Inversion vs. Priority Inheritance", fontsize=10.5, fontweight="bold", color=NAVY)
    ax2.grid(axis="x", linestyle="--", alpha=0.35)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout(pad=1.6)
    fig.savefig(os.path.join(OUT_DIR, "fig7_starvation_aging_pi.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig8_deadlock_rag_banker():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.9), dpi=300)

    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.axis("off")
    ax1.set_title("A. Resource Allocation Graph (RAG) Cycle & Victim Recovery", fontsize=10.5, fontweight="bold", color=NAVY)

    c1 = Circle((0.17, 0.52), 0.11, facecolor=ICE, edgecolor=BLUE, linewidth=2.2, zorder=3)
    c2 = Circle((0.83, 0.52), 0.11, facecolor=CORAL_BG, edgecolor=CORAL, linewidth=2.2, zorder=3)
    ax1.add_patch(c1)
    ax1.add_patch(c2)
    ax1.text(0.17, 0.54, "Req-X", ha="center", va="center", fontsize=9.5, fontweight="bold", color=NAVY, zorder=4)
    ax1.text(0.17, 0.47, "(Hosp A • P2)", ha="center", va="center", fontsize=7.5, color=SLATE, zorder=4)
    ax1.text(0.83, 0.54, "Req-Y", ha="center", va="center", fontsize=9.5, fontweight="bold", color=CORAL, zorder=4)
    ax1.text(0.83, 0.47, "(Victim • P5)", ha="center", va="center", fontsize=7.5, color=CORAL, zorder=4)

    draw_box(ax1, 0.36, 0.77, 0.28, 0.13, "R1: ICU Bed", "(1 unit)", fc=GREEN_BG, ec=GREEN, tc=GREEN, fs=9, sub_fs=7.5)
    draw_box(ax1, 0.36, 0.14, 0.28, 0.13, "R2: Ventilator", "(1 unit)", fc=GREEN_BG, ec=GREEN, tc=GREEN, fs=9, sub_fs=7.5)

    draw_arrow(ax1, 0.35, 0.82, 0.22, 0.62, "holds", color=GREEN, lx_off=-0.06, ly_off=0.03)
    draw_arrow(ax1, 0.24, 0.42, 0.36, 0.23, "waits", color=CORAL, lx_off=-0.06, ly_off=-0.03, ls="--")
    draw_arrow(ax1, 0.65, 0.22, 0.78, 0.41, "holds", color=GREEN, lx_off=0.06, ly_off=-0.03)
    draw_arrow(ax1, 0.76, 0.62, 0.65, 0.82, "waits", color=CORAL, lx_off=0.06, ly_off=0.03, ls="--")

    ax1.text(0.50, 0.52, "DEADLOCK CYCLE\nX -> R2 -> Y -> R1 -> X\n\nRecovery: Preempt Req-Y\nRelease R2:Ventilator",
             ha="center", va="center", fontsize=7.8, fontweight="bold", color=NAVY,
             bbox=dict(boxstyle="round,pad=0.35", fc="#FFFBEB", ec=AMBER, lw=1.2))

    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis("off")
    ax2.set_title("B. Banker's Algorithm Safe-State Verification Flow", fontsize=10.5, fontweight="bold", color=NAVY)

    draw_box(ax2, 0.10, 0.82, 0.72, 0.11, "1. Trial Allocation", "Work = Avail - Req; Alloc[i] += Req; Need[i] -= Req", fc=ICE, ec=BLUE, tc=NAVY, fs=8.5, sub_fs=7.0)
    draw_box(ax2, 0.10, 0.61, 0.72, 0.11, "2. Find Unfinished Req j: Need[j] <= Work?", "Hospital B: Total=[3,2,1], Avail=[1,1,0]", fc=AMBER_BG, ec=AMBER, tc=AMBER, fs=8.5, sub_fs=7.0)
    draw_box(ax2, 0.10, 0.39, 0.65, 0.11, "3. Simulate Completion", "Work = Work + Alloc[j]; Finish[j] = True", fc=INDIGO_BG, ec=INDIGO, tc=INDIGO, fs=8.5, sub_fs=7.0)
    draw_box(ax2, 0.04, 0.10, 0.42, 0.14, "SAFE Sequence Found", "GRANT Request (e.g., Req-B)", fc=GREEN_BG, ec=GREEN, tc=GREEN, fs=8.4, sub_fs=7.0)
    draw_box(ax2, 0.54, 0.10, 0.43, 0.14, "UNSAFE (No Sequence)", "DENY / DEFER (e.g., Req-C)", fc=CORAL_BG, ec=CORAL, tc=CORAL, fs=8.4, sub_fs=7.0)

    draw_arrow(ax2, 0.46, 0.81, 0.46, 0.73, color=NAVY)
    draw_arrow(ax2, 0.42, 0.60, 0.42, 0.51, "Found j", color=GREEN, lx_off=-0.07)
    draw_arrow(ax2, 0.76, 0.445, 0.83, 0.665, "Loop", color=INDIGO, rad=-0.28, lx_off=0.05)
    draw_arrow(ax2, 0.34, 0.38, 0.25, 0.25, "All Finish", color=GREEN, lx_off=-0.08)
    # Route Stuck arrow around the right side cleanly outside Box 3
    draw_arrow(ax2, 0.83, 0.64, 0.86, 0.25, "Stuck", color=CORAL, rad=-0.22, lx_off=0.05)

    fig.tight_layout(pad=1.6)
    fig.savefig(os.path.join(OUT_DIR, "fig8_deadlock_rag_banker.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig9_network_and_surge():
    surge = ScenarioSimulator.run_surge_simulation(num_requests=20)
    dist = surge["distribution"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.6), dpi=300)

    # Left: 10-hospital network map with explicit non-overlapping label offsets
    pins = [
        ("JAIN (Origin)", 77.4404, 12.6418, CORAL, -0.005, -0.020),
        ("KNG (2 ICU)", 77.4199, 12.5462, BLUE, 0.015, -0.018),
        ("DSH (2 ICU)", 77.4512, 12.6685, GREEN, 0.018, 0.016),
        ("RRM (3 ICU)", 77.4608, 12.8858, BLUE, -0.025, 0.016),
        ("BGS (4 ICU)", 77.4956, 12.9012, BLUE, -0.025, 0.024),
        ("APL (3 ICU)", 77.5988, 12.8962, BLUE, 0.035, -0.022),
        ("SGR (Stale)", 77.5994, 12.9288, AMBER, -0.038, 0.022),
        ("NAR (5 ICU)", 77.6948, 12.8105, TEAL, -0.010, 0.018),
        ("MNI (3 ICU)", 77.5912, 12.9178, BLUE, -0.045, -0.014),
        ("STJ (4 ICU)", 77.6209, 12.9293, BLUE, 0.048, 0.016),
    ]
    ox, oy = 77.4404, 12.6418
    for name, lng, lat, col, dx, dy in pins:
        if "JAIN" not in name:
            ax1.plot([ox, lng], [oy, lat], linestyle=":", color="#CBD5E1", linewidth=1.1, zorder=1)
        ax1.scatter([lng], [lat], s=95 if "JAIN" in name else 65, color=col, edgecolor="white", linewidth=1.5, zorder=3)
        ax1.annotate(
            name, xy=(lng, lat), xytext=(lng + dx, lat + dy),
            ha="center", va="center", fontsize=7.0, fontweight="bold", color=NAVY,
            arrowprops=dict(arrowstyle="-", color="#CBD5E1", lw=0.8) if abs(dx) > 0.02 or abs(dy) > 0.02 else None,
            zorder=4
        )

    ax1.set_xlim(77.37, 77.75)
    ax1.set_ylim(12.50, 12.99)
    ax1.set_xlabel("Longitude (°E)", fontsize=8.5, color=NAVY)
    ax1.set_ylabel("Latitude (°N)", fontsize=8.5, color=NAVY)
    ax1.set_title("A. 10-Hospital Kanakapura–Bengaluru Network", fontsize=10.5, fontweight="bold", color=NAVY)
    ax1.grid(True, linestyle="--", alpha=0.3)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    hids = list(dist.keys())[::-1]
    cnts = [dist[h] for h in hids]
    bars = ax2.barh(hids, cnts, color=TEAL, height=0.55, edgecolor="white")
    for b, v in zip(bars, cnts):
        ax2.text(v + 0.15, b.get_y() + b.get_height() / 2, f"{v} P1 patients", va="center", fontsize=8.5, fontweight="bold", color=NAVY)
    ax2.set_xlim(0, max(cnts) + 2.4)
    ax2.set_xlabel("Assigned Priority-1 Surge Requests (Total = 20)", fontsize=8.8, fontweight="bold", color=NAVY)
    ax2.set_title("B. Surge Mode: FIFO + Capacity Load Balancing", fontsize=10.5, fontweight="bold", color=NAVY)
    ax2.grid(axis="x", linestyle="--", alpha=0.35)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout(pad=1.6)
    fig.savefig(os.path.join(OUT_DIR, "fig9_network_and_surge.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    fig1_architecture()
    fig2_dispatch_flowchart()
    fig3_process_states()
    fig4_gantt_charts()
    fig5_metrics_and_quantum()
    fig6_synchronization_two_phase()
    fig7_starvation_aging_pi()
    fig8_deadlock_rag_banker()
    fig9_network_and_surge()
    print(f"Regenerated 9 clean figures in {OUT_DIR}")
