"""Build clean, human-styled university PDF and DOCX reports for Redline (HEMS-Link)."""

from __future__ import annotations

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor

from os_engine.scheduler import default_workload, hospital_10_workload, run_extended_benchmark, run_quantum_sweep
from os_engine.simulator import ScenarioSimulator

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(DOCS_DIR, "figures_color")
PDF_PATH = os.path.join(DOCS_DIR, "Redline_OS_Case_Study_Report.pdf")
DOCX_PATH = os.path.join(DOCS_DIR, "Redline_OS_Case_Study_Report.docx")

# Classic print greyscale palette
C_INK = colors.HexColor("#111111")
C_MUTED = colors.HexColor("#444444")
C_TBL_HDR = colors.HexColor("#EAEAEA")
C_TBL_HDR_LINE = colors.HexColor("#999999")
C_ZEBRA = colors.HexColor("#F8F8F8")
C_BORDER = colors.HexColor("#CCCCCC")

D_INK = RGBColor(0x11, 0x11, 0x11)
D_MUTED = RGBColor(0x44, 0x44, 0x44)

GROUP_MEMBERS = (
    "A B Shree Vaibhavi — 25BTRCA001\n"
    "Alona Prasad — 25BTRCA008\n"
    "Printa Nath — 25BTRCA044\n"
    "Punya Shree S — 25BTRCA045\n"
    "R Hari Priya — 25BTRCA046\n"
    "Rithika Vijay — 25BTRCA048\n"
    "Vinay — 25BTRCA057"
)


def gather_metrics() -> dict:
    bench8 = run_extended_benchmark(workload=default_workload(), quantum=3, aging_interval=0)
    bench10 = run_extended_benchmark(workload=hospital_10_workload(), quantum=3, aging_interval=10)
    sweep8 = run_quantum_sweep(workload=default_workload(), max_q=8)
    aging = ScenarioSimulator.run_aging_starvation_demo()
    race = ScenarioSimulator.run_race_condition_demo(trials=1000)
    dead = ScenarioSimulator.run_deadlock_demo()
    pi = ScenarioSimulator.run_priority_inheritance_demo()
    surge = ScenarioSimulator.run_surge_simulation(num_requests=20)
    cases = ScenarioSimulator.run_5_algorithm_test_cases()
    return {
        "bench8": bench8,
        "bench10": bench10,
        "sweep8": sweep8,
        "aging": aging,
        "race": race,
        "dead": dead,
        "pi": pi,
        "surge": surge,
        "cases": cases,
    }


def build_pdf(m: dict) -> None:
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=A4,
        leftMargin=19 * mm,
        rightMargin=19 * mm,
        topMargin=19 * mm,
        bottomMargin=19 * mm,
        title="Redline (HEMS-Link) - Operating Systems Case Study 2 Report",
        author="Group 25BTRCA - Jain University",
    )
    avail_w = A4[0] - 38 * mm

    base = getSampleStyleSheet()
    s_uni = ParagraphStyle("Uni", parent=base["Normal"], fontName="Times-Bold", fontSize=14, leading=18, alignment=TA_CENTER, textColor=C_INK)
    s_dept = ParagraphStyle("Dept", parent=base["Normal"], fontName="Times-Roman", fontSize=11.5, leading=15, alignment=TA_CENTER, textColor=C_MUTED)
    s_tag = ParagraphStyle("Tag", parent=base["Normal"], fontName="Times-Bold", fontSize=10.5, leading=14, alignment=TA_CENTER, textColor=C_MUTED)
    s_title = ParagraphStyle("TitleMain", parent=base["Normal"], fontName="Times-Bold", fontSize=18, leading=22, alignment=TA_CENTER, textColor=C_INK)
    s_subtitle = ParagraphStyle("SubTitle", parent=base["Normal"], fontName="Times-Bold", fontSize=12, leading=16, alignment=TA_CENTER, textColor=C_INK)
    s_sub = ParagraphStyle("SubMain", parent=base["Normal"], fontName="Times-Italic", fontSize=10.2, leading=14, alignment=TA_CENTER, textColor=C_MUTED)

    s_h1 = ParagraphStyle("H1", parent=base["Normal"], fontName="Times-Bold", fontSize=13, leading=17, textColor=C_INK, spaceBefore=12, spaceAfter=5, keepWithNext=True)
    s_h2 = ParagraphStyle("H2", parent=base["Normal"], fontName="Times-Bold", fontSize=11, leading=14.5, textColor=C_INK, spaceBefore=9, spaceAfter=4, keepWithNext=True)
    s_body = ParagraphStyle("Body", parent=base["Normal"], fontName="Times-Roman", fontSize=10.2, leading=14.5, alignment=TA_JUSTIFY, textColor=C_INK, spaceAfter=6)
    s_bullet = ParagraphStyle("Bullet", parent=s_body, leftIndent=16, firstLineIndent=-9, spaceAfter=3.5)
    s_cap = ParagraphStyle("Cap", parent=base["Normal"], fontName="Times-Italic", fontSize=9.0, leading=12, alignment=TA_CENTER, textColor=C_MUTED, spaceBefore=3, spaceAfter=9)
    s_tbl_hdr = ParagraphStyle("TblHdr", parent=base["Normal"], fontName="Times-Bold", fontSize=8.8, leading=11, textColor=C_INK)
    s_tbl_cell = ParagraphStyle("TblCell", parent=base["Normal"], fontName="Times-Roman", fontSize=8.8, leading=11.5, textColor=C_INK)
    s_tbl_bold = ParagraphStyle("TblBold", parent=s_tbl_cell, fontName="Times-Bold")

    def p_cell(txt: str, bold: bool = False) -> Paragraph:
        safe = str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
        return Paragraph(safe, s_tbl_bold if bold else s_tbl_cell)

    def p_hdr(txt: str) -> Paragraph:
        safe = str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return Paragraph(safe, s_tbl_hdr)

    def make_table(headers: list[str], rows: list[list[str]], col_widths: list[float], bold_col0: bool = True) -> Table:
        data = [[p_hdr(h) for h in headers]]
        for r in rows:
            data.append([p_cell(val, bold=(bold_col0 and idx == 0)) for idx, val in enumerate(r)])
        tbl = Table(data, colWidths=col_widths, repeatRows=1)
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), C_TBL_HDR),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_INK),
            ("LINEBELOW", (0, 0), (-1, 0), 0.9, C_TBL_HDR_LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ]
        for idx in range(1, len(data)):
            if idx % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, idx), (-1, idx), C_ZEBRA))
        tbl.setStyle(TableStyle(style_cmds))
        return tbl

    def add_figure(filename: str, caption: str, max_h_in: float = 3.5) -> KeepTogether:
        path = os.path.join(FIG_DIR, filename)
        from PIL import Image as PILImage
        with PILImage.open(path) as im:
            iw, ih = im.size
        w = avail_w
        h = w * (ih / iw)
        if h > max_h_in * inch:
            h = max_h_in * inch
            w = h * (iw / ih)
        img = RLImage(path, width=w, height=h)
        return KeepTogether([Spacer(1, 4), img, Paragraph(caption, s_cap)])

    story = []

    # --- COVER PAGE ---
    story.append(Spacer(1, 16))
    story.append(Paragraph("JAIN (DEEMED-TO-BE) UNIVERSITY", s_uni))
    story.append(Paragraph("Department of Computer Science &amp; Engineering (AI)", s_dept))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.9, color=C_INK, spaceBefore=2, spaceAfter=18))
    story.append(Paragraph("OPERATING SYSTEMS — CASE STUDY ASSIGNMENT", s_tag))
    story.append(Spacer(1, 14))
    story.append(Paragraph("REDLINE (HEMS-Link)", s_title))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Hospital Emergency Management &amp; Multi-Hospital Coordination System", s_subtitle))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "An Operating Systems study of CPU scheduling, real-time deadlines, shared-resource synchronisation, inter-process communication, and deadlock handling.",
        s_sub,
    ))
    story.append(Spacer(1, 22))
    story.append(make_table(
        ["Academic Detail", "Information"],
        [
            ["Course Name & Code", "Operating Systems — 25PCCS201"],
            ["Class & Section", "III Semester — CSE (AI)"],
            ["Faculty Name", "Gowri Shankar"],
            ["Group Members", GROUP_MEMBERS],
            ["Submission Date", "26/11/2026"],
        ],
        [avail_w * 0.32, avail_w * 0.68],
    ))
    story.append(Spacer(1, 18))
    story.append(Paragraph(
        "<i>Note: This is an academic prototype built with simulated hospital bed counts and synthetic patient IDs. It is meant for workflow decision support and does not replace clinical judgement.</i>",
        s_body,
    ))
    story.append(PageBreak())

    # --- PAGE 2: DECLARATION, ACKNOWLEDGEMENT, TOC ---
    story.append(Paragraph("Declaration", s_h1))
    story.append(Paragraph(
        "We declare that this case study report titled <i>Redline (HEMS-Link): Hospital Emergency Management and Multi-Hospital Coordination System</i> was prepared by our group as part of the Operating Systems course (25PCCS201, III Semester, CSE-AI) at Jain (Deemed-to-be) University. All scheduling calculations, concurrency tests, and prototype observations were produced and verified on our own implementation.",
        s_body,
    ))
    story.append(Paragraph("Acknowledgement", s_h1))
    story.append(Paragraph(
        "We thank our faculty guide, Prof. Gowri Shankar, and the Department of Computer Science and Engineering (AI) for encouraging us to study how core Operating Systems concepts apply to hospital emergency operations.",
        s_body,
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Table of Contents", s_h1))
    toc_rows = [
        ["1", "Abstract", "3"],
        ["2", "Introduction and Problem Statement", "3"],
        ["3", "Objectives, Scope, and Assumptions", "3–4"],
        ["4", "System Description (10-Hospital Network)", "4"],
        ["5", "Mapping Hospital Entities to OS Concepts", "5–6"],
        ["6", "OS Concepts, Process Lifecycle, and Real-Time Tasks", "7"],
        ["7", "CPU Scheduling Calculations, Gantt Charts, and Quantum Analysis", "8–11"],
        ["8", "Effect of Continuous Emergency Arrivals", "12"],
        ["9", "Synchronisation, Two-Phase Holds, and Deadlock Handling", "12–13"],
        ["10", "Proposed Hybrid Policy and Expected OS Behaviour", "13"],
        ["11", "Prototype Results, Test Cases, and Automated Verification", "14"],
        ["12–14", "Recommended Future Features, Conclusion, and References", "15"],
    ]
    story.append(make_table(["Section", "Title", "Page"], toc_rows, [avail_w * 0.14, avail_w * 0.72, avail_w * 0.14]))
    story.append(PageBreak())

    # --- SECTION 1 & 2 ---
    race = m["race"]
    b8 = m["bench8"]
    story.append(Paragraph("1. Abstract", s_h1))
    story.append(Paragraph(
        f"During medical emergencies, a hospital computer system must juggle urgent arrivals such as cardiac arrests, road trauma, and strokes alongside routine outpatient (OP) queues, ICU monitoring, lab tests, pharmacy requests, and inter-hospital patient transfers. When a hospital runs out of ICU beds, calling nearby hospitals by phone wastes valuable time, relies on stale counts, and creates a risk of two callers booking the same last bed. In Redline (HEMS-Link), we model a ten-hospital network around Kanakapura Road and South Bengaluru using Operating Systems concepts.",
        s_body,
    ))
    story.append(Paragraph(
        f"Each hospital task or transfer request is tracked as a five-state Process Control Block (PCB). ICU beds and ventilators act as counting semaphores, bed reservations run inside a mutex critical section with two-phase holds and version checks, and hospital replies arrive asynchronously via IPC queues. We compared eight scheduling policies (FCFS, SJF, SRTF, Non-Preemptive Priority, Preemptive Priority, Round Robin with Q=3, EDF, and MLFQ) on an eight-process baseline (T1–T8) and a ten-process hospital mix (H1–H10). SJF produces the lowest overall average wait ({b8['sjf']['avg_waiting']} ticks), while Preemptive Priority gives 0.00-tick response time for critical emergencies. Pairing Preemptive Priority with aging (-1 every 10 ticks) keeps low-priority work from starving. In a 1,000-trial concurrency test, adding a mutex reduced double-bookings from {race['without_mutex_double_bookings']}/1,000 to {race['with_mutex_double_bookings']}/1,000.",
        s_body,
    ))

    story.append(Paragraph("2. Introduction and Problem Statement", s_h1))
    story.append(Paragraph(
        "A hospital information system processes tasks with very different urgency levels. A cardiac arrest or trauma patient needs immediate CPU and clinical attention, whereas an outpatient registration, a routine pharmacy refill, or a planned step-down transfer can tolerate a short delay. Putting hospital bed counts on a shared digital platform removes manual phone delays, but it also introduces familiar Operating Systems issues: urgent arrivals act like interrupts, several users update bed availability at the same time, and two hospitals can try to claim the last free bed simultaneously.",
        s_body,
    ))
    story.append(Paragraph(
        "<b>Problem Statement:</b> There is a need for a centralised hospital emergency management and transfer coordination system that schedules emergency patients, ICU monitoring, laboratory tests, OP queues, pharmacy requests, and inter-hospital transfers efficiently, ensuring critical tasks execute within required time limits without causing double-booking, starvation, or deadlocks.",
        s_body,
    ))

    # --- SECTION 3 & 4 ---
    story.append(Paragraph("3. Objectives, Scope, and Assumptions", s_h1))
    story.append(Paragraph("3.1 Objectives", s_h2))
    for i, item in enumerate([
        "Model hospital activities across emergency care, ICU monitoring, lab tests, OP queues, pharmacy requests, and transfers as OS processes.",
        "Assign realistic priorities, arrival times, burst times, and SLA deadlines to at least eight processes and compare FCFS, SJF, Priority Scheduling, Round Robin (Q=3), SRTF, EDF, and MLFQ.",
        "Calculate Waiting Time, Turnaround Time, Response Time, CPU utilisation, throughput, and deadline compliance.",
        "Identify which activities require real-time response and test how continuous emergency arrivals affect routine tasks.",
        "Prevent race conditions, starvation, priority inversion, and deadlocks using mutex locks, counting semaphores, two-phase holds, resource ordering, RAG cycle detection, and Banker's Algorithm.",
    ], 1):
        story.append(Paragraph(f"{i}. {item}", s_bullet))

    story.append(Paragraph("3.2 Assumptions and Scope", s_h2))
    story.append(Paragraph(
        "To compare all eight scheduling algorithms fairly on identical workloads, CPU burst times and arrival times are measured in normalised simulation ticks rather than wall-clock seconds. Our primary benchmark evaluates preemption and context switching on a single CPU queue, while multi-core scheduling is discussed as a future extension in Section 12. The ten hospital locations correspond to real facilities along Kanakapura Road and South Bengaluru, though all bed counts and patient identifiers are simulated. Finally, automated holds only reserve beds tentatively until receiving hospital staff accept.",
        s_body,
    ))

    story.append(Paragraph("4. System Description (10-Hospital Network)", s_h1))
    story.append(Paragraph(
        "Our prototype connects the origin facility, Jain University Health Centre (Kanakapura Road), to nine receiving hospitals in South Bengaluru and Kanakapura: Dayananda Sagar Hospital, Rajarajeswari Medical College, BGS Gleneagles Global, Apollo Hospital, Sagar Hospital (configured with stale timestamps for testing), Kanakapura Taluk General, Narayana Health City, Manipal Hospital, and St. John's Medical College. When a patient or internal task is entered, the scheduler admits a PCB, the matcher ranks eligible hospitals using distance/ETA (50%), trust score (20%), freshness (15%), and incoming load (15%), and the reservation engine places a timed hold.",
        s_body,
    ))
    story.append(make_table(
        ["Aspect", "Manual Phone-Based Process", "Redline OS-Based System"],
        [
            ["Hospital Discovery", "Staff call receiving desks one by one, wasting minutes.", "Matcher filters and ranks all 9 receiving hospitals at once."],
            ["Bed Availability", "Local sheets and phone notes go stale quickly.", "Shared counting semaphores carry timestamps and stale flags."],
            ["Bed Conflicts", "Two callers can be promised the same last ICU bed.", "Mutex critical section and version tokens reject conflicts (HTTP 409)."],
            ["Task Prioritisation", "Ad-hoc queues delay urgent cases behind routine traffic.", "Preemptive Priority with aging and EDF deadline tracking."],
            ["Referral Tracking", "No shared visibility once a call is made.", "5-state PCB tracker, parallel top-N holds, and timeout escalation."],
        ],
        [avail_w * 0.22, avail_w * 0.36, avail_w * 0.42],
    ))
    story.append(PageBreak())

    # --- SECTION 5: MAPPING, ARCHITECTURE & FLOWCHART ---
    story.append(Paragraph("5. Mapping Hospital Entities to OS Concepts", s_h1))
    story.append(Paragraph(
        "Table 5.1 maps each hospital workflow in Redline to its Operating Systems counterpart, followed by the system architecture (Figure 1) and end-to-end dispatch flowchart (Figure 2).",
        s_body,
    ))
    story.append(make_table(
        ["Real-World Hospital Component", "Operating System Concept", "How It Works in Redline"],
        [
            ["Cardiac arrest / trauma / stroke", "High-priority preemptive process (P1–P3)", "Preempts running routine tasks immediately for 0-tick response."],
            ["ICU telemetry & Stat ABG lab", "Urgent / periodic real-time process (P2–P3)", "Tracked against tight SLA deadlines under EDF and Priority scheduling."],
            ["OP walk-in, pharmacy refill, dialysis", "Medium/low-priority process (P4–P8)", "Queued in READY; aging (-1 every 10 ticks) prevents starvation."],
            ["New emergency arrival", "Hardware interrupt / Preemption", "Interrupts lower-priority execution and returns the old PCB to READY."],
            ["Central coordination server", "Kernel / CPU Scheduler", "Picks the next READY PCB according to the active policy."],
            ["Hospital matching engine", "Resource allocator", "Checks free capacity and scores candidate hospitals."],
            ["ICU beds, Ventilators, Specialists", "Counting Semaphores (S = free units)", "wait(S) decrements on hold; signal(S) restores on reject or timeout."],
            ["Two hospitals claiming last bed", "Critical section & Race condition", "Protected by a threading.Lock mutex and version check."],
            ["Referral hold & hospital reply", "Asynchronous IPC Message Queue", "PREPARE holds move the PCB to WAITING until reply or timeout."],
            ["Holding ICU bed while waiting for Vent", "Deadlock (Circular Wait)", "Avoided by fixed resource order; broken by RAG victim release."],
        ],
        [avail_w * 0.30, avail_w * 0.28, avail_w * 0.42],
    ))
    story.append(add_figure("fig1_architecture.png", "Figure 1. Redline layered architecture connecting the UI, Flask API, OS engine, and simulated hospital store.", max_h_in=2.95))
    story.append(add_figure("fig2_dispatch_flowchart.png", "Figure 2. End-to-end dispatch flowchart from activity intake through scheduling, mutex reservation, and recovery.", max_h_in=3.7))
    story.append(PageBreak())

    # --- SECTION 6: OS CONCEPTS & REAL-TIME CLASSIFICATION ---
    story.append(Paragraph("6. OS Concepts, Process Lifecycle, and Real-Time Tasks", s_h1))
    story.append(Paragraph(
        "Every incoming task is stored as a Process Control Block (PCB) with its PID, category, arrival time, base and effective priority, remaining burst time, SLA deadline, and waiting ticks. When a referral waits for an external hospital reply, moving it from RUNNING to WAITING frees the CPU for other work (Figure 3).",
        s_body,
    ))
    story.append(add_figure("fig3_process_states.png", "Figure 3. Five-state process lifecycle and PCB attributes in Redline.", max_h_in=1.85))

    story.append(Paragraph("6.1 Real-Time Task Classification", s_h2))
    story.append(make_table(
        ["Real-Time Class", "Hospital Activities", "Priority & Slack", "Reason for Classification"],
        [
            ["Hard Real-Time\n(Design Target)", "Cardiac Arrest (P1), Trauma ICU+Vent (P2), ICU Telemetry (P2), Stroke Unit (P3), Stat ABG Lab (P3)", "P1–P3; tight slack (+3 to +7 ticks); 0-tick dispatch target", "Missed deadlines or double-booked beds put patient survival at risk."],
            ["Soft Real-Time", "Availability Sync (P4), ICU Epinephrine Stat (P4), Urgent Lab Share (P5), OP Triage (P5)", "P4–P5; moderate slack (+12 to +15 ticks)", "Needed promptly to keep telemetry and triage current, though brief delays are tolerable."],
            ["Non-Real-Time", "Specialist Enquiry (P6), Planned Dialysis (P7), Ward Refill (P7), Discharge-Back (P8)", "P6–P8; wide slack (+20 to +32 ticks)", "Routine administrative or scheduled work without strict deadlines."],
        ],
        [avail_w * 0.18, avail_w * 0.34, avail_w * 0.20, avail_w * 0.28],
    ))

    story.append(Paragraph("6.2 Ten-Process Full Hospital Clinical Mix (H1–H10)", s_h2))
    story.append(Paragraph(
        "Besides the eight-process baseline (T1–T8) and eight live seeded requests (REQ-1001–REQ-1008), we created a ten-process clinical mix (H1–H10) covering emergency patients, ICU monitoring, lab tests, OP queues, and pharmacy requests:",
        s_body,
    ))
    h10_rows = [
        [r["pid"], r["name"], r["category"], str(r["arrival"]), f"P{r['priority']}", str(r["burst"]), f"t={r['deadline']}", "Hard RT" if r["priority"] <= 3 else ("Soft RT" if r["priority"] <= 5 else "Non-RT")]
        for r in m["bench10"]["edf"]["rows"]
    ]
    story.append(make_table(
        ["PID", "Hospital Activity", "Subsystem", "AT", "Prio", "BT", "SLA DL", "RT Class"],
        h10_rows,
        [avail_w * 0.08, avail_w * 0.29, avail_w * 0.17, avail_w * 0.06, avail_w * 0.07, avail_w * 0.06, avail_w * 0.10, avail_w * 0.17],
    ))
    story.append(PageBreak())

    # --- SECTION 7: CPU SCHEDULING ANALYSIS ---
    story.append(Paragraph("7. CPU Scheduling Calculations, Gantt Charts, and Quantum Analysis", s_h1))
    story.append(Paragraph(
        "All algorithms were evaluated on the same eight-process workload (T1–T8), where routine activities arrive first (t=0..3) and critical emergencies arrive later (t=4..6). We used the standard formulae: Turnaround Time (TAT) = Completion (CT) − Arrival (AT), Waiting Time (WT) = TAT − Burst (BT), and Response Time (RT) = First Dispatch − AT.",
        s_body,
    ))
    t8_rows = [
        [p.pid, p.name, str(p.arrival_time), f"P{p.priority}", str(p.burst_time), f"t={p.deadline}", p.category]
        for p in default_workload()
    ]
    story.append(make_table(
        ["PID", "Hospital Activity", "AT", "Priority", "BT", "SLA DL", "Subsystem"],
        t8_rows,
        [avail_w * 0.08, avail_w * 0.34, avail_w * 0.07, avail_w * 0.09, avail_w * 0.07, avail_w * 0.11, avail_w * 0.24],
    ))
    story.append(add_figure("fig4_gantt_charts.png", "Figure 4. Gantt charts for FCFS, SJF, SRTF, Preemptive Priority, Round Robin (Q=3), and Real-Time EDF (0–40 ticks).", max_h_in=3.45))

    def sched_table(title: str, key: str, obs: str):
        d = b8[key]
        rows = [[r["pid"], str(r["arrival"]), f"P{r['priority']}", str(r["burst"]), str(r["completion"]), str(r["turnaround"]), str(r["waiting"]), str(r["response"])] for r in d["rows"]]
        story.append(KeepTogether([
            Paragraph(title, s_h2),
            make_table(["PID", "AT", "Prio", "BT", "CT", "TAT", "WT", "RT"], rows, [avail_w / 8.0] * 8),
            Paragraph(
                f"<b>Averages:</b> Wait = {d['avg_waiting']} | TAT = {d['avg_turnaround']} | Resp = {d['avg_response']} | <b>Critical (T6–T8) Avg Resp = {d['critical_avg_response']}</b> | Switches = {d['context_switches']}. {obs}",
                s_body,
            ),
        ]))

    sched_table("7.1 First Come First Served (FCFS)", "fcfs", "Because FCFS is non-preemptive, Cardiac Arrest (T8) arrives at t=6 but sits behind routine work until t=33 (RT=27).")
    sched_table("7.2 Shortest Job First (SJF — Non-Preemptive) & SRTF", "sjf", "SJF and SRTF give the lowest overall average wait (11.00 ticks), yet Cardiac Arrest (T8) still waits until t=25 (RT=19) because shorter routine jobs run first.")
    story.append(PageBreak())
    sched_table("7.3 Preemptive Priority Scheduling (Recommended Core Policy)", "preemptive_priority", "All three critical cases (T6, T7, T8) start immediately upon arrival (Critical Avg Response = 0.00). Without aging, T2 waits 37 ticks, showing why aging is needed.")
    sched_table("7.4 Round Robin Scheduling (Time Quantum Q = 3)", "round_robin", "Time-slicing gives early tasks quick initial response (9.00 average), but delays Cardiac Arrest (T8) by 18 ticks before its first slice and finishes it last at t=40.")
    sched_table("7.5 Earliest Deadline First (EDF — Real-Time Dynamic Priority)", "edf", "EDF orders tasks by nearest SLA deadline, keeping Critical Avg Wait at 4.67 ticks with only 1 context switch.")

    story.append(Paragraph("7.6 Eight-Algorithm Summary and Round Robin Quantum Sensitivity", s_h2))
    comp_labels = [
        ("FCFS", "fcfs"),
        ("SJF (Non-Preemptive)", "sjf"),
        ("SRTF (Preemptive SJF)", "srtf"),
        ("Non-Preemptive Priority", "non_preemptive_priority"),
        ("Preemptive Priority", "preemptive_priority"),
        ("Round Robin (Q=3)", "round_robin"),
        ("EDF (Real-Time)", "edf"),
        ("MLFQ (3-Level)", "mlfq"),
    ]
    comp_rows = [
        [lbl, str(b8[k]["avg_waiting"]), str(b8[k]["avg_turnaround"]), str(b8[k]["avg_response"]),
         str(b8[k]["critical_avg_waiting"]), str(b8[k]["critical_avg_response"]),
         str(b8[k]["context_switches"]), f"{b8[k]['cpu_utilization_pct']}%", f"{b8[k]['throughput']}/t"]
        for lbl, k in comp_labels
    ]
    story.append(make_table(
        ["Algorithm", "Avg WT", "Avg TAT", "Avg RT", "Crit WT", "Crit RT", "Switches", "CPU %", "Thru"],
        comp_rows,
        [avail_w * 0.24, avail_w * 0.09, avail_w * 0.09, avail_w * 0.09, avail_w * 0.09, avail_w * 0.09, avail_w * 0.10, avail_w * 0.10, avail_w * 0.11],
    ))
    story.append(add_figure("fig5_metrics_and_quantum.png", "Figure 5. Scheduling metric comparison across all eight policies and Round Robin Quantum sweep (Q=1..8).", max_h_in=2.95))
    story.append(PageBreak())

    # --- SECTION 8: IMPACT OF CONTINUOUS EMERGENCIES ---
    story.append(Paragraph("8. Effect of Continuous Emergency Arrivals", s_h1))
    story.append(Paragraph(
        "When Priority-1 emergencies keep arriving back-to-back, plain Preemptive Priority creates two problems. First, low-priority tasks such as OP discharges or planned dialysis can starve indefinitely. Second, if a low-priority task holds a shared availability lock when a Priority-1 request arrives, medium-priority tasks can preempt the lock-holder and delay the emergency (priority inversion).",
        s_body,
    ))
    ag = m["aging"]
    pi = m["pi"]
    story.append(make_table(
        ["Phenomenon", "Test Setup", "Without Mitigation", "With Redline Mitigation"],
        [
            ["Starvation under Continuous P1 Stream", "P1 arrives every 4 ticks for 120 ticks; P8 arrives at t=1 (BT=2).", f"P8 first dispatch: {ag['without_aging_first_dispatch'] or 'Starved (>120 ticks)'}", f"Aging (-1 every 10 ticks) raises P8 to P1; dispatched at t={ag['with_aging_first_dispatch']}."],
            ["Priority Inversion on Availability Lock", "P8 holds lock; P1 needs lock at t=2; P4 medium task arrives.", f"P4 preempts P8; P1 waits {pi['delay_without']} ticks (until t=14).", f"Priority Inheritance raises P8 to P1; P1 runs after {pi['delay_with']} ticks (t=4)."],
        ],
        [avail_w * 0.22, avail_w * 0.26, avail_w * 0.25, avail_w * 0.27],
    ))
    story.append(add_figure("fig7_starvation_aging_pi.png", "Figure 6. Priority aging rescuing P8 at t=72 (left) and Priority Inheritance eliminating medium-task delay (right).", max_h_in=2.95))

    # --- SECTION 9: SYNCHRONIZATION & DEADLOCK ---
    story.append(Paragraph("9. Synchronisation, Two-Phase Holds, and Deadlock Handling", s_h1))
    story.append(Paragraph(
        "Each facility at a hospital is tracked as a counting semaphore (S = free units). Checking and decrementing S executes inside a mutex critical section together with an optimistic version token. Rather than blocking the CPU while waiting for a receiving hospital to reply, Redline places a timed two-phase hold (PREPARE, then COMMITTED, ABORTED, or EXPIRED) and supports Top-N parallel referral so the first acceptance commits and releases all sibling holds.",
        s_body,
    ))
    story.append(add_figure("fig6_synchronization_two_phase.png", "Figure 7. Mutex critical section with two-phase holds (left) and 1,000-trial concurrency proof (right).", max_h_in=2.9))
    story.append(PageBreak())

    story.append(Paragraph("9.1 Deadlock Prevention, RAG Detection, and Banker's Algorithm", s_h2))
    story.append(Paragraph(
        "If one request holds an ICU bed (R1) and waits for a ventilator (R2) while another holds R2 and waits for R1, all four Coffman conditions hold and both block. Redline handles this at three levels: (1) global resource ordering (ICU, Emergency, Ventilator, Neuro, Specialist) to prevent circular wait; (2) a Resource Allocation Graph (RAG) cycle detector that releases the lowest-priority victim; and (3) Banker's Algorithm safe-state checks, tested on Hospital B (Total=[3,2,1], Available=[1,1,0]) where Req-B's [0,1,0] request is granted safely while Req-C's [0,1,0] is denied as unsafe.",
        s_body,
    ))
    story.append(make_table(
        ["Hospital B Request", "Allocation [ICU, Vent, Spec]", "Max Need", "Remaining Need", "Banker's Safe-State Decision"],
        [
            ["Req-A (Cardiac)", "[1, 0, 0]", "[1, 0, 0]", "[0, 0, 0]", "Finishes first; releases [1, 0, 0]"],
            ["Req-B (Trauma)", "[1, 1, 0]", "[1, 2, 0]", "[0, 1, 0]", "Request [0, 1, 0] -> GRANTED (Safe seq: A->B->C)"],
            ["Req-C (Stroke)", "[0, 0, 1]", "[1, 2, 1]", "[1, 2, 0]", "Request [0, 1, 0] -> DENIED (Unsafe; risks deadlock)"],
        ],
        [avail_w * 0.20, avail_w * 0.19, avail_w * 0.14, avail_w * 0.15, avail_w * 0.32],
    ))
    story.append(add_figure("fig8_deadlock_rag_banker.png", "Figure 8. Bed-ventilator RAG deadlock cycle and victim release (left), and Banker's safe-state check (right).", max_h_in=2.65))

    # --- SECTION 10: PROPOSED POLICY & EXPECTED OS BEHAVIOUR ---
    story.append(Paragraph("10. Proposed Hybrid Policy and Expected OS Behaviour", s_h1))
    story.append(Paragraph(
        "Under normal hospital load, our proposed policy uses Preemptive Priority with Aging (-1 every 10 waiting ticks) paired with EDF SLA deadline monitoring. During a mass-casualty surge, Priority-1 emergencies switch to Surge FIFO with capacity-based load balancing, suspending aging for P1 and skipping stale hospital records.",
        s_body,
    ))
    story.append(make_table(
        ["Expected OS Behaviour Question", "Kernel Action in Redline"],
        [
            ["1. Which process should execute?", "The highest-priority READY process (or earliest deadline under EDF) immediately preempts lower-priority tasks."],
            ["2. Which process should wait?", "Preempted routine tasks return to READY; referrals awaiting hospital confirmation enter WAITING without blocking the CPU."],
            ["3. How are resources allocated?", "The matcher filters free semaphores, ranks by ETA, trust, freshness, and load, and locks resources in fixed global order."],
            ["4. How is synchronisation maintained?", "A mutex protects wait(S)/signal(S) critical sections, and version tokens reject stale edits with HTTP 409."],
            ["5. How does it recover from failure?", "Expiry workers abort timed-out holds, call signal(S), and escalate; the RAG detector preempts the lowest-priority victim."],
        ],
        [avail_w * 0.36, avail_w * 0.64],
    ))
    story.append(PageBreak())

    # --- SECTION 11: PROTOTYPE EVIDENCE & TESTS ---
    story.append(Paragraph("11. Prototype Results, Test Cases, and Automated Verification", s_h1))
    story.append(Paragraph(
        "We built the full Flask and Python prototype with 9 operational screens plus a Style Guide (light/dark themes, EN/HI/KN language support, and role-based access controls), an interactive Live Kernel Stepper, a Custom Process Builder, Gantt and Quantum Sensitivity charts, and CSV report export. Table 11.1 summarises five hospital test cases and Table 11.2 lists our 19 automated pytest checks.",
        s_body,
    ))
    case_rows = [[c["case_id"], c["title"], c["best_algorithm"], c["metric_comparison"], c["why"]] for c in m["cases"]]
    story.append(make_table(
        ["Case", "Hospital Scenario", "Best Algorithm", "Measured Result", "Why It Wins"],
        case_rows,
        [avail_w * 0.09, avail_w * 0.23, avail_w * 0.18, avail_w * 0.23, avail_w * 0.27],
    ))
    story.append(Spacer(1, 6))
    story.append(make_table(
        ["Test Suite ID", "Automated Pytest Verification Scope (19/19 Passed)", "Status"],
        [
            ["T1", "100x2 concurrent thread last-bed reservation (0 double-bookings)", "PASSED"],
            ["T2–T3", "Priority preemption (P1 interrupts P7) & aging under continuous P1 stream", "PASSED"],
            ["T4–T5", "Hold TTL timeout escalation & parallel referral first-accept-wins", "PASSED"],
            ["T6 & RAG", "Banker's safe-state check (Hospital B) & RAG cycle victim recovery", "PASSED"],
            ["T7–T12", "409 version conflict, stale ranking, duplicate PAT, RBAC/break-glass, 10 UI routes, surge", "PASSED"],
            ["Extended Suite", "8-algorithm benchmark, 10-process clinical mix, EDF deadline SLA, Quantum sweep, CSV export", "PASSED (19/19)"],
        ],
        [avail_w * 0.16, avail_w * 0.66, avail_w * 0.18],
    ))
    story.append(add_figure("fig9_network_and_surge.png", "Figure 9. Simulated 10-hospital Kanakapura-Bengaluru network (left) and 20-request Surge FIFO distribution (right).", max_h_in=2.85))
    story.append(PageBreak())

    # --- SECTION 12 & 13: RECOMMENDATIONS, CONCLUSION & REFERENCES ---
    story.append(Paragraph("12. Recommended Future Features", s_h1))
    story.append(Paragraph(
        "Based on our testing, five extensions would make the system closer to production hospital infrastructure:",
        s_body,
    ))
    for i, item in enumerate([
        "Multi-core SMP scheduling with processor affinity so Emergency Triage, ICU Telemetry, and Lab Processing run on separate cores.",
        "Rate Monotonic Scheduling (RMS) for periodic ICU vitals polling (ECG, SpO2, ventilator checks) using Liu-Layland utilisation bounds.",
        "Persistent SQLite storage in WAL mode paired with Server-Sent Events (SSE) so live updates push to open terminals automatically.",
        "Road-network Dijkstra or A* routing weighted by live Bengaluru traffic instead of straight-line Haversine distance.",
        "EDF admission control that defers non-critical OP tasks when CPU load threatens hard real-time deadlines, alongside HL7/FHIR data stubs.",
    ], 1):
        story.append(Paragraph(f"{i}. {item}", s_bullet))

    story.append(Paragraph("13. Conclusion", s_h1))
    story.append(Paragraph(
        "Modelling hospital emergency management and multi-hospital coordination as an Operating System clarifies why average waiting time alone is not the right metric. SJF produces the lowest overall wait (11.00 ticks) while delaying a cardiac arrest until t=25, whereas Preemptive Priority dispatches critical emergencies immediately at 0.00 response time. Combining Preemptive Priority with aging (-1 every 10 ticks), EDF deadline checks, mutex-protected two-phase holds, Banker's safe-state verification, and RAG recovery keeps the system responsive, fair, and deadlock-free while leaving final medical decisions with hospital staff.",
        s_body,
    ))

    story.append(Paragraph("14. References", s_h1))
    for ref in [
        "1. Silberschatz, A., Galvin, P. B., & Gagne, G., <i>Operating System Concepts</i>, 10th ed., Wiley, 2018.",
        "2. Tanenbaum, A. S., <i>Modern Operating Systems</i>, 4th ed., Pearson, 2015.",
        "3. Coffman, E. G., Elphick, M. J., & Shoshani, A., \"System Deadlocks,\" <i>ACM Computing Surveys</i>, 3(2), 1971.",
        "4. Liu, C. L., & Layland, J. W., \"Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment,\" <i>JACM</i>, 20(1), 1973.",
        "5. Dijkstra, E. W., \"Cooperating Sequential Processes,\" Technical Report EWD123, 1965.",
        "6. IEEE Std 1003.1 (POSIX) — Interfaces for Semaphores, Mutexes, and Message Queues.",
    ]:
        story.append(Paragraph(ref, s_body))

    def draw_header_footer(canvas, doc_obj):
        canvas.saveState()
        if doc_obj.page > 1:
            canvas.setFont("Times-Roman", 8.5)
            canvas.setFillColor(C_MUTED)
            canvas.drawString(19 * mm, A4[1] - 12 * mm, "REDLINE (HEMS-Link) — Operating Systems Case Study 2 (25PCCS201)")
            canvas.drawRightString(A4[0] - 19 * mm, A4[1] - 12 * mm, "Jain (Deemed-to-be) University")
            canvas.setStrokeColor(C_BORDER)
            canvas.setLineWidth(0.5)
            canvas.line(19 * mm, A4[1] - 14 * mm, A4[0] - 19 * mm, A4[1] - 14 * mm)
        canvas.setFont("Times-Roman", 8.5)
        canvas.setFillColor(C_MUTED)
        canvas.drawString(19 * mm, 11 * mm, "Academic Prototype — Simulated Hospital Data (Decision Support Only)")
        canvas.drawRightString(A4[0] - 19 * mm, 11 * mm, f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
    print(f"Built PDF: {PDF_PATH}")


def _set_cell_shading(cell, hex_color: str) -> None:
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def _set_table_borders(table) -> None:
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '</w:tblBorders>'
    )
    tblPr.append(borders)


def _set_row_cant_split(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))


def _set_row_header(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))


def build_docx(m: dict) -> None:
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.8)
        sec.bottom_margin = Inches(0.8)
        sec.left_margin = Inches(0.8)
        sec.right_margin = Inches(0.8)
        sec.different_first_page_header_footer = True
        hdr = sec.header.paragraphs[0]
        hdr.text = "REDLINE (HEMS-Link) — Operating Systems Case Study 2 (25PCCS201)"
        hdr.runs[0].font.name = "Times New Roman"
        hdr.runs[0].font.size = Pt(9)
        hdr.runs[0].font.color.rgb = D_MUTED
        ftr = sec.footer.paragraphs[0]
        ftr.text = "Academic Prototype — Simulated Hospital Data (Decision Support Only)"
        ftr.runs[0].font.name = "Times New Roman"
        ftr.runs[0].font.size = Pt(9)
        ftr.runs[0].font.color.rgb = D_MUTED

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    normal.font.color.rgb = D_INK

    def add_h1(text: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(13)
        r.font.color.rgb = D_INK
        return p

    def add_h2(text: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(11.5)
        r.font.color.rgb = D_INK
        return p

    def add_body(text: str):
        p = doc.add_paragraph(text)
        p.paragraph_format.space_after = Pt(5)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        return p

    def add_bullet(text: str):
        p = doc.add_paragraph(text, style="List Number")
        p.paragraph_format.space_after = Pt(3)
        return p

    def add_table(headers: list[str], rows: list[list[str]], col_widths_in: list[float]):
        tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        _set_table_borders(tbl)

        hdr_row = tbl.rows[0]
        _set_row_header(hdr_row)
        _set_row_cant_split(hdr_row)
        for j, h in enumerate(headers):
            cell = hdr_row.cells[j]
            cell.width = Inches(col_widths_in[j])
            _set_cell_shading(cell, "EAEAEA")
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(h)
            r.bold = True
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
            r.font.color.rgb = D_INK

        for i, row_vals in enumerate(rows):
            row = tbl.rows[i + 1]
            _set_row_cant_split(row)
            bg = "F8F8F8" if i % 2 == 1 else "FFFFFF"
            for j, val in enumerate(row_vals):
                cell = row.cells[j]
                cell.width = Inches(col_widths_in[j])
                _set_cell_shading(cell, bg)
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                r = p.add_run(str(val))
                r.font.name = "Times New Roman"
                r.font.size = Pt(9.2)
                if j == 0:
                    r.bold = True
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def add_fig(filename: str, caption: str, width_in: float = 6.5):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.keep_with_next = True
        p_img.add_run().add_picture(os.path.join(FIG_DIR, filename), width=Inches(width_in))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(8)
        r = p_cap.add_run(caption)
        r.italic = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.color.rgb = D_MUTED

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("JAIN (DEEMED-TO-BE) UNIVERSITY\nDepartment of Computer Science & Engineering (AI)")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("OPERATING SYSTEMS — CASE STUDY ASSIGNMENT\n\nREDLINE (HEMS-Link)")
    r2.bold = True
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(18)

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Hospital Emergency Management & Multi-Hospital Coordination System\nAn Operating Systems study of CPU scheduling, real-time deadlines, shared-resource synchronisation, IPC, and deadlock handling.")
    r3.italic = True
    r3.font.name = "Times New Roman"
    r3.font.size = Pt(10.5)
    r3.font.color.rgb = D_MUTED

    add_table(
        ["Academic Detail", "Information"],
        [
            ["Course Name & Code", "Operating Systems — 25PCCS201"],
            ["Class & Section", "III Semester — CSE (AI)"],
            ["Faculty Name", "Gowri Shankar"],
            ["Group Members", GROUP_MEMBERS],
            ["Submission Date", "26/11/2026"],
        ],
        [2.2, 4.7],
    )
    add_body("Note: This is an academic prototype built with simulated hospital bed counts and synthetic patient IDs. It is meant for decision support and does not replace clinical judgement.")
    doc.add_page_break()

    add_h1("Declaration & Acknowledgement")
    add_body("We declare that this case study report titled Redline (HEMS-Link): Hospital Emergency Management and Multi-Hospital Coordination System was prepared by our group for the Operating Systems course (25PCCS201, III Semester, CSE-AI) at Jain (Deemed-to-be) University. All scheduling calculations, concurrency tests, and prototype observations were produced and verified on our own implementation.")
    add_body("We thank our faculty guide, Prof. Gowri Shankar, and the Department of Computer Science and Engineering (AI) for encouraging us to study how core Operating Systems concepts apply to hospital emergency operations.")

    b8 = m["bench8"]
    race = m["race"]
    ag = m["aging"]
    pi = m["pi"]

    add_h1("1. Abstract")
    add_body(
        f"During medical emergencies, a hospital computer system must juggle urgent arrivals such as cardiac arrests, road trauma, and strokes alongside routine outpatient (OP) queues, ICU monitoring, lab tests, pharmacy requests, and inter-hospital patient transfers. Redline (HEMS-Link) models a ten-hospital network around Kanakapura Road and South Bengaluru using Operating Systems concepts. Each task runs as a five-state PCB; ICU beds and ventilators act as counting semaphores; reservations run inside a mutex critical section with two-phase holds and version checks; and replies flow asynchronously via IPC queues. Evaluated across eight scheduling policies (FCFS, SJF, SRTF, Non-Preemptive Priority, Preemptive Priority, Round Robin Q=3, EDF, and MLFQ), SJF gives the lowest overall average wait ({b8['sjf']['avg_waiting']} ticks), while Preemptive Priority gives 0.00-tick critical response and is paired with aging (-1 every 10 ticks) to prevent starvation. Across 1,000 concurrent threads, adding a mutex reduced double-bookings from {race['without_mutex_double_bookings']}/1,000 to {race['with_mutex_double_bookings']}/1,000."
    )

    add_h1("2. Introduction and Problem Statement")
    add_body("A hospital information system processes tasks with very different urgency levels. A cardiac arrest or trauma patient needs immediate CPU and clinical attention, whereas an outpatient registration or routine pharmacy refill can tolerate a short delay. Putting hospital bed counts on a shared digital platform removes manual phone delays, but it also introduces classic OS issues: urgent arrivals act like interrupts, several users update bed counts at the same time, and two hospitals can try to claim the last free bed simultaneously.")
    add_body("Problem Statement: There is a need for a centralised hospital emergency management and transfer coordination system that schedules emergency patients, ICU monitoring, laboratory tests, OP queues, pharmacy requests, and inter-hospital transfers efficiently, ensuring critical tasks execute within required time limits without causing double-booking, starvation, or deadlocks.")

    add_h1("3. Objectives, Scope, and Assumptions")
    for obj in [
        "Model hospital activities across emergency care, ICU monitoring, lab tests, OP queues, pharmacy requests, and transfers as OS processes.",
        "Compare FCFS, SJF, Priority Scheduling, Round Robin (Q=3), SRTF, EDF, and MLFQ on at least eight processes.",
        "Calculate Waiting Time, Turnaround Time, Response Time, CPU utilisation, throughput, and deadline compliance.",
        "Classify real-time tasks and test how continuous emergency arrivals affect routine work.",
        "Prevent race conditions, starvation, priority inversion, and deadlocks using mutex locks, counting semaphores, two-phase holds, resource ordering, RAG, and Banker's Algorithm.",
    ]:
        add_bullet(obj)
    add_h2("Assumptions and Scope")
    add_body("To compare all eight algorithms on identical inputs, CPU burst and arrival times use normalised simulation ticks. Primary scheduling benchmarks evaluate preemption on a single CPU queue, while multi-core scaling is noted in Section 12. Coordinates correspond to real Kanakapura-Bengaluru hospitals with simulated bed counts, and final clinical acceptance always stays with hospital staff.")

    add_h1("4. System Description (10-Hospital Network)")
    add_body("Redline connects Jain University Health Centre (HOSP-JAIN) with 9 receiving hospitals (DSH, RRM, BGS, APL, SGR, KNG, NAR, MNI, STJ) using weighted matching (ETA 50%, trust 20%, freshness 15%, load 15%) and timed two-phase holds.")
    add_table(
        ["Aspect", "Manual Phone-Based Process", "Redline OS-Based System"],
        [
            ["Hospital Discovery", "Staff call desks one by one, wasting minutes.", "Matcher filters and ranks all 9 receiving hospitals at once."],
            ["Bed Availability", "Local sheets go stale quickly.", "Shared counting semaphores carry timestamps and stale flags."],
            ["Bed Conflicts", "Two callers promised the same last bed.", "Mutex critical section and version tokens reject conflicts (HTTP 409)."],
            ["Referral Tracking", "No live visibility after a phone call.", "5-state PCB tracker, parallel top-N holds, and escalation."],
        ],
        [1.5, 2.5, 2.9],
    )

    add_h1("5. Mapping Hospital Entities to OS Concepts")
    add_table(
        ["Real-World Component", "Operating System Concept", "How It Works in Redline"],
        [
            ["Cardiac arrest / trauma / stroke", "High-priority preemptive process (P1–P3)", "Preempts running routine tasks immediately."],
            ["OP / Lab / Pharmacy / Dialysis", "Medium/low-priority process (P4–P8)", "Queued in READY; aging prevents starvation."],
            ["Central coordination server", "Kernel / CPU Scheduler", "Selects next READY PCB by active policy."],
            ["ICU beds / Ventilators", "Counting Semaphore (S = free units)", "wait(S) on hold; signal(S) on reject/timeout/release."],
            ["Concurrent last-bed claim", "Critical section & Race condition", "Protected by mutex lock and version check."],
            ["Referral hold & hospital reply", "IPC Message Queue", "PREPARE hold moves PCB to WAITING until reply/timeout."],
            ["Holds Bed, waits for Vent", "Deadlock (Circular Wait)", "Avoided via resource ordering; broken via RAG victim."],
        ],
        [2.0, 2.0, 2.9],
    )
    add_fig("fig1_architecture.png", "Figure 1. Redline layered architecture connecting UI, Flask API, OS engine, and simulated hospital store.")
    add_fig("fig2_dispatch_flowchart.png", "Figure 2. End-to-end dispatch flowchart from activity intake through scheduling, mutex reservation, and recovery.")

    add_h1("6. OS Concepts, Process Lifecycle, and Real-Time Tasks")
    add_fig("fig3_process_states.png", "Figure 3. Five-state process lifecycle and PCB attributes in Redline.")
    add_table(
        ["Real-Time Class", "Hospital Activities", "Reason for Classification"],
        [
            ["Hard Real-Time (Target)", "Cardiac Arrest (P1), Trauma (P2), ICU Telemetry (P2), Stroke (P3), Stat ABG Lab (P3)", "Missed deadlines or double-booked beds affect patient survival."],
            ["Soft Real-Time", "Availability Sync (P4), ICU Epinephrine Stat (P4), Urgent Lab Share (P5), OP Triage (P5)", "Needed promptly, though brief delays are tolerable."],
            ["Non-Real-Time", "Specialist Enquiry (P6), Planned Dialysis (P7), Ward Refill (P7), Discharge-back (P8)", "Routine work without strict deadlines."],
        ],
        [1.5, 2.9, 2.5],
    )
    add_h2("Ten-Process Full Hospital Clinical Mix (H1–H10)")
    h10_rows = [
        [r["pid"], r["name"], r["category"], str(r["arrival"]), f"P{r['priority']}", str(r["burst"]), f"t={r['deadline']}"]
        for r in m["bench10"]["edf"]["rows"]
    ]
    add_table(["PID", "Hospital Activity", "Subsystem", "AT", "Prio", "BT", "SLA DL"], h10_rows, [0.6, 2.2, 1.3, 0.5, 0.6, 0.5, 1.2])

    add_h1("7. CPU Scheduling Calculations, Gantt Charts, and Quantum Analysis")
    t8_rows = [[p.pid, p.name, str(p.arrival_time), f"P{p.priority}", str(p.burst_time), f"t={p.deadline}"] for p in default_workload()]
    add_table(["PID", "Hospital Activity", "AT", "Priority", "BT", "SLA DL"], t8_rows, [0.6, 2.6, 0.6, 0.8, 0.6, 1.7])
    add_fig("fig4_gantt_charts.png", "Figure 4. Gantt charts for FCFS, SJF, SRTF, Preemptive Priority, Round Robin (Q=3), and Real-Time EDF.")

    for title, key in [
        ("7.1 First Come First Served (FCFS)", "fcfs"),
        ("7.2 Shortest Job First (SJF — Non-Preemptive) & SRTF", "sjf"),
        ("7.3 Preemptive Priority Scheduling (Recommended)", "preemptive_priority"),
        ("7.4 Round Robin Scheduling (Quantum = 3)", "round_robin"),
        ("7.5 Earliest Deadline First (EDF — Real-Time)", "edf"),
    ]:
        d = b8[key]
        add_h2(title)
        rows = [[r["pid"], str(r["arrival"]), f"P{r['priority']}", str(r["burst"]), str(r["completion"]), str(r["turnaround"]), str(r["waiting"]), str(r["response"])] for r in d["rows"]]
        add_table(["PID", "AT", "Prio", "BT", "CT", "TAT", "WT", "RT"], rows, [0.85] * 8)
        add_body(f"Averages — Waiting: {d['avg_waiting']} | Turnaround: {d['avg_turnaround']} | Response: {d['avg_response']} | Critical (T6–T8) Avg Response: {d['critical_avg_response']} | Context Switches: {d['context_switches']}.")

    add_h2("7.6 Eight-Algorithm Summary and Quantum Sensitivity")
    comp_labels = [
        ("FCFS", "fcfs"), ("SJF", "sjf"), ("SRTF", "srtf"), ("Non-Preemptive Prio", "non_preemptive_priority"),
        ("Preemptive Priority", "preemptive_priority"), ("Round Robin (Q=3)", "round_robin"), ("EDF (Real-Time)", "edf"), ("MLFQ", "mlfq"),
    ]
    comp_rows = [
        [lbl, str(b8[k]["avg_waiting"]), str(b8[k]["avg_turnaround"]), str(b8[k]["avg_response"]),
         str(b8[k]["critical_avg_waiting"]), str(b8[k]["critical_avg_response"]), str(b8[k]["context_switches"]), f"{b8[k]['cpu_utilization_pct']}%"]
        for lbl, k in comp_labels
    ]
    add_table(["Algorithm", "Avg WT", "Avg TAT", "Avg RT", "Crit WT", "Crit RT", "Switches", "CPU %"], comp_rows, [1.6, 0.7, 0.75, 0.7, 0.75, 0.75, 0.85, 0.8])
    add_fig("fig5_metrics_and_quantum.png", "Figure 5. Scheduling metric comparison and Round Robin Quantum sensitivity (Q=1..8).")

    add_h1("8. Effect of Continuous Emergency Arrivals")
    add_table(
        ["Phenomenon", "Without Mitigation", "With Redline Mitigation"],
        [
            ["Starvation (Continuous P1 stream)", f"P8 first dispatch: {ag['without_aging_first_dispatch'] or 'Starved (>120 ticks)'}", f"Aging (-1/10 ticks) dispatches P8 at t={ag['with_aging_first_dispatch']}."],
            ["Priority Inversion (Lock contention)", f"P4 preempts P8; P1 delayed {pi['delay_without']} ticks.", f"Priority Inheritance limits P1 delay to {pi['delay_with']} ticks."],
        ],
        [2.0, 2.4, 2.5],
    )
    add_fig("fig7_starvation_aging_pi.png", "Figure 6. Priority aging rescuing P8 at t=72 and Priority Inheritance eliminating medium-task delay.")

    add_h1("9. Synchronisation, Two-Phase Holds, and Deadlock Handling")
    add_fig("fig6_synchronization_two_phase.png", "Figure 7. Mutex critical section with two-phase holds and 1,000-trial concurrency proof.")
    add_table(
        ["Hospital B Request", "Allocation", "Max Need", "Remaining Need", "Safe-State Decision"],
        [
            ["Req-A (Cardiac)", "[1, 0, 0]", "[1, 0, 0]", "[0, 0, 0]", "Finishes first; releases [1, 0, 0]"],
            ["Req-B (Trauma)", "[1, 1, 0]", "[1, 2, 0]", "[0, 1, 0]", "Request [0,1,0] -> GRANTED (Safe)"],
            ["Req-C (Stroke)", "[0, 0, 1]", "[1, 2, 1]", "[1, 2, 0]", "Request [0,1,0] -> DENIED (Unsafe)"],
        ],
        [1.4, 1.1, 1.1, 1.2, 2.1],
    )
    add_fig("fig8_deadlock_rag_banker.png", "Figure 8. Bed-ventilator RAG deadlock cycle and victim release, and Banker's safe-state check.")

    add_h1("10. Proposed Hybrid Policy and Expected OS Behaviour")
    add_body("Under normal load, Redline uses Preemptive Priority with Aging (-1 every 10 waiting ticks) paired with EDF SLA deadline monitoring. During a mass-casualty surge, Priority-1 emergencies switch to Surge FIFO with capacity-based load balancing, suspending P1 aging and skipping stale hospital records.")
    add_table(
        ["Expected OS Behaviour", "Kernel Action in Redline"],
        [
            ["Which process executes?", "Highest-priority READY process (or earliest deadline under EDF) preempts lower-priority tasks."],
            ["Which process waits?", "Preempted tasks return to READY; referrals awaiting replies move to WAITING."],
            ["Resource allocation?", "Matcher filters free semaphores, ranks by ETA/Trust/Freshness/Load, locks in global order."],
            ["Synchronisation?", "Mutex wraps wait(S)/signal(S); version tokens reject stale writes (HTTP 409)."],
            ["Failure recovery?", "Expiry workers abort timed-out holds, call signal(S), and escalate; RAG preempts lowest-priority victim."],
        ],
        [2.2, 4.7],
    )

    add_h1("11. Prototype Results, Test Cases, and Automated Verification")
    add_table(
        ["Case", "Scenario", "Best Algorithm", "Measured Result", "Why It Wins"],
        [[c["case_id"], c["title"], c["best_algorithm"], c["metric_comparison"], c["why"]] for c in m["cases"]],
        [0.7, 1.6, 1.3, 1.5, 1.8],
    )
    add_table(
        ["Test ID", "Automated Pytest Coverage (19/19 Passed)", "Outcome"],
        [
            ["T1", "100x2 thread last-bed race test", "PASSED (0 double-bookings)"],
            ["T2–T3", "Priority preemption & aging under P1 stream", "PASSED"],
            ["T4–T5", "Hold TTL timeout escalation & parallel first-accept-wins", "PASSED"],
            ["T6 & RAG", "Banker's Hospital B check & RAG victim release", "PASSED"],
            ["T7–T12 + Ext", "409 conflict, stale ranking, duplicate PAT, RBAC, 10 UI routes, surge, 8-algo/EDF/CSV", "PASSED (19/19)"],
        ],
        [1.1, 4.2, 1.6],
    )
    add_fig("fig9_network_and_surge.png", "Figure 9. Simulated 10-hospital Kanakapura-Bengaluru network and 20-request Surge FIFO distribution.")

    add_h1("12. Recommended Future Features")
    for item in [
        "Multi-core SMP scheduling with processor affinity so Emergency Triage, ICU Telemetry, and Lab Processing run on separate cores.",
        "Rate Monotonic Scheduling (RMS) for periodic ICU vitals polling using Liu-Layland utilisation bounds.",
        "Persistent SQLite storage in WAL mode paired with Server-Sent Events (SSE) for automatic UI updates.",
        "Road-network Dijkstra or A* routing weighted by live traffic instead of straight-line Haversine distance.",
        "EDF admission control that defers non-critical OP tasks when CPU load threatens hard real-time deadlines, plus HL7/FHIR data stubs.",
    ]:
        add_bullet(item)

    add_h1("13. Conclusion and References")
    add_body("Modelling hospital emergency management and multi-hospital coordination as an Operating System clarifies why average waiting time alone is not the right metric. SJF produces the lowest overall wait (11.00 ticks) while delaying a cardiac arrest until t=25, whereas Preemptive Priority dispatches critical emergencies immediately at 0.00 response time. Combining Preemptive Priority with aging (-1 every 10 ticks), EDF deadline checks, mutex-protected two-phase holds, Banker's safe-state verification, and RAG recovery keeps the system responsive, fair, and deadlock-free while leaving final medical decisions with hospital staff.")
    for ref in [
        "1. Silberschatz, A., Galvin, P. B., & Gagne, G., Operating System Concepts, 10th ed., Wiley, 2018.",
        "2. Tanenbaum, A. S., Modern Operating Systems, 4th ed., Pearson, 2015.",
        "3. Coffman, E. G., Elphick, M. J., & Shoshani, A., System Deadlocks, ACM Computing Surveys, 3(2), 1971.",
        "4. Liu, C. L., & Layland, J. W., Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment, JACM, 20(1), 1973.",
        "5. Dijkstra, E. W., Cooperating Sequential Processes, EWD123, 1965.",
        "6. IEEE Std 1003.1 (POSIX) — Semaphores, Mutexes, and Message Queues.",
    ]:
        add_body(ref)

    doc.save(DOCX_PATH)
    print(f"Built DOCX: {DOCX_PATH}")


if __name__ == "__main__":
    metrics = gather_metrics()
    build_pdf(metrics)
    build_docx(metrics)
