"""Build publication-grade color PDF and DOCX reports for Redline (HEMS-Link) Case Study 2."""

from __future__ import annotations

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
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
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

from os_engine.scheduler import default_workload, hospital_10_workload, run_extended_benchmark, run_quantum_sweep
from os_engine.simulator import ScenarioSimulator

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(DOCS_DIR, "figures_color")
PDF_PATH = os.path.join(DOCS_DIR, "Redline_OS_Case_Study_Report.pdf")
DOCX_PATH = os.path.join(DOCS_DIR, "Redline_OS_Case_Study_Report.docx")

# Palette
C_NAVY = colors.HexColor("#0F2942")
C_TEAL = colors.HexColor("#0D7377")
C_TBL_HDR = colors.HexColor("#1B3B5A")
C_ZEBRA = colors.HexColor("#F4F8FB")
C_BORDER = colors.HexColor("#CBD5E1")
C_TEXT = colors.HexColor("#1E293B")
C_MUTED = colors.HexColor("#475569")
C_CALLOUT_BG = colors.HexColor("#EFF6FF")
C_CALLOUT_WARN = colors.HexColor("#FEF3C7")
C_CALLOUT_OK = colors.HexColor("#DCFCE7")

D_NAVY = RGBColor(0x0F, 0x29, 0x42)
D_TEAL = RGBColor(0x0D, 0x73, 0x77)
D_TEXT = RGBColor(0x1E, 0x29, 0x3B)
D_MUTED = RGBColor(0x47, 0x55, 0x69)

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
        author="R Hari Priya et al. — Jain University",
    )
    avail_w = A4[0] - 34 * mm

    base = getSampleStyleSheet()
    s_uni = ParagraphStyle("Uni", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=14, leading=18, alignment=TA_CENTER, textColor=C_NAVY)
    s_dept = ParagraphStyle("Dept", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=11, leading=15, alignment=TA_CENTER, textColor=C_TEAL)
    s_tag = ParagraphStyle("Tag", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=14, alignment=TA_CENTER, textColor=C_MUTED)
    s_title = ParagraphStyle("TitleMain", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=20, leading=24, alignment=TA_CENTER, textColor=C_NAVY)
    s_sub = ParagraphStyle("SubMain", parent=base["Normal"], fontName="Helvetica", fontSize=11, leading=15, alignment=TA_CENTER, textColor=C_MUTED)

    s_h1 = ParagraphStyle("H1", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=13.5, leading=17, textColor=C_NAVY, spaceBefore=12, spaceAfter=5)
    s_h2 = ParagraphStyle("H2", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=C_TEAL, spaceBefore=9, spaceAfter=4)
    s_body = ParagraphStyle("Body", parent=base["Normal"], fontName="Helvetica", fontSize=9.6, leading=14, alignment=TA_JUSTIFY, textColor=C_TEXT, spaceAfter=5)
    s_bullet = ParagraphStyle("Bullet", parent=s_body, leftIndent=14, firstLineIndent=-8, spaceAfter=3)
    s_cap = ParagraphStyle("Cap", parent=base["Normal"], fontName="Helvetica-Oblique", fontSize=8.6, leading=11.5, alignment=TA_CENTER, textColor=C_MUTED, spaceBefore=3, spaceAfter=8)
    s_tbl_hdr = ParagraphStyle("TblHdr", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.4, leading=10.5, textColor=colors.white)
    s_tbl_cell = ParagraphStyle("TblCell", parent=base["Normal"], fontName="Helvetica", fontSize=8.2, leading=10.8, textColor=C_TEXT)
    s_tbl_bold = ParagraphStyle("TblBold", parent=s_tbl_cell, fontName="Helvetica-Bold")
    s_code = ParagraphStyle("Code", parent=base["Normal"], fontName="Courier", fontSize=8.0, leading=11, textColor=C_NAVY, backColor=C_ZEBRA, leftIndent=8, rightIndent=8)

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
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ]
        for idx in range(1, len(data)):
            if idx % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, idx), (-1, idx), C_ZEBRA))
        tbl.setStyle(TableStyle(style_cmds))
        return tbl

    def callout(title: str, body: str, bg=C_CALLOUT_BG, accent=C_TEAL) -> Table:
        content = Paragraph(f"<b><font color='{accent.hexval()}'>{title}:</font></b> {body}", s_body)
        t = Table([[content]], colWidths=[avail_w])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("LINEBEFORE", (0, 0), (0, -1), 3.5, accent),
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
    banner = Table([[Paragraph(
        "<font color='white'><b>JAIN (DEEMED-TO-BE) UNIVERSITY</b><br/>Department of Computer Science &amp; Engineering (AI)</font>",
        ParagraphStyle("Ban", parent=base["Normal"], fontSize=13, leading=18, alignment=TA_CENTER, textColor=colors.white),
    )]], colWidths=[avail_w])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(banner)
    story.append(Spacer(1, 18))
    story.append(Paragraph("OPERATING SYSTEMS — CASE STUDY 2 REPORT", s_tag))
    story.append(Spacer(1, 8))
    story.append(Paragraph("REDLINE (HEMS-Link)", s_title))
    story.append(Paragraph("Hospital Emergency Management &amp; Multi-Hospital Coordination System", ParagraphStyle("SubTitle", parent=s_title, fontSize=13.5, leading=18, textColor=C_TEAL)))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<i>An Operating Systems Analysis of CPU Scheduling, Real-Time Deadlines, Shared-Resource Synchronisation, Inter-Process Communication, and Deadlock Handling</i>",
        s_sub,
    ))
    story.append(Spacer(1, 16))
    story.append(make_table(
        ["Academic Detail", "Information"],
        [
            ["Course Name & Code", "Operating Systems — 25PCCS201"],
            ["Class & Section", "III Semester — CSE (AI)"],
            ["Faculty Name", "Gowri Shankar"],
            ["Group Members", GROUP_MEMBERS],
            ["Submission Date", "26/11/2026"],
            ["System Scope", "Academic Prototype • Simulated Hospital Data • Decision Support Only"],
        ],
        [avail_w * 0.32, avail_w * 0.68],
    ))
    story.append(Spacer(1, 16))
    story.append(callout(
        "Clinical & Simulation Notice",
        "All hospital bed capacities, patient hashes, and ambulance ETAs in this report are simulated for Operating Systems coursework evaluation. Redline supports dispatch staff and does not replace clinical judgement.",
        bg=C_CALLOUT_WARN, accent=colors.HexColor("#B45309"),
    ))
    story.append(PageBreak())

    # --- PAGE 2: DECLARATION, ACKNOWLEDGEMENT, TOC ---
    story.append(Paragraph("DECLARATION", s_h1))
    story.append(Paragraph(
        "We hereby declare that this case study report titled <b>Redline (HEMS-Link): Hospital Emergency Management &amp; Multi-Hospital Coordination System</b> has been prepared as part of the Operating Systems coursework (25PCCS201, III Semester, CSE-AI) at Jain (Deemed-to-be) University. All scheduling calculations, concurrency experiments, real-time analyses, and automated verification results were independently derived and validated on our prototype.",
        s_body,
    ))
    story.append(Paragraph("ACKNOWLEDGEMENT", s_h1))
    story.append(Paragraph(
        "We express our sincere gratitude to Prof. <b>Gowri Shankar</b> and the Department of Computer Science &amp; Engineering (AI) for guiding us to analyse real-world hospital operations through core Operating Systems abstractions including CPU scheduling, real-time deadlines, synchronisation primitives, inter-process communication, and deadlock management.",
        s_body,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("TABLE OF CONTENTS", s_h1))
    toc_rows = [
        ["1", "Abstract", "3"],
        ["2", "Introduction & Problem Statement", "3"],
        ["3", "Objectives, Scope & Explicit Assumptions", "3–4"],
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
        f"Hospital computing environments must simultaneously orchestrate time-critical emergency care (cardiac arrest, multi-organ trauma, stroke), continuous ICU ventilator telemetry, stat diagnostic lab panels, outpatient (OP) queues, pharmacy dispatches, and inter-hospital patient transfers. When an origin facility reaches capacity, manual phone coordination wastes golden minutes, exposes stale bed counts, and risks double-booking the last available ICU bed. <b>Redline (HEMS-Link)</b> models a ten-hospital emergency coordination network centred on Jain University Health Centre (Kanakapura Road, South Bengaluru) as a deterministic Operating System kernel.",
        s_body,
    ))
    story.append(Paragraph(
        f"Every clinical activity and referral executes as a five-state Process Control Block (PCB); ICU beds and ventilators act as counting semaphores; concurrent reservations run inside a mutex-protected critical section with two-phase holds and optimistic version tokens; and hospital responses flow via asynchronous IPC queues. We evaluate eight scheduling policies—FCFS, SJF, SRTF, Non-Preemptive Priority, Preemptive Priority, Round Robin (Q=3), Real-Time EDF, and MLFQ—on the eight-process baseline (T1–T8) and a ten-process hospital clinical mix (H1–H10). While SJF achieves the lowest overall wait ({b8['sjf']['avg_waiting']} ticks), Preemptive Priority delivers <b>0.00-tick critical response</b> and is paired with priority aging (-1 every 10 ticks) to prevent starvation. In a 1,000-trial concurrency test, mutex protection reduces double-bookings from <b>{race['without_mutex_double_bookings']}/1,000</b> to <b>{race['with_mutex_double_bookings']}/1,000</b>.",
        s_body,
    ))

    story.append(Paragraph("2. INTRODUCTION & PROBLEM STATEMENT", s_h1))
    story.append(Paragraph(
        "A modern hospital computer system is an archetypal concurrent, resource-constrained environment. Emergency admissions arrive unpredictably like hardware interrupts while routine outpatient registrations, laboratory batches, pharmacy refills, and planned step-down transfers compete for the same CPU scheduler and clinical staff attention. Extending coordination across multiple hospitals introduces distributed systems hazards: availability figures age quickly, two referring hospitals can view the same free ventilator at once, and a patient holding an ICU bed while waiting for a ventilator can trigger a circular wait.",
        s_body,
    ))
    story.append(callout(
        "Problem Statement",
        "Design and analyse an Operating Systems-driven hospital emergency management and coordination architecture that efficiently schedules emergency patients, ICU monitoring, laboratory tests, OP queues, pharmacy requests, and inter-hospital transfers—ensuring hard real-time responsiveness for critical emergencies without starvation, race conditions, stale-data dispatch, or multi-resource deadlocks.",
    ))

    # --- SECTION 3 & 4 ---
    story.append(Paragraph("3. OBJECTIVES, SCOPE & EXPLICIT ASSUMPTIONS", s_h1))
    story.append(Paragraph("3.1 Case Study Objectives", s_h2))
    for item in [
        "Model diverse hospital activities (Emergency, ICU Monitoring, Lab, OP, Pharmacy, Transfers) as OS processes with defined arrival times, priorities, burst times, and SLA deadlines.",
        "Apply and compare FCFS, SJF, Preemptive Priority, and Round Robin (Q=3), alongside extended policies (SRTF, Non-Preemptive Priority, Real-Time EDF, MLFQ).",
        "Compute Completion Time (CT), Turnaround Time (TAT), Waiting Time (WT), Response Time (RT), CPU Utilization, Throughput, and SLA Compliance.",
        "Classify tasks into Hard Real-Time, Soft Real-Time, and Non-Real-Time categories and examine the impact of continuously arriving emergencies.",
        "Prevent race conditions, starvation, priority inversion, and deadlocks using Mutex locks, Counting Semaphores, Two-Phase Holds, Aging, Resource Ordering, RAG detection, and Banker's Algorithm.",
    ]:
        story.append(Paragraph(f"• {item}", s_bullet))

    story.append(Paragraph("3.2 Explicit Engineering Assumptions & Scope", s_h2))
    for item in [
        "<b>Normalised Time Quantum:</b> CPU burst times and arrivals are expressed in normalised scheduling ticks (1 tick = 1 unit of dispatch/processing work) for reproducible cross-algorithm math.",
        "<b>Single-CPU Scheduler Core:</b> The core scheduling comparison evaluates single-processor preemption and context switching; multi-core SMP extension is documented in Section 12.",
        "<b>Simulated Availability & Telemetry:</b> Hospital bed counts, trust scores, and coordinates represent realistic Kanakapura–Bengaluru locations with synthetic capacities.",
        "<b>Decision-Support Boundary:</b> Automated matching and two-phase holds reserve capacity tentatively; final clinical admission always requires receiving hospital acceptance.",
    ]:
        story.append(Paragraph(f"• {item}", s_bullet))

    story.append(Paragraph("4. SYSTEM DESCRIPTION (10-HOSPITAL NETWORK)", s_h1))
    story.append(Paragraph(
        "Redline connects the origin node—<b>Jain University Health Centre (Kanakapura Rd)</b>—to <b>nine receiving hospitals</b> across South Bengaluru and Kanakapura. On the Live Dispatch console, staff submit patient or internal hospital tasks; the OS Engine admits a PCB, ranks eligible hospitals using Haversine ETA (50%), clinical trust (20%), data freshness (15%), and incoming load (15%), and executes a mutex-protected two-phase hold.",
        s_body,
    ))
    story.append(make_table(
        ["Aspect", "Traditional Manual Phone Process", "Redline OS-Based Coordination"],
        [
            ["Hospital Discovery", "Staff call receiving desks sequentially, losing golden minutes.", "Two-stage matcher filters and ranks all 9 receiving hospitals simultaneously."],
            ["Bed Availability", "Isolated spreadsheets/phone notes go stale within minutes.", "Shared counting semaphores with ISO-8601 timestamps & stale-node flags."],
            ["Double-Booking Risk", "Two callers verbally promised the same final ICU bed.", "Mutex critical section + optimistic version tokens (HTTP 409 on conflict)."],
            ["Task Prioritisation", "Ad-hoc queuing delays stroke/cardiac tasks behind routine traffic.", "Preemptive Priority + Aging + Real-Time EDF deadline tracking."],
            ["Referral Visibility", "No live state tracking once a call is placed.", "5-state PCB tracker, parallel top-N holds (first-accept-wins) & escalation."],
        ],
        [avail_w * 0.22, avail_w * 0.36, avail_w * 0.42],
    ))
    story.append(PageBreak())

    # --- SECTION 5: MAPPING, ARCHITECTURE & FLOWCHART ---
    story.append(Paragraph("5. REAL-WORLD TO OS MAPPING & SYSTEM DIAGRAMS", s_h1))
    story.append(make_table(
        ["Real-World Hospital Entity / Event", "Operating System Concept", "Role & Justification in Redline"],
        [
            ["Cardiac arrest / trauma / stroke", "High-priority preemptive process (P1–P3)", "Immediately preempts running routine tasks for 0-tick first response."],
            ["ICU telemetry & Stat ABG lab", "Periodic / urgent real-time process (P2–P3)", "Tracked against strict SLA deadlines under EDF and Priority scheduling."],
            ["OP walk-in, pharmacy refill, dialysis", "Medium/low-priority process (P4–P8)", "Queued in READY; protected from starvation by aging (-1 / 10 ticks)."],
            ["Emergency arrival during routine work", "Hardware interrupt / Preemption", "Triggers context switch, saving interrupted PCB back to READY."],
            ["Central coordination server", "Kernel / CPU Scheduler", "Selects next READY PCB according to active policy (Priority, EDF, MLFQ, etc.)."],
            ["Hospital matching engine", "Resource allocator", "Evaluates feasibility and scores candidate hospitals transparently."],
            ["ICU beds, Ventilators, Specialists", "Counting Semaphores (S = free units)", "wait(S) decrements on PREPARE hold; signal(S) restores on reject/expiry."],
            ["Simultaneous last-bed claims", "Critical section & Race condition", "Serialized via threading.Lock mutex + compare-and-swap version token."],
            ["Referral hold & hospital reply", "Asynchronous IPC Message Queue", "Non-blocking PREPARE holds move PCB to WAITING until reply or timeout."],
            ["Holding ICU bed while waiting for Vent", "Deadlock (Circular Wait)", "Prevented by global resource ordering; resolved by RAG victim release."],
        ],
        [avail_w * 0.30, avail_w * 0.28, avail_w * 0.42],
    ))
    story.append(add_figure("fig1_architecture.png", "Figure 1. Redline layered architecture connecting the 9-screen UI, Flask API, 8-policy OS Kernel, and 10-hospital data store.", max_h_in=3.1))
    story.append(add_figure("fig2_dispatch_flowchart.png", "Figure 2. End-to-end hospital activity dispatch, duplicate check, CPU scheduling, mutex reservation, and recovery flowchart.", max_h_in=3.8))
    story.append(PageBreak())

    # --- SECTION 6: OS CONCEPTS & REAL-TIME CLASSIFICATION ---
    story.append(Paragraph("6. OS CONCEPTS, 5-STATE LIFECYCLE & REAL-TIME CLASSIFICATION", s_h1))
    story.append(Paragraph(
        "Every hospital task is instantiated as a <b>Process Control Block (PCB)</b> carrying its PID, subsystem category, arrival time, base and effective priority, remaining burst time, real-time SLA deadline, and waiting-tick counter. Tasks transition cleanly across five states so CPU dispatch never stalls while awaiting external hospital replies.",
        s_body,
    ))
    story.append(add_figure("fig3_process_states.png", "Figure 3. Five-state PCB lifecycle showing preemption back to READY and non-blocking WAITING during parallel holds.", max_h_in=2.1))

    story.append(Paragraph("6.1 Real-Time Task Classification Across All Hospital Subsystems", s_h2))
    story.append(make_table(
        ["Real-Time Class", "Hospital Activities Covered", "Priority & SLA Target", "OS Scheduling Justification"],
        [
            ["Hard Real-Time\n(Design Target)", "Cardiac Arrest (P1), Trauma ICU+Vent (P2), ICU Ventilator Telemetry (P2), Stroke Unit (P3), Stat ABG Lab (P3)", "P1–P3; Tight SLA slack (+3 to +7 ticks); 0-tick dispatch target", "Missed deadline or double-booked bed directly endangers patient survival; requires immediate preemption."],
            ["Soft Real-Time", "Hospital Availability Sync (P4), ICU Epinephrine Stat Pharmacy (P4), Urgent Lab/Record Share (P5), OP Triage (P5)", "P4–P5; Moderate slack (+12 to +15 ticks)", "Timely execution keeps hospital telemetry fresh and pharmacy/triage responsive; brief delay is tolerable."],
            ["Non-Real-Time", "Specialist Enquiry (P6), Planned Dialysis Transfer (P7), Pharmacy Ward Refill (P7), Discharge-Back (P8)", "P6–P8; High slack (+20 to +32 ticks)", "Background/routine workflows without hard deadlines; must avoid starvation via aging."],
        ],
        [avail_w * 0.18, avail_w * 0.34, avail_w * 0.20, avail_w * 0.28],
    ))

    story.append(Paragraph("6.2 Ten-Process Full Hospital Clinical Mix (H1–H10)", s_h2))
    story.append(Paragraph(
        "In addition to the 8-process baseline (T1–T8) and 8 live seeded system requests (REQ-1001–REQ-1008), Redline includes a 10-process clinical mix (H1–H10) covering all five Case Study 2 subsystems:",
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
        "To compare policies without bias, all algorithms are evaluated on the standard eight-process workload (T1–T8), where routine tasks arrive early (t=0..3) and critical emergencies arrive later (t=4..6). Scheduling formulae: <b>Turnaround Time (TAT) = Completion (CT) − Arrival (AT)</b>, <b>Waiting Time (WT) = TAT − Burst (BT)</b>, and <b>Response Time (RT) = First Dispatch − AT</b>.",
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
    story.append(add_figure("fig4_gantt_charts.png", "Figure 4. Color-coded Gantt charts across FCFS, SJF, SRTF, Preemptive Priority, Round Robin (Q=3), and Real-Time EDF (0–40 ticks).", max_h_in=3.6))

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

    sched_table("7.1 First Come First Served (FCFS)", "fcfs", "Non-preemptive FIFO causes severe convoy delay: Cardiac Arrest (T8) arrives at t=6 but waits until t=33 (RT=27).")
    sched_table("7.2 Shortest Job First (SJF — Non-Preemptive) & SRTF", "sjf", "SJF and SRTF achieve the lowest overall average wait (11.00 ticks) on this set, but still delay Cardiac Arrest (T8) until t=25 (RT=19) behind shorter routine tasks.")
    story.append(PageBreak())
    sched_table("7.3 Preemptive Priority Scheduling (Recommended Core Policy)", "preemptive_priority", "Every critical emergency (T6, T7, T8) is dispatched instantaneously upon arrival (Critical Avg Response = 0.00). Low-priority T2 waits 37 ticks without aging, demonstrating why aging is essential.")
    sched_table("7.4 Round Robin Scheduling (Time Quantum Q = 3)", "round_robin", "Time-slicing improves average response (9.00) for early arrivals, but forces Cardiac Arrest (T8) to wait 18 ticks for its first CPU slice and finish last at t=40.")
    sched_table("7.5 Earliest Deadline First (EDF — Real-Time Dynamic Priority)", "edf", "EDF dynamically prioritises tightest SLA deadlines, achieving Critical Avg Wait of 4.67 ticks with only 1 context switch.")

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
    story.append(add_figure("fig5_metrics_and_quantum.png", "Figure 5. (A) 8-algorithm metric comparison; (B) Round Robin Quantum sensitivity (Q=1..8) showing wait-time vs. context-switch trade-off.", max_h_in=3.1))
    story.append(PageBreak())

    # --- SECTION 8: IMPACT OF CONTINUOUS EMERGENCIES ---
    story.append(Paragraph("8. IMPACT OF CONTINUOUSLY ARRIVING EMERGENCIES (TASK 7)", s_h1))
    story.append(Paragraph(
        "Under strict static Preemptive Priority, a sustained burst of Priority-1 emergencies creates two well-known real-time hazards: <b>indefinite starvation</b> of routine tasks (such as OP discharges or planned dialysis) and <b>priority inversion</b> when a low-priority task holds a shared availability lock.",
        s_body,
    ))
    ag = m["aging"]
    pi = m["pi"]
    story.append(make_table(
        ["Phenomenon", "Experimental Setup", "Without Mitigation", "With Redline Mitigation"],
        [
            ["Starvation under Continuous P1 Stream", "P1 arrives every 4 ticks for 120 ticks; P8 arrives at t=1 (BT=2).", f"P8 first dispatch: {ag['without_aging_first_dispatch'] or 'Starved (>120 ticks)'}", f"Aging (-1 every 10 ticks) boosts P8 -> P1; dispatched at t={ag['with_aging_first_dispatch']}."],
            ["Priority Inversion on Availability Lock", "P8 holds lock; P1 needs lock at t=2; P4 medium task arrives.", f"P4 preempts P8; P1 delayed {pi['delay_without']} ticks (until t=14).", f"Priority Inheritance boosts P8 -> P1; P1 unblocked in {pi['delay_with']} ticks (t=4)."],
        ],
        [avail_w * 0.22, avail_w * 0.26, avail_w * 0.25, avail_w * 0.27],
    ))
    story.append(add_figure("fig7_starvation_aging_pi.png", "Figure 6. (A) Priority aging step curve rescuing P8 from starvation at t=72; (B) Priority Inheritance eliminating medium-priority interference.", max_h_in=3.1))

    # --- SECTION 9: SYNCHRONIZATION & DEADLOCK ---
    story.append(Paragraph("9. SYNCHRONISATION, TWO-PHASE HOLDS & DEADLOCK HANDLING", s_h1))
    story.append(Paragraph(
        "Each hospital facility acts as a <b>Counting Semaphore (S = free_units)</b>. Checking and decrementing S executes inside a <b>Mutex Critical Section</b> coupled with an optimistic version token. Rather than blocking the CPU while waiting for a hospital reply, Redline uses a <b>Two-Phase Hold</b> (PREPARE → COMMITTED / ABORTED / EXPIRED) and supports <b>Top-N Parallel Referral</b> where the first hospital to accept commits its hold and atomically releases all sibling holds.",
        s_body,
    ))
    story.append(add_figure("fig6_synchronization_two_phase.png", "Figure 7. (A) Mutex-guarded semaphore acquisition & two-phase hold; (B) 1,000-trial race test proving 0 double-bookings with mutex.", max_h_in=3.0))
    story.append(PageBreak())

    story.append(Paragraph("9.1 Deadlock Prevention, RAG Detection & Banker's Safe-State Check", s_h2))
    story.append(Paragraph(
        "When a critical patient requires both an ICU Bed (R1) and a Ventilator (R2), unconstrained acquisition can satisfy all four Coffman conditions (Mutual Exclusion, Hold-and-Wait, No Preemption, Circular Wait). Redline layers three defences: (1) <b>Global Resource Ordering</b> (ICU → Emergency → Ventilator → Neuro → Specialist) breaking Circular Wait; (2) <b>Resource Allocation Graph (RAG)</b> cycle detection releasing the lowest-priority victim; and (3) <b>Banker's Algorithm</b> safe-state verification (demonstrated on Hospital B: Total=[3,2,1], Available=[1,1,0], where Req-B's [0,1,0] request is GRANTED safely while Req-C's [0,1,0] is DENIED as unsafe).",
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
    story.append(add_figure("fig8_deadlock_rag_banker.png", "Figure 8. (A) Bed–Ventilator RAG deadlock cycle & victim preemption (Req-Y); (B) Banker's Algorithm safe-state verification flow.", max_h_in=2.65))

    # --- SECTION 10: PROPOSED POLICY & EXPECTED OS BEHAVIOUR ---
    story.append(Paragraph("10. PROPOSED HYBRID POLICY & EXPECTED OS BEHAVIOUR", s_h1))
    story.append(Paragraph(
        "<b>Proposed Scheduling Policy:</b> Redline adopts a hybrid <b>Preemptive Priority + Aging (-1 per 10 ticks)</b> kernel paired with <b>EDF Real-Time SLA Deadline Monitoring</b> during normal operations, and switches Priority-1 emergencies to <b>Surge FIFO + Capacity Load Balancing</b> (suspending P1 aging and skipping stale nodes) during mass-casualty surges.",
        s_body,
    ))
    story.append(make_table(
        ["Expected OS Behaviour Question / Stress Case", "Verified Kernel Response in Redline"],
        [
            ["1. Which process should execute?", "Highest-priority READY process (or earliest deadline under EDF) immediately preempts lower-priority running tasks."],
            ["2. Which process should wait?", "Preempted routine tasks return to READY; referrals awaiting hospital confirmation enter WAITING without blocking the CPU."],
            ["3. How are resources allocated?", "Matcher filters free semaphores, ranks by ETA/Trust/Freshness/Load, and locks resources in fixed global order."],
            ["4. How is synchronisation maintained?", "Mutex guards wait(S)/signal(S) critical sections; optimistic version tokens reject stale edits with HTTP 409."],
            ["5. How does it recover from failure?", "TTL expiry workers abort timed-out holds, restore S, and escalate; RAG cycle detector preempts lowest-priority victim."],
        ],
        [avail_w * 0.38, avail_w * 0.62],
    ))
    story.append(PageBreak())

    # --- SECTION 11: PROTOTYPE EVIDENCE & TESTS ---
    story.append(Paragraph("11. PROTOTYPE IMPLEMENTATION, 5 TEST CASES & PYTEST (19/19)", s_h1))
    story.append(Paragraph(
        "The full-stack Flask + OS Engine prototype provides <b>9 operational screens + Style Guide</b> (Light/Dark Liquid Glass UI, EN/HI/KN i18n, RBAC switcher), including an interactive <b>Live Kernel Stepper</b>, <b>Custom Process Builder</b>, <b>SVG Gantt & Quantum Sensitivity Lab</b>, and <b>CSV Report Export</b>.",
        s_body,
    ))
    case_rows = [[c["case_id"], c["title"], c["best_algorithm"], c["metric_comparison"], c["why"]] for c in m["cases"]]
    story.append(make_table(
        ["Case", "Hospital Scenario", "Best Algorithm", "Measured Result", "Engineering Rationale"],
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
    story.append(add_figure("fig9_network_and_surge.png", "Figure 9. (A) 10-hospital Kanakapura–Bengaluru simulated network; (B) Surge Mode distributing 20 Priority-1 requests via FIFO load balancing.", max_h_in=3.0))
    story.append(PageBreak())

    # --- SECTION 12 & 13: RECOMMENDATIONS, CONCLUSION & REFERENCES ---
    story.append(Paragraph("12. RECOMMENDED ADDITIONAL FEATURES (FUTURE ROADMAP)", s_h1))
    for item in [
        "<b>Multi-Core SMP Hospital CPU Scheduling:</b> Extend the single-CPU scheduler to N-core symmetric multiprocessing with dedicated core affinity for Emergency Triage, ICU Telemetry, and Lab Processing.",
        "<b>Rate Monotonic Scheduling (RMS) for Periodic ICU Vitals:</b> Model continuous ECG/SpO2/ventilator polling as periodic tasks (Ci, Ti) with Liu–Layland utilisation bound checks.",
        "<b>Persistent SQLite (WAL Mode) + Server-Sent Events (SSE):</b> Replace in-memory state with concurrent WAL-mode SQLite persistence and real-time SSE push updates across dispatch terminals.",
        "<b>Road-Network Dijkstra/A* Ambulance Routing:</b> Upgrade Haversine ETA to graph-based shortest-path routing weighted by live Bengaluru traffic multipliers.",
        "<b>Real-Time EDF Admission Control & HL7/FHIR Stubs:</b> Shed or defer non-critical OP tasks when CPU utilisation threatens hard real-time deadlines, and expose FHIR ServiceRequest payloads.",
    ]:
        story.append(Paragraph(f"• {item}", s_bullet))

    story.append(Paragraph("13. CONCLUSION", s_h1))
    story.append(Paragraph(
        "Redline (HEMS-Link) demonstrates that hospital emergency management and multi-hospital coordination map directly to core Operating Systems abstractions. Evaluating eight scheduling policies confirms that overall average waiting time alone is clinically deceptive: SJF minimises aggregate wait (11.00 ticks) while delaying a cardiac arrest until t=25, whereas Preemptive Priority delivers 0.00-tick critical response and—when combined with Aging (-1 per 10 ticks), EDF SLA monitoring, mutex-protected two-phase holds, Banker's checks, and RAG recovery—guarantees responsiveness, fairness, and deadlock safety while leaving final clinical judgement with hospital staff.",
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
        canvas.drawString(17 * mm, 10 * mm, "Academic Prototype • Simulated Hospital Data • Decision Support Only")
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
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
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
        ftr.text = "Academic Prototype • Simulated Hospital Data • Decision Support Only"
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
        r.font.size = Pt(13.5)
        r.font.color.rgb = D_NAVY
        return p

    def add_h2(text: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(11)
        r.font.color.rgb = D_TEAL
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
            _set_cell_shading(cell, "1B3B5A")
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(h)
            r.bold = True
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        for i, row_vals in enumerate(rows):
            row = tbl.rows[i + 1]
            _set_row_cant_split(row)
            bg = "F4F8FB" if i % 2 == 1 else "FFFFFF"
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
    r.font.size = Pt(15)
    r.font.color.rgb = D_NAVY

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("OPERATING SYSTEMS — CASE STUDY 2 ASSIGNMENT\n\nREDLINE (HEMS-Link)")
    r2.bold = True
    r2.font.size = Pt(20)
    r2.font.color.rgb = D_NAVY

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Hospital Emergency Management & Multi-Hospital Coordination System\nAn Operating Systems Analysis of CPU Scheduling, Real-Time Deadlines, Shared-Resource Synchronisation, IPC, and Deadlock Handling\n(Academic Prototype • Simulated Hospital Data • Decision Support Only)")
    r3.italic = True
    r3.font.size = Pt(10.5)
    r3.font.color.rgb = D_TEAL

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
    add_body("We hereby declare that this case study report titled Redline (HEMS-Link): Hospital Emergency Management & Multi-Hospital Coordination System has been prepared as part of the Operating Systems coursework (25PCCS201, III Semester, CSE-AI) at Jain (Deemed-to-be) University. All scheduling calculations, concurrency experiments, and prototype observations are based on simulated hospital workloads.")
    add_body("We express our sincere gratitude to Prof. Gowri Shankar for guiding us to analyse real-world hospital coordination challenges through core Operating Systems principles.")

    b8 = m["bench8"]
    race = m["race"]
    ag = m["aging"]
    pi = m["pi"]

    add_h1("1. ABSTRACT")
    add_body(
        f"Hospital computer systems concurrently manage time-critical emergencies (cardiac arrest, road trauma, stroke), continuous ICU telemetry, stat laboratory tests, outpatient (OP) queues, pharmacy requests, and inter-hospital patient transfers. Redline (HEMS-Link) models a ten-hospital network centred on Jain University Health Centre (Kanakapura Road, South Bengaluru) as an Operating System kernel. Hospital activities execute as five-state PCBs; ICU beds and ventilators act as counting semaphores; reservations run inside a mutex-protected critical section with two-phase holds and optimistic version tokens; and hospital replies flow via asynchronous IPC queues. Evaluated across eight scheduling policies (FCFS, SJF, SRTF, Non-Preemptive Priority, Preemptive Priority, Round Robin Q=3, EDF, and MLFQ), SJF attains the lowest overall wait ({b8['sjf']['avg_waiting']} ticks), whereas Preemptive Priority achieves 0.00-tick critical response and is paired with aging (-1 every 10 ticks) to prevent starvation. Concurrency tests show {race['without_mutex_double_bookings']}/1,000 double-bookings without a mutex versus {race['with_mutex_double_bookings']}/1,000 with mutex protection."
    )

    add_h1("2. INTRODUCTION & PROBLEM STATEMENT")
    add_body("Hospital environments combine unpredictable emergency arrivals (analogous to hardware interrupts) with routine OP, pharmacy, laboratory, and planned transfer workloads. Centralising hospital coordination makes concurrency hazards explicit: bed records go stale, concurrent callers race for the last ICU bed, and multi-resource holds can deadlock.")
    add_body("Problem Statement: Design and evaluate an OS-driven Hospital Emergency Management and Multi-Hospital Coordination System that schedules emergency patients, ICU monitoring, laboratory tests, OP patients, pharmacy requests, and inter-hospital transfers efficiently—guaranteeing critical responsiveness without starvation, race conditions, or deadlocks.")

    add_h1("3. OBJECTIVES, SCOPE & EXPLICIT ASSUMPTIONS")
    for obj in [
        "Model hospital activities across Emergency, ICU Monitoring, Laboratory, OP, Pharmacy, and Transfers as OS processes.",
        "Apply and compare FCFS, SJF, SRTF, Non-Preemptive Priority, Preemptive Priority, Round Robin (Q=3), Real-Time EDF, and MLFQ.",
        "Compute Waiting Time, Turnaround Time, Response Time, CPU Utilisation, Throughput, and SLA Compliance.",
        "Classify tasks into Hard Real-Time, Soft Real-Time, and Non-Real-Time categories and analyse continuous emergency streams.",
        "Prevent race conditions and deadlocks using Mutex locks, Counting Semaphores, Two-Phase Holds, Resource Ordering, RAG, and Banker's Algorithm.",
    ]:
        add_bullet(obj)
    add_h2("Explicit Assumptions")
    for a in [
        "CPU burst and arrival times use normalised simulation ticks for fair cross-algorithm comparison.",
        "Single-core scheduling is benchmarked in the primary kernel; multi-core SMP extension is specified in Section 12.",
        "All hospital locations are real Kanakapura–Bengaluru coordinates paired with simulated bed counts; final clinical acceptance stays with hospital staff.",
    ]:
        add_bullet(a)

    add_h1("4. SYSTEM DESCRIPTION (10-HOSPITAL NETWORK)")
    add_body("Redline links Jain University Health Centre (HOSP-JAIN) with 9 receiving hospitals (DSH, RRM, BGS, APL, SGR, KNG, NAR, MNI, STJ) using explainable weighted matching (ETA 50%, Trust 20%, Freshness 15%, Load 15%) and live two-phase holds.")
    add_table(
        ["Aspect", "Manual Phone Process", "Redline OS-Based System"],
        [
            ["Hospital Discovery", "Sequential phone calls waste golden minutes.", "Filters and ranks all 9 receiving hospitals simultaneously."],
            ["Bed Availability", "Isolated notes go stale rapidly.", "Shared counting semaphores with freshness timestamps."],
            ["Bed Conflicts", "Two callers promised the same last bed.", "Mutex critical section + HTTP 409 version tokens."],
            ["Status Tracking", "No shared lifecycle visibility.", "5-state PCB tracker + parallel holds + escalation."],
        ],
        [1.5, 2.5, 2.9],
    )

    add_h1("5. REAL-WORLD TO OS MAPPING & ARCHITECTURE")
    add_table(
        ["Real-World Component", "Operating System Concept", "Justification in Redline"],
        [
            ["Cardiac arrest / trauma / stroke", "High-priority preemptive process (P1–P3)", "Immediately preempts running routine tasks."],
            ["OP / Lab / Pharmacy / Dialysis", "Medium/low-priority process (P4–P8)", "Queued in READY; protected from starvation by aging."],
            ["Central coordination server", "Kernel / CPU Scheduler", "Dispatches processes by active policy."],
            ["ICU beds / Ventilators", "Counting Semaphore (S = free units)", "wait(S) on hold; signal(S) on reject/timeout/release."],
            ["Concurrent last-bed claim", "Critical section / Race condition", "Mutex lock + optimistic version check."],
            ["Referral hold & hospital reply", "IPC Message Queue", "Non-blocking PREPARE hold puts PCB in WAITING."],
            ["Holds Bed, waits for Vent", "Deadlock (Circular Wait)", "Prevented by resource ordering; broken via RAG victim."],
        ],
        [2.0, 2.0, 2.9],
    )
    add_fig("fig1_architecture.png", "Figure 1. Redline layered architecture connecting UI, Flask API, 8-policy OS Kernel, and 10-hospital data store.")
    add_fig("fig2_dispatch_flowchart.png", "Figure 2. End-to-end hospital activity dispatch, duplicate check, scheduling, mutex reservation, and recovery flowchart.")

    add_h1("6. OS CONCEPTS, 5-STATE LIFECYCLE & REAL-TIME CLASSIFICATION")
    add_fig("fig3_process_states.png", "Figure 3. Five-state PCB lifecycle showing preemption and non-blocking WAITING during parallel holds.")
    add_table(
        ["Real-Time Class", "Hospital Platform Activities", "Reasoning"],
        [
            ["Hard Real-Time (Target)", "Cardiac Arrest (P1), Trauma (P2), ICU Telemetry (P2), Stroke (P3), Stat ABG Lab (P3)", "Missed SLA or double-booking risks patient safety."],
            ["Soft Real-Time", "Availability Sync (P4), ICU Epinephrine Stat (P4), Record Share (P5), OP Triage (P5)", "Prompt delivery expected; slight delay tolerable."],
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
    add_fig("fig4_gantt_charts.png", "Figure 4. Color-coded Gantt charts across FCFS, SJF, SRTF, Preemptive Priority, Round Robin (Q=3), and EDF.")

    for title, key in [
        ("7.1 First Come First Served (FCFS)", "fcfs"),
        ("7.2 Shortest Job First (SJF — Non-Preemptive)", "sjf"),
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
    add_fig("fig5_metrics_and_quantum.png", "Figure 5. 8-algorithm comparison bar chart and Round Robin Quantum sensitivity curve (Q=1..8).")

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
    add_fig("fig6_synchronization_two_phase.png", "Figure 7. Mutex critical section, two-phase hold, and 1,000-trial race proof.")
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
    add_body("Redline uses Preemptive Priority + Aging (-1 per 10 ticks) paired with EDF SLA deadline monitoring in normal mode, and switches Priority-1 requests to Surge FIFO + Capacity Load Balancing during mass-casualty surges.")
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
    add_fig("fig9_network_and_surge.png", "Figure 9. 10-hospital Kanakapura–Bengaluru network and 20-request P1 Surge FIFO distribution.")

    add_h1("12. RECOMMENDED ADDITIONAL FEATURES")
    for item in [
        "Multi-Core SMP Hospital CPU Scheduling & Processor Affinity across Emergency, ICU Telemetry, and Lab cores.",
        "Rate Monotonic Scheduling (RMS) for periodic ICU vitals monitoring with Liu–Layland utilisation checks.",
        "Persistent SQLite (WAL mode) + Server-Sent Events (SSE) real-time push streaming.",
        "Road-network Dijkstra/A* ambulance routing with live traffic weights.",
        "Real-time EDF admission control & HL7/FHIR interoperability stubs.",
    ]:
        add_bullet(item)

    add_h1("13. CONCLUSION & REFERENCES")
    add_body("Redline demonstrates that hospital emergency management and multi-hospital coordination map directly to OS abstractions. Preemptive Priority with Aging achieves 0.00-tick critical response without starvation, while mutex-protected semaphores, two-phase holds, resource ordering, RAG recovery, and Banker's Algorithm ensure safe resource allocation.")
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
