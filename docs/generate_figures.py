"""Generate 9 clean, understated academic OS diagrams and plots for the Redline Case Study 2 Report."""

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

# Understated academic / IEEE print palette (subtle greys + muted steel/sage/brick)
INK = "#1F2937"
MUTED = "#4B5563"
BORDER_DARK = "#374151"
BORDER_LIGHT = "#9CA3AF"
FILL_WHITE = "#FFFFFF"
FILL_GREY1 = "#F9FAFB"
FILL_GREY2 = "#F3F4F6"
FILL_GREY3 = "#E5E7EB"

STEEL = "#3B5B78"
STEEL_SOFT = "#EEF2F6"
SAGE = "#3D6B52"
SAGE_SOFT = "#EEF5F0"
BRICK = "#993D3D"
BRICK_SOFT = "#F9EEEE"
OCHRE = "#8C6229"
OCHRE_SOFT = "#F8F3EB"
SLATE_LINE = "#6B7280"

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#9CA3AF"


def draw_box(ax, x, y, w, h, title, subtitle="", fc=FILL_GREY2, ec=BORDER_DARK, tc=INK, lw=1.15, fs=9.0, sub_fs=7.4, radius=0.012):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.008,rounding_size={radius}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3
    )
    ax.add_patch(patch)
    if subtitle:
        ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=fs, fontweight="bold", color=tc, zorder=4)
        ax.text(x + w / 2, y + h * 0.28, subtitle, ha="center", va="center", fontsize=sub_fs, color=MUTED, zorder=4)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=fs, fontweight="bold", color=tc, zorder=4)


def draw_arrow(ax, x1, y1, x2, y2, label="", color=BORDER_DARK, rad=0.0, lx_off=0.0, ly_off=0.0, lw=1.25, ls="-"):
    arr = FancyArrowPatch(
        (x1, y1), (x2, y2),
        connectionstyle=f"arc3,rad={rad}",
        arrowstyle="-|>,head_length=5.5,head_width=3.2",
        color=color, linewidth=lw, linestyle=ls, zorder=2
    )
    ax.add_patch(arr)
    if label:
        mx = (x1 + x2) / 2 + lx_off
        my = (y1 + y2) / 2 + ly_off
        ax.text(mx, my, label, ha="center", va="center", fontsize=7.6, fontweight="bold", color=color,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.92), zorder=5)


def fig1_architecture():
    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.96, "Redline (HEMS-Link) — Layered System Architecture",
            ha="center", va="center", fontsize=11.5, fontweight="bold", color=INK)

    layers = [
        (0.75, "PRESENTATION LAYER (Web UI, Light/Dark Themes, EN/HI/KN, RBAC Switcher)",
         "9 Operational Screens (Dispatch, OS Kernel Workbench, Analytics, Bed Board, Surge, Tracker, Matches, Coordination, New Request) + Style Guide",
         FILL_GREY1, BORDER_DARK),
        (0.53, "FLASK REST API & ACCESS CONTROL LAYER (app.py)",
         "/api/requests (409 Dup)  |  /api/matches  |  /api/refer  |  /api/facilities (409 Ver)  |  /api/monitor  |  /api/scheduler/control  |  /api/export/csv",
         FILL_GREY2, BORDER_DARK),
        (0.30, "OS KERNEL & SIMULATION ENGINE (os_engine/)",
         "8-Policy Scheduler + Aging + EDF + MLFQ  |  Explainable Matcher  |  Mutex + Semaphores + 2-Phase Hold  |  Banker's  |  RAG Deadlock  |  Workers",
         STEEL_SOFT, STEEL),
        (0.08, "SIMULATED DATA, TELEMETRY & AUDIT LAYER",
         "10 Kanakapura-Bengaluru Hospitals  |  Versioned Facility Semaphores  |  8+ Seeded Hospital Processes  |  IPC Event Log & RBAC Audit Trail",
         FILL_GREY3, BORDER_DARK),
    ]

    for y, title, sub, fc, ec in layers:
        draw_box(ax, 0.03, y, 0.94, 0.15, title, sub, fc=fc, ec=ec, tc=INK, fs=9.0, sub_fs=7.0, lw=1.2)

    draw_arrow(ax, 0.5, 0.74, 0.5, 0.695, color=BORDER_DARK)
    draw_arrow(ax, 0.5, 0.52, 0.5, 0.465, color=BORDER_DARK)
    draw_arrow(ax, 0.5, 0.29, 0.5, 0.245, color=BORDER_DARK)

    fig.savefig(os.path.join(OUT_DIR, "fig1_architecture.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig2_dispatch_flowchart():
    fig, ax = plt.subplots(figsize=(11, 7.0), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.97, "Hospital Activity Dispatch and OS Kernel Flowchart",
            ha="center", va="center", fontsize=11.5, fontweight="bold", color=INK)

    draw_box(ax, 0.03, 0.82, 0.20, 0.09, "1. Activity Intake", "Emerg, ICU, Lab, OP, Pharm", fc=FILL_GREY1, ec=BORDER_DARK, tc=INK, fs=8.4, sub_fs=7.0)
    draw_box(ax, 0.28, 0.82, 0.20, 0.09, "2. Duplicate Check?", "Active patient_hash?", fc=FILL_GREY2, ec=BORDER_DARK, tc=INK, fs=8.4, sub_fs=7.0)
    draw_box(ax, 0.54, 0.82, 0.20, 0.09, "3. Admit PCB (READY)", "Assign P1-P8, BT, SLA DL", fc=STEEL_SOFT, ec=STEEL, tc=INK, fs=8.4, sub_fs=7.0)
    draw_box(ax, 0.79, 0.82, 0.18, 0.09, "4. CPU Scheduler", "Preempt if P_new < P_run", fc=STEEL_SOFT, ec=STEEL, tc=INK, fs=8.4, sub_fs=7.0)

    draw_box(ax, 0.28, 0.64, 0.20, 0.085, "HTTP 409 Warning", "Prompt override or abort", fc=BRICK_SOFT, ec=BRICK, tc=BRICK, fs=8.2, sub_fs=7.0)

    draw_box(ax, 0.73, 0.45, 0.24, 0.10, "5. Hospital Matcher", "Filter free S>0; rank ETA/Trust", fc=FILL_GREY1, ec=BORDER_DARK, tc=INK, fs=8.4, sub_fs=7.0)
    draw_box(ax, 0.41, 0.45, 0.26, 0.10, "6. Mutex Critical Section", "Order resources; S--, v++, PREPARE", fc=FILL_GREY2, ec=BORDER_DARK, tc=INK, fs=8.4, sub_fs=7.0)
    draw_box(ax, 0.06, 0.45, 0.28, 0.10, "7. Parallel Top-N Hold", "PCB -> WAITING; await reply", fc=OCHRE_SOFT, ec=OCHRE, tc=INK, fs=8.4, sub_fs=7.0)

    draw_box(ax, 0.04, 0.22, 0.26, 0.105, "8a. ACCEPT (First Wins)", "COMMITTED; sibling signal(S)", fc=SAGE_SOFT, ec=SAGE, tc=SAGE, fs=8.3, sub_fs=7.0)
    draw_box(ax, 0.37, 0.22, 0.26, 0.105, "8b. REJECT / EXPIRED", "signal(S) restores; Escalate", fc=BRICK_SOFT, ec=BRICK, tc=BRICK, fs=8.3, sub_fs=7.0)
    draw_box(ax, 0.70, 0.22, 0.26, 0.105, "8c. Banker / RAG Check", "Deadlock -> release victim", fc=FILL_GREY2, ec=BORDER_DARK, tc=INK, fs=8.3, sub_fs=7.0)

    draw_box(ax, 0.28, 0.04, 0.44, 0.095, "9. TERMINATED & Audit Logged", "Ambulance ETA dispatched | Audit trail updated", fc=FILL_GREY3, ec=BORDER_DARK, tc=INK, fs=8.8, sub_fs=7.2)

    draw_arrow(ax, 0.24, 0.865, 0.27, 0.865)
    draw_arrow(ax, 0.38, 0.81, 0.38, 0.735, "Yes", color=BRICK, lx_off=0.03)
    draw_arrow(ax, 0.49, 0.865, 0.53, 0.865, "No", color=SAGE, ly_off=0.025)
    draw_arrow(ax, 0.75, 0.865, 0.78, 0.865)
    draw_arrow(ax, 0.88, 0.81, 0.88, 0.56)
    draw_arrow(ax, 0.72, 0.50, 0.68, 0.50)
    draw_arrow(ax, 0.40, 0.50, 0.35, 0.50)
    draw_arrow(ax, 0.17, 0.44, 0.17, 0.335, "Accept", color=SAGE, lx_off=-0.045)
    draw_arrow(ax, 0.27, 0.44, 0.47, 0.335, "Timeout / Reject", color=BRICK, lx_off=0.055)
    draw_arrow(ax, 0.58, 0.44, 0.80, 0.335, "Multi-Res", color=MUTED, lx_off=0.045)
    draw_arrow(ax, 0.54, 0.335, 0.78, 0.44, "Retry Next", color=OCHRE, rad=-0.18, ly_off=-0.02, ls="--")
    draw_arrow(ax, 0.17, 0.21, 0.36, 0.145, color=SAGE)
    draw_arrow(ax, 0.83, 0.21, 0.64, 0.145, color=MUTED)

    fig.savefig(os.path.join(OUT_DIR, "fig2_dispatch_flowchart.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig3_process_states():
    fig, ax = plt.subplots(figsize=(10.8, 4.4), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.94, "Five-State Process Lifecycle and PCB Fields",
            ha="center", va="center", fontsize=11.5, fontweight="bold", color=INK)

    draw_box(ax, 0.04, 0.56, 0.14, 0.16, "NEW", "Intake created", fc=FILL_GREY1, ec=BORDER_DARK, tc=INK, fs=9.5, sub_fs=7.4)
    draw_box(ax, 0.26, 0.56, 0.16, 0.16, "READY", "Priority + Aging Q", fc=STEEL_SOFT, ec=STEEL, tc=INK, fs=9.5, sub_fs=7.4)
    draw_box(ax, 0.52, 0.56, 0.16, 0.16, "RUNNING", "Matching & Mutex", fc=SAGE_SOFT, ec=SAGE, tc=INK, fs=9.5, sub_fs=7.4)
    draw_box(ax, 0.78, 0.56, 0.18, 0.16, "TERMINATED", "Committed / Done", fc=FILL_GREY3, ec=BORDER_DARK, tc=INK, fs=9.5, sub_fs=7.4)
    draw_box(ax, 0.39, 0.19, 0.20, 0.16, "WAITING", "Awaiting Hold Reply", fc=FILL_GREY2, ec=BORDER_DARK, tc=INK, fs=9.5, sub_fs=7.4)

    draw_arrow(ax, 0.19, 0.64, 0.25, 0.64, "admit", ly_off=0.045)
    draw_arrow(ax, 0.43, 0.67, 0.51, 0.67, "dispatch", color=SAGE, ly_off=0.045)
    draw_arrow(ax, 0.51, 0.60, 0.43, 0.60, "preempt / Q", color=BRICK, ly_off=-0.05)
    draw_arrow(ax, 0.69, 0.64, 0.77, 0.64, "accept / finish", ly_off=0.045)
    draw_arrow(ax, 0.60, 0.55, 0.52, 0.36, "parallel hold / I/O", color=MUTED, lx_off=0.08)
    draw_arrow(ax, 0.46, 0.36, 0.36, 0.55, "reply / signal(S)", color=STEEL, lx_off=-0.08)

    draw_box(ax, 0.02, 0.02, 0.96, 0.09,
             "PCB Fields:  PID  |  Category  |  Arrival Time (AT)  |  Base & Effective Priority (P1-P8)  |  Burst / Remaining  |  SLA Deadline  |  Wait Ticks  |  State",
             fc=FILL_GREY1, ec=BORDER_LIGHT, tc=INK, fs=7.3, lw=1.0)

    fig.savefig(os.path.join(OUT_DIR, "fig3_process_states.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig4_gantt_charts():
    bench = run_extended_benchmark(workload=default_workload(), quantum=3, aging_interval=0)
    algos = [
        ("FCFS", bench["fcfs"]["gantt"]),
        ("SJF (Non-Preemptive)", bench["sjf"]["gantt"]),
        ("SRTF (Preemptive SJF)", bench["srtf"]["gantt"]),
        ("Preemptive Priority", bench["preemptive_priority"]["gantt"]),
        ("Round Robin (Q = 3)", bench["round_robin"]["gantt"]),
        ("EDF (Real-Time)", bench["edf"]["gantt"]),
    ]

    # Muted academic color scheme: greys/cool blues for routine, muted brick/ochre for critical
    pid_colors = {
        "T1": "#5B7894",
        "T2": "#9CA3AF",
        "T3": "#7B93A8",
        "T4": "#6E8B84",
        "T5": "#6B7280",
        "T6": "#A67C46",
        "T7": "#B05B45",
        "T8": "#8C3333",
    }

    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=300)
    y_positions = np.arange(len(algos))[::-1]

    for y, (label, gantt) in zip(y_positions, algos):
        for seg in gantt:
            s, e, pid = seg["start"], seg["end"], seg["pid"]
            w = e - s
            col = pid_colors.get(pid, SLATE_LINE)
            ax.barh(y, w, left=s, height=0.56, color=col, edgecolor="white", linewidth=1.1)
            ax.text(s + w / 2, y, pid, ha="center", va="center", color="white",
                    fontsize=7.8 if w >= 2 else 6.8, fontweight="bold")

    ax.set_yticks(y_positions)
    ax.set_yticklabels([a[0] for a in algos], fontsize=9.2, fontweight="bold", color=INK)
    ax.set_xlim(0, 40)
    ax.set_xticks(range(0, 41, 2))
    ax.set_xlabel("Normalised Time Units (0 to 40 ticks)", fontsize=9.2, fontweight="bold", color=INK)
    ax.set_title("Gantt Charts on Eight-Process Workload (T1-T8)", fontsize=11.5, fontweight="bold", color=INK, pad=12)
    ax.grid(axis="x", linestyle="--", alpha=0.35, color="#9CA3AF")
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

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.5), dpi=300)

    x = np.arange(len(order))
    w = 0.26
    wt = [bench[k]["avg_waiting"] for _, k in order]
    tat = [bench[k]["avg_turnaround"] for _, k in order]
    crit = [bench[k]["critical_avg_response"] for _, k in order]

    ax1.bar(x - w, wt, width=w, label="Avg Waiting Time", color=STEEL)
    ax1.bar(x, tat, width=w, label="Avg Turnaround Time", color="#8A99A8")
    ax1.bar(x + w, crit, width=w, label="Critical Response (T6-T8)", color=BRICK)
    ax1.set_xticks(x)
    ax1.set_xticklabels([lbl for lbl, _ in order], fontsize=8, rotation=20, ha="right", color=INK, fontweight="bold")
    ax1.set_ylabel("Normalised Time Units (ticks)", fontsize=8.8, fontweight="bold", color=INK)
    ax1.set_title("A. Eight-Algorithm Scheduling Criteria Comparison", fontsize=10.2, fontweight="bold", color=INK)
    ax1.grid(axis="y", linestyle="--", alpha=0.35, color="#9CA3AF")
    ax1.legend(fontsize=7.8, frameon=False)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    qs = [d["quantum"] for d in sweep]
    q_wt = [d["avg_waiting"] for d in sweep]
    q_sw = [d["context_switches"] for d in sweep]

    l1 = ax2.plot(qs, q_wt, marker="o", linewidth=2.0, color=STEEL, label="Avg Waiting Time")
    ax2.set_xlabel("Round Robin Time Quantum (Q)", fontsize=8.8, fontweight="bold", color=INK)
    ax2.set_ylabel("Avg Waiting Time (ticks)", fontsize=8.8, fontweight="bold", color=STEEL)
    ax2.tick_params(axis="y", labelcolor=STEEL)
    ax2.set_xticks(qs)
    ax2.grid(True, linestyle="--", alpha=0.35, color="#9CA3AF")
    ax2.spines["top"].set_visible(False)

    ax2_r = ax2.twinx()
    l2 = ax2_r.plot(qs, q_sw, marker="s", linestyle="--", linewidth=1.8, color=BRICK, label="Context Switches")
    ax2_r.set_ylabel("Context Switches", fontsize=8.8, fontweight="bold", color=BRICK)
    ax2_r.tick_params(axis="y", labelcolor=BRICK)
    ax2_r.spines["top"].set_visible(False)

    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc="upper right", fontsize=7.8, frameon=False)
    ax2.set_title("B. Round Robin Quantum Sensitivity (Q = 1 to 8)", fontsize=10.2, fontweight="bold", color=INK)

    fig.tight_layout(pad=1.8)
    fig.savefig(os.path.join(OUT_DIR, "fig5_metrics_and_quantum.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig6_synchronization_two_phase():
    race = ScenarioSimulator.run_race_condition_demo(trials=1000)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.6), dpi=300, gridspec_kw={"width_ratios": [1.5, 1]})

    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.axis("off")
    ax1.set_title("A. Mutex Critical Section, Counting Semaphore & 2-Phase Hold", fontsize=10.2, fontweight="bold", color=INK)

    draw_box(ax1, 0.03, 0.82, 0.22, 0.11, "Req-1 (Thread A)", "Needs last ICU bed", fc=FILL_GREY1, ec=BORDER_DARK, tc=INK, fs=8.2, sub_fs=7.0)
    draw_box(ax1, 0.39, 0.82, 0.24, 0.11, "Mutex + Semaphore", "S = 1, version = v1", fc=FILL_GREY2, ec=BORDER_DARK, tc=INK, fs=8.2, sub_fs=7.0)
    draw_box(ax1, 0.74, 0.82, 0.23, 0.11, "Req-2 (Thread B)", "Concurrent claim", fc=FILL_GREY1, ec=BORDER_DARK, tc=INK, fs=8.2, sub_fs=7.0)

    for x in (0.14, 0.51, 0.855):
        ax1.plot([x, x], [0.16, 0.81], linestyle=":", color=BORDER_LIGHT, linewidth=1.2)

    draw_arrow(ax1, 0.15, 0.72, 0.49, 0.72, "1. lock() & wait(S)", color=STEEL, ly_off=0.04)
    draw_box(ax1, 0.35, 0.53, 0.32, 0.12, "CRITICAL SECTION (A)", "S: 1->0, v: 1->2, PREPARE Hold", fc=SAGE_SOFT, ec=SAGE, tc=SAGE, fs=7.8, sub_fs=6.8)
    draw_arrow(ax1, 0.49, 0.47, 0.15, 0.47, "2. Hold ID + unlock()", color=SAGE, ly_off=0.035)
    draw_arrow(ax1, 0.84, 0.38, 0.53, 0.38, "3. lock() & check S", color=MUTED, ly_off=0.04)
    draw_arrow(ax1, 0.53, 0.27, 0.84, 0.27, "4. S==0 -> Denied (Safe)", color=BRICK, ly_off=0.035)
    draw_box(ax1, 0.02, 0.03, 0.96, 0.12,
             "Parallel Top-N Commit (First-Accept-Wins)",
             "Winner ACCEPT -> Phase=COMMITTED  |  Sibling PREPARE Holds -> ABORTED & signal(S) restores S",
             fc=FILL_GREY2, ec=BORDER_DARK, tc=INK, fs=7.8, sub_fs=6.8, lw=1.1)

    cats = ["Without Mutex\n(Unsafe Check-Then-Act)", "With Mutex Lock\n(Atomic Critical Section)"]
    vals = [race["without_mutex_double_bookings"], race["with_mutex_double_bookings"]]
    bars = ax2.bar(cats, vals, color=[BRICK, SAGE], width=0.45, edgecolor="white")
    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + 22, f"{v} / 1000\ndouble-bookings",
                 ha="center", va="bottom", fontsize=8.8, fontweight="bold", color=INK)
    ax2.set_ylim(0, 1180)
    ax2.set_ylabel("Double-Bookings (1,000 Trials)", fontsize=8.8, fontweight="bold", color=INK)
    ax2.set_title("B. Concurrency Race Test (1,000 Trials)", fontsize=10.2, fontweight="bold", color=INK)
    ax2.grid(axis="y", linestyle="--", alpha=0.35, color="#9CA3AF")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout(pad=1.6)
    fig.savefig(os.path.join(OUT_DIR, "fig6_synchronization_two_phase.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig7_starvation_aging_pi():
    aging = ScenarioSimulator.run_aging_starvation_demo()
    trace = aging["aging_trace"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.5), dpi=300)

    ticks = [pt["tick"] for pt in trace]
    prios = [pt["effective_priority"] for pt in trace]
    ax1.step(ticks, prios, where="post", linewidth=2.2, color=SAGE, label="With Aging (-1 / 10 ticks)")
    ax1.axhline(8, linestyle="--", color=BRICK, linewidth=1.8, label="Without Aging (Starves >120)")
    ax1.scatter([aging["with_aging_first_dispatch"]], [1], color=STEEL, s=65, zorder=5)
    ax1.annotate(f"P8 Dispatched (t={aging['with_aging_first_dispatch']})",
                 xy=(aging["with_aging_first_dispatch"], 1),
                 xytext=(max(5, aging["with_aging_first_dispatch"] - 36), 2.1),
                 arrowprops=dict(arrowstyle="->", color=STEEL, lw=1.4),
                 fontsize=8.3, fontweight="bold", color=STEEL)
    ax1.invert_yaxis()
    ax1.set_yticks(range(1, 9))
    ax1.set_yticklabels([f"P{i}" for i in range(1, 9)], fontsize=8.3, fontweight="bold", color=INK)
    ax1.set_xlabel("Simulation Time (ticks under continuous P1 stream)", fontsize=8.6, fontweight="bold", color=INK)
    ax1.set_ylabel("Effective Priority (P1 = highest)", fontsize=8.8, fontweight="bold", color=INK)
    ax1.set_title("A. Starvation Prevention via Priority Aging", fontsize=10.2, fontweight="bold", color=INK)
    ax1.grid(True, linestyle="--", alpha=0.35, color="#9CA3AF")
    ax1.legend(loc="lower left", fontsize=7.8, frameon=True, facecolor="white", edgecolor="#D1D5DB")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    ax2.barh(1.2, 2, left=0, height=0.38, color="#6B7280", edgecolor="white")
    ax2.text(1, 1.2, "P8\n(Lock)", ha="center", va="center", color="white", fontsize=7.4, fontweight="bold")
    ax2.barh(1.2, 2, left=2, height=0.38, color=BRICK, edgecolor="white")
    ax2.text(3, 1.2, "P1\nWait", ha="center", va="center", color="white", fontsize=7.4, fontweight="bold")
    ax2.barh(1.2, 8, left=4, height=0.38, color=OCHRE, edgecolor="white")
    ax2.text(8, 1.2, "P4 Preempts P8\n(Priority Inversion)", ha="center", va="center", color="white", fontsize=7.4, fontweight="bold")
    ax2.barh(1.2, 2, left=12, height=0.38, color="#6B7280", edgecolor="white")
    ax2.text(13, 1.2, "P8", ha="center", va="center", color="white", fontsize=7.4, fontweight="bold")
    ax2.barh(1.2, 3, left=14, height=0.38, color=SAGE, edgecolor="white")
    ax2.text(15.5, 1.2, "P1 Runs\n(t=14)", ha="center", va="center", color="white", fontsize=7.4, fontweight="bold")

    ax2.barh(0.3, 2, left=0, height=0.38, color="#6B7280", edgecolor="white")
    ax2.text(1, 0.3, "P8\n(Lock)", ha="center", va="center", color="white", fontsize=7.4, fontweight="bold")
    ax2.barh(0.3, 2, left=2, height=0.38, color=STEEL, edgecolor="white")
    ax2.text(3, 0.3, "P8->P1", ha="center", va="center", color="white", fontsize=7.4, fontweight="bold")
    ax2.barh(0.3, 3, left=4, height=0.38, color=SAGE, edgecolor="white")
    ax2.text(5.5, 0.3, "P1 Runs\n(t=4)", ha="center", va="center", color="white", fontsize=7.4, fontweight="bold")
    ax2.barh(0.3, 8, left=7, height=0.38, color=OCHRE, edgecolor="white")
    ax2.text(11, 0.3, "P4 Runs After P1", ha="center", va="center", color="white", fontsize=7.4, fontweight="bold")

    ax2.set_yticks([0.3, 1.2])
    ax2.set_yticklabels(["With Priority\nInheritance\n(Delay = 2t)", "Without\nInheritance\n(Delay = 12t)"], fontsize=8.3, fontweight="bold", color=INK)
    ax2.set_xlim(0, 18)
    ax2.set_xticks(range(0, 19, 2))
    ax2.set_xlabel("Ticks", fontsize=8.8, fontweight="bold", color=INK)
    ax2.set_title("B. Priority Inversion vs. Priority Inheritance", fontsize=10.2, fontweight="bold", color=INK)
    ax2.grid(axis="x", linestyle="--", alpha=0.35, color="#9CA3AF")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout(pad=1.6)
    fig.savefig(os.path.join(OUT_DIR, "fig7_starvation_aging_pi.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig8_deadlock_rag_banker():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=300)

    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.axis("off")
    ax1.set_title("A. Resource Allocation Graph (RAG) Cycle & Victim Recovery", fontsize=10.2, fontweight="bold", color=INK)

    c1 = Circle((0.17, 0.52), 0.11, facecolor=FILL_GREY1, edgecolor=BORDER_DARK, linewidth=1.6, zorder=3)
    c2 = Circle((0.83, 0.52), 0.11, facecolor=BRICK_SOFT, edgecolor=BRICK, linewidth=1.6, zorder=3)
    ax1.add_patch(c1)
    ax1.add_patch(c2)
    ax1.text(0.17, 0.54, "Req-X", ha="center", va="center", fontsize=9.2, fontweight="bold", color=INK, zorder=4)
    ax1.text(0.17, 0.47, "(Hosp A | P2)", ha="center", va="center", fontsize=7.3, color=MUTED, zorder=4)
    ax1.text(0.83, 0.54, "Req-Y", ha="center", va="center", fontsize=9.2, fontweight="bold", color=BRICK, zorder=4)
    ax1.text(0.83, 0.47, "(Victim | P5)", ha="center", va="center", fontsize=7.3, color=BRICK, zorder=4)

    draw_box(ax1, 0.36, 0.77, 0.28, 0.13, "R1: ICU Bed", "(1 unit)", fc=FILL_GREY2, ec=BORDER_DARK, tc=INK, fs=8.8, sub_fs=7.3)
    draw_box(ax1, 0.36, 0.14, 0.28, 0.13, "R2: Ventilator", "(1 unit)", fc=FILL_GREY2, ec=BORDER_DARK, tc=INK, fs=8.8, sub_fs=7.3)

    draw_arrow(ax1, 0.35, 0.82, 0.22, 0.62, "holds", color=BORDER_DARK, lx_off=-0.06, ly_off=0.03)
    draw_arrow(ax1, 0.24, 0.42, 0.36, 0.23, "waits", color=BRICK, lx_off=-0.06, ly_off=-0.03, ls="--")
    draw_arrow(ax1, 0.65, 0.22, 0.78, 0.41, "holds", color=BORDER_DARK, lx_off=0.06, ly_off=-0.03)
    draw_arrow(ax1, 0.76, 0.62, 0.65, 0.82, "waits", color=BRICK, lx_off=0.06, ly_off=0.03, ls="--")

    ax1.text(0.50, 0.52, "DEADLOCK CYCLE\nX -> R2 -> Y -> R1 -> X\n\nRecovery: Preempt Req-Y\nRelease R2:Ventilator",
             ha="center", va="center", fontsize=7.6, fontweight="bold", color=INK,
             bbox=dict(boxstyle="round,pad=0.32", fc=FILL_GREY1, ec=BORDER_LIGHT, lw=1.0))

    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis("off")
    ax2.set_title("B. Banker's Algorithm Safe-State Verification Flow", fontsize=10.2, fontweight="bold", color=INK)

    draw_box(ax2, 0.10, 0.82, 0.72, 0.11, "1. Trial Allocation", "Work = Avail - Req; Alloc[i] += Req; Need[i] -= Req", fc=FILL_GREY1, ec=BORDER_DARK, tc=INK, fs=8.3, sub_fs=7.0)
    draw_box(ax2, 0.10, 0.61, 0.72, 0.11, "2. Find Unfinished Req j: Need[j] <= Work?", "Hospital B: Total=[3,2,1], Avail=[1,1,0]", fc=FILL_GREY2, ec=BORDER_DARK, tc=INK, fs=8.3, sub_fs=7.0)
    draw_box(ax2, 0.10, 0.39, 0.65, 0.11, "3. Simulate Completion", "Work = Work + Alloc[j]; Finish[j] = True", fc=STEEL_SOFT, ec=STEEL, tc=INK, fs=8.3, sub_fs=7.0)
    draw_box(ax2, 0.04, 0.10, 0.42, 0.14, "SAFE Sequence Found", "GRANT Request (e.g., Req-B)", fc=SAGE_SOFT, ec=SAGE, tc=SAGE, fs=8.3, sub_fs=7.0)
    draw_box(ax2, 0.54, 0.10, 0.43, 0.14, "UNSAFE (No Sequence)", "DENY / DEFER (e.g., Req-C)", fc=BRICK_SOFT, ec=BRICK, tc=BRICK, fs=8.3, sub_fs=7.0)

    draw_arrow(ax2, 0.46, 0.81, 0.46, 0.73)
    draw_arrow(ax2, 0.42, 0.60, 0.42, 0.51, "Found j", color=SAGE, lx_off=-0.07)
    draw_arrow(ax2, 0.76, 0.445, 0.83, 0.665, "Loop", color=STEEL, rad=-0.28, lx_off=0.05)
    draw_arrow(ax2, 0.34, 0.38, 0.25, 0.25, "All Finish", color=SAGE, lx_off=-0.08)
    draw_arrow(ax2, 0.83, 0.64, 0.86, 0.25, "Stuck", color=BRICK, rad=-0.22, lx_off=0.05)

    fig.tight_layout(pad=1.6)
    fig.savefig(os.path.join(OUT_DIR, "fig8_deadlock_rag_banker.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig9_network_and_surge():
    surge = ScenarioSimulator.run_surge_simulation(num_requests=20)
    dist = surge["distribution"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.5), dpi=300)

    pins = [
        ("JAIN (Origin)", 77.4404, 12.6418, BRICK, -0.005, -0.020),
        ("KNG (2 ICU)", 77.4199, 12.5462, STEEL, 0.015, -0.018),
        ("DSH (2 ICU)", 77.4512, 12.6685, SAGE, 0.018, 0.016),
        ("RRM (3 ICU)", 77.4608, 12.8858, STEEL, -0.025, 0.016),
        ("BGS (4 ICU)", 77.4956, 12.9012, STEEL, -0.025, 0.024),
        ("APL (3 ICU)", 77.5988, 12.8962, STEEL, 0.035, -0.022),
        ("SGR (Stale)", 77.5994, 12.9288, OCHRE, -0.038, 0.022),
        ("NAR (5 ICU)", 77.6948, 12.8105, STEEL, -0.010, 0.018),
        ("MNI (3 ICU)", 77.5912, 12.9178, STEEL, -0.045, -0.014),
        ("STJ (4 ICU)", 77.6209, 12.9293, STEEL, 0.048, 0.016),
    ]
    ox, oy = 77.4404, 12.6418
    for name, lng, lat, col, dx, dy in pins:
        if "JAIN" not in name:
            ax1.plot([ox, lng], [oy, lat], linestyle=":", color="#CBD5E1", linewidth=1.0, zorder=1)
        ax1.scatter([lng], [lat], s=85 if "JAIN" in name else 58, color=col, edgecolor="white", linewidth=1.3, zorder=3)
        ax1.annotate(
            name, xy=(lng, lat), xytext=(lng + dx, lat + dy),
            ha="center", va="center", fontsize=7.0, fontweight="bold", color=INK,
            arrowprops=dict(arrowstyle="-", color="#CBD5E1", lw=0.8) if abs(dx) > 0.02 or abs(dy) > 0.02 else None,
            zorder=4
        )

    ax1.set_xlim(77.37, 77.75)
    ax1.set_ylim(12.50, 12.99)
    ax1.set_xlabel("Longitude (°E)", fontsize=8.5, color=INK)
    ax1.set_ylabel("Latitude (°N)", fontsize=8.5, color=INK)
    ax1.set_title("A. 10-Hospital Kanakapura-Bengaluru Network", fontsize=10.2, fontweight="bold", color=INK)
    ax1.grid(True, linestyle="--", alpha=0.3, color="#9CA3AF")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    hids = list(dist.keys())[::-1]
    cnts = [dist[h] for h in hids]
    bars = ax2.barh(hids, cnts, color=STEEL, height=0.52, edgecolor="white")
    for b, v in zip(bars, cnts):
        ax2.text(v + 0.15, b.get_y() + b.get_height() / 2, f"{v} P1 patients", va="center", fontsize=8.4, fontweight="bold", color=INK)
    ax2.set_xlim(0, max(cnts) + 2.4)
    ax2.set_xlabel("Assigned Priority-1 Surge Requests (Total = 20)", fontsize=8.6, fontweight="bold", color=INK)
    ax2.set_title("B. Surge Mode: FIFO + Capacity Load Balancing", fontsize=10.2, fontweight="bold", color=INK)
    ax2.grid(axis="x", linestyle="--", alpha=0.35, color="#9CA3AF")
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
    print(f"Generated 9 understated academic figures in {OUT_DIR}")
