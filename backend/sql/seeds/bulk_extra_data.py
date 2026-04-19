"""Append large demo data volume for QueryMind.

This script adds 1000 records to each QueryMind domain table where that is
valid for the relational model. Framework tables such as Django auth,
sessions, migrations, and derived analytics tables are intentionally skipped.
Run the ETL endpoint after this script to refresh analytics facts.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from faker import Faker
from sqlalchemy import create_engine, text


EXTRA_PER_TABLE = 1000
fake = Faker("en_IN")


@dataclass(slots=True)
class DbConfig:
    db_name: str
    user: str
    password: str
    host: str
    port: int

    @property
    def url(self) -> str:
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"


def get_db_config() -> DbConfig:
    return DbConfig(
        db_name=os.getenv("POSTGRES_DB", "querymind"),
        user=os.getenv("POSTGRES_USER", "querymind"),
        password=os.getenv("POSTGRES_PASSWORD", "querymind"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
    )


def random_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def insert_person(conn, person_type: str, token: str, index: int) -> int:
    first_name = fake.first_name()
    last_name = fake.last_name()
    return int(
        conn.execute(
            text(
                """
                INSERT INTO person (
                    first_name, last_name, date_of_birth, gender, email, phone,
                    address_line, city, state, postal_code, person_type
                ) VALUES (
                    :first_name, :last_name, :dob, :gender, :email, :phone,
                    :address_line, :city, :state, :postal_code, :person_type
                )
                RETURNING person_id;
                """
            ),
            {
                "first_name": first_name,
                "last_name": last_name,
                "dob": fake.date_of_birth(minimum_age=18, maximum_age=62),
                "gender": random.choice(["Male", "Female"]),
                "email": f"{person_type}.{token}.{index}@querymind.local",
                "phone": fake.phone_number()[:20],
                "address_line": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "postal_code": fake.postcode(),
                "person_type": person_type,
            },
        ).scalar_one()
    )


def seed_departments(conn, token: str) -> list[int]:
    ids: list[int] = []
    for index in range(EXTRA_PER_TABLE):
        ids.append(
            int(
                conn.execute(
                    text(
                        """
                        INSERT INTO department (
                            department_code, department_name, office_phone, office_email, building_name, budget
                        ) VALUES (
                            :code, :name, :phone, :email, :building, :budget
                        )
                        RETURNING department_id;
                        """
                    ),
                    {
                        "code": f"XD{token}{index:04d}"[:20],
                        "name": f"Extended Department {token}-{index:04d}",
                        "phone": fake.phone_number()[:20],
                        "email": f"dept.{token}.{index}@querymind.local",
                        "building": f"Research Block {index % 50}",
                        "budget": Decimal(random.randint(20, 180)) * Decimal("100000.00"),
                    },
                ).scalar_one()
            )
        )
    return ids


def seed_semesters(conn, token: str) -> list[int]:
    ids: list[int] = []
    terms = ["Monsoon", "Winter", "Summer"]
    for index in range(EXTRA_PER_TABLE):
        year = 2030 + (index // 3)
        term = terms[index % 3]
        start_month = {"Monsoon": 7, "Winter": 12, "Summer": 5}[term]
        start = date(year, start_month, 1)
        end = start + timedelta(days=105)
        ids.append(
            int(
                conn.execute(
                    text(
                        """
                        INSERT INTO semester (academic_year, term_name, start_date, end_date, is_current)
                        VALUES (:academic_year, :term_name, :start_date, :end_date, FALSE)
                        RETURNING semester_id;
                        """
                    ),
                    {
                        "academic_year": f"{year}-{year + 1}",
                        "term_name": term,
                        "start_date": start,
                        "end_date": end,
                    },
                ).scalar_one()
            )
        )
    return ids


def seed_people_roles(conn, token: str, department_ids: list[int]) -> tuple[list[int], list[int], list[int]]:
    students: list[int] = []
    faculty: list[int] = []
    staff: list[int] = []
    for index in range(EXTRA_PER_TABLE):
        person_id = insert_person(conn, "student", token, index)
        conn.execute(
            text(
                """
                INSERT INTO student (
                    student_id, roll_number, department_id, admission_date,
                    current_year, program_level, status, cgpa
                ) VALUES (
                    :student_id, :roll_number, :department_id, :admission_date,
                    :current_year, :program_level, :status, :cgpa
                );
                """
            ),
            {
                "student_id": person_id,
                "roll_number": f"XST{token}{index:05d}"[:30],
                "department_id": random.choice(department_ids),
                "admission_date": random_date(date(2022, 6, 1), date(2026, 8, 1)),
                "current_year": random.randint(1, 4),
                "program_level": random.choice(["undergraduate", "postgraduate", "doctoral"]),
                "status": random.choice(["active", "active", "active", "on_leave", "graduated"]),
                "cgpa": Decimal(str(round(random.uniform(5.0, 9.95), 2))),
            },
        )
        students.append(person_id)

    for index in range(EXTRA_PER_TABLE):
        person_id = insert_person(conn, "faculty", token, index)
        conn.execute(
            text(
                """
                INSERT INTO faculty (
                    faculty_id, employee_code, department_id, designation,
                    hire_date, salary, specialization
                ) VALUES (
                    :faculty_id, :employee_code, :department_id, :designation,
                    :hire_date, :salary, :specialization
                );
                """
            ),
            {
                "faculty_id": person_id,
                "employee_code": f"XFAC{token}{index:05d}"[:30],
                "department_id": random.choice(department_ids),
                "designation": random.choice(["Assistant Professor", "Associate Professor", "Professor"]),
                "hire_date": random_date(date(2012, 1, 1), date(2026, 1, 1)),
                "salary": Decimal(random.randint(7, 28)) * Decimal("100000.00"),
                "specialization": random.choice(["Databases", "AI", "Networks", "Systems", "Analytics", "Cloud"]),
            },
        )
        faculty.append(person_id)

    for index in range(EXTRA_PER_TABLE):
        person_id = insert_person(conn, "staff", token, index)
        conn.execute(
            text(
                """
                INSERT INTO staff (
                    staff_id, employee_code, department_id, job_title, hire_date, salary
                ) VALUES (
                    :staff_id, :employee_code, :department_id, :job_title, :hire_date, :salary
                );
                """
            ),
            {
                "staff_id": person_id,
                "employee_code": f"XSTF{token}{index:05d}"[:30],
                "department_id": random.choice(department_ids),
                "job_title": random.choice(["Lab Assistant", "Registrar Associate", "Finance Officer", "Hostel Coordinator"]),
                "hire_date": random_date(date(2015, 1, 1), date(2026, 1, 1)),
                "salary": Decimal(random.randint(4, 14)) * Decimal("100000.00"),
            },
        )
        staff.append(person_id)

    return students, faculty, staff


def seed_courses_and_prerequisites(conn, token: str, department_ids: list[int]) -> list[int]:
    courses: list[int] = []
    for index in range(EXTRA_PER_TABLE):
        courses.append(
            int(
                conn.execute(
                    text(
                        """
                        INSERT INTO course (
                            course_code, department_id, course_title, credits, course_level, course_type, description
                        ) VALUES (
                            :course_code, :department_id, :course_title, :credits, :course_level, :course_type, :description
                        )
                        RETURNING course_id;
                        """
                    ),
                    {
                        "course_code": f"XC{token}{index:05d}"[:20],
                        "department_id": random.choice(department_ids),
                        "course_title": f"{fake.catch_phrase()} {index}",
                        "credits": random.choice([2, 3, 4, 5]),
                        "course_level": random.choice([100, 200, 300, 400, 500, 600]),
                        "course_type": random.choice(["core", "elective", "lab", "seminar"]),
                        "description": "Bulk QueryMind course used for larger NL2SQL demonstrations.",
                    },
                ).scalar_one()
            )
        )
    for index in range(EXTRA_PER_TABLE):
        conn.execute(
            text(
                """
                INSERT INTO course_prerequisite (course_id, prerequisite_course_id)
                VALUES (:course_id, :prerequisite_course_id);
                """
            ),
            {
                "course_id": courses[index],
                "prerequisite_course_id": courses[(index + 1) % len(courses)],
            },
        )
    return courses


def seed_hostels_and_rooms(conn, token: str) -> tuple[list[int], list[int]]:
    hostels: list[int] = []
    rooms: list[int] = []
    for index in range(EXTRA_PER_TABLE):
        hostel_id = int(
            conn.execute(
                text(
                    """
                    INSERT INTO hostel (hostel_name, hostel_type, capacity, warden_name, contact_number)
                    VALUES (:hostel_name, :hostel_type, :capacity, :warden_name, :contact_number)
                    RETURNING hostel_id;
                    """
                ),
                {
                    "hostel_name": f"Extended Hostel {token}-{index:04d}",
                    "hostel_type": random.choice(["boys", "girls", "mixed"]),
                    "capacity": random.randint(60, 220),
                    "warden_name": fake.name(),
                    "contact_number": fake.phone_number()[:20],
                },
            ).scalar_one()
        )
        hostels.append(hostel_id)
        rooms.append(
            int(
                conn.execute(
                    text(
                        """
                        INSERT INTO hostel_room (hostel_id, room_number, floor_no, bed_capacity, room_type)
                        VALUES (:hostel_id, :room_number, :floor_no, :bed_capacity, :room_type)
                        RETURNING room_id;
                        """
                    ),
                    {
                        "hostel_id": hostel_id,
                        "room_number": f"X{index:04d}",
                        "floor_no": random.randint(1, 12),
                        "bed_capacity": random.choice([1, 2, 3]),
                        "room_type": random.choice(["single", "double", "triple"]),
                    },
                ).scalar_one()
            )
        )
    return hostels, rooms


def seed_sections_and_enrollments(
    conn,
    token: str,
    course_ids: list[int],
    semester_ids: list[int],
    faculty_ids: list[int],
    student_ids: list[int],
) -> list[int]:
    sections: list[int] = []
    for index in range(EXTRA_PER_TABLE):
        sections.append(
            int(
                conn.execute(
                    text(
                        """
                        INSERT INTO section (
                            course_id, semester_id, faculty_id, section_code,
                            room_no, schedule_pattern, capacity, delivery_mode
                        ) VALUES (
                            :course_id, :semester_id, :faculty_id, :section_code,
                            :room_no, :schedule_pattern, :capacity, :delivery_mode
                        )
                        RETURNING section_id;
                        """
                    ),
                    {
                        "course_id": course_ids[index],
                        "semester_id": semester_ids[index],
                        "faculty_id": random.choice(faculty_ids),
                        "section_code": f"X{token}{index:04d}"[:20],
                        "room_no": f"XR-{index % 500}",
                        "schedule_pattern": random.choice(["Mon/Wed 10:00", "Tue/Thu 14:00", "Fri 09:00"]),
                        "capacity": random.randint(35, 120),
                        "delivery_mode": random.choice(["offline", "online", "hybrid"]),
                    },
                ).scalar_one()
            )
        )
    for index in range(EXTRA_PER_TABLE):
        conn.execute(
            text(
                """
                INSERT INTO enrollment (
                    student_id, section_id, enrollment_date, enrollment_status,
                    attendance_pct, final_grade_letter, final_grade_points
                ) VALUES (
                    :student_id, :section_id, :enrollment_date, :status,
                    :attendance_pct, :grade_letter, :grade_points
                );
                """
            ),
            {
                "student_id": student_ids[index],
                "section_id": sections[index],
                "enrollment_date": random_date(date(2025, 7, 1), date(2026, 1, 15)),
                "status": random.choice(["enrolled", "completed", "completed", "dropped", "waitlisted"]),
                "attendance_pct": Decimal(str(round(random.uniform(45.0, 99.0), 2))),
                "grade_letter": random.choice(["A", "A-", "B+", "B", "C", "D"]),
                "grade_points": Decimal(str(round(random.uniform(4.0, 10.0), 2))),
            },
        )
    return sections


def seed_assessments(conn, section_ids: list[int], student_ids: list[int]) -> tuple[list[int], list[int]]:
    exams: list[int] = []
    assignments: list[int] = []
    for index in range(EXTRA_PER_TABLE):
        assessment_id = int(
            conn.execute(
                text(
                    """
                    INSERT INTO assessment (section_id, title, assessment_type, max_marks, weightage_pct, due_date)
                    VALUES (:section_id, :title, 'exam', 100, 40, :due_date)
                    RETURNING assessment_id;
                    """
                ),
                {
                    "section_id": section_ids[index],
                    "title": f"Bulk Final Exam {index}",
                    "due_date": date(2026, 4, 15),
                },
            ).scalar_one()
        )
        conn.execute(
            text(
                """
                INSERT INTO exam (exam_id, exam_mode, exam_date, duration_minutes, exam_hall)
                VALUES (:exam_id, :exam_mode, :exam_date, 120, :exam_hall);
                """
            ),
            {
                "exam_id": assessment_id,
                "exam_mode": random.choice(["offline", "online"]),
                "exam_date": date(2026, 4, 15),
                "exam_hall": f"BX-{index % 200}",
            },
        )
        exams.append(assessment_id)
        conn.execute(
            text(
                """
                INSERT INTO exam_result (
                    exam_id, student_id, marks_obtained, grade_letter, evaluated_at, remarks
                ) VALUES (
                    :exam_id, :student_id, :marks_obtained, :grade_letter, :evaluated_at, :remarks
                );
                """
            ),
            {
                "exam_id": assessment_id,
                "student_id": student_ids[index],
                "marks_obtained": Decimal(str(round(random.uniform(35.0, 99.0), 2))),
                "grade_letter": random.choice(["A", "A-", "B+", "B", "C", "D"]),
                "evaluated_at": datetime.now(timezone.utc),
                "remarks": random.choice(["Excellent", "Good", "Satisfactory", "Needs improvement"]),
            },
        )

    for index in range(EXTRA_PER_TABLE):
        assessment_id = int(
            conn.execute(
                text(
                    """
                    INSERT INTO assessment (section_id, title, assessment_type, max_marks, weightage_pct, due_date)
                    VALUES (:section_id, :title, 'assignment', 50, 20, :due_date)
                    RETURNING assessment_id;
                    """
                ),
                {
                    "section_id": section_ids[index],
                    "title": f"Bulk Assignment {index}",
                    "due_date": date(2026, 3, 10),
                },
            ).scalar_one()
        )
        conn.execute(
            text(
                """
                INSERT INTO assignment (assignment_id, release_date, submission_mode, max_attempts)
                VALUES (:assignment_id, :release_date, :submission_mode, 2);
                """
            ),
            {
                "assignment_id": assessment_id,
                "release_date": date(2026, 2, 10),
                "submission_mode": random.choice(["portal", "email", "classroom"]),
            },
        )
        assignments.append(assessment_id)
        conn.execute(
            text(
                """
                INSERT INTO assignment_submission (
                    assignment_id, student_id, attempt_no, submitted_at, score, status, feedback
                ) VALUES (
                    :assignment_id, :student_id, 1, :submitted_at, :score, :status, :feedback
                );
                """
            ),
            {
                "assignment_id": assessment_id,
                "student_id": student_ids[index],
                "submitted_at": datetime.now(timezone.utc),
                "score": Decimal(str(round(random.uniform(20.0, 50.0), 2))),
                "status": random.choice(["submitted", "graded", "graded", "pending"]),
                "feedback": random.choice(["Strong work", "Good attempt", "Revise query design", "Improve normalization"]),
            },
        )
    return exams, assignments


def seed_finance_and_hostel(conn, token: str, student_ids: list[int], semester_ids: list[int], room_ids: list[int]) -> None:
    invoices: list[int] = []
    for index in range(EXTRA_PER_TABLE):
        tuition = Decimal(random.choice([85000, 90000, 95000, 110000]))
        hostel = Decimal(random.choice([0, 25000, 35000]))
        scholarship = Decimal(random.choice([0, 10000, 15000, 25000]))
        penalty = Decimal(random.choice([0, 500, 1500]))
        total = tuition + hostel + penalty - scholarship
        invoice_id = int(
            conn.execute(
                text(
                    """
                    INSERT INTO fee_invoice (
                        student_id, semester_id, invoice_number, invoice_date,
                        tuition_amount, hostel_amount, scholarship_amount, penalty_amount,
                        total_amount, status, due_date
                    ) VALUES (
                        :student_id, :semester_id, :invoice_number, :invoice_date,
                        :tuition_amount, :hostel_amount, :scholarship_amount, :penalty_amount,
                        :total_amount, :status, :due_date
                    )
                    RETURNING invoice_id;
                    """
                ),
                {
                    "student_id": student_ids[index],
                    "semester_id": semester_ids[index],
                    "invoice_number": f"XINV-{token}-{index:05d}",
                    "invoice_date": date(2026, 1, 10),
                    "tuition_amount": tuition,
                    "hostel_amount": hostel,
                    "scholarship_amount": scholarship,
                    "penalty_amount": penalty,
                    "total_amount": total,
                    "status": random.choice(["unpaid", "partial", "paid", "overdue"]),
                    "due_date": date(2026, 2, 10),
                },
            ).scalar_one()
        )
        invoices.append(invoice_id)
        conn.execute(
            text(
                """
                INSERT INTO fee_payment (
                    invoice_id, payment_date, amount_paid, payment_method, transaction_ref, payment_status
                ) VALUES (
                    :invoice_id, NOW(), :amount_paid, :payment_method, :transaction_ref, :payment_status
                );
                """
            ),
            {
                "invoice_id": invoice_id,
                "amount_paid": Decimal(str(round(float(total) * random.uniform(0.25, 1.0), 2))),
                "payment_method": random.choice(["upi", "card", "netbanking", "cash"]),
                "transaction_ref": f"XTXN-{token}-{index:05d}",
                "payment_status": random.choice(["success", "success", "initiated", "failed"]),
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO hostel_allotment (
                    student_id, room_id, semester_id, allotted_from, allotted_to, status
                ) VALUES (
                    :student_id, :room_id, :semester_id, :allotted_from, :allotted_to, :status
                );
                """
            ),
            {
                "student_id": student_ids[index],
                "room_id": room_ids[index],
                "semester_id": semester_ids[index],
                "allotted_from": date(2026, 1, 5),
                "allotted_to": None,
                "status": random.choice(["active", "completed", "cancelled"]),
            },
        )


def seed_query_log(conn, token: str) -> None:
    prompt_templates = [
        "Show top students by GPA",
        "Find overdue invoices",
        "List faculty workload",
        "Show department enrollment trend",
        "Rank students within each department",
        "Show average grades by course",
        "Find hostel occupancy by department",
        "Show ROLLUP revenue by semester",
    ]
    for index in range(EXTRA_PER_TABLE):
        prompt = f"{random.choice(prompt_templates)} #{token}-{index}"
        conn.execute(
            text(
                """
                INSERT INTO query_log (
                    user_input, generated_sql, explanation, execution_status,
                    execution_time_ms, result_row_count, created_at
                ) VALUES (
                    :user_input, :generated_sql, :explanation, :execution_status,
                    :execution_time_ms, :result_row_count, :created_at
                );
                """
            ),
            {
                "user_input": prompt,
                "generated_sql": "SELECT 1 AS demo_result;",
                "explanation": "Bulk generated sample query history for QueryMind demos.",
                "execution_status": random.choice(["success", "success", "success", "failed"]),
                "execution_time_ms": random.randint(25, 900),
                "result_row_count": random.randint(0, 500),
                "created_at": datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 20000)),
            },
        )


def main() -> None:
    random.seed()
    token = datetime.now(timezone.utc).strftime("%d%H%M%S")
    engine = create_engine(get_db_config().url)
    with engine.begin() as conn:
        department_ids = seed_departments(conn, token)
        semester_ids = seed_semesters(conn, token)
        student_ids, faculty_ids, _staff_ids = seed_people_roles(conn, token, department_ids)
        course_ids = seed_courses_and_prerequisites(conn, token, department_ids)
        _hostel_ids, room_ids = seed_hostels_and_rooms(conn, token)
        section_ids = seed_sections_and_enrollments(conn, token, course_ids, semester_ids, faculty_ids, student_ids)
        seed_assessments(conn, section_ids, student_ids)
        seed_finance_and_hostel(conn, token, student_ids, semester_ids, room_ids)
        seed_query_log(conn, token)
    print(f"Bulk QueryMind sample data inserted successfully with token {token}.")


if __name__ == "__main__":
    main()
