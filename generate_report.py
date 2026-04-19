#!/usr/bin/env python3
"""Generate a comprehensive PDF report for the QueryMind project."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas
from datetime import datetime

# ── Colour palette ──────────────────────────────────────────────
DARK      = HexColor("#0f1117")
ACCENT    = HexColor("#3b82f6")
ACCENT2   = HexColor("#8b5cf6")
PINK      = HexColor("#ec4899")
GRAY_BG   = HexColor("#f8fafc")
GRAY_BD   = HexColor("#e2e8f0")
GRAY_TEXT = HexColor("#64748b")
DARK_TEXT = HexColor("#1e293b")
GREEN     = HexColor("#22c55e")
ORANGE    = HexColor("#f97316")
TEAL      = HexColor("#14b8a6")

W, H = A4


# ── Custom flowables ────────────────────────────────────────────
class GradientRect(Flowable):
    """A horizontal gradient rectangle used as a section divider."""
    def __init__(self, width, height, color_l, color_r):
        super().__init__()
        self.width = width
        self.height = height
        self.cl = color_l
        self.cr = color_r

    def draw(self):
        c = self.canv
        steps = 80
        sw = self.width / steps
        for i in range(steps):
            t = i / steps
            r = self.cl.red   + t * (self.cr.red   - self.cl.red)
            g = self.cl.green + t * (self.cr.green - self.cl.green)
            b = self.cl.blue  + t * (self.cr.blue  - self.cl.blue)
            c.setFillColorRGB(r, g, b)
            c.rect(i * sw, 0, sw + 1, self.height, stroke=0, fill=1)


class Badge(Flowable):
    """Small coloured badge (pill)."""
    def __init__(self, text, bg_color, text_color=white, font_size=8):
        super().__init__()
        self.text = text
        self.bg = bg_color
        self.tc = text_color
        self.fs = font_size
        self.width = len(text) * self.fs * 0.55 + 12
        self.height = self.fs + 8

    def draw(self):
        c = self.canv
        r = self.height / 2
        c.setFillColor(self.bg)
        c.roundRect(0, 0, self.width, self.height, r, stroke=0, fill=1)
        c.setFillColor(self.tc)
        c.setFont("Helvetica-Bold", self.fs)
        c.drawCentredString(self.width / 2, 4, self.text)


# ── Page templates ──────────────────────────────────────────────
def cover_page(c, doc):
    c.saveState()
    # Full-page dark background
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    # Gradient accent bar
    bar_y = H - 8 * mm
    for i in range(int(W)):
        t = i / W
        r = ACCENT.red   + t * (PINK.red   - ACCENT.red)
        g = ACCENT.green + t * (PINK.green - ACCENT.green)
        b = ACCENT.blue  + t * (PINK.blue  - ACCENT.blue)
        c.setFillColorRGB(r, g, b)
        c.rect(i, bar_y, 2, 8 * mm, stroke=0, fill=1)
    # Project name
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 52)
    c.drawCentredString(W / 2, H - 220, "QueryMind")
    # Tagline
    c.setFillColor(HexColor("#94a3b8"))
    c.setFont("Helvetica", 18)
    c.drawCentredString(W / 2, H - 260, "Natural Language to SQL  \u2022  Full-Stack Platform")
    # Divider line
    c.setStrokeColor(HexColor("#334155"))
    c.setLineWidth(0.5)
    c.line(W / 2 - 120, H - 290, W / 2 + 120, H - 290)
    # Meta info
    c.setFillColor(HexColor("#94a3b8"))
    c.setFont("Helvetica", 11)
    c.drawCentredString(W / 2, H - 320, "Comprehensive Project Report")
    c.setFont("Helvetica", 10)
    c.drawCentredString(W / 2, H - 342, f"Generated: {datetime.now().strftime('%B %d, %Y')}")
    # Tech badges row
    techs = ["Angular 18", "Django 5", "PostgreSQL 16", "Claude AI", "Docker", "AWS"]
    bw = 80
    start_x = W / 2 - (len(techs) * bw) / 2
    for i, t in enumerate(techs):
        x = start_x + i * bw
        c.setFillColor(HexColor("#1e293b"))
        c.roundRect(x, H - 400, bw - 8, 24, 12, stroke=0, fill=1)
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + (bw - 8) / 2, H - 393, t)
    # Bottom
    c.setFillColor(HexColor("#475569"))
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, 50, "University Management System  |  DBMS Portfolio Project")
    c.restoreState()


def later_pages(c, doc):
    c.saveState()
    # Header bar
    c.setFillColor(DARK)
    c.rect(0, H - 28, W, 28, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(30, H - 20, "QUERYMIND PROJECT REPORT")
    c.setFillColor(HexColor("#94a3b8"))
    c.setFont("Helvetica", 8)
    c.drawRightString(W - 30, H - 20, f"Page {doc.page}")
    # Accent line
    for i in range(int(W)):
        t = i / W
        r = ACCENT.red   + t * (PINK.red   - ACCENT.red)
        g = ACCENT.green + t * (PINK.green - ACCENT.green)
        b = ACCENT.blue  + t * (PINK.blue  - ACCENT.blue)
        c.setFillColorRGB(r, g, b)
        c.rect(i, H - 30, 2, 2, stroke=0, fill=1)
    # Footer
    c.setStrokeColor(GRAY_BD)
    c.setLineWidth(0.3)
    c.line(30, 35, W - 30, 35)
    c.setFillColor(GRAY_TEXT)
    c.setFont("Helvetica", 7)
    c.drawString(30, 22, "QueryMind \u2014 NL2SQL Platform")
    c.drawRightString(W - 30, 22, datetime.now().strftime("%Y-%m-%d"))
    c.restoreState()


# ── Styles ──────────────────────────────────────────────────────
styles = getSampleStyleSheet()

s_h1 = ParagraphStyle("H1", parent=styles["Heading1"],
    fontSize=22, leading=28, textColor=DARK_TEXT,
    spaceAfter=6, spaceBefore=18, fontName="Helvetica-Bold")

s_h2 = ParagraphStyle("H2", parent=styles["Heading2"],
    fontSize=15, leading=20, textColor=ACCENT,
    spaceAfter=4, spaceBefore=14, fontName="Helvetica-Bold")

s_h3 = ParagraphStyle("H3", parent=styles["Heading3"],
    fontSize=12, leading=16, textColor=ACCENT2,
    spaceAfter=3, spaceBefore=10, fontName="Helvetica-Bold")

s_body = ParagraphStyle("Body", parent=styles["Normal"],
    fontSize=9.5, leading=14, textColor=DARK_TEXT,
    alignment=TA_JUSTIFY, spaceAfter=6)

s_bullet = ParagraphStyle("Bullet", parent=s_body,
    leftIndent=18, bulletIndent=6, spaceBefore=2, spaceAfter=2)

s_code = ParagraphStyle("Code", parent=styles["Normal"],
    fontSize=8, leading=11, fontName="Courier",
    textColor=HexColor("#334155"), backColor=HexColor("#f1f5f9"),
    leftIndent=12, rightIndent=12, spaceBefore=4, spaceAfter=4,
    borderPadding=6)

s_caption = ParagraphStyle("Caption", parent=styles["Normal"],
    fontSize=8, textColor=GRAY_TEXT, alignment=TA_CENTER,
    spaceBefore=2, spaceAfter=8)


# ── Helper functions ────────────────────────────────────────────
def heading(text, level=1):
    st = {1: s_h1, 2: s_h2, 3: s_h3}[level]
    items = []
    if level == 1:
        items.append(Spacer(1, 6))
        items.append(GradientRect(W - 60, 3, ACCENT, PINK))
        items.append(Spacer(1, 2))
    items.append(Paragraph(text, st))
    return items

def body(text):
    return Paragraph(text, s_body)

def bullet(text):
    return Paragraph(f"\u2022  {text}", s_bullet)

def code(text):
    return Paragraph(text.replace("\n", "<br/>"), s_code)

def caption(text):
    return Paragraph(text, s_caption)

def spacer(h=8):
    return Spacer(1, h)

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=GRAY_BD,
                       spaceBefore=6, spaceAfter=6)

def make_table(headers, rows, col_widths=None):
    data = [headers] + rows
    if col_widths is None:
        col_widths = [(W - 80) / len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 8),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("LEADING",       (0, 0), (-1, -1), 12),
        ("BACKGROUND",    (0, 1), (-1, -1), white),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, GRAY_BG]),
        ("TEXTCOLOR",     (0, 1), (-1, -1), DARK_TEXT),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.4, GRAY_BD),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


# ── Build document ──────────────────────────────────────────────
def build():
    outpath = "/Users/apple/querymind/QueryMind_Project_Report.pdf"
    doc = SimpleDocTemplate(
        outpath, pagesize=A4,
        leftMargin=30, rightMargin=30,
        topMargin=45, bottomMargin=50,
    )
    story = []

    # ════════════════════════════════════════════════════════════
    # COVER  (blank frame – drawn by cover_page callback)
    # ════════════════════════════════════════════════════════════
    # Small spacer + PageBreak; actual cover is drawn by cover_page callback
    story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ════════════════════════════════════════════════════════════
    story += heading("Table of Contents")
    toc_items = [
        ("1", "Executive Summary"),
        ("2", "Technology Stack"),
        ("3", "System Architecture"),
        ("4", "Backend: Django REST API"),
        ("5", "Database Design"),
        ("6", "NL2SQL AI Engine"),
        ("7", "Frontend: Angular 18 SPA"),
        ("8", "Analytics & OLAP"),
        ("9", "Transaction Management"),
        ("10", "API Reference"),
        ("11", "DevOps & Deployment"),
        ("12", "Documentation & Phases"),
        ("13", "Project Statistics"),
    ]
    for num, title in toc_items:
        story.append(Paragraph(
            f'<font color="{ACCENT.hexval()}">{num}.</font>  {title}',
            ParagraphStyle("toc", parent=s_body, fontSize=11, leading=20,
                           leftIndent=20, textColor=DARK_TEXT)))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 1. EXECUTIVE SUMMARY
    # ════════════════════════════════════════════════════════════
    story += heading("1. Executive Summary")
    story.append(body(
        "<b>QueryMind</b> is a production-grade, full-stack Natural Language to SQL (NL2SQL) "
        "platform built around a University Management System demo database. It enables users "
        "to query a relational database using plain English, powered by Anthropic's Claude AI. "
        "The platform is designed as a comprehensive DBMS portfolio project that demonstrates "
        "mastery across the entire database syllabus: ER modeling, relational conversion, "
        "normalization (BCNF), SQL, joins, indexing, ACID transactions, OLAP analytics, ETL "
        "pipelines, and an AI-powered natural language interface."
    ))
    story.append(spacer(6))
    story.append(body(
        "The system features an animated Angular 18 frontend with Three.js particle effects, "
        "GSAP transitions, D3.js OLAP visualizations, and a Monaco SQL editor; a Django 5 REST "
        "API backend with schema-aware query generation, SQL validation, and rate-limited "
        "execution; and a PostgreSQL 16 database with both normalized OLTP and denormalized "
        "star-schema analytics layers."
    ))
    story.append(spacer(6))

    # Key highlights box
    highlights = [
        ["Natural Language Queries", "Ask questions in plain English; get validated SQL and live results instantly."],
        ["Schema-Aware AI", "Claude AI receives full database schema context for accurate SQL generation."],
        ["Interactive ER Diagrams", "Canvas-based entity-relationship diagrams with drag, zoom, and domain filtering."],
        ["OLAP Analytics Dashboard", "D3.js visualizations with ROLLUP, CUBE, and GROUPING SETS analytics."],
        ["ACID Transactions", "Serializable isolation for enrollment, grading, and payment workflows."],
        ["Production Deployment", "Docker Compose locally; AWS ECS Fargate, RDS, S3, CloudFront in production."],
    ]
    ht = make_table(
        ["Feature", "Description"],
        highlights,
        col_widths=[140, W - 80 - 140]
    )
    story.append(ht)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 2. TECHNOLOGY STACK
    # ════════════════════════════════════════════════════════════
    story += heading("2. Technology Stack")

    story += heading("2.1 Frontend", 2)
    fe_rows = [
        ["Angular", "18.2", "Core SPA framework with standalone components"],
        ["TypeScript", "5.5.4", "Type-safe application logic"],
        ["Three.js", "0.183.2", "WebGL particle background animations"],
        ["GSAP", "3.14.2", "Timeline-based UI transitions and animations"],
        ["D3.js", "7.9.0", "Custom SVG charts for OLAP analytics"],
        ["Monaco Editor", "0.55.1", "VS Code-quality SQL display and editing"],
        ["RxJS", "7.8.1", "Reactive streams and SSE handling"],
    ]
    story.append(make_table(["Library", "Version", "Purpose"], fe_rows,
                            col_widths=[100, 60, W - 80 - 160]))
    story.append(spacer(10))

    story += heading("2.2 Backend", 2)
    be_rows = [
        ["Python", "3.11+", "Runtime environment"],
        ["Django", "5.1.5", "Web framework"],
        ["Django REST Framework", "3.15.2", "RESTful API layer"],
        ["psycopg", "3.2.13", "PostgreSQL async driver (binary)"],
        ["Anthropic SDK", "0.49.0", "Claude AI integration for NL2SQL"],
        ["sqlparse", "0.5.3", "SQL parsing and safety validation"],
        ["Gunicorn", "23.0.0", "Production WSGI server"],
        ["Sentry SDK", "2.19.2", "Error tracking and monitoring"],
        ["SQLAlchemy", "2.0.36", "ORM for seed data generation"],
        ["Faker", "33.3.1", "Realistic test data generation"],
    ]
    story.append(make_table(["Technology", "Version", "Purpose"], be_rows,
                            col_widths=[120, 60, W - 80 - 180]))
    story.append(spacer(10))

    story += heading("2.3 Infrastructure", 2)
    infra_rows = [
        ["PostgreSQL", "16", "Primary OLTP + OLAP database"],
        ["Docker Compose", "Latest", "Local development orchestration"],
        ["Nginx", "1.27", "Reverse proxy and SPA serving"],
        ["AWS ECS Fargate", "-", "Serverless container hosting"],
        ["AWS RDS", "-", "Managed PostgreSQL"],
        ["AWS S3 + CloudFront", "-", "Static frontend hosting + CDN"],
        ["GitHub Actions", "-", "CI/CD pipelines"],
    ]
    story.append(make_table(["Technology", "Version", "Purpose"], infra_rows,
                            col_widths=[120, 60, W - 80 - 180]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 3. SYSTEM ARCHITECTURE
    # ════════════════════════════════════════════════════════════
    story += heading("3. System Architecture")
    story.append(body(
        "QueryMind follows a classic three-tier architecture with a clear separation between "
        "the presentation layer (Angular SPA), application layer (Django REST API), and data "
        "layer (PostgreSQL). Communication flows through a RESTful API with JSON payloads, "
        "supplemented by Server-Sent Events (SSE) for real-time token streaming during AI "
        "query generation."
    ))
    story.append(spacer(8))

    story += heading("3.1 Project Directory Structure", 2)
    dirs = [
        [".github/workflows/", "CI/CD pipeline definitions (ci.yml, deploy.yml)"],
        ["backend/core/", "Core Django app: models, views, services, NL2SQL engine"],
        ["backend/querymind_api/", "Django project settings (base, local, production)"],
        ["backend/sql/ddl/", "Database DDL scripts (schema, views, indexes)"],
        ["backend/sql/warehouse/", "Star schema and OLAP query definitions"],
        ["backend/sql/seeds/", "Data generation scripts (SQLAlchemy + Faker)"],
        ["frontend/src/app/", "Angular standalone AppComponent (ts, html, css)"],
        ["frontend/src/assets/", "Static assets"],
        ["frontend/src/environments/", "Angular environment configurations"],
        ["infrastructure/", "AWS setup scripts and IAM policies"],
        ["docs/", "8-phase DBMS documentation"],
        ["db/", "Docker entrypoint SQL initialization files"],
    ]
    story.append(make_table(["Directory", "Purpose"], dirs,
                            col_widths=[150, W - 80 - 150]))
    story.append(spacer(8))

    story += heading("3.2 Data Flow", 2)
    flow_steps = [
        "User types a natural language question in the Angular frontend.",
        "Frontend sends POST /api/query with the question; SSE stream opens for thinking overlay.",
        "Django view invokes the NL2SQL Agent, which serializes the live database schema.",
        "Agent retrieves similar past queries for few-shot prompting context.",
        "Claude AI (claude-sonnet-4-20250514) generates SQL with schema awareness.",
        "sqlparse validates the SQL; destructive statements are rejected.",
        "Validated SQL executes in a read-only PostgreSQL transaction.",
        "Results, explanation, and metadata return to the frontend as JSON.",
        "Frontend renders results in a data table, Monaco editor, and optional chart.",
        "Query is logged to QueryLog for history, metrics, and future few-shot retrieval.",
    ]
    for i, step in enumerate(flow_steps, 1):
        story.append(Paragraph(
            f'<font color="{ACCENT.hexval()}"><b>Step {i}.</b></font>  {step}',
            ParagraphStyle("step", parent=s_body, leftIndent=18, spaceBefore=2, spaceAfter=2)))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 4. BACKEND – DJANGO REST API
    # ════════════════════════════════════════════════════════════
    story += heading("4. Backend: Django REST API")

    story += heading("4.1 Django Models", 2)
    story.append(body(
        "The backend uses two lightweight Django models for operational tracking, while the "
        "rich university schema lives directly in PostgreSQL (managed via raw DDL scripts)."
    ))
    models_rows = [
        ["QueryLog", "Stores every NL query attempt: input text, generated SQL, execution status, "
                     "timing, row count, explanation, and error details."],
        ["EtlLog", "Tracks analytics ETL pipeline runs: status, records loaded, "
                   "start/finish timestamps, and error messages."],
    ]
    story.append(make_table(["Model", "Description"], models_rows,
                            col_widths=[100, W - 80 - 100]))
    story.append(spacer(8))

    story += heading("4.2 Core Services", 2)
    services = [
        ["get_schema_payload()", "Returns tables, columns, constraints, relationships, and insertable tables for the frontend schema browser."],
        ["get_table_intelligence()", "Per-table analytics: row count, null rates, indexes, sample rows, and suggested queries."],
        ["get_relationship_preview()", "Sample joined rows for a foreign key relationship (interactive ER preview)."],
        ["insert_record()", "Safely inserts into whitelisted tables with input validation."],
        ["execute_demo_sql()", "Deterministic demo query execution (no AI involved)."],
        ["generate_demo_query()", "Heuristic local SQL generator as fallback when AI is unavailable."],
        ["extract_limit()", "Parses row limits from natural language ('top 10' -> 10, 'twenty five' -> 25)."],
    ]
    story.append(make_table(["Function", "Description"], services,
                            col_widths=[145, W - 80 - 145]))
    story.append(spacer(8))

    story += heading("4.3 Configuration", 2)
    story.append(body(
        "Django settings are split across <b>base.py</b> (shared), <b>local.py</b> (development), "
        "and <b>production.py</b> (AWS). Key configuration includes:"
    ))
    config_items = [
        "PostgreSQL connection via psycopg3 with connection pooling",
        "CORS whitelist: localhost:4200, localhost:80, 127.0.0.1",
        "REST Framework: JSON-only renderer, custom rate throttling",
        "Sentry SDK integration for production error tracking",
        "No authentication layer (open API with rate limiting for portfolio demo)",
        "Environment variables for secrets (DJANGO_SECRET_KEY, ANTHROPIC_API_KEY)",
    ]
    for item in config_items:
        story.append(bullet(item))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 5. DATABASE DESIGN
    # ════════════════════════════════════════════════════════════
    story += heading("5. Database Design")

    story += heading("5.1 OLTP Schema (20 Entities)", 2)
    story.append(body(
        "The normalized OLTP schema models a complete university management system with "
        "entities spanning academic, financial, and housing domains. The design includes "
        "ISA hierarchies (Person -> Student/Faculty/Staff, Assessment -> Exam/Assignment), "
        "weak entities with composite keys, and comprehensive constraints."
    ))
    story.append(spacer(6))

    entities = [
        ["Department", "40", "Master", "Academic unit with budget, office, and contact info. PK: department_id."],
        ["Person", "~1,000", "Supertype", "Base entity with ISA hierarchy. Type discriminator: person_type (student/faculty/staff)."],
        ["Student", "~600", "Entity", "Subtype of Person. Roll number, CGPA, program level, admission status."],
        ["Faculty", "~80", "Entity", "Subtype of Person. Employee code, designation, salary, specialization."],
        ["Staff", "~100", "Entity", "Subtype of Person. Job title, department assignment (nullable for central admin)."],
        ["Semester", "~20", "Master", "Academic periods: Monsoon, Winter, Summer terms with date ranges."],
        ["Course", "~60", "Entity", "Courses with credits (1-6), levels (100-900), types (core/elective/lab/seminar)."],
        ["Course_Prerequisite", "-", "Weak", "Composite PK (course_id, prerequisite_course_id). Self-ref prevented."],
        ["Section", "~200", "Transaction", "Course offering per semester. Capacity, delivery mode, schedule pattern."],
        ["Enrollment", "~2,000", "Transaction", "Student-section registration. Grades, attendance, status tracking."],
        ["Assessment", "~600", "Weak", "Base for Exam/Assignment ISA. Type, max marks, weightage percentage."],
        ["Exam", "-", "Subtype", "Mode (offline/online), date, duration, hall assignment."],
        ["Assignment", "-", "Subtype", "Release date, submission mode, max attempts."],
        ["Exam_Result", "-", "Weak", "Composite PK (exam_id, student_id). Marks, grade letter, remarks."],
        ["Assignment_Submission", "-", "Weak", "Composite PK (assignment_id, student_id, attempt_no). Score, feedback."],
        ["Fee_Invoice", "~3,000", "Transaction", "Per-student per-semester billing. Tuition, hostel, scholarship amounts."],
        ["Fee_Payment", "~3,000", "Transaction", "Payment records. Method (UPI/card/netbanking/cash), status tracking."],
        ["Hostel", "~10", "Master", "Residential facilities. Type (boys/girls/mixed), capacity, warden."],
        ["Hostel_Room", "~200", "Weak", "Rooms within hostels. Floor, bed capacity, room type."],
        ["Hostel_Allotment", "~800", "Transaction", "Student room assignments per semester with date ranges."],
    ]
    story.append(make_table(
        ["Entity", "Est. Rows", "Kind", "Description"],
        entities,
        col_widths=[105, 55, 65, W - 80 - 225]
    ))
    story.append(spacer(8))

    story += heading("5.2 Constraints & Integrity", 2)
    constraint_items = [
        "<b>Foreign Keys:</b> ON DELETE CASCADE for ISA subtypes, ON DELETE RESTRICT for business references.",
        "<b>CHECK Constraints:</b> Enum validation (person_type, delivery_mode, payment_method), numeric ranges (credits 1-6, level 100-900).",
        "<b>UNIQUE Constraints:</b> Business keys (roll_number, employee_code, course_code, invoice UUID, transaction_ref).",
        "<b>Date Validation:</b> end_date > start_date enforced on semesters and allotments.",
        "<b>Composite Keys:</b> Weak entities use multi-column primary keys (exam_id + student_id, etc.).",
    ]
    for item in constraint_items:
        story.append(bullet(item))
    story.append(spacer(8))

    story += heading("5.3 Database Views", 2)
    views_rows = [
        ["student_transcript", "Full enrollment history: student info, course, semester, grades, attendance percentage."],
        ["faculty_load", "Sections taught per faculty per semester with total capacity."],
        ["department_summary", "Aggregate department stats: student count, faculty count, course count, average CGPA."],
    ]
    story.append(make_table(["View Name", "Description"], views_rows,
                            col_widths=[130, W - 80 - 130]))
    story.append(spacer(8))

    story += heading("5.4 Analytics Star Schema", 2)
    story.append(body(
        "A denormalized star schema in the <b>analytics</b> namespace supports OLAP workloads "
        "without impacting OLTP performance."
    ))
    star_rows = [
        ["dim_department", "Dimension", "department_id, code, name"],
        ["dim_student", "Dimension", "student_id, roll_number, full_name, department, program_level, hostel_flag"],
        ["dim_faculty", "Dimension", "faculty_id, employee_code, full_name, designation, department"],
        ["dim_course", "Dimension", "course_id, code, title, credits, type"],
        ["dim_time", "Dimension", "semester_id, academic_year, term_name, start/end dates"],
        ["fact_enrollments", "Fact", "enrollment_id, dimension keys, grade_points, fees_paid, attendance_pct"],
    ]
    story.append(make_table(["Table", "Type", "Key Columns"], star_rows,
                            col_widths=[120, 70, W - 80 - 190]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 6. NL2SQL AI ENGINE
    # ════════════════════════════════════════════════════════════
    story += heading("6. NL2SQL AI Engine")
    story.append(body(
        "The NL2SQL engine is the core intelligence of QueryMind, translating natural language "
        "questions into validated, safe SQL queries using Anthropic's Claude AI."
    ))
    story.append(spacer(6))

    story += heading("6.1 Architecture (NL2SQLAgent)", 2)
    agent_steps = [
        ["Schema Serialization", "Introspects PostgreSQL information_schema to build a live snapshot of all tables, columns, constraints, foreign keys, and views. This ensures the AI always has accurate, up-to-date schema context."],
        ["Few-Shot Retrieval", "Searches past successful queries using sequence matching to find similar questions. These are injected into the prompt as examples, improving accuracy over time."],
        ["AI Generation", "Sends the schema context, similar examples, and user question to Claude (claude-sonnet-4-20250514, 800 max tokens). The system prompt includes safety rules and output format instructions."],
        ["SQL Validation", "Uses sqlparse to verify SQL structure. Rejects destructive statements: DROP, TRUNCATE, ALTER, INSERT, UPDATE, DELETE (without WHERE clause)."],
        ["Safe Execution", "Runs validated SQL in a read-only PostgreSQL transaction path."],
        ["Retry Logic", "If execution fails, the error message is fed back to Claude for auto-correction (configurable retry count)."],
    ]
    story.append(make_table(["Stage", "Description"], agent_steps,
                            col_widths=[120, W - 80 - 120]))
    story.append(spacer(8))

    story += heading("6.2 Safety Measures", 2)
    safety = [
        "SQL parsed and validated via sqlparse before any execution",
        "Destructive keywords (DROP, TRUNCATE, ALTER) are blocked at the validation layer",
        "DELETE/UPDATE without WHERE clause rejected",
        "Read-only transaction mode for all AI-generated queries",
        "Rate throttling: 10 queries per minute per IP address",
        "Query timeout limits to prevent long-running operations",
        "No authentication bypass \u2014 open API by design with strict validation",
    ]
    for s in safety:
        story.append(bullet(s))
    story.append(spacer(8))

    story += heading("6.3 Streaming & UX", 2)
    story.append(body(
        "The frontend subscribes to an SSE (Server-Sent Events) endpoint at <b>/api/query/stream</b> "
        "to receive token-by-token updates during AI generation. This powers a 3-stage thinking "
        "overlay animation: Schema Analysis -> SQL Generation -> Execution. Tokens are throttled "
        "at 40ms intervals for smooth visual feedback."
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 7. FRONTEND
    # ════════════════════════════════════════════════════════════
    story += heading("7. Frontend: Angular 18 SPA")

    story += heading("7.1 Application Tabs", 2)
    tabs_rows = [
        ["Query", "Natural language input, example chips, chat thread, thinking overlay, results table, Monaco SQL editor, chart visualization, EXPLAIN plan, auto-repair."],
        ["History", "Paginated query logs with status filtering (all/success/failed). Click to re-hydrate a past query."],
        ["Analytics", "D3.js OLAP dashboard: department bar chart, enrollment trend area chart, course mix donut chart, query activity heatmap."],
        ["ER Diagram", "Canvas-based interactive entity-relationship diagrams with domain filtering (academic/finance/housing/all), drag nodes, zoom/pan, relationship preview."],
        ["Schema Browser", "Searchable table list with column details, constraint badges, domain/entity classification. Intelligence panel (row counts, null rates, indexes, samples). Insert form for data entry."],
        ["Settings", "Theme selection (dark/light/oled/sepia), motion reduction toggle, tour reset, DDL viewer."],
    ]
    story.append(make_table(["Tab", "Features"], tabs_rows,
                            col_widths=[85, W - 80 - 85]))
    story.append(spacer(8))

    story += heading("7.2 Visual Design", 2)
    design_items = [
        "<b>Theme:</b> Modern dark UI with electric blue accents and neon pink highlights. Four theme options: dark, light, OLED, and sepia.",
        "<b>Landing Page:</b> Hero section with Three.js particle canvas background, gradient text, and feature strip cards.",
        "<b>Transitions:</b> GSAP-driven tab switches, launch wipe animation, chat scroll, and thinking overlay stage progression.",
        "<b>Custom Cursor:</b> Halo effect that follows mouse movement across the application.",
        "<b>Responsive:</b> CSS Grid and Flexbox layout with reduced-motion support (prefers-reduced-motion media query).",
        "<b>Toast System:</b> Top-right notification toasts with auto-dismiss for user feedback.",
    ]
    for item in design_items:
        story.append(bullet(item))
    story.append(spacer(8))

    story += heading("7.3 Key Capabilities", 2)
    cap_items = [
        "<b>Voice Input:</b> Web Speech API integration for dictating queries via microphone.",
        "<b>Text-to-Speech:</b> Speak query explanations aloud using the SpeechSynthesis API.",
        "<b>Command Palette:</b> Cmd+K shortcut opens a command palette for quick navigation.",
        "<b>Keyboard Shortcuts:</b> Cmd+Enter to submit, Escape to close modals, full keyboard accessibility.",
        "<b>Share Links:</b> Generate shareable URLs for specific query results.",
        "<b>CSV Export:</b> One-click export of query results to CSV files.",
        "<b>97 Example Queries:</b> Predefined examples grouped by topic (students, faculty, courses, finance, hostel, advanced).",
    ]
    for item in cap_items:
        story.append(bullet(item))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 8. ANALYTICS & OLAP
    # ════════════════════════════════════════════════════════════
    story += heading("8. Analytics & OLAP")
    story.append(body(
        "QueryMind includes a full analytics layer demonstrating advanced SQL aggregation "
        "techniques against the star schema warehouse."
    ))
    story.append(spacer(6))

    olap_rows = [
        ["ROLLUP Query", "Hierarchical grade point aggregation: department -> semester -> grand total. Uses GROUPING() function for level detection."],
        ["Department Performance", "Per-department metrics: enrollment count, average grade points, attendance rates."],
        ["Term Trends", "Semester-over-semester enrollment and grade trends as time-series data."],
        ["Faculty Impact", "Faculty contribution analysis: enrollment counts and grade distributions."],
        ["Course Mix", "Enrollment distribution by course type (core/elective/lab/seminar)."],
        ["Query Activity", "Hourly distribution of API query usage from QueryLog timestamps."],
    ]
    story.append(make_table(["Query", "Description"], olap_rows,
                            col_widths=[120, W - 80 - 120]))
    story.append(spacer(8))

    story += heading("8.1 ETL Pipeline", 2)
    story.append(body(
        "An incremental ETL pipeline (<b>run_incremental_etl()</b>) loads new enrollments "
        "into the analytics star schema. It operates with SERIALIZABLE isolation, performs "
        "dimension upserts (department, time, course, faculty, student), loads fact rows, "
        "and tracks the last processed enrollment ID for incremental runs. Each run is logged "
        "to the EtlLog model with status, record counts, and timing."
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 9. TRANSACTION MANAGEMENT
    # ════════════════════════════════════════════════════════════
    story += heading("9. Transaction Management")
    story.append(body(
        "QueryMind demonstrates ACID transaction management with three carefully designed "
        "transactional workflows, each using appropriate PostgreSQL isolation levels."
    ))
    story.append(spacer(6))

    tx_rows = [
        ["enroll_student()", "SERIALIZABLE", "Checks section capacity with SELECT FOR UPDATE, inserts enrollment record, creates fee invoice. Prevents over-enrollment via row-level locking."],
        ["submit_grade()", "REPEATABLE READ", "Upserts exam result, updates enrollment grade fields. Consistent read snapshot prevents phantom reads during grade calculation."],
        ["record_fee_payment()", "SERIALIZABLE", "Validates outstanding balance, records payment, updates invoice status. Full serializability prevents double-payment race conditions."],
    ]
    story.append(make_table(
        ["Function", "Isolation Level", "Behavior"],
        tx_rows,
        col_widths=[115, 95, W - 80 - 210]
    ))
    story.append(spacer(8))
    story.append(body(
        "All transactions use atomic blocks with appropriate isolation. The enrollment "
        "transaction uses SELECT FOR UPDATE to acquire row-level locks on sections, preventing "
        "concurrent over-enrollment. The payment transaction uses full serializability to "
        "prevent race conditions where two payments could exceed the outstanding balance."
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 10. API REFERENCE
    # ════════════════════════════════════════════════════════════
    story += heading("10. API Reference")

    api_rows = [
        ["GET", "/api/", "API index with available endpoints"],
        ["GET", "/api/health", "Health check / smoke test"],
        ["GET", "/api/schema", "Compact schema for frontend (tables, columns, constraints, relationships)"],
        ["GET", "/api/schema/intelligence?table_name=X", "Table stats: row count, null rates, indexes, samples, query suggestions"],
        ["GET", "/api/schema/relationship-preview?...", "Sample joined rows for a foreign key relationship"],
        ["POST", "/api/query", "Generate and execute NL query (rate limited: 10/min)"],
        ["GET", "/api/query/stream", "SSE stream of token generation for thinking overlay"],
        ["POST", "/api/query/explain", "EXPLAIN (FORMAT JSON) for a SQL string"],
        ["POST", "/api/query/fixit", "Auto-repair failing SQL using Claude"],
        ["GET", "/api/history", "Paginated query history (10 per page)"],
        ["GET", "/api/history/<id>", "Single query log detail (share link hydration)"],
        ["GET", "/api/metrics", "Aggregated metrics: total queries, success rate, latency stats"],
        ["GET", "/api/analytics/rollup", "OLAP rollup data for dashboard charts"],
        ["POST", "/api/admin/etl/run", "Trigger incremental ETL pipeline"],
        ["POST", "/api/records/insert", "Insert record into whitelisted table"],
    ]
    story.append(make_table(
        ["Method", "Endpoint", "Description"],
        api_rows,
        col_widths=[45, 185, W - 80 - 230]
    ))
    story.append(spacer(8))

    story += heading("10.1 Rate Limiting", 2)
    story.append(body(
        "A custom <b>QueryRateThrottle</b> (extending DRF's SimpleRateThrottle) limits query "
        "generation to <b>10 requests per minute per IP address</b>. This is cache-based and "
        "applies only to the /api/query endpoint to prevent API abuse while keeping other "
        "endpoints freely accessible."
    ))
    story.append(spacer(8))

    story += heading("10.2 Serializers", 2)
    ser_rows = [
        ["QueryRequestSerializer", "Accepts natural_language (required) and prior_sql (optional, for query refinement)."],
        ["InsertRecordSerializer", "Accepts table_name and record dict for safe data insertion."],
        ["QueryLogSerializer", "Full query history with all metadata fields."],
        ["EtlLogSerializer", "ETL run metadata with timing and status."],
    ]
    story.append(make_table(["Serializer", "Description"], ser_rows,
                            col_widths=[145, W - 80 - 145]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 11. DEVOPS & DEPLOYMENT
    # ════════════════════════════════════════════════════════════
    story += heading("11. DevOps & Deployment")

    story += heading("11.1 Docker Compose (Local)", 2)
    docker_rows = [
        ["postgres", "postgres:16", "PostgreSQL database with persistent volume. Health check via pg_isready. Init scripts from /db/sql/."],
        ["django", "./backend", "Django API with Gunicorn (2 workers, 4 threads) on port 8000. Depends on postgres health."],
        ["nginx", "./frontend", "Multi-stage build: Node 20 (Angular build) + Nginx 1.27 (serve). Proxies /api/ to django:8000. Port 80."],
    ]
    story.append(make_table(
        ["Service", "Image/Build", "Details"],
        docker_rows,
        col_widths=[65, 90, W - 80 - 155]
    ))
    story.append(spacer(8))

    story += heading("11.2 CI/CD Pipelines", 2)
    story.append(body("<b>CI Pipeline (ci.yml)</b> \u2014 Runs on PR and push to main:"))
    ci_items = [
        "Backend: Python 3.11, pip install, django check",
        "Frontend: Node 20, npm ci, Angular production build",
        "Docker: Validate docker-compose config",
    ]
    for item in ci_items:
        story.append(bullet(item))
    story.append(spacer(4))
    story.append(body("<b>Deploy Pipeline (deploy.yml)</b> \u2014 Push to main or manual dispatch:"))
    deploy_items = [
        "Assume AWS IAM role via OIDC",
        "Build and push backend image to ECR",
        "Build frontend and sync to S3 bucket",
        "Invalidate CloudFront distribution cache",
        "Force ECS Fargate service redeployment",
    ]
    for item in deploy_items:
        story.append(bullet(item))
    story.append(spacer(8))

    story += heading("11.3 AWS Production Architecture", 2)
    aws_rows = [
        ["ECS Fargate", "Serverless container hosting for Django API"],
        ["RDS PostgreSQL", "Managed database with automated backups"],
        ["S3", "Static hosting for Angular build artifacts"],
        ["CloudFront", "CDN for frontend with edge caching"],
        ["Route 53", "DNS management and domain routing"],
        ["Secrets Manager", "Production secrets (Django key, Anthropic key, DB password)"],
        ["CloudWatch", "Logging and monitoring"],
        ["ECR", "Docker image registry for backend"],
    ]
    story.append(make_table(["Service", "Purpose"], aws_rows,
                            col_widths=[120, W - 80 - 120]))
    story.append(spacer(8))

    story += heading("11.4 Environment Variables", 2)
    env_rows = [
        ["DJANGO_SECRET_KEY", "Django cryptographic signing key"],
        ["DJANGO_DEBUG", "Debug mode toggle (0 in production)"],
        ["ANTHROPIC_API_KEY", "Claude AI API key for NL2SQL"],
        ["POSTGRES_DB", "Database name (default: querymind)"],
        ["POSTGRES_USER", "Database user"],
        ["POSTGRES_PASSWORD", "Database password"],
        ["POSTGRES_HOST", "Database host (postgres in Docker, RDS endpoint in prod)"],
        ["POSTGRES_PORT", "Database port (default: 5432)"],
        ["SENTRY_DSN", "Sentry error tracking endpoint"],
    ]
    story.append(make_table(["Variable", "Description"], env_rows,
                            col_widths=[145, W - 80 - 145]))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 12. DOCUMENTATION PHASES
    # ════════════════════════════════════════════════════════════
    story += heading("12. Documentation & DBMS Phases")
    story.append(body(
        "The project documentation is organized into 8 phases covering the complete DBMS "
        "curriculum, available in the /docs/ directory."
    ))
    story.append(spacer(6))

    phases_rows = [
        ["Phase 1", "ER & Relational Design", "ER diagram (20 entities, 2 ISA hierarchies), relational schema conversion, normalization audit (BCNF), DDL walkthrough, seed data strategy."],
        ["Phase 2", "Demo Queries", "30+ curated SQL examples demonstrating joins, aggregations, subqueries, window functions, and common query patterns."],
        ["Phase 3", "Star Schema & OLAP", "Fact/dimension design rationale, denormalization decisions, ROLLUP, CUBE, and GROUPING SETS examples with explanations."],
        ["Phase 4", "Transaction Management", "ACID properties in context, isolation levels (SERIALIZABLE, REPEATABLE READ, READ COMMITTED), deadlock analysis."],
        ["Phase 5", "Agent & Learning Layer", "NL2SQL architecture, Claude integration design, schema serialization strategy, few-shot learning from query history."],
        ["Phase 6-7", "API & Frontend", "REST endpoint specifications, Angular component architecture, UI/UX decisions (GSAP, Three.js, D3, Monaco)."],
        ["Phase 8", "Resume & Interview", "2-minute presentation script, resume bullet points, architectural decision rationale for interviews."],
    ]
    story.append(make_table(
        ["Phase", "Title", "Content"],
        phases_rows,
        col_widths=[50, 120, W - 80 - 170]
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════
    # 13. PROJECT STATISTICS
    # ════════════════════════════════════════════════════════════
    story += heading("13. Project Statistics")

    stats_rows = [
        ["Database Tables", "20 OLTP entities + 6 star schema tables"],
        ["Database Views", "3 (student_transcript, faculty_load, department_summary)"],
        ["API Endpoints", "15 RESTful endpoints"],
        ["Example Queries", "97 predefined NL query examples"],
        ["Frontend Tabs", "6 (Query, History, Analytics, ER Diagram, Schema, Settings)"],
        ["Themes", "4 (Dark, Light, OLED, Sepia)"],
        ["AI Model", "claude-sonnet-4-20250514 (800 max tokens)"],
        ["Docker Services", "3 (PostgreSQL, Django, Nginx)"],
        ["CI/CD Pipelines", "2 (CI validation, Production deploy)"],
        ["AWS Services Used", "8 (ECS, RDS, S3, CloudFront, Route 53, Secrets Manager, CloudWatch, ECR)"],
        ["Est. Seed Data Rows", "~8,000+ across all tables"],
        ["OLAP Query Types", "6 (ROLLUP, Department, Trend, Faculty, Course Mix, Activity)"],
        ["Transaction Workflows", "3 (Enrollment, Grading, Payment)"],
        ["Documentation Phases", "8 covering complete DBMS curriculum"],
    ]
    story.append(make_table(["Metric", "Value"], stats_rows,
                            col_widths=[145, W - 80 - 145]))
    story.append(spacer(12))

    story += heading("13.1 Key Architectural Decisions", 2)
    decisions = [
        "<b>Single Angular Component:</b> Monolithic AppComponent (~1000 lines) for simplicity in a demo/portfolio context, avoiding over-engineering.",
        "<b>No Authentication:</b> Open API with rate limiting instead of JWT/sessions \u2014 appropriate for a portfolio showcase.",
        "<b>Dynamic Schema Introspection:</b> Live information_schema queries vs. hardcoded ORM models ensures AI always sees current state.",
        "<b>Few-Shot Learning:</b> Similarity-based query history retrieval improves AI accuracy over time without fine-tuning.",
        "<b>SSE Streaming:</b> Token-by-token thinking overlay with 40ms throttle for engaging visual feedback.",
        "<b>Separate Star Schema:</b> Dedicated analytics namespace prevents expensive OLAP joins from impacting OLTP performance.",
        "<b>GSAP over CSS Animations:</b> Timeline-based, interruptible transitions for complex animation sequences.",
        "<b>D3 over Chart.js:</b> Custom SVG rendering for fine-grained OLAP visualization control.",
        "<b>Monaco Editor:</b> VS Code-quality SQL display reinforces the 'serious tool' aesthetic.",
        "<b>Docker Compose Override:</b> Local dev credentials embedded; production uses AWS Secrets Manager.",
    ]
    for d in decisions:
        story.append(bullet(d))
    story.append(spacer(16))

    # ── Closing ─────────────────────────────────────────────────
    story.append(hr())
    story.append(spacer(4))
    story.append(Paragraph(
        "This report was auto-generated from the QueryMind source code and project documentation.",
        ParagraphStyle("footer_note", parent=s_body, fontSize=8,
                       textColor=GRAY_TEXT, alignment=TA_CENTER)))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}",
        ParagraphStyle("footer_date", parent=s_body, fontSize=8,
                       textColor=GRAY_TEXT, alignment=TA_CENTER)))

    # ── Build ───────────────────────────────────────────────────
    doc.build(story, onFirstPage=cover_page, onLaterPages=later_pages)
    print(f"Report generated: {outpath}")


if __name__ == "__main__":
    build()
