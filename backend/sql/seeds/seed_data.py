"""Seed realistic University Management System data for QueryMind Phase 1.5.

Targets:
    - 5 departments
    - 20 faculty
    - 200 students
    - 30 courses
    - 2 semesters of enrollment and grade data

The script uses SQLAlchemy Core plus Faker and expects the normalized schema in
``backend/sql/ddl`` or ``db/sql/01_schema.sql`` to be applied first.
"""
from __future__ import annotations

import os
import random
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from faker import Faker
from sqlalchemy import create_engine, text


fake = Faker("en_IN")
random.seed(42)
Faker.seed(42)


@dataclass(slots=True)
class DbConfig:
    """Database connection settings."""

    db_name: str
    user: str
    password: str
    host: str
    port: int

    @property
    def url(self) -> str:
        """Return the SQLAlchemy database URL."""
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"


DEPARTMENTS: list[tuple[str, str]] = [
    ("CSE", "Computer Engineering"),
    ("IT", "Information Technology"),
    ("DS", "Data Science"),
    ("ECE", "Electronics and Communication"),
    ("ME", "Mechanical Engineering"),
]

COURSE_TITLES: list[str] = [
    "Database Systems",
    "Operating Systems",
    "Data Structures",
    "Computer Networks",
    "Machine Learning",
    "Artificial Intelligence",
    "Statistics for Data Science",
    "Software Engineering",
    "Web Technologies",
    "Cloud Computing",
    "Compiler Design",
    "Linear Algebra",
    "Discrete Mathematics",
    "Signal Processing",
    "Digital Logic",
    "Thermodynamics",
    "Computer Architecture",
    "Big Data Analytics",
    "Data Warehousing",
    "Information Retrieval",
    "Natural Language Processing",
    "Design and Analysis of Algorithms",
    "Probability Models",
    "Cyber Security",
    "DevOps Engineering",
    "Business Intelligence",
    "Embedded Systems",
    "Robotics Fundamentals",
    "Optimization Techniques",
    "Distributed Systems",
]


def get_db_config() -> DbConfig:
    """Build database config from environment variables."""
    return DbConfig(
        db_name=os.getenv("POSTGRES_DB", "querymind"),
        user=os.getenv("POSTGRES_USER", "querymind"),
        password=os.getenv("POSTGRES_PASSWORD", "querymind"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
    )


def random_date(start: date, end: date) -> date:
    """Return a random date between two bounds."""
    return start + timedelta(days=random.randint(0, (end - start).days))


def seed_departments(conn) -> list[int]:
    """Insert department master data and return created IDs."""
    department_ids: list[int] = []
    for code, name in DEPARTMENTS:
        result = conn.execute(
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
                "code": code,
                "name": name,
                "phone": fake.phone_number()[:20],
                "email": f"{code.lower()}@querymind.edu",
                "building": f"{name.split()[0]} Block",
                "budget": Decimal(random.randint(20, 80)) * Decimal("100000.00"),
            },
        )
        department_ids.append(int(result.scalar_one()))
    return department_ids


def seed_semesters(conn) -> list[int]:
    """Insert two academic semesters."""
    semesters = [
        ("2025-26", "Monsoon", date(2025, 7, 15), date(2025, 11, 25), False),
        ("2025-26", "Winter", date(2025, 12, 10), date(2026, 4, 25), True),
    ]
    semester_ids: list[int] = []
    for academic_year, term_name, start_date, end_date, is_current in semesters:
        result = conn.execute(
            text(
                """
                INSERT INTO semester (academic_year, term_name, start_date, end_date, is_current)
                VALUES (:academic_year, :term_name, :start_date, :end_date, :is_current)
                RETURNING semester_id;
                """
            ),
            {
                "academic_year": academic_year,
                "term_name": term_name,
                "start_date": start_date,
                "end_date": end_date,
                "is_current": is_current,
            },
        )
        semester_ids.append(int(result.scalar_one()))
    return semester_ids


def insert_person(conn, person_type: str) -> int:
    """Insert a generic person record and return the generated ID."""
    first_name = fake.first_name()
    last_name = fake.last_name()
    result = conn.execute(
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
            "dob": fake.date_of_birth(minimum_age=18, maximum_age=58),
            "gender": random.choice(["Male", "Female"]),
            "email": fake.unique.email(),
            "phone": fake.phone_number()[:20],
            "address_line": fake.street_address(),
            "city": fake.city(),
            "state": fake.state(),
            "postal_code": fake.postcode(),
            "person_type": person_type,
        },
    )
    return int(result.scalar_one())


def seed_faculty(conn, department_ids: Sequence[int]) -> list[int]:
    """Insert faculty records."""
    faculty_ids: list[int] = []
    designations = ["Assistant Professor", "Associate Professor", "Professor"]
    specializations = ["Databases", "AI", "Networks", "Systems", "Analytics", "Cloud"]
    for index in range(20):
        person_id = insert_person(conn, "faculty")
        conn.execute(
            text(
                """
                INSERT INTO faculty (
                    faculty_id, employee_code, department_id, designation, hire_date, salary, specialization
                ) VALUES (
                    :faculty_id, :employee_code, :department_id, :designation, :hire_date, :salary, :specialization
                );
                """
            ),
            {
                "faculty_id": person_id,
                "employee_code": f"FAC{2020 + index:04d}",
                "department_id": random.choice(department_ids),
                "designation": random.choice(designations),
                "hire_date": random_date(date(2014, 1, 1), date(2024, 1, 1)),
                "salary": Decimal(random.randint(7, 18)) * Decimal("100000.00"),
                "specialization": random.choice(specializations),
            },
        )
        faculty_ids.append(person_id)
    return faculty_ids


def seed_students(conn, department_ids: Sequence[int]) -> list[int]:
    """Insert student records."""
    student_ids: list[int] = []
    for index in range(200):
        person_id = insert_person(conn, "student")
        conn.execute(
            text(
                """
                INSERT INTO student (
                    student_id, roll_number, department_id, admission_date, current_year, program_level, status, cgpa
                ) VALUES (
                    :student_id, :roll_number, :department_id, :admission_date, :current_year, :program_level, :status, :cgpa
                );
                """
            ),
            {
                "student_id": person_id,
                "roll_number": f"MPSTME2024{index + 1:03d}",
                "department_id": random.choice(department_ids),
                "admission_date": random_date(date(2022, 6, 1), date(2024, 8, 1)),
                "current_year": random.randint(1, 4),
                "program_level": "undergraduate",
                "status": "active",
                "cgpa": Decimal(str(round(random.uniform(6.0, 9.8), 2))),
            },
        )
        student_ids.append(person_id)
    return student_ids


def seed_courses(conn, department_ids: Sequence[int]) -> list[int]:
    """Insert 30 courses."""
    course_ids: list[int] = []
    for index, title in enumerate(COURSE_TITLES[:30], start=1):
        result = conn.execute(
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
                "course_code": f"QM{100 + index}",
                "department_id": random.choice(department_ids),
                "course_title": title,
                "credits": random.choice([2, 3, 4]),
                "course_level": random.choice([200, 300, 400]),
                "course_type": random.choice(["core", "elective", "lab"]),
                "description": f"{title} course for QueryMind demo schema.",
            },
        )
        course_ids.append(int(result.scalar_one()))
    return course_ids


def seed_hostels(conn) -> list[int]:
    """Insert hostels and rooms."""
    hostel_ids: list[int] = []
    for name, hostel_type in [("Aster Hostel", "boys"), ("Maple Hostel", "girls"), ("Cedar Residency", "mixed")]:
        result = conn.execute(
            text(
                """
                INSERT INTO hostel (hostel_name, hostel_type, capacity, warden_name, contact_number)
                VALUES (:hostel_name, :hostel_type, :capacity, :warden_name, :contact_number)
                RETURNING hostel_id;
                """
            ),
            {
                "hostel_name": name,
                "hostel_type": hostel_type,
                "capacity": 80,
                "warden_name": fake.name(),
                "contact_number": fake.phone_number()[:20],
            },
        )
        hostel_id = int(result.scalar_one())
        hostel_ids.append(hostel_id)
        for room_index in range(1, 21):
            conn.execute(
                text(
                    """
                    INSERT INTO hostel_room (hostel_id, room_number, floor_no, bed_capacity, room_type)
                    VALUES (:hostel_id, :room_number, :floor_no, :bed_capacity, :room_type);
                    """
                ),
                {
                    "hostel_id": hostel_id,
                    "room_number": f"{hostel_id}{room_index:03d}",
                    "floor_no": ((room_index - 1) // 10) + 1,
                    "bed_capacity": 2,
                    "room_type": "double",
                },
            )
    return hostel_ids


def seed_sections_and_enrollments(conn, course_ids: Sequence[int], faculty_ids: Sequence[int], student_ids: Sequence[int], semester_ids: Sequence[int]) -> None:
    """Insert sections, assessments, enrollments, invoices, payments, and hostel allotments."""
    section_ids: list[int] = []
    for semester_id in semester_ids:
        for course_id in course_ids:
            result = conn.execute(
                text(
                    """
                    INSERT INTO section (
                        course_id, semester_id, faculty_id, section_code, room_no, schedule_pattern, capacity, delivery_mode
                    ) VALUES (
                        :course_id, :semester_id, :faculty_id, :section_code, :room_no, :schedule_pattern, :capacity, :delivery_mode
                    )
                    RETURNING section_id;
                    """
                ),
                {
                    "course_id": course_id,
                    "semester_id": semester_id,
                    "faculty_id": random.choice(faculty_ids),
                    "section_code": random.choice(["A", "B"]),
                    "room_no": f"R-{random.randint(100, 410)}",
                    "schedule_pattern": random.choice(["Mon/Wed 10:00-11:00", "Tue/Thu 09:00-10:30", "Fri 14:00-17:00"]),
                    "capacity": 60,
                    "delivery_mode": random.choice(["offline", "hybrid"]),
                },
            )
            section_ids.append(int(result.scalar_one()))

    room_ids = [row[0] for row in conn.execute(text("SELECT room_id FROM hostel_room")).fetchall()]
    for student_id in random.sample(list(student_ids), 80):
        for semester_id in semester_ids:
            conn.execute(
                text(
                    """
                    INSERT INTO hostel_allotment (
                        student_id, room_id, semester_id, allotted_from, allotted_to, status
                    ) VALUES (
                        :student_id, :room_id, :semester_id, :allotted_from, :allotted_to, 'active'
                    );
                    """
                ),
                {
                    "student_id": student_id,
                    "room_id": random.choice(room_ids),
                    "semester_id": semester_id,
                    "allotted_from": date(2025, 7, 15),
                    "allotted_to": None,
                },
            )

    for student_id in student_ids:
        chosen_sections = random.sample(section_ids, k=4)
        for section_id in chosen_sections:
            conn.execute(
                text(
                    """
                    INSERT INTO enrollment (
                        student_id, section_id, enrollment_date, enrollment_status, attendance_pct, final_grade_letter, final_grade_points
                    ) VALUES (
                        :student_id, :section_id, :enrollment_date, 'completed', :attendance_pct, :grade_letter, :grade_points
                    )
                    ON CONFLICT (student_id, section_id) DO NOTHING;
                    """
                ),
                {
                    "student_id": student_id,
                    "section_id": section_id,
                    "enrollment_date": random_date(date(2025, 7, 1), date(2026, 1, 15)),
                    "attendance_pct": Decimal(str(round(random.uniform(65.0, 98.0), 2))),
                    "grade_letter": random.choice(["A", "A-", "B+", "B", "C"]),
                    "grade_points": Decimal(str(round(random.uniform(6.0, 10.0), 2))),
                },
            )

    for section_id, semester_id in conn.execute(text("SELECT section_id, semester_id FROM section")).fetchall():
        assessment_result = conn.execute(
            text(
                """
                INSERT INTO assessment (
                    section_id, title, assessment_type, max_marks, weightage_pct, due_date
                ) VALUES (
                    :section_id, :title, 'exam', 100, 40, :due_date
                )
                RETURNING assessment_id;
                """
            ),
            {"section_id": section_id, "title": "End Semester Exam", "due_date": date(2026, 4, 15)},
        )
        exam_id = int(assessment_result.scalar_one())
        conn.execute(
            text(
                """
                INSERT INTO exam (exam_id, exam_mode, exam_date, duration_minutes, exam_hall)
                VALUES (:exam_id, 'offline', :exam_date, 120, :exam_hall);
                """
            ),
            {"exam_id": exam_id, "exam_date": date(2026, 4, 15), "exam_hall": f"H-{random.randint(1, 20)}"},
        )

        enrolled_students = conn.execute(
            text("SELECT student_id FROM enrollment WHERE section_id = :section_id LIMIT 15"),
            {"section_id": section_id},
        ).fetchall()
        for (student_id,) in enrolled_students:
            marks = Decimal(str(round(random.uniform(50.0, 95.0), 2)))
            conn.execute(
                text(
                    """
                    INSERT INTO exam_result (
                        exam_id, student_id, marks_obtained, grade_letter, evaluated_at, remarks
                    ) VALUES (
                        :exam_id, :student_id, :marks_obtained, :grade_letter, :evaluated_at, :remarks
                    )
                    ON CONFLICT (exam_id, student_id) DO NOTHING;
                    """
                ),
                {
                    "exam_id": exam_id,
                    "student_id": student_id,
                    "marks_obtained": marks,
                    "grade_letter": random.choice(["A", "A-", "B+", "B", "C"]),
                    "evaluated_at": datetime.utcnow(),
                    "remarks": random.choice(["Excellent", "Good", "Needs improvement"]),
                },
            )

    for student_id in student_ids:
        for semester_id in semester_ids:
            tuition_amount = Decimal(random.choice([85000, 90000, 95000]))
            hostel_amount = Decimal(random.choice([0, 25000]))
            scholarship_amount = Decimal(random.choice([0, 10000, 15000]))
            penalty_amount = Decimal(random.choice([0, 500]))
            total_amount = tuition_amount + hostel_amount + penalty_amount - scholarship_amount
            invoice_result = conn.execute(
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
                    "student_id": student_id,
                    "semester_id": semester_id,
                    "invoice_number": fake.unique.bothify(text="INV-######"),
                    "invoice_date": date(2025, 7, 20),
                    "tuition_amount": tuition_amount,
                    "hostel_amount": hostel_amount,
                    "scholarship_amount": scholarship_amount,
                    "penalty_amount": penalty_amount,
                    "total_amount": total_amount,
                    "status": random.choice(["paid", "partial", "unpaid"]),
                    "due_date": date(2025, 8, 10),
                },
            )
            invoice_id = int(invoice_result.scalar_one())
            if random.random() < 0.75:
                conn.execute(
                    text(
                        """
                        INSERT INTO fee_payment (
                            invoice_id, payment_date, amount_paid, payment_method, transaction_ref, payment_status
                        ) VALUES (
                            :invoice_id, NOW(), :amount_paid, :payment_method, :transaction_ref, 'success'
                        );
                        """
                    ),
                    {
                        "invoice_id": invoice_id,
                        "amount_paid": Decimal(str(round(float(total_amount) * random.uniform(0.5, 1.0), 2))),
                        "payment_method": random.choice(["upi", "card", "netbanking"]),
                        "transaction_ref": fake.unique.bothify(text="TXN########"),
                    },
                )


def main() -> None:
    """Run the seed process."""
    engine = create_engine(get_db_config().url)
    with engine.begin() as conn:
        department_ids = seed_departments(conn)
        semester_ids = seed_semesters(conn)
        faculty_ids = seed_faculty(conn, department_ids)
        student_ids = seed_students(conn, department_ids)
        seed_hostels(conn)
        course_ids = seed_courses(conn, department_ids)
        seed_sections_and_enrollments(conn, course_ids, faculty_ids, student_ids, semester_ids)
    print("QueryMind seed data inserted successfully.")


if __name__ == "__main__":
    main()
