"""Transactional workflows for QueryMind."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.db import connection, transaction


@dataclass(slots=True)
class EnrollmentRequest:
    """Inputs required for student enrollment."""

    student_id: int
    section_id: int
    semester_id: int
    tuition_amount: Decimal
    hostel_amount: Decimal = Decimal("0.00")


def enroll_student(request: EnrollmentRequest) -> None:
    """Atomically enroll a student, reserve a seat, and create a fee invoice."""
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;")
            cursor.execute(
                """
                SELECT sec.capacity, COUNT(e.enrollment_id) AS seats_taken
                FROM section AS sec
                LEFT JOIN enrollment AS e
                  ON e.section_id = sec.section_id
                 AND e.enrollment_status IN ('enrolled', 'completed')
                WHERE sec.section_id = %s
                GROUP BY sec.section_id, sec.capacity
                FOR UPDATE;
                """,
                [request.section_id],
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError("Section not found.")
            capacity, seats_taken = row
            if seats_taken >= capacity:
                raise ValueError("No seats available.")

            cursor.execute(
                """
                INSERT INTO enrollment (
                    student_id,
                    section_id,
                    enrollment_date,
                    enrollment_status
                ) VALUES (%s, %s, CURRENT_DATE, 'enrolled');
                """,
                [request.student_id, request.section_id],
            )

            total_amount = request.tuition_amount + request.hostel_amount
            cursor.execute(
                """
                INSERT INTO fee_invoice (
                    student_id,
                    semester_id,
                    invoice_number,
                    invoice_date,
                    tuition_amount,
                    hostel_amount,
                    scholarship_amount,
                    penalty_amount,
                    total_amount,
                    status,
                    due_date
                ) VALUES (
                    %s,
                    %s,
                    gen_random_uuid()::text,
                    CURRENT_DATE,
                    %s,
                    %s,
                    0,
                    0,
                    %s,
                    'unpaid',
                    CURRENT_DATE + INTERVAL '14 days'
                );
                """,
                [request.student_id, request.semester_id, request.tuition_amount, request.hostel_amount, total_amount],
            )


def submit_grade(exam_id: int, student_id: int, marks_obtained: Decimal, grade_letter: str, grade_points: Decimal) -> None:
    """Atomically submit a grade and update the enrollment summary."""
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;")
            cursor.execute(
                """
                INSERT INTO exam_result (exam_id, student_id, marks_obtained, grade_letter, evaluated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (exam_id, student_id)
                DO UPDATE SET
                    marks_obtained = EXCLUDED.marks_obtained,
                    grade_letter = EXCLUDED.grade_letter,
                    evaluated_at = EXCLUDED.evaluated_at;
                """,
                [exam_id, student_id, marks_obtained, grade_letter],
            )
            cursor.execute(
                """
                UPDATE enrollment AS e
                SET final_grade_letter = %s,
                    final_grade_points = %s
                FROM assessment AS a
                JOIN section AS sec ON sec.section_id = a.section_id
                WHERE a.assessment_id = %s
                  AND e.section_id = sec.section_id
                  AND e.student_id = %s;
                """,
                [grade_letter, grade_points, exam_id, student_id],
            )


def record_fee_payment(invoice_id: int, amount_paid: Decimal, payment_method: str, transaction_ref: str) -> None:
    """Atomically record a fee payment and update invoice status."""
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;")
            cursor.execute(
                """
                SELECT
                    fi.total_amount,
                    COALESCE(SUM(fp.amount_paid) FILTER (WHERE fp.payment_status = 'success'), 0) AS paid_so_far
                FROM fee_invoice AS fi
                LEFT JOIN fee_payment AS fp ON fp.invoice_id = fi.invoice_id
                WHERE fi.invoice_id = %s
                GROUP BY fi.invoice_id
                FOR UPDATE;
                """,
                [invoice_id],
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError("Invoice not found.")
            total_amount, paid_so_far = row
            outstanding = Decimal(total_amount) - Decimal(paid_so_far)
            if amount_paid > outstanding:
                raise ValueError("Payment exceeds outstanding amount.")

            cursor.execute(
                """
                INSERT INTO fee_payment (
                    invoice_id,
                    payment_date,
                    amount_paid,
                    payment_method,
                    transaction_ref,
                    payment_status
                ) VALUES (%s, NOW(), %s, %s, %s, 'success');
                """,
                [invoice_id, amount_paid, payment_method, transaction_ref],
            )

            new_paid_total = Decimal(paid_so_far) + amount_paid
            status = "paid" if new_paid_total >= Decimal(total_amount) else "partial"
            cursor.execute(
                "UPDATE fee_invoice SET status = %s WHERE invoice_id = %s;",
                [status, invoice_id],
            )

