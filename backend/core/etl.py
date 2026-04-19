"""Incremental ETL utilities for QueryMind analytics."""
from __future__ import annotations

from dataclasses import dataclass

from django.db import connection, transaction
from django.utils import timezone


@dataclass(slots=True)
class EtlRunResult:
    """Summary of an ETL execution."""

    records_loaded: int
    last_processed_enrollment_id: int | None
    status: str
    message: str


def run_incremental_etl() -> EtlRunResult:
    """Load new enrollments into the analytics schema and record the run."""
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO etl_log (run_started_at, status, records_loaded, message)
                VALUES (%s, 'running', 0, 'Incremental ETL started')
                RETURNING id;
                """,
                [timezone.now()],
            )
            etl_log_id = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COALESCE(MAX(last_processed_enrollment_id), 0) FROM etl_log WHERE status = 'success';"
            )
            last_processed = cursor.fetchone()[0] or 0

            # Dimension upserts
            cursor.execute(
                """
                INSERT INTO analytics.dim_department (department_id, department_code, department_name)
                SELECT d.department_id, d.department_code, d.department_name
                FROM department AS d
                ON CONFLICT (department_id) DO UPDATE
                SET department_code = EXCLUDED.department_code,
                    department_name = EXCLUDED.department_name;
                """
            )
            cursor.execute(
                """
                INSERT INTO analytics.dim_time (semester_id, academic_year, term_name, start_date, end_date)
                SELECT sem.semester_id, sem.academic_year, sem.term_name, sem.start_date, sem.end_date
                FROM semester AS sem
                ON CONFLICT (semester_id) DO UPDATE
                SET academic_year = EXCLUDED.academic_year,
                    term_name = EXCLUDED.term_name,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date;
                """
            )
            cursor.execute(
                """
                INSERT INTO analytics.dim_course (course_id, course_code, course_title, credits, course_type)
                SELECT c.course_id, c.course_code, c.course_title, c.credits, c.course_type
                FROM course AS c
                ON CONFLICT (course_id) DO UPDATE
                SET course_code = EXCLUDED.course_code,
                    course_title = EXCLUDED.course_title,
                    credits = EXCLUDED.credits,
                    course_type = EXCLUDED.course_type;
                """
            )
            cursor.execute(
                """
                INSERT INTO analytics.dim_faculty (faculty_id, employee_code, full_name, designation, department_name)
                SELECT
                    f.faculty_id,
                    f.employee_code,
                    p.first_name || ' ' || p.last_name,
                    f.designation,
                    d.department_name
                FROM faculty AS f
                JOIN person AS p ON p.person_id = f.faculty_id
                JOIN department AS d ON d.department_id = f.department_id
                ON CONFLICT (faculty_id) DO UPDATE
                SET employee_code = EXCLUDED.employee_code,
                    full_name = EXCLUDED.full_name,
                    designation = EXCLUDED.designation,
                    department_name = EXCLUDED.department_name;
                """
            )
            cursor.execute(
                """
                INSERT INTO analytics.dim_student (
                    student_id,
                    roll_number,
                    full_name,
                    department_name,
                    program_level,
                    admission_year,
                    hostel_flag
                )
                SELECT
                    s.student_id,
                    s.roll_number,
                    p.first_name || ' ' || p.last_name,
                    d.department_name,
                    s.program_level,
                    EXTRACT(YEAR FROM s.admission_date)::INTEGER,
                    EXISTS (
                        SELECT 1
                        FROM hostel_allotment AS ha
                        WHERE ha.student_id = s.student_id
                          AND ha.status = 'active'
                    ) AS hostel_flag
                FROM student AS s
                JOIN person AS p ON p.person_id = s.student_id
                JOIN department AS d ON d.department_id = s.department_id
                ON CONFLICT (student_id) DO UPDATE
                SET roll_number = EXCLUDED.roll_number,
                    full_name = EXCLUDED.full_name,
                    department_name = EXCLUDED.department_name,
                    program_level = EXCLUDED.program_level,
                    admission_year = EXCLUDED.admission_year,
                    hostel_flag = EXCLUDED.hostel_flag;
                """
            )

            cursor.execute(
                """
                WITH payment_totals AS (
                    SELECT fi.student_id, fi.semester_id, COALESCE(SUM(fp.amount_paid), 0) AS fees_paid
                    FROM fee_invoice AS fi
                    LEFT JOIN fee_payment AS fp
                      ON fp.invoice_id = fi.invoice_id
                     AND fp.payment_status = 'success'
                    GROUP BY fi.student_id, fi.semester_id
                )
                INSERT INTO analytics.fact_enrollments (
                    enrollment_id,
                    student_key,
                    course_key,
                    faculty_key,
                    department_key,
                    time_key,
                    grade_points,
                    fees_paid,
                    attendance_pct
                )
                SELECT
                    e.enrollment_id,
                    ds.student_key,
                    dc.course_key,
                    df.faculty_key,
                    dd.department_key,
                    dt.time_key,
                    e.final_grade_points,
                    COALESCE(pt.fees_paid, 0),
                    e.attendance_pct
                FROM enrollment AS e
                JOIN section AS sec ON sec.section_id = e.section_id
                JOIN course AS c ON c.course_id = sec.course_id
                JOIN student AS s ON s.student_id = e.student_id
                JOIN analytics.dim_student AS ds ON ds.student_id = s.student_id
                JOIN analytics.dim_course AS dc ON dc.course_id = c.course_id
                JOIN analytics.dim_faculty AS df ON df.faculty_id = sec.faculty_id
                JOIN analytics.dim_department AS dd ON dd.department_id = s.department_id
                JOIN analytics.dim_time AS dt ON dt.semester_id = sec.semester_id
                LEFT JOIN payment_totals AS pt
                  ON pt.student_id = e.student_id
                 AND pt.semester_id = sec.semester_id
                WHERE e.enrollment_id > %s
                ON CONFLICT (enrollment_id) DO UPDATE
                SET grade_points = EXCLUDED.grade_points,
                    fees_paid = EXCLUDED.fees_paid,
                    attendance_pct = EXCLUDED.attendance_pct,
                    loaded_at = NOW()
                RETURNING enrollment_id;
                """,
                [last_processed],
            )
            loaded_rows = cursor.fetchall()
            records_loaded = len(loaded_rows)
            new_last_processed = max((row[0] for row in loaded_rows), default=last_processed or None)

            cursor.execute(
                """
                UPDATE etl_log
                SET status = 'success',
                    run_finished_at = NOW(),
                    records_loaded = %s,
                    last_processed_enrollment_id = %s,
                    message = 'Incremental ETL completed successfully'
                WHERE id = %s;
                """,
                [records_loaded, new_last_processed, etl_log_id],
            )

    return EtlRunResult(
        records_loaded=records_loaded,
        last_processed_enrollment_id=new_last_processed,
        status="success",
        message="Incremental ETL completed successfully",
    )
