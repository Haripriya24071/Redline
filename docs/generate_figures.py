"""Generate clean textbook / Draw.io style OS diagrams and academic charts for Redline."""

from __future__ import annotations

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Patch, Polygon, Rectangle
import numpy as np

from os_engine.scheduler import default_workload, run_extended_benchmark, run_quantum_sweep
from os_engine.simulator import ScenarioSimulator

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures_color")
os.makedirs(OUT_DIR, exist_ok=True)

# Clean print / textbook neutral greys + restrained muted accents
INK = "#1A1A1A"
DARK_GREY = "#333333"
MID_GREY = "#666666"
LIGHT_BORDER = "#888888"
BOX_FILL = "#F5F5F5"
ALT_FILL = "#EBEBEB"
WHITE = "#FFFFFF"

MUTED_STEEL = "#4A6572"
MUTED_RED = "#8B3A3A"
MUTED_GREEN = "#3F6A4E"
MUTED_OCHRE = "#8A6D3B"

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial"]
plt.rcParams["axes.edgecolor"] = "#777777"
plt.rcParams["axes.linewidth"] = 0.8


def rect_box(ax, x, y, w, h, text, fc=BOX_FILL, ec=DARK_GREY, tc=INK, fs=8.5, lw=1.0, bold=False):
    r = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3)
    ax.add_patch(r)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, linespacing=1.35, zorder=4)


def round_term(ax, x, y, w, h, text, fc=ALT_FILL, ec=DARK_GREY, fs=8.5):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=0.035",
                       facecolor=fc, edgecolor=ec, linewidth=1.0, zorder=3)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold", color=INK, zorder=4)


def diamond(ax, cx, cy, w, h, text, fc=WHITE, ec=DARK_GREY, fs=8.0):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    poly = Polygon(pts, closed=True, facecolor=fc, edgecolor=ec, linewidth=1.0, zorder=3)
    ax.add_patch(poly)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.25, zorder=4)


def arrow(ax, x1, y1, x2, y2, label="", color=DARK_GREY, rad=0.0, lx=0.0, ly=0.0, ls="-", lw=1.1):
    arr = FancyArrowPatch(
        (x1, y1), (x2, y2),
        connectionstyle=f"arc3,rad={rad}",
        arrowstyle="-|>,head_length=5,head_width=2.8",
        color=color, linewidth=lw, linestyle=ls, zorder=2
    )
    ax.add_patch(arr)
    if label:
        ax.text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, ha="center", va="center",
                fontsize=7.6, color=color,
                bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none", alpha=0.9), zorder=5)


def fig1_architecture():
    fig, ax = plt.subplots(figsize=(10.2, 4.8), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    layers = [
        (0.76, "Presentation Layer (Flask Templates + JavaScript)\n9 Operational Screens, Style Guide, Light/Dark Themes, EN/HI/KN Switcher, Role Selector", WHITE),
        (0.54, "REST API Layer (app.py)\n/api/requests, /api/matches, /api/refer, /api/facilities (409 conflict), /api/monitor, /api/analytics, /api/export/csv", BOX_FILL),
        (0.32, "OS Engine (os_engine/)\nScheduler (FCFS, SJF, SRTF, Priority+Aging, RR, EDF, MLFQ) | Matcher | Reservation & Mutex | Banker's | RAG | Workers", ALT_FILL),
        (0.10, "Simulated Data & Logging Layer\n10 Bengaluru/Kanakapura Hospitals | Versioned Facility Semaphores | 8+ Seeded Processes | Audit & Event Logs", BOX_FILL),
    ]
    for y, txt, fc in layers:
        rect_box(ax, 0.05, y, 0.90, 0.14, txt, fc=fc, ec=DARK_GREY, fs=8.3)

    arrow(ax, 0.5, 0.76, 0.5, 0.68)
    arrow(ax, 0.5, 0.54, 0.5, 0.46)
    arrow(ax, 0.5, 0.32, 0.5, 0.24)

    fig.savefig(os.path.join(OUT_DIR, "fig1_architecture.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig2_dispatch_flowchart():
    fig, ax = plt.subplots(figsize=(10.8, 6.8), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Start / Intake
    round_term(ax, 0.03, 0.85, 0.17, 0.075, "Activity Intake")
    diamond(ax, 0.34, 0.887, 0.17, 0.11, "Duplicate\npatient_hash?")
    rect_box(ax, 0.255, 0.65, 0.17, 0.075, "Return HTTP 409\n(Confirm Override)", fc=WHITE, ec=MUTED_RED, tc=MUTED_RED, fs=7.8)

    rect_box(ax, 0.51, 0.85, 0.20, 0.075, "Create PCB (READY)\nAssign Priority & SLA", fc=BOX_FILL, fs=8.0)
    rect_box(ax, 0.77, 0.85, 0.19, 0.075, "CPU Scheduler\nPreempt if Higher Prio", fc=BOX_FILL, fs=8.0)

    # Matching & Mutex
    rect_box(ax, 0.75, 0.48, 0.21, 0.085, "Hospital Matcher\nFilter S>0 & Score ETA", fc=BOX_FILL, fs=8.0)
    rect_box(ax, 0.45, 0.48, 0.23, 0.085, "Mutex Critical Section\nResource Order, S--, PREPARE", fc=ALT_FILL, fs=8.0)
    rect_box(ax, 0.06, 0.48, 0.26, 0.085, "Parallel Top-N Hold\nMove PCB to WAITING", fc=BOX_FILL, fs=8.0)

    # Decision on reply
    diamond(ax, 0.19, 0.28, 0.19, 0.11, "Hospital\nResponse?")
    rect_box(ax, 0.04, 0.06, 0.25, 0.08, "ACCEPT: COMMITTED\nSibling holds released; TERMINATED", fc=BOX_FILL, ec=MUTED_GREEN, fs=7.8)
    rect_box(ax, 0.42, 0.24, 0.23, 0.08, "REJECT / TTL Expired\nsignal(S) & Escalate", fc=WHITE, ec=MUTED_RED, fs=7.8)
    rect_box(ax, 0.71, 0.24, 0.25, 0.08, "Banker's / RAG Check\nRelease victim if cycle", fc=BOX_FILL, fs=7.8)
    round_term(ax, 0.52, 0.06, 0.28, 0.08, "Update Audit Log & Tracker")

    arrow(ax, 0.20, 0.887, 0.255, 0.887)
    arrow(ax, 0.34, 0.832, 0.34, 0.725, "Yes", color=MUTED_RED, lx=0.025)
    arrow(ax, 0.425, 0.887, 0.51, 0.887, "No", color=DARK_GREY, ly=0.022)
    arrow(ax, 0.71, 0.887, 0.77, 0.887)
    arrow(ax, 0.865, 0.85, 0.865, 0.565)
    arrow(ax, 0.75, 0.522, 0.68, 0.522)
    arrow(ax, 0.45, 0.522, 0.32, 0.522)
    arrow(ax, 0.19, 0.48, 0.19, 0.335)
    arrow(ax, 0.16, 0.225, 0.16, 0.14, "Accept", color=MUTED_GREEN, lx=-0.04)
    arrow(ax, 0.285, 0.28, 0.42, 0.28, "Reject / Timeout", color=MUTED_RED, ly=0.025)
    arrow(ax, 0.535, 0.32, 0.79, 0.48, "Retry Next", color=MID_GREY, rad=-0.18, ls="--", ly=0.02)
    arrow(ax, 0.60, 0.48, 0.83, 0.32, "Multi-Resource", color=MID_GREY, lx=0.05)
    arrow(ax, 0.29, 0.10, 0.52, 0.10)
    arrow(ax, 0.83, 0.24, 0.70, 0.14)

    fig.savefig(os.path.join(OUT_DIR, "fig2_dispatch_flowchart.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig3_process_states():
    fig, ax = plt.subplots(figsize=(10.2, 4.1), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    rect_box(ax, 0.04, 0.58, 0.14, 0.15, "NEW", fc=WHITE, fs=9.5, bold=True)
    rect_box(ax, 0.27, 0.58, 0.16, 0.15, "READY", fc=BOX_FILL, fs=9.5, bold=True)
    rect_box(ax, 0.53, 0.58, 0.16, 0.15, "RUNNING", fc=ALT_FILL, fs=9.5, bold=True)
    rect_box(ax, 0.79, 0.58, 0.17, 0.15, "TERMINATED", fc=WHITE, fs=9.5, bold=True)
    rect_box(ax, 0.40, 0.20, 0.19, 0.15, "WAITING", fc=BOX_FILL, fs=9.5, bold=True)

    arrow(ax, 0.18, 0.655, 0.27, 0.655, "admit", ly=0.04)
    arrow(ax, 0.43, 0.685, 0.53, 0.685, "dispatch", ly=0.04)
    arrow(ax, 0.53, 0.62, 0.43, 0.62, "preempt / quantum", ly=-0.045)
    arrow(ax, 0.69, 0.655, 0.79, 0.655, "exit", ly=0.04)
    arrow(ax, 0.60, 0.58, 0.52, 0.35, "hold / await reply", lx=0.08)
    arrow(ax, 0.46, 0.35, 0.37, 0.58, "reply / signal(S)", lx=-0.08)

    rect_box(ax, 0.04, 0.03, 0.92, 0.085,
             "PCB attributes: PID, Category, Arrival Time, Base/Effective Priority (P1-P8), Burst/Remaining, SLA Deadline, Wait Ticks, State",
             fc=WHITE, ec=LIGHT_BORDER, fs=7.8)

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

    pid_colors = {
        "T1": "#607D8B",
        "T2": "#A8B2B8",
        "T3": "#78909C",
        "T4": "#8D99AE",
        "T5": "#546E7A",
        "T6": "#9E7B4F",
        "T7": "#A35A4A",
        "T8": "#7F2F2F",
    }

    fig, ax = plt.subplots(figsize=(10.8, 5.2), dpi=300)
    y_positions = np.arange(len(algos))[::-1]

    for y, (_, gantt) in zip(y_positions, algos):
        for seg in gantt:
            s, e, pid = seg["start"], seg["end"], seg["pid"]
            w = e - s
            ax.barh(y, w, left=s, height=0.55, color=pid_colors.get(pid, "#777777"), edgecolor="white", linewidth=1.0)
            ax.text(s + w / 2, y, pid, ha="center", va="center", color="white",
                    fontsize=7.6 if w >= 2 else 6.6, fontweight="bold")

    ax.set_yticks(y_positions)
    ax.set_yticklabels([a[0] for a in algos], fontsize=9.0, color=INK)
    ax.set_xlim(0, 40)
    ax.set_xticks(range(0, 41, 2))
    ax.set_xlabel("Normalised Time Units (0 to 40 ticks)", fontsize=9.0, color=INK)
    ax.grid(axis="x", linestyle=":", alpha=0.45, color="#999999")
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

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.3), dpi=300)

    x = np.arange(len(order))
    w = 0.26
    wt = [bench[k]["avg_waiting"] for _, k in order]
    tat = [bench[k]["avg_turnaround"] for _, k in order]
    crit = [bench[k]["critical_avg_response"] for _, k in order]

    ax1.bar(x - w, wt, width=w, label="Avg Waiting Time", color="#546E7A")
    ax1.bar(x, tat, width=w, label="Avg Turnaround Time", color="#90A4AE")
    ax1.bar(x + w, crit, width=w, label="Critical Response (T6-T8)", color=MUTED_RED)
    ax1.set_xticks(x)
    ax1.set_xticklabels([lbl for lbl, _ in order], fontsize=8, rotation=20, ha="right", color=INK)
    ax1.set_ylabel("Normalised Time Units (ticks)", fontsize=8.8, color=INK)
    ax1.set_title("Scheduling Metrics Comparison (T1-T8)", fontsize=9.8, color=INK)
    ax1.grid(axis="y", linestyle=":", alpha=0.45, color="#999999")
    ax1.legend(fontsize=7.6, frameon=False)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    qs = [d["quantum"] for d in sweep]
    q_wt = [d["avg_waiting"] for d in sweep]
    q_sw = [d["context_switches"] for d in sweep]

    l1 = ax2.plot(qs, q_wt, marker="o", linewidth=1.8, color=DARK_GREY, label="Avg Waiting Time")
    ax2.set_xlabel("Round Robin Time Quantum (Q)", fontsize=8.8, color=INK)
    ax2.set_ylabel("Avg Waiting Time (ticks)", fontsize=8.8, color=DARK_GREY)
    ax2.set_xticks(qs)
    ax2.grid(True, linestyle=":", alpha=0.45, color="#999999")
    ax2.spines["top"].set_visible(False)

    ax2_r = ax2.twinx()
    l2 = ax2_r.plot(qs, q_sw, marker="s", linestyle="--", linewidth=1.6, color=MUTED_RED, label="Context Switches")
    ax2_r.set_ylabel("Context Switches", fontsize=8.8, color=MUTED_RED)
    ax2_r.tick_params(axis="y", labelcolor=MUTED_RED)
    ax2_r.spines["top"].set_visible(False)

    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc="upper right", fontsize=7.6, frameon=False)
    ax2.set_title("Round Robin Quantum Sensitivity (Q = 1 to 8)", fontsize=9.8, color=INK)

    fig.tight_layout(pad=1.6)
    fig.savefig(os.path.join(OUT_DIR, "fig5_metrics_and_quantum.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig6_synchronization_two_phase():
    race = ScenarioSimulator.run_race_condition_demo(trials=1000)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.4), dpi=300, gridspec_kw={"width_ratios": [1.5, 1]})

    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.axis("off")
    ax1.set_title("Mutex Lock, Semaphore & Two-Phase Hold Sequence", fontsize=9.8, color=INK)

    rect_box(ax1, 0.03, 0.83, 0.22, 0.10, "Thread A (Req-1)", fc=WHITE, fs=8.2, bold=True)
    rect_box(ax1, 0.39, 0.83, 0.24, 0.10, "Mutex + Semaphore (S=1)", fc=BOX_FILL, fs=8.0, bold=True)
    rect_box(ax1, 0.74, 0.83, 0.23, 0.10, "Thread B (Req-2)", fc=WHITE, fs=8.2, bold=True)

    for x in (0.14, 0.51, 0.855):
        ax1.plot([x, x], [0.16, 0.83], linestyle=":", color=LIGHT_BORDER, linewidth=1.1)

    arrow(ax1, 0.14, 0.73, 0.50, 0.73, "1. lock() & wait(S)", ly=0.035)
    rect_box(ax1, 0.35, 0.54, 0.32, 0.11, "Critical Section (Thread A)\nS: 1->0, v: 1->2, PREPARE hold", fc=ALT_FILL, fs=7.5)
    arrow(ax1, 0.50, 0.48, 0.14, 0.48, "2. return Hold ID & unlock()", color=MUTED_GREEN, ly=0.035)
    arrow(ax1, 0.85, 0.39, 0.52, 0.39, "3. lock() & check S", ly=0.035)
    arrow(ax1, 0.52, 0.28, 0.85, 0.28, "4. S==0 -> Denied", color=MUTED_RED, ly=0.035)
    rect_box(ax1, 0.03, 0.03, 0.94, 0.11,
             "Parallel Top-N Referral: First hospital ACCEPT -> Phase=COMMITTED; sibling PREPARE holds -> ABORTED and signal(S) restores S",
             fc=BOX_FILL, ec=LIGHT_BORDER, fs=7.2)

    cats = ["Without Mutex\n(Unsafe Check-Then-Act)", "With Mutex Lock\n(Atomic Critical Section)"]
    vals = [race["without_mutex_double_bookings"], race["with_mutex_double_bookings"]]
    bars = ax2.bar(cats, vals, color=[MUTED_RED, MUTED_GREEN], width=0.44, edgecolor="white")
    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + 22, f"{v} / 1000\ndouble-bookings",
                 ha="center", va="bottom", fontsize=8.5, color=INK)
    ax2.set_ylim(0, 1180)
    ax2.set_ylabel("Double-Bookings (1,000 Trials)", fontsize=8.6, color=INK)
    ax2.set_title("Concurrency Race Experiment (1,000 Trials)", fontsize=9.8, color=INK)
    ax2.grid(axis="y", linestyle=":", alpha=0.45, color="#999999")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout(pad=1.6)
    fig.savefig(os.path.join(OUT_DIR, "fig6_synchronization_two_phase.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig7_starvation_aging_pi():
    aging = ScenarioSimulator.run_aging_starvation_demo()
    trace = aging["aging_trace"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.3), dpi=300)

    ticks = [pt["tick"] for pt in trace]
    prios = [pt["effective_priority"] for pt in trace]
    ax1.step(ticks, prios, where="post", linewidth=2.0, color=MUTED_GREEN, label="With Aging (-1 / 10 ticks)")
    ax1.axhline(8, linestyle="--", color=MUTED_RED, linewidth=1.6, label="Without Aging (Starves >120)")
    ax1.scatter([aging["with_aging_first_dispatch"]], [1], color=DARK_GREY, s=55, zorder=5)
    ax1.annotate(f"P8 Dispatched (t={aging['with_aging_first_dispatch']})",
                 xy=(aging["with_aging_first_dispatch"], 1),
                 xytext=(max(5, aging["with_aging_first_dispatch"] - 36), 2.1),
                 arrowprops=dict(arrowstyle="->", color=DARK_GREY, lw=1.2),
                 fontsize=8.2, color=INK)
    ax1.invert_yaxis()
    ax1.set_yticks(range(1, 9))
    ax1.set_yticklabels([f"P{i}" for i in range(1, 9)], fontsize=8.2, color=INK)
    ax1.set_xlabel("Simulation Time (ticks under continuous P1 stream)", fontsize=8.5, color=INK)
    ax1.set_ylabel("Effective Priority (P1 = highest)", fontsize=8.6, color=INK)
    ax1.set_title("Starvation Prevention via Priority Aging", fontsize=9.8, color=INK)
    ax1.grid(True, linestyle=":", alpha=0.45, color="#999999")
    ax1.legend(loc="lower left", fontsize=7.8, frameon=True, facecolor="white", edgecolor="#CCCCCC")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    ax2.barh(1.2, 2, left=0, height=0.36, color="#777777", edgecolor="white")
    ax2.text(1, 1.2, "P8\n(Lock)", ha="center", va="center", color="white", fontsize=7.3)
    ax2.barh(1.2, 2, left=2, height=0.36, color=MUTED_RED, edgecolor="white")
    ax2.text(3, 1.2, "P1\nWait", ha="center", va="center", color="white", fontsize=7.3)
    ax2.barh(1.2, 8, left=4, height=0.36, color=MUTED_OCHRE, edgecolor="white")
    ax2.text(8, 1.2, "P4 Preempts P8\n(Priority Inversion)", ha="center", va="center", color="white", fontsize=7.3)
    ax2.barh(1.2, 2, left=12, height=0.36, color="#777777", edgecolor="white")
    ax2.text(13, 1.2, "P8", ha="center", va="center", color="white", fontsize=7.3)
    ax2.barh(1.2, 3, left=14, height=0.36, color=MUTED_GREEN, edgecolor="white")
    ax2.text(15.5, 1.2, "P1 Runs\n(t=14)", ha="center", va="center", color="white", fontsize=7.3)

    ax2.barh(0.3, 2, left=0, height=0.36, color="#777777", edgecolor="white")
    ax2.text(1, 0.3, "P8\n(Lock)", ha="center", va="center", color="white", fontsize=7.3)
    ax2.barh(0.3, 2, left=2, height=0.36, color=MUTED_STEEL, edgecolor="white")
    ax2.text(3, 0.3, "P8->P1", ha="center", va="center", color="white", fontsize=7.3)
    ax2.barh(0.3, 3, left=4, height=0.36, color=MUTED_GREEN, edgecolor="white")
    ax2.text(5.5, 0.3, "P1 Runs\n(t=4)", ha="center", va="center", color="white", fontsize=7.3)
    ax2.barh(0.3, 8, left=7, height=0.36, color=MUTED_OCHRE, edgecolor="white")
    ax2.text(11, 0.3, "P4 Runs After P1", ha="center", va="center", color="white", fontsize=7.3)

    ax2.set_yticks([0.3, 1.2])
    ax2.set_yticklabels(["With Priority\nInheritance\n(Delay = 2t)", "Without\nInheritance\n(Delay = 12t)"], fontsize=8.2, color=INK)
    ax2.set_xlim(0, 18)
    ax2.set_xticks(range(0, 19, 2))
    ax2.set_xlabel("Ticks", fontsize=8.6, color=INK)
    ax2.set_title("Priority Inversion vs. Priority Inheritance", fontsize=9.8, color=INK)
    ax2.grid(axis="x", linestyle=":", alpha=0.45, color="#999999")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout(pad=1.6)
    fig.savefig(os.path.join(OUT_DIR, "fig7_starvation_aging_pi.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig8_deadlock_rag_banker():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.7), dpi=300)

    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.axis("off")
    ax1.set_title("Resource Allocation Graph (RAG) & Victim Recovery", fontsize=9.8, color=INK)

    c1 = Circle((0.17, 0.52), 0.105, facecolor=WHITE, edgecolor=DARK_GREY, linewidth=1.2, zorder=3)
    c2 = Circle((0.83, 0.52), 0.105, facecolor=WHITE, edgecolor=MUTED_RED, linewidth=1.2, zorder=3)
    ax1.add_patch(c1)
    ax1.add_patch(c2)
    ax1.text(0.17, 0.53, "Req-X\n(Hosp A, P2)", ha="center", va="center", fontsize=8.0, color=INK, zorder=4)
    ax1.text(0.83, 0.53, "Req-Y\n(Victim, P5)", ha="center", va="center", fontsize=8.0, color=MUTED_RED, zorder=4)

    rect_box(ax1, 0.36, 0.78, 0.28, 0.12, "R1: ICU Bed (1 unit)", fc=BOX_FILL, fs=8.2)
    rect_box(ax1, 0.36, 0.14, 0.28, 0.12, "R2: Ventilator (1 unit)", fc=BOX_FILL, fs=8.2)

    arrow(ax1, 0.36, 0.83, 0.23, 0.61, "holds", lx=-0.06, ly=0.03)
    arrow(ax1, 0.24, 0.43, 0.36, 0.21, "waits", color=MUTED_RED, lx=-0.06, ly=-0.03, ls="--")
    arrow(ax1, 0.64, 0.21, 0.77, 0.42, "holds", lx=0.06, ly=-0.03)
    arrow(ax1, 0.76, 0.62, 0.64, 0.83, "waits", color=MUTED_RED, lx=0.06, ly=0.03, ls="--")

    ax1.text(0.50, 0.52, "Deadlock Cycle:\nX -> R2 -> Y -> R1 -> X\n\nPreempt Req-Y\nRelease R2:Ventilator",
             ha="center", va="center", fontsize=7.5, color=INK,
             bbox=dict(boxstyle="square,pad=0.3", fc=BOX_FILL, ec=LIGHT_BORDER, lw=0.8))

    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis("off")
    ax2.set_title("Banker's Algorithm Safe-State Verification", fontsize=9.8, color=INK)

    rect_box(ax2, 0.10, 0.83, 0.72, 0.10, "Trial Allocation: Work = Avail - Req; Alloc += Req; Need -= Req", fc=WHITE, fs=7.8)
    diamond(ax2, 0.46, 0.64, 0.68, 0.17, "Need[j] <= Work?\n(for unfinished j)", fc=BOX_FILL, fs=7.8)
    rect_box(ax2, 0.10, 0.38, 0.64, 0.10, "Simulate completion: Work += Alloc[j]; Finish[j] = True", fc=ALT_FILL, fs=7.8)
    rect_box(ax2, 0.04, 0.10, 0.42, 0.13, "Safe sequence found\nGrant Request (Req-B)", fc=WHITE, ec=MUTED_GREEN, tc=MUTED_GREEN, fs=7.8)
    rect_box(ax2, 0.54, 0.10, 0.43, 0.13, "Unsafe (no sequence)\nDeny / Defer (Req-C)", fc=WHITE, ec=MUTED_RED, tc=MUTED_RED, fs=7.8)

    arrow(ax2, 0.46, 0.83, 0.46, 0.72)
    arrow(ax2, 0.42, 0.56, 0.42, 0.48, "Yes", color=MUTED_GREEN, lx=-0.05)
    arrow(ax2, 0.74, 0.43, 0.80, 0.64, "Loop", color=DARK_GREY, rad=-0.25, lx=0.05)
    arrow(ax2, 0.34, 0.38, 0.25, 0.23, "All Finish", color=MUTED_GREEN, lx=-0.08)
    arrow(ax2, 0.80, 0.64, 0.85, 0.23, "No", color=MUTED_RED, rad=-0.22, lx=0.04)

    fig.tight_layout(pad=1.6)
    fig.savefig(os.path.join(OUT_DIR, "fig8_deadlock_rag_banker.png"), bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def fig9_network_and_surge():
    surge = ScenarioSimulator.run_surge_simulation(num_requests=20)
    dist = surge["distribution"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.3), dpi=300)

    pins = [
        ("JAIN (Origin)", 77.4404, 12.6418, MUTED_RED, -0.005, -0.020),
        ("KNG (2 ICU)", 77.4199, 12.5462, MUTED_STEEL, 0.015, -0.018),
        ("DSH (2 ICU)", 77.4512, 12.6685, MUTED_GREEN, 0.018, 0.016),
        ("RRM (3 ICU)", 77.4608, 12.8858, MUTED_STEEL, -0.025, 0.016),
        ("BGS (4 ICU)", 77.4956, 12.9012, MUTED_STEEL, -0.025, 0.024),
        ("APL (3 ICU)", 77.5988, 12.8962, MUTED_STEEL, 0.035, -0.022),
        ("SGR (Stale)", 77.5994, 12.9288, MUTED_OCHRE, -0.038, 0.022),
        ("NAR (5 ICU)", 77.6948, 12.8105, MUTED_STEEL, -0.010, 0.018),
        ("MNI (3 ICU)", 77.5912, 12.9178, MUTED_STEEL, -0.045, -0.014),
        ("STJ (4 ICU)", 77.6209, 12.9293, MUTED_STEEL, 0.048, 0.016),
    ]
    ox, oy = 77.4404, 12.6418
    for name, lng, lat, col, dx, dy in pins:
        if "JAIN" not in name:
            ax1.plot([ox, lng], [oy, lat], linestyle=":", color="#BBBBBB", linewidth=0.9, zorder=1)
        ax1.scatter([lng], [lat], s=75 if "JAIN" in name else 50, color=col, edgecolor="white", linewidth=1.1, zorder=3)
        ax1.annotate(
            name, xy=(lng, lat), xytext=(lng + dx, lat + dy),
            ha="center", va="center", fontsize=6.9, color=INK,
            arrowprops=dict(arrowstyle="-", color="#BBBBBB", lw=0.7) if abs(dx) > 0.02 or abs(dy) > 0.02 else None,
            zorder=4
        )

    ax1.set_xlim(77.37, 77.75)
    ax1.set_ylim(12.50, 12.99)
    ax1.set_xlabel("Longitude (°E)", fontsize=8.4, color=INK)
    ax1.set_ylabel("Latitude (°N)", fontsize=8.4, color=INK)
    ax1.set_title("10-Hospital Kanakapura-Bengaluru Network", fontsize=9.8, color=INK)
    ax1.grid(True, linestyle=":", alpha=0.35, color="#AAAAAA")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    hids = list(dist.keys())[::-1]
    cnts = [dist[h] for h in hids]
    bars = ax2.barh(hids, cnts, color=MUTED_STEEL, height=0.5, edgecolor="white")
    for b, v in zip(bars, cnts):
        ax2.text(v + 0.15, b.get_y() + b.get_height() / 2, f"{v} P1 patients", va="center", fontsize=8.2, color=INK)
    ax2.set_xlim(0, max(cnts) + 2.4)
    ax2.set_xlabel("Assigned Priority-1 Requests (Total = 20)", fontsize=8.5, color=INK)
    ax2.set_title("Surge Mode: FIFO + Capacity Load Balancing", fontsize=9.8, color=INK)
    ax2.grid(axis="x", linestyle=":", alpha=0.45, color="#999999")
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
    print(f"Generated 9 textbook/Draw.io style figures in {OUT_DIR}")
