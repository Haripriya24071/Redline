"""Build clean academic PDF and DOCX reports for Redline (HEMS-Link) Case Study 2."""

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

# Subtle neutral grey academic palette
C_INK = colors.HexColor("#111827")
C_SUBINK = colors.HexColor("#374151")
C_TEXT = colors.HexColor("#1F2937")
C_MUTED = colors.HexColor("#4B5563")
C_TBL_HDR = colors.HexColor("#E5E7EB")
C_TBL_HDR_LINE = colors.HexColor("#9CA3AF")
C_ZEBRA = colors.HexColor("#F9FAFB")
C_BORDER = colors.HexColor("#D1D5DB")
C_CALLOUT_BG = colors.HexColor("#F3F4F6")
C_CALLOUT_BAR = colors.HexColor("#6B7280")

D_INK = RGBColor(0x11, 0x18, 0x27)
D_SUBINK = RGBColor(0x37, 0x41, 0x51)
D_TEXT = RGBColor(0x1F, 0x29, 0x37)
D_MUTED = RGBColor(0x4B, 0x55, 0x63)

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


# ---------------------------------------------------------------------------
# PDF Builder (ReportLab)
# ---------------------------------------------------------------------------
def build_pdf(m: dict) -> None:
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=A4,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Redline (HEMS-Link) — Operating Systems Case Study 2 Report",
        author="Group 25BTRCA — Jain University",
    )
    avail_w = A4[0] - 34 * mm

    base = getSampleStyleSheet()
    s_uni = ParagraphStyle("Uni", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=14, leading=18, alignment=TA_CENTER, textColor=C_INK)
    s_dept = ParagraphStyle("Dept", parent=base["Normal"], fontName="Helvetica", fontSize=11, leading=15, alignment=TA_CENTER, textColor=C_SUBINK)
    s_tag = ParagraphStyle("Tag", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=14, alignment=TA_CENTER, textColor=C_MUTED)
    s_title = ParagraphStyle("TitleMain", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=19.5, leading=24, alignment=TA_CENTER, textColor=C_INK)
    s_subtitle = ParagraphStyle("SubTitle", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=12.5, leading=17, alignment=TA_CENTER, textColor=C_SUBINK)
    s_sub = ParagraphStyle("SubMain", parent=base["Normal"], fontName="Helvetica", fontSize=10.2, leading=14.5, alignment=TA_CENTER, textColor=C_MUTED)

    s_h1 = ParagraphStyle("H1", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=12.8, leading=16.5, textColor=C_INK, spaceBefore=12, spaceAfter=5, keepWithNext=True)
    s_h2 = ParagraphStyle("H2", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10.6, leading=14, textColor=C_SUBINK, spaceBefore=9, spaceAfter=4, keepWithNext=True)
    s_body = ParagraphStyle("Body", parent=base["Normal"], fontName="Helvetica", fontSize=9.6, leading=14, alignment=TA_JUSTIFY, textColor=C_TEXT, spaceAfter=5)
    s_bullet = ParagraphStyle("Bullet", parent=s_body, leftIndent=14, firstLineIndent=-8, spaceAfter=3.5)
    s_cap = ParagraphStyle("Cap", parent=base["Normal"], fontName="Helvetica-Oblique", fontSize=8.5, leading=11.5, alignment=TA_CENTER, textColor=C_MUTED, spaceBefore=3, spaceAfter=8)
    s_tbl_hdr = ParagraphStyle("TblHdr", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.4, leading=10.5, textColor=C_INK)
    s_tbl_cell = ParagraphStyle("TblCell", parent=base["Normal"], fontName="Helvetica", fontSize=8.2, leading=10.8, textColor=C_TEXT)
    s_tbl_bold = ParagraphStyle("TblBold", parent=s_tbl_cell, fontName="Helvetica-Bold")

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
            ("LINEBELOW", (0, 0), (-1, 0), 1.0, C_TBL_HDR_LINE),
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

    def callout(title: str, body: str) -> Table:
        content = Paragraph(f"<b>{title}:</b> {body}", s_body)
        t = Table([[content]], colWidths=[avail_w])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_CALLOUT_BG),
            ("LINEBEFORE", (0, 0), (0, -1), 2.5, C_CALLOUT_BAR),
            ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        return t

    def add_figure(filename: str, caption: str, max_h_in: float = 3.6) -> KeepTogether:
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
    story.append(Spacer(1, 10))
    story.append(Paragraph("JAIN (DEEMED-TO-BE) UNIVERSITY", s_uni))
    story.append(Paragraph("Department of Computer Science &amp; Engineering (AI)", s_dept))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.2, color=C_SUBINK, spaceBefore=2, spaceAfter=14))
    story.append(Paragraph("OPERATING SYSTEMS — CASE STUDY 2 REPORT", s_tag))
    story.append(Spacer(1, 10))
    story.append(Paragraph("REDLINE (HEMS-Link)", s_title))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Hospital Emergency Management &amp; Multi-Hospital Coordination System", s_subtitle))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<i>An Operating Systems analysis of CPU scheduling, real-time deadlines, shared-resource synchronisation, inter-process communication, and deadlock handling</i>",
        s_sub,
    ))
    story.append(Spacer(1, 18))
    story.append(make_table(
        ["Academic Detail", "Information"],
        [
            ["Course Name & Code", "Operating Systems — 25PCCS201"],
            ["Class & Section", "III Semester — CSE (AI)"],
            ["Faculty Name", "Gowri Shankar"],
            ["Group Members", GROUP_MEMBERS],
            ["Submission Date", "26/11/2026"],
            ["System Scope", "Academic Prototype | Simulated Hospital Data | Decision Support Only"],
        ],
        [avail_w * 0.32, avail_w * 0.68],
    ))
    story.append(Spacer(1, 16))
    story.append(callout(
        "Simulation Notice",
        "All hospital bed counts, patient reference IDs, and ambulance ETAs in this report are simulated for coursework evaluation. The system is intended for decision support and does not replace clinical judgement.",
    ))
    story.append(PageBreak())

    # --- PAGE 2: DECLARATION, ACKNOWLEDGEMENT, TOC ---
    story.append(Paragraph("DECLARATION", s_h1))
    story.append(Paragraph(
        "We declare that this case study report titled <b>Redline (HEMS-Link): Hospital Emergency Management &amp; Multi-Hospital Coordination System</b> was prepared by our group for the Operating Systems course (25PCCS201, III Semester, CSE-AI) at Jain (Deemed-to-be) University. All scheduling tables, concurrency trials, real-time deadline checks, and prototype tests were produced and verified on our implementation.",
        s_body,
    ))
    story.append(Paragraph("ACKNOWLEDGEMENT", s_h1))
    story.append(Paragraph(
        "We thank our course faculty, Prof. <b>Gowri Shankar</b>, and the Department of Computer Science &amp; Engineering (AI) for guiding us in applying Operating Systems concepts—process management, CPU scheduling, synchronisation, IPC, and deadlock handling—to a practical hospital coordination problem.",
        s_body,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("TABLE OF CONTENTS", s_h1))
    toc_rows = [
        ["1", "Abstract", "3"],
        ["2", "Introduction & Problem Statement", "3"],
        ["3", "Objectives, Scope & Assumptions", "3–4"],
        ["4", "System Description (10-Hospital Kanakapura–Bengaluru Network)", "4"],
        ["5", "Real-World to OS Mapping, Architecture & Dispatch Flowchart", "5–6"],
        ["6", "OS Concepts, 5-State Lifecycle & Real-Time Classification", "7"],
        ["7", "CPU Scheduling Analysis, Calculations, Gantt Charts & Quantum Sweep", "8–11"],
        ["8", "Impact of Continuous Emergencies: Starvation, Aging & Priority Inheritance", "12"],
        ["9", "Synchronisation, Two-Phase Holds & Deadlock Handling (RAG & Banker's)", "12–13"],
        ["10", "Proposed Hybrid Policy & Expected OS Behaviour", "13"],
        ["11", "Prototype Evidence, 5 Test Cases & Pytest Verification (19/19)", "14"],
        ["12–14", "Recommended Additional Features, Conclusion & References", "15"],
    ]
    story.append(make_table(["Section", "Title", "Page"], toc_rows, [avail_w * 0.14, avail_w * 0.72, avail_w * 0.14]))
    story.append(PageBreak())

    # --- SECTION 1 & 2 ---
    race = m["race"]
    b8 = m["bench8"]
    story.append(Paragraph("1. ABSTRACT", s_h1))
    story.append(Paragraph(
        f"A hospital computer system has to handle urgent emergency admissions (cardiac arrest, road trauma, stroke) alongside ongoing ICU telemetry, stat lab panels, outpatient (OP) queues, pharmacy requests, and inter-hospital patient transfers. When a hospital runs out of ICU beds or specialist units, calling nearby hospitals by phone wastes time, relies on outdated counts, and can easily result in two callers claiming the same last bed. <b>Redline (HEMS-Link)</b> models a ten-hospital network centred on Jain University Health Centre (Kanakapura Road, South Bengaluru) using Operating Systems primitives.",
        s_body,
    ))
    story.append(Paragraph(
        f"Each hospital task runs as a five-state Process Control Block (PCB). ICU beds and ventilators are tracked as counting semaphores, bed reservations execute inside a mutex critical section with two-phase holds and version checks, and hospital replies arrive asynchronously through IPC queues. We evaluate eight scheduling algorithms—FCFS, SJF, SRTF, Non-Preemptive Priority, Preemptive Priority, Round Robin (Q=3), EDF, and MLFQ—on the eight-process baseline (T1–T8) and a ten-process clinical mix (H1–H10). Although SJF gives the lowest overall average wait ({b8['sjf']['avg_waiting']} ticks), Preemptive Priority reaches <b>0.00-tick response time for critical emergencies</b> and is paired with aging (-1 every 10 ticks) so routine tasks do not starve. Across 1,000 concurrent threads, adding a mutex drops double-bookings from <b>{race['without_mutex_double_bookings']}/1,000</b> to <b>{race['with_mutex_double_bookings']}/1,000</b>.",
        s_body,
    ))

    story.append(Paragraph("2. INTRODUCTION & PROBLEM STATEMENT", s_h1))
    story.append(Paragraph(
        "Hospital software systems handle mixed workloads that do not share the same urgency. A cardiac arrest or trauma arrival cannot sit behind an outpatient registration or a routine pharmacy refill. At the same time, routine tasks cannot be ignored forever. Moving hospital availability onto a shared platform solves manual phone delays, yet it also exposes classic Operating Systems problems: emergency requests arrive unpredictably like interrupts, multiple coordinators update bed counts at the same time, and two hospitals can request the final free bed simultaneously.",
        s_body,
    ))
    story.append(callout(
        "Problem Statement",
        "Build and analyse a hospital emergency management and coordination system using OS principles so that emergency patients, ICU monitoring, lab tests, OP queues, pharmacy requests, and inter-hospital transfers are scheduled efficiently, giving critical cases immediate CPU attention while preventing starvation, race conditions, stale-data dispatch, and multi-resource deadlocks.",
    ))

    # --- SECTION 3 & 4 ---
    story.append(Paragraph("3. OBJECTIVES, SCOPE & ASSUMPTIONS", s_h1))
    story.append(Paragraph("3.1 Case Study Objectives", s_h2))
    for item in [
        "Model hospital activities (Emergency, ICU Monitoring, Lab, OP, Pharmacy, Transfers) as OS processes with arrival times, priorities, burst times, and SLA deadlines.",
        "Apply and compare FCFS, SJF, Preemptive Priority, and Round Robin (Q=3), along with SRTF, Non-Preemptive Priority, Real-Time EDF, and MLFQ.",
        "Calculate Completion Time (CT), Turnaround Time (TAT), Waiting Time (WT), Response Time (RT), CPU Utilisation, Throughput, and SLA Compliance.",
        "Classify activities into Hard Real-Time, Soft Real-Time, and Non-Real-Time groups and study how continuous emergency arrivals affect lower-priority work.",
        "Prevent race conditions, starvation, priority inversion, and deadlocks via Mutex locks, Counting Semaphores, Two-Phase Holds, Aging, Resource Ordering, RAG detection, and Banker's Algorithm.",
    ]:
        story.append(Paragraph(f"• {item}", s_bullet))

    story.append(Paragraph("3.2 Engineering Assumptions & Scope", s_h2))
    for item in [
        "<b>Normalised Time Units:</b> Burst times and arrivals are measured in discrete simulation ticks so all eight algorithms can be compared on identical inputs.",
        "<b>Single-Core Benchmark Model:</b> The scheduling comparison evaluates preemption and context switching on one CPU queue; multi-core SMP scaling is noted in Section 12.",
        "<b>Simulated Data:</b> Coordinates correspond to real Kanakapura and South Bengaluru hospitals, while bed capacities and patient records are synthetic.",
        "<b>Human Confirmation Boundary:</b> Automated matching and two-phase holds only reserve a bed tentatively; actual admission requires receiving hospital staff to accept.",
    ]:
        story.append(Paragraph(f"• {item}", s_bullet))

    story.append(Paragraph("4. SYSTEM DESCRIPTION (10-HOSPITAL NETWORK)", s_h1))
    story.append(Paragraph(
        "Redline links <b>Jain University Health Centre (Kanakapura Rd)</b> with <b>nine receiving hospitals</b> across South Bengaluru and Kanakapura. When staff log an activity or transfer request on the dispatch screen, the system creates a PCB, filters hospitals with free units, scores them using Haversine ETA (50%), trust score (20%), data freshness (15%), and incoming load (15%), and places a timed hold.",
        s_body,
    ))
    story.append(make_table(
        ["Aspect", "Traditional Manual Phone Process", "Redline OS-Based Coordination"],
        [
            ["Hospital Discovery", "Staff call receiving desks one by one, losing time.", "Matcher filters and ranks all 9 receiving hospitals together."],
            ["Bed Availability", "Paper notes or local sheets go stale quickly.", "Shared counting semaphores carry ISO-8601 timestamps and stale flags."],
            ["Double-Booking Risk", "Two callers can be promised the same last ICU bed.", "Mutex critical section and version tokens reject conflicts (HTTP 409)."],
            ["Task Prioritisation", "Ad-hoc handling delays urgent cases behind routine queues.", "Preemptive Priority with Aging and EDF deadline tracking."],
            ["Referral Visibility", "No live status tracking after a phone call.", "5-state PCB tracker, parallel top-N holds (first-accept-wins) and escalation."],
        ],
        [avail_w * 0.22, avail_w * 0.36, avail_w * 0.42],
    ))
    story.append(PageBreak())

    # --- SECTION 5: MAPPING, ARCHITECTURE & FLOWCHART ---
    story.append(Paragraph("5. REAL-WORLD TO OS MAPPING & SYSTEM DIAGRAMS", s_h1))
    story.append(make_table(
        ["Real-World Hospital Entity / Event", "Operating System Concept", "Role & Justification in Redline"],
        [
            ["Cardiac arrest / trauma / stroke", "High-priority preemptive process (P1–P3)", "Preempts running routine work immediately for 0-tick response."],
            ["ICU telemetry & Stat ABG lab", "Urgent / periodic real-time process (P2–P3)", "Tracked against strict SLA deadlines under EDF and Priority scheduling."],
            ["OP walk-in, pharmacy refill, dialysis", "Medium/low-priority process (P4–P8)", "Queued in READY; protected from starvation by aging (-1 / 10 ticks)."],
            ["Emergency arrival during routine work", "Hardware interrupt / Preemption", "Triggers a context switch and returns the interrupted PCB to READY."],
            ["Central coordination server", "Kernel / CPU Scheduler", "Selects the next READY PCB using the active scheduling policy."],
            ["Hospital matching engine", "Resource allocator", "Checks feasibility and ranks eligible hospitals by score."],
            ["ICU beds, Ventilators, Specialists", "Counting Semaphores (S = free units)", "wait(S) decrements on PREPARE hold; signal(S) restores on reject/expiry."],
            ["Simultaneous last-bed claims", "Critical section & Race condition", "Serialized using threading.Lock mutex and version comparison."],
            ["Referral hold & hospital reply", "Asynchronous IPC Message Queue", "PREPARE holds move the PCB to WAITING until reply or TTL expiry."],
            ["Holding ICU bed while waiting for Vent", "Deadlock (Circular Wait)", "Avoided via global resource ordering; broken by RAG victim release."],
        ],
        [avail_w * 0.30, avail_w * 0.28, avail_w * 0.42],
    ))
    story.append(add_figure("fig1_architecture.png", "Figure 1. Redline layered architecture connecting the web UI, Flask API, 8-policy OS kernel, and 10-hospital data store.", max_h_in=3.05))
    story.append(add_figure("fig2_dispatch_flowchart.png", "Figure 2. End-to-end hospital activity dispatch, duplicate check, CPU scheduling, mutex reservation, and recovery flowchart.", max_h_in=3.75))
    story.append(PageBreak())

    # --- SECTION 6: OS CONCEPTS & REAL-TIME CLASSIFICATION ---
    story.append(Paragraph("6. OS CONCEPTS, 5-STATE LIFECYCLE & REAL-TIME CLASSIFICATION", s_h1))
    story.append(Paragraph(
        "Each hospital activity is stored as a <b>Process Control Block (PCB)</b> containing its PID, subsystem category, arrival time, base and effective priority, remaining burst time, SLA deadline, and waiting ticks. Moving a waiting referral out of RUNNING into WAITING keeps the CPU free to serve other requests.",
        s_body,
    ))
    story.append(add_figure("fig3_process_states.png", "Figure 3. Five-state PCB lifecycle showing preemption back to READY and non-blocking WAITING during parallel holds.", max_h_in=1.9))

    story.append(Paragraph("6.1 Real-Time Task Classification Across All Hospital Subsystems", s_h2))
    story.append(make_table(
        ["Real-Time Class", "Hospital Activities Covered", "Priority & SLA Target", "OS Scheduling Justification"],
        [
            ["Hard Real-Time\n(Design Target)", "Cardiac Arrest (P1), Trauma ICU+Vent (P2), ICU Ventilator Telemetry (P2), Stroke Unit (P3), Stat ABG Lab (P3)", "P1–P3; tight slack (+3 to +7 ticks); 0-tick dispatch target", "Missed deadlines or double-booked beds directly affect patient survival, so immediate preemption is required."],
            ["Soft Real-Time", "Hospital Availability Sync (P4), ICU Epinephrine Stat Pharmacy (P4), Urgent Lab/Record Share (P5), OP Triage (P5)", "P4–P5; moderate slack (+12 to +15 ticks)", "Timely completion keeps bed telemetry accurate and pharmacy/triage responsive; small delays are acceptable."],
            ["Non-Real-Time", "Specialist Enquiry (P6), Planned Dialysis Transfer (P7), Pharmacy Ward Refill (P7), Discharge-Back (P8)", "P6–P8; wide slack (+20 to +32 ticks)", "Routine work without strict deadlines; needs aging so emergencies do not block it forever."],
        ],
        [avail_w * 0.18, avail_w * 0.34, avail_w * 0.20, avail_w * 0.28],
    ))

    story.append(Paragraph("6.2 Ten-Process Full Hospital Clinical Mix (H1–H10)", s_h2))
    story.append(Paragraph(
        "Alongside the 8-process baseline (T1–T8) and 8 live seeded requests (REQ-1001–REQ-1008), Redline includes a 10-process clinical mix (H1–H10) covering all five subsystems from the problem statement:",
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
    story.append(Paragraph("7. CPU SCHEDULING ANALYSIS, CALCULATIONS & GANTT CHARTS", s_h1))
    story.append(Paragraph(
        "Every algorithm is tested on the same eight-process workload (T1–T8), where routine activities arrive first (t=0..3) and critical emergencies arrive later (t=4..6). We compute <b>Turnaround Time (TAT) = Completion (CT) − Arrival (AT)</b>, <b>Waiting Time (WT) = TAT − Burst (BT)</b>, and <b>Response Time (RT) = First Dispatch − AT</b>.",
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
    story.append(add_figure("fig4_gantt_charts.png", "Figure 4. Gantt charts across FCFS, SJF, SRTF, Preemptive Priority, Round Robin (Q=3), and Real-Time EDF (0–40 ticks).", max_h_in=3.55))

    def sched_table(title: str, key: str, obs: str):
        d = b8[key]
        rows = [[r["pid"], str(r["arrival"]), f"P{r['priority']}", str(r["burst"]), str(r["completion"]), str(r["turnaround"]), str(r["waiting"]), str(r["response"])] for r in d["rows"]]
        story.append(KeepTogether([
            Paragraph(title, s_h2),
            make_table(["PID", "AT", "Prio", "BT", "CT", "TAT", "WT", "RT"], rows, [avail_w / 8.0] * 8),
            Paragraph(
                f"<b>Averages:</b> Wait = {d['avg_waiting']} | TAT = {d['avg_turnaround']} | Resp = {d['avg_response']} | <b>Critical (T6–T8) Avg Resp = {d['critical_avg_response']}</b> | Switches = {d['context_switches']}. <i>Observation:</i> {obs}",
                s_body,
            ),
        ]))

    sched_table("7.1 First Come First Served (FCFS)", "fcfs", "Non-preemptive FIFO causes a convoy effect: Cardiac Arrest (T8) arrives at t=6 but sits behind routine work until t=33 (RT=27).")
    sched_table("7.2 Shortest Job First (SJF — Non-Preemptive) & SRTF", "sjf", "SJF and SRTF produce the lowest overall average wait (11.00 ticks) on this workload, yet Cardiac Arrest (T8) still waits until t=25 (RT=19) because shorter routine jobs run ahead of it.")
    story.append(PageBreak())
    sched_table("7.3 Preemptive Priority Scheduling (Recommended Core Policy)", "preemptive_priority", "All three critical cases (T6, T7, T8) start the moment they arrive (Critical Avg Response = 0.00). T2 waits 37 ticks without aging, which shows why aging is necessary.")
    sched_table("7.4 Round Robin Scheduling (Time Quantum Q = 3)", "round_robin", "Time-slicing gives early processes quick initial response (9.00 average), but delays Cardiac Arrest (T8) by 18 ticks before its first slice and pushes its completion to t=40.")
    sched_table("7.5 Earliest Deadline First (EDF — Real-Time Dynamic Priority)", "edf", "EDF orders tasks by nearest deadline, keeping Critical Avg Wait low (4.67 ticks) with just 1 context switch.")

    story.append(Paragraph("7.6 Eight-Algorithm Criteria Comparison & Quantum Sensitivity", s_h2))
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
    story.append(add_figure("fig5_metrics_and_quantum.png", "Figure 5. (A) Eight-algorithm metric comparison; (B) Round Robin Quantum sensitivity (Q=1..8) showing wait time vs. context switches.", max_h_in=3.05))
    story.append(PageBreak())

    # --- SECTION 8: IMPACT OF CONTINUOUS EMERGENCIES ---
    story.append(Paragraph("8. IMPACT OF CONTINUOUSLY ARRIVING EMERGENCIES (TASK 7)", s_h1))
    story.append(Paragraph(
        "If Priority-1 emergencies keep arriving back-to-back, plain Preemptive Priority introduces two problems: low-priority tasks such as OP discharges or planned dialysis can <b>starve indefinitely</b>, and a low-priority task holding a shared lock can cause <b>priority inversion</b> for an incoming critical request.",
        s_body,
    ))
    ag = m["aging"]
    pi = m["pi"]
    story.append(make_table(
        ["Phenomenon", "Experimental Setup", "Without Mitigation", "With Redline Mitigation"],
        [
            ["Starvation under Continuous P1 Stream", "P1 arrives every 4 ticks for 120 ticks; P8 arrives at t=1 (BT=2).", f"P8 first dispatch: {ag['without_aging_first_dispatch'] or 'Starved (>120 ticks)'}", f"Aging (-1 every 10 ticks) boosts P8 to P1; dispatched at t={ag['with_aging_first_dispatch']}."],
            ["Priority Inversion on Availability Lock", "P8 holds lock; P1 needs lock at t=2; P4 medium task arrives.", f"P4 preempts P8; P1 waits {pi['delay_without']} ticks (until t=14).", f"Priority Inheritance raises P8 to P1; P1 runs after {pi['delay_with']} ticks (t=4)."],
        ],
        [avail_w * 0.22, avail_w * 0.26, avail_w * 0.25, avail_w * 0.27],
    ))
    story.append(add_figure("fig7_starvation_aging_pi.png", "Figure 6. (A) Priority aging curve rescuing P8 from starvation at t=72; (B) Priority Inheritance preventing medium-task interference.", max_h_in=3.05))

    # --- SECTION 9: SYNCHRONIZATION & DEADLOCK ---
    story.append(Paragraph("9. SYNCHRONISATION, TWO-PHASE HOLDS & DEADLOCK HANDLING", s_h1))
    story.append(Paragraph(
        "Each hospital resource type is represented by a <b>Counting Semaphore (S = free_units)</b>. Checking and updating S takes place inside a <b>Mutex Critical Section</b> alongside an optimistic version number. Instead of holding the CPU idle while waiting for another hospital to answer, Redline places a <b>Two-Phase Hold</b> (PREPARE → COMMITTED / ABORTED / EXPIRED) and supports <b>Top-N Parallel Referral</b> where the first acceptance commits and releases all sibling holds.",
        s_body,
    ))
    story.append(add_figure("fig6_synchronization_two_phase.png", "Figure 7. (A) Mutex-guarded semaphore acquisition & two-phase hold; (B) 1,000-trial concurrency test showing 0 double-bookings with mutex.", max_h_in=2.95))
    story.append(PageBreak())

    story.append(Paragraph("9.1 Deadlock Prevention, RAG Detection & Banker's Safe-State Check", s_h2))
    story.append(Paragraph(
        "When a trauma patient needs both an ICU Bed (R1) and a Ventilator (R2), locking them in arbitrary order satisfies all four Coffman conditions (Mutual Exclusion, Hold-and-Wait, No Preemption, Circular Wait). Redline prevents and resolves deadlocks in three layers: (1) <b>Global Resource Ordering</b> (ICU → Emergency → Ventilator → Neuro → Specialist) to prevent cycles; (2) <b>Resource Allocation Graph (RAG)</b> cycle detection to preempt the lowest-priority victim; and (3) <b>Banker's Algorithm</b> safe-state checks (at Hospital B with Total=[3,2,1] and Available=[1,1,0], Req-B's [0,1,0] request is granted safely while Req-C's [0,1,0] is denied because it leads to an unsafe state).",
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
    story.append(add_figure("fig8_deadlock_rag_banker.png", "Figure 8. (A) Bed-ventilator RAG deadlock cycle & victim preemption (Req-Y); (B) Banker's Algorithm safe-state verification flow.", max_h_in=2.65))

    # --- SECTION 10: PROPOSED POLICY & EXPECTED OS BEHAVIOUR ---
    story.append(Paragraph("10. PROPOSED HYBRID POLICY & EXPECTED OS BEHAVIOUR", s_h1))
    story.append(Paragraph(
        "<b>Proposed Policy:</b> Under normal traffic, Redline runs <b>Preemptive Priority with Aging (-1 every 10 ticks)</b> alongside <b>EDF SLA deadline monitoring</b>. During a mass-casualty surge, Priority-1 emergencies switch to <b>Surge FIFO with capacity-based load balancing</b> (suspending P1 aging and skipping stale hospitals).",
        s_body,
    ))
    story.append(make_table(
        ["Expected OS Behaviour Question", "Verified Kernel Response in Redline"],
        [
            ["1. Which process should execute?", "The highest-priority READY process (or earliest deadline under EDF) immediately preempts lower-priority running tasks."],
            ["2. Which process should wait?", "Preempted routine tasks return to READY; referrals awaiting hospital confirmation enter WAITING without blocking the CPU."],
            ["3. How are resources allocated?", "The matcher filters free semaphores, ranks by ETA, trust, freshness, and load, and acquires resources in fixed global order."],
            ["4. How is synchronisation maintained?", "A mutex protects wait(S)/signal(S) critical sections, and version tokens reject stale edits with HTTP 409."],
            ["5. How does it recover from failure?", "Expiry workers abort timed-out holds, call signal(S), and escalate; the RAG detector preempts the lowest-priority victim."],
        ],
        [avail_w * 0.36, avail_w * 0.64],
    ))
    story.append(PageBreak())

    # --- SECTION 11: PROTOTYPE EVIDENCE & TESTS ---
    story.append(Paragraph("11. PROTOTYPE IMPLEMENTATION, 5 TEST CASES & PYTEST (19/19)", s_h1))
    story.append(Paragraph(
        "The Flask and OS Engine prototype includes <b>9 operational screens and a Style Guide</b> (Light/Dark themes, EN/HI/KN language switcher, RBAC role switcher), an interactive <b>Live Kernel Stepper</b>, a <b>Custom Process Builder</b>, <b>SVG Gantt and Quantum Sensitivity charts</b>, and <b>CSV Report Export</b>.",
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
    story.append(add_figure("fig9_network_and_surge.png", "Figure 9. (A) 10-hospital Kanakapura-Bengaluru simulated network; (B) Surge Mode distributing 20 Priority-1 requests via FIFO load balancing.", max_h_in=2.95))
    story.append(PageBreak())

    # --- SECTION 12 & 13: RECOMMENDATIONS, CONCLUSION & REFERENCES ---
    story.append(Paragraph("12. RECOMMENDED ADDITIONAL FEATURES (FUTURE ROADMAP)", s_h1))
    for item in [
        "<b>Multi-Core SMP Hospital CPU Scheduling:</b> Extend the single-CPU scheduler to N-core symmetric multiprocessing with core affinity for Emergency Triage, ICU Telemetry, and Lab Processing.",
        "<b>Rate Monotonic Scheduling (RMS) for Periodic ICU Vitals:</b> Model periodic ECG, SpO2, and ventilator polling tasks (Ci, Ti) using Liu-Layland utilisation bounds.",
        "<b>Persistent SQLite (WAL Mode) + Server-Sent Events (SSE):</b> Replace in-memory state with WAL-mode SQLite persistence and live SSE push updates across open terminals.",
        "<b>Road-Network Dijkstra/A* Ambulance Routing:</b> Replace Haversine ETA estimates with graph shortest-path routing weighted by Bengaluru traffic conditions.",
        "<b>Real-Time EDF Admission Control & HL7/FHIR Stubs:</b> Defer non-critical OP tasks when CPU load threatens hard real-time deadlines, and add FHIR ServiceRequest payloads.",
    ]:
        story.append(Paragraph(f"• {item}", s_bullet))

    story.append(Paragraph("13. CONCLUSION", s_h1))
    story.append(Paragraph(
        "Redline (HEMS-Link) shows how hospital emergency management and inter-hospital coordination map cleanly to Operating Systems mechanisms. Comparing eight scheduling algorithms shows why average waiting time alone can be misleading: SJF gives the lowest overall wait (11.00 ticks) while delaying a cardiac arrest until t=25, whereas Preemptive Priority achieves 0.00-tick critical response. Combining Preemptive Priority with Aging (-1 every 10 ticks), EDF deadline checks, mutex-guarded two-phase holds, Banker's safe-state verification, and RAG recovery keeps the system responsive, fair, and deadlock-free while leaving final clinical decisions with hospital staff.",
        s_body,
    ))

    story.append(Paragraph("14. REFERENCES", s_h1))
    for ref in [
        "1. Silberschatz, A., Galvin, P. B., & Gagne, G. — <i>Operating System Concepts</i>, 10th ed., Wiley, 2018.",
        "2. Tanenbaum, A. S. — <i>Modern Operating Systems</i>, 4th ed., Pearson, 2015.",
        "3. Coffman, E. G., Elphick, M. J., & Shoshani, A. — \"System Deadlocks,\" <i>ACM Computing Surveys</i>, 3(2), 1971.",
        "4. Liu, C. L., & Layland, J. W. — \"Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment,\" <i>JACM</i>, 20(1), 1973.",
        "5. Dijkstra, E. W. — \"Cooperating Sequential Processes,\" Technical Report EWD123, 1965.",
        "6. IEEE Std 1003.1 (POSIX) — Interfaces for Semaphores, Mutexes, and Message Queues.",
    ]:
        story.append(Paragraph(ref, s_body))

    def draw_header_footer(canvas, doc_obj):
        canvas.saveState()
        if doc_obj.page > 1:
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(C_MUTED)
            canvas.drawString(17 * mm, A4[1] - 11 * mm, "REDLINE (HEMS-Link) — Operating Systems Case Study 2 (25PCCS201)")
            canvas.drawRightString(A4[0] - 17 * mm, A4[1] - 11 * mm, "Jain (Deemed-to-be) University")
            canvas.setStrokeColor(C_BORDER)
            canvas.setLineWidth(0.5)
            canvas.line(17 * mm, A4[1] - 13 * mm, A4[0] - 17 * mm, A4[1] - 13 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(C_MUTED)
        canvas.drawString(17 * mm, 10 * mm, "Academic Prototype | Simulated Hospital Data | Decision Support Only")
        canvas.drawRightString(A4[0] - 17 * mm, 10 * mm, f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
    print(f"Built PDF: {PDF_PATH}")


# ---------------------------------------------------------------------------
# DOCX Builder (python-docx)
# ---------------------------------------------------------------------------
def _set_cell_shading(cell, hex_color: str) -> None:
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def _set_table_borders(table) -> None:
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="D1D5DB"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="D1D5DB"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="D1D5DB"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="D1D5DB"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D1D5DB"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="D1D5DB"/>'
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
        sec.top_margin = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin = Inches(0.75)
        sec.right_margin = Inches(0.75)
        sec.different_first_page_header_footer = True
        hdr = sec.header.paragraphs[0]
        hdr.text = "REDLINE (HEMS-Link) — Operating Systems Case Study 2 (25PCCS201) | Jain University"
        hdr.runs[0].font.size = Pt(8.5)
        hdr.runs[0].font.color.rgb = D_MUTED
        ftr = sec.footer.paragraphs[0]
        ftr.text = "Academic Prototype | Simulated Hospital Data | Decision Support Only"
        ftr.runs[0].font.size = Pt(8.5)
        ftr.runs[0].font.color.rgb = D_MUTED

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = D_TEXT

    def add_h1(text: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
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
        r.font.size = Pt(11)
        r.font.color.rgb = D_SUBINK
        return p

    def add_body(text: str):
        p = doc.add_paragraph(text)
        p.paragraph_format.space_after = Pt(5)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        return p

    def add_bullet(text: str):
        p = doc.add_paragraph(text, style="List Bullet")
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
            _set_cell_shading(cell, "E5E7EB")
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(h)
            r.bold = True
            r.font.size = Pt(9)
            r.font.color.rgb = D_INK

        for i, row_vals in enumerate(rows):
            row = tbl.rows[i + 1]
            _set_row_cant_split(row)
            bg = "F9FAFB" if i % 2 == 1 else "FFFFFF"
            for j, val in enumerate(row_vals):
                cell = row.cells[j]
                cell.width = Inches(col_widths_in[j])
                _set_cell_shading(cell, bg)
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                r = p.add_run(str(val))
                r.font.size = Pt(8.8)
                if j == 0:
                    r.bold = True
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def add_fig(filename: str, caption: str, width_in: float = 6.7):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.keep_with_next = True
        p_img.add_run().add_picture(os.path.join(FIG_DIR, filename), width=Inches(width_in))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(8)
        r = p_cap.add_run(caption)
        r.italic = True
        r.font.size = Pt(9)
        r.font.color.rgb = D_MUTED

    # Cover
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("JAIN (DEEMED-TO-BE) UNIVERSITY\nDepartment of Computer Science & Engineering (AI)")
    r.bold = True
    r.font.size = Pt(14.5)
    r.font.color.rgb = D_INK

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("OPERATING SYSTEMS — CASE STUDY 2 REPORT\n\nREDLINE (HEMS-Link)")
    r2.bold = True
    r2.font.size = Pt(19.5)
    r2.font.color.rgb = D_INK

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Hospital Emergency Management & Multi-Hospital Coordination System\nAn Operating Systems analysis of CPU scheduling, real-time deadlines, shared-resource synchronisation, IPC, and deadlock handling\n(Academic Prototype | Simulated Hospital Data | Decision Support Only)")
    r3.italic = True
    r3.font.size = Pt(10.2)
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
    doc.add_page_break()

    add_h1("DECLARATION & ACKNOWLEDGEMENT")
    add_body("We declare that this case study report titled Redline (HEMS-Link): Hospital Emergency Management & Multi-Hospital Coordination System was prepared by our group for the Operating Systems course (25PCCS201, III Semester, CSE-AI) at Jain (Deemed-to-be) University. All scheduling tables, concurrency trials, and prototype tests were produced and verified on our implementation.")
    add_body("We thank our course faculty, Prof. Gowri Shankar, and the Department of Computer Science & Engineering (AI) for guiding us in applying Operating Systems concepts to a practical hospital coordination problem.")

    b8 = m["bench8"]
    race = m["race"]
    ag = m["aging"]
    pi = m["pi"]

    add_h1("1. ABSTRACT")
    add_body(
        f"A hospital computer system handles urgent emergency admissions (cardiac arrest, road trauma, stroke) alongside ongoing ICU telemetry, stat lab panels, outpatient (OP) queues, pharmacy requests, and inter-hospital patient transfers. When a hospital runs out of ICU beds, calling nearby hospitals by phone wastes time and risks two callers claiming the same last bed. Redline (HEMS-Link) models a ten-hospital network centred on Jain University Health Centre (Kanakapura Road, South Bengaluru) using Operating Systems primitives. Each task runs as a five-state PCB; ICU beds and ventilators act as counting semaphores; bed reservations execute inside a mutex critical section with two-phase holds and version tokens; and replies flow asynchronously through IPC queues. Evaluated across eight scheduling algorithms (FCFS, SJF, SRTF, Non-Preemptive Priority, Preemptive Priority, Round Robin Q=3, EDF, and MLFQ), SJF gives the lowest overall wait ({b8['sjf']['avg_waiting']} ticks), while Preemptive Priority achieves 0.00-tick critical response and is paired with aging (-1 every 10 ticks) to prevent starvation. Across 1,000 concurrent threads, mutex protection drops double-bookings from {race['without_mutex_double_bookings']}/1,000 to {race['with_mutex_double_bookings']}/1,000."
    )

    add_h1("2. INTRODUCTION & PROBLEM STATEMENT")
    add_body("Hospital software systems handle mixed workloads that do not share the same urgency. A cardiac arrest arrival cannot sit behind an outpatient registration or a routine pharmacy refill, while routine tasks cannot be ignored forever. Extending coordination across hospitals exposes classic OS problems: urgent requests arrive like interrupts, bed counts go stale, and two hospitals can request the final bed simultaneously.")
    add_body("Problem Statement: Build and analyse a hospital emergency management and coordination system using OS principles so that emergency patients, ICU monitoring, lab tests, OP queues, pharmacy requests, and inter-hospital transfers are scheduled efficiently without starvation, race conditions, stale-data dispatch, or multi-resource deadlocks.")

    add_h1("3. OBJECTIVES, SCOPE & ASSUMPTIONS")
    for obj in [
        "Model hospital activities across Emergency, ICU Monitoring, Laboratory, OP, Pharmacy, and Transfers as OS processes.",
        "Apply and compare FCFS, SJF, SRTF, Non-Preemptive Priority, Preemptive Priority, Round Robin (Q=3), Real-Time EDF, and MLFQ.",
        "Calculate Waiting Time, Turnaround Time, Response Time, CPU Utilisation, Throughput, and SLA Compliance.",
        "Classify activities into Hard Real-Time, Soft Real-Time, and Non-Real-Time groups and analyse continuous emergency streams.",
        "Prevent race conditions and deadlocks using Mutex locks, Counting Semaphores, Two-Phase Holds, Resource Ordering, RAG, and Banker's Algorithm.",
    ]:
        add_bullet(obj)
    add_h2("Engineering Assumptions")
    for a in [
        "Burst and arrival times use normalised simulation ticks so all algorithms compare on identical inputs.",
        "Single-core scheduling is evaluated in the primary kernel; multi-core SMP extension is outlined in Section 12.",
        "Hospital coordinates match real Kanakapura-Bengaluru locations with simulated bed counts; final admission stays with hospital staff.",
    ]:
        add_bullet(a)

    add_h1("4. SYSTEM DESCRIPTION (10-HOSPITAL NETWORK)")
    add_body("Redline links Jain University Health Centre (HOSP-JAIN) with 9 receiving hospitals (DSH, RRM, BGS, APL, SGR, KNG, NAR, MNI, STJ) using weighted matching (ETA 50%, Trust 20%, Freshness 15%, Load 15%) and live two-phase holds.")
    add_table(
        ["Aspect", "Traditional Manual Phone Process", "Redline OS-Based Coordination"],
        [
            ["Hospital Discovery", "Sequential phone calls lose time.", "Filters and ranks all 9 receiving hospitals together."],
            ["Bed Availability", "Local notes go stale quickly.", "Shared counting semaphores with freshness timestamps."],
            ["Double-Booking Risk", "Two callers promised the same last bed.", "Mutex critical section + HTTP 409 version tokens."],
            ["Referral Visibility", "No live status tracking after a call.", "5-state PCB tracker, parallel holds and escalation."],
        ],
        [1.5, 2.5, 2.9],
    )

    add_h1("5. REAL-WORLD TO OS MAPPING & ARCHITECTURE")
    add_table(
        ["Real-World Component", "Operating System Concept", "Role & Justification in Redline"],
        [
            ["Cardiac arrest / trauma / stroke", "High-priority preemptive process (P1–P3)", "Preempts running routine tasks immediately."],
            ["OP / Lab / Pharmacy / Dialysis", "Medium/low-priority process (P4–P8)", "Queued in READY; protected from starvation by aging."],
            ["Central coordination server", "Kernel / CPU Scheduler", "Selects next READY PCB by active policy."],
            ["ICU beds / Ventilators", "Counting Semaphore (S = free units)", "wait(S) on hold; signal(S) on reject/timeout/release."],
            ["Concurrent last-bed claim", "Critical section / Race condition", "Mutex lock + optimistic version check."],
            ["Referral hold & hospital reply", "IPC Message Queue", "PREPARE hold puts PCB in WAITING until reply/timeout."],
            ["Holds Bed, waits for Vent", "Deadlock (Circular Wait)", "Avoided via resource ordering; broken via RAG victim."],
        ],
        [2.0, 2.0, 2.9],
    )
    add_fig("fig1_architecture.png", "Figure 1. Redline layered architecture connecting UI, Flask API, 8-policy OS kernel, and 10-hospital data store.")
    add_fig("fig2_dispatch_flowchart.png", "Figure 2. End-to-end hospital activity dispatch, duplicate check, scheduling, mutex reservation, and recovery flowchart.")

    add_h1("6. OS CONCEPTS, 5-STATE LIFECYCLE & REAL-TIME CLASSIFICATION")
    add_fig("fig3_process_states.png", "Figure 3. Five-state PCB lifecycle showing preemption and non-blocking WAITING during parallel holds.")
    add_table(
        ["Real-Time Class", "Hospital Platform Activities", "Reasoning"],
        [
            ["Hard Real-Time (Target)", "Cardiac Arrest (P1), Trauma (P2), ICU Telemetry (P2), Stroke (P3), Stat ABG Lab (P3)", "Missed SLA or double-booking affects patient safety."],
            ["Soft Real-Time", "Availability Sync (P4), ICU Epinephrine Stat (P4), Record Share (P5), OP Triage (P5)", "Prompt delivery expected; brief delay tolerable."],
            ["Non-Real-Time", "Specialist Enquiry (P6), Planned Dialysis (P7), Ward Refill (P7), Discharge-back (P8)", "Routine workflows protected by priority aging."],
        ],
        [1.5, 2.9, 2.5],
    )
    add_h2("10-Process Full Hospital Clinical Mix (H1–H10)")
    h10_rows = [
        [r["pid"], r["name"], r["category"], str(r["arrival"]), f"P{r['priority']}", str(r["burst"]), f"t={r['deadline']}"]
        for r in m["bench10"]["edf"]["rows"]
    ]
    add_table(["PID", "Hospital Activity", "Subsystem", "AT", "Prio", "BT", "SLA DL"], h10_rows, [0.6, 2.2, 1.3, 0.5, 0.6, 0.5, 1.2])

    add_h1("7. CPU SCHEDULING ANALYSIS, CALCULATIONS & GANTT CHARTS")
    t8_rows = [[p.pid, p.name, str(p.arrival_time), f"P{p.priority}", str(p.burst_time), f"t={p.deadline}"] for p in default_workload()]
    add_table(["PID", "Hospital Activity", "AT", "Priority", "BT", "SLA DL"], t8_rows, [0.6, 2.6, 0.6, 0.8, 0.6, 1.7])
    add_fig("fig4_gantt_charts.png", "Figure 4. Gantt charts across FCFS, SJF, SRTF, Preemptive Priority, Round Robin (Q=3), and EDF.")

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

    add_h2("7.6 Eight-Algorithm Summary & Quantum Sensitivity")
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
    add_fig("fig5_metrics_and_quantum.png", "Figure 5. Eight-algorithm comparison bar chart and Round Robin Quantum sensitivity curve (Q=1..8).")

    add_h1("8. IMPACT OF CONTINUOUS EMERGENCIES: STARVATION & PRIORITY INHERITANCE")
    add_table(
        ["Phenomenon", "Without Mitigation", "With Redline Mitigation"],
        [
            ["Starvation (Continuous P1 stream)", f"P8 first dispatch: {ag['without_aging_first_dispatch'] or 'Starved (>120 ticks)'}", f"Aging (-1/10 ticks) dispatches P8 at t={ag['with_aging_first_dispatch']}."],
            ["Priority Inversion (Lock contention)", f"P4 preempts P8; P1 delayed {pi['delay_without']} ticks.", f"Priority Inheritance limits P1 delay to {pi['delay_with']} ticks."],
        ],
        [2.0, 2.4, 2.5],
    )
    add_fig("fig7_starvation_aging_pi.png", "Figure 6. Priority aging curve rescuing P8 and Priority Inheritance resolving lock contention.")

    add_h1("9. SYNCHRONISATION, TWO-PHASE HOLDS & DEADLOCK HANDLING")
    add_fig("fig6_synchronization_two_phase.png", "Figure 7. Mutex critical section, two-phase hold, and 1,000-trial race test.")
    add_table(
        ["Hospital B Request", "Allocation", "Max Need", "Remaining Need", "Safe-State Decision"],
        [
            ["Req-A (Cardiac)", "[1, 0, 0]", "[1, 0, 0]", "[0, 0, 0]", "Finishes first; releases [1, 0, 0]"],
            ["Req-B (Trauma)", "[1, 1, 0]", "[1, 2, 0]", "[0, 1, 0]", "Request [0,1,0] -> GRANTED (Safe)"],
            ["Req-C (Stroke)", "[0, 0, 1]", "[1, 2, 1]", "[1, 2, 0]", "Request [0,1,0] -> DENIED (Unsafe)"],
        ],
        [1.4, 1.1, 1.1, 1.2, 2.1],
    )
    add_fig("fig8_deadlock_rag_banker.png", "Figure 8. Deadlock RAG cycle detection/recovery and Banker's Algorithm verification flow.")

    add_h1("10. PROPOSED HYBRID POLICY & EXPECTED OS BEHAVIOUR")
    add_body("Redline runs Preemptive Priority + Aging (-1 per 10 ticks) paired with EDF SLA deadline monitoring in normal mode, and switches Priority-1 requests to Surge FIFO + Capacity Load Balancing during mass-casualty surges.")
    add_table(
        ["Expected OS Behaviour", "Verified Action in Redline"],
        [
            ["Which process executes?", "Highest-priority READY process (or earliest deadline under EDF) preempts lower-priority tasks."],
            ["Which process waits?", "Preempted tasks return to READY; referrals awaiting replies move to WAITING."],
            ["Resource allocation?", "Matcher filters free semaphores, ranks by ETA/Trust/Freshness/Load, locks in global order."],
            ["Synchronisation?", "Mutex wraps wait(S)/signal(S); optimistic version tokens reject stale writes (HTTP 409)."],
            ["Failure recovery?", "TTL expiry aborts stale holds, restores S, escalates; RAG preempts lowest-priority victim."],
        ],
        [2.2, 4.7],
    )

    add_h1("11. PROTOTYPE EVIDENCE, 5 TEST CASES & PYTEST (19/19)")
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
    add_fig("fig9_network_and_surge.png", "Figure 9. 10-hospital Kanakapura-Bengaluru network and 20-request P1 Surge FIFO distribution.")

    add_h1("12. RECOMMENDED ADDITIONAL FEATURES")
    for item in [
        "Multi-Core SMP Hospital CPU Scheduling & Processor Affinity across Emergency, ICU Telemetry, and Lab cores.",
        "Rate Monotonic Scheduling (RMS) for periodic ICU vitals monitoring with Liu-Layland utilisation bounds.",
        "Persistent SQLite (WAL mode) + Server-Sent Events (SSE) real-time push updates.",
        "Road-network Dijkstra/A* ambulance routing weighted by live traffic.",
        "Real-time EDF admission control & HL7/FHIR interoperability stubs.",
    ]:
        add_bullet(item)

    add_h1("13. CONCLUSION & REFERENCES")
    add_body("Redline shows how hospital emergency management and multi-hospital coordination map directly to OS mechanisms. Preemptive Priority with Aging achieves 0.00-tick critical response without starvation, while mutex-protected semaphores, two-phase holds, resource ordering, RAG recovery, and Banker's Algorithm keep shared-resource allocation safe.")
    for ref in [
        "1. Silberschatz, A., Galvin, P. B., & Gagne, G. — Operating System Concepts, 10th ed., Wiley, 2018.",
        "2. Tanenbaum, A. S. — Modern Operating Systems, 4th ed., Pearson, 2015.",
        "3. Coffman, E. G., Elphick, M. J., & Shoshani, A. — System Deadlocks, ACM Computing Surveys, 3(2), 1971.",
        "4. Liu, C. L., & Layland, J. W. — Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment, JACM, 20(1), 1973.",
        "5. Dijkstra, E. W. — Cooperating Sequential Processes, EWD123, 1965.",
        "6. IEEE Std 1003.1 (POSIX) — Semaphores, Mutexes, and Message Queues.",
    ]:
        add_body(ref)

    doc.save(DOCX_PATH)
    print(f"Built DOCX: {DOCX_PATH}")


if __name__ == "__main__":
    metrics = gather_metrics()
    build_pdf(metrics)
    build_docx(metrics)
