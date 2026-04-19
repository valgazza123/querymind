-- QueryMind normalized OLTP schema for PostgreSQL

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS department (
    department_id BIGSERIAL PRIMARY KEY,
    department_code VARCHAR(20) NOT NULL UNIQUE,
    department_name VARCHAR(120) NOT NULL UNIQUE,
    office_phone VARCHAR(20),
    office_email VARCHAR(120) UNIQUE,
    building_name VARCHAR(100),
    budget NUMERIC(14,2) NOT NULL DEFAULT 0.00 CHECK (budget >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS person (
    person_id BIGSERIAL PRIMARY KEY,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20),
    address_line VARCHAR(255),
    city VARCHAR(80),
    state VARCHAR(80),
    postal_code VARCHAR(20),
    person_type VARCHAR(20) NOT NULL CHECK (person_type IN ('student', 'faculty', 'staff')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS student (
    student_id BIGINT PRIMARY KEY REFERENCES person(person_id) ON DELETE CASCADE,
    roll_number VARCHAR(30) NOT NULL UNIQUE,
    department_id BIGINT NOT NULL REFERENCES department(department_id) ON DELETE RESTRICT,
    admission_date DATE NOT NULL,
    current_year SMALLINT NOT NULL CHECK (current_year BETWEEN 1 AND 6),
    program_level VARCHAR(20) NOT NULL CHECK (program_level IN ('undergraduate', 'postgraduate', 'doctoral')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'graduated', 'dropped', 'on_leave')),
    cgpa NUMERIC(4,2) CHECK (cgpa BETWEEN 0 AND 10)
);

CREATE TABLE IF NOT EXISTS faculty (
    faculty_id BIGINT PRIMARY KEY REFERENCES person(person_id) ON DELETE CASCADE,
    employee_code VARCHAR(30) NOT NULL UNIQUE,
    department_id BIGINT NOT NULL REFERENCES department(department_id) ON DELETE RESTRICT,
    designation VARCHAR(60) NOT NULL,
    hire_date DATE NOT NULL,
    salary NUMERIC(12,2) NOT NULL CHECK (salary >= 0),
    specialization VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS staff (
    staff_id BIGINT PRIMARY KEY REFERENCES person(person_id) ON DELETE CASCADE,
    employee_code VARCHAR(30) NOT NULL UNIQUE,
    department_id BIGINT REFERENCES department(department_id) ON DELETE SET NULL,
    job_title VARCHAR(80) NOT NULL,
    hire_date DATE NOT NULL,
    salary NUMERIC(12,2) NOT NULL CHECK (salary >= 0)
);

CREATE TABLE IF NOT EXISTS semester (
    semester_id BIGSERIAL PRIMARY KEY,
    academic_year VARCHAR(9) NOT NULL,
    term_name VARCHAR(20) NOT NULL CHECK (term_name IN ('Monsoon', 'Winter', 'Summer')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_semester UNIQUE (academic_year, term_name),
    CONSTRAINT chk_semester_dates CHECK (end_date > start_date)
);

CREATE TABLE IF NOT EXISTS course (
    course_id BIGSERIAL PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    department_id BIGINT NOT NULL REFERENCES department(department_id) ON DELETE RESTRICT,
    course_title VARCHAR(150) NOT NULL,
    credits SMALLINT NOT NULL CHECK (credits BETWEEN 1 AND 6),
    course_level SMALLINT NOT NULL CHECK (course_level BETWEEN 100 AND 900),
    course_type VARCHAR(30) NOT NULL CHECK (course_type IN ('core', 'elective', 'lab', 'seminar')),
    description TEXT
);

CREATE TABLE IF NOT EXISTS course_prerequisite (
    course_id BIGINT NOT NULL REFERENCES course(course_id) ON DELETE CASCADE,
    prerequisite_course_id BIGINT NOT NULL REFERENCES course(course_id) ON DELETE RESTRICT,
    PRIMARY KEY (course_id, prerequisite_course_id),
    CONSTRAINT chk_no_self_prerequisite CHECK (course_id <> prerequisite_course_id)
);

CREATE TABLE IF NOT EXISTS hostel (
    hostel_id BIGSERIAL PRIMARY KEY,
    hostel_name VARCHAR(80) NOT NULL UNIQUE,
    hostel_type VARCHAR(20) NOT NULL CHECK (hostel_type IN ('boys', 'girls', 'mixed')),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    warden_name VARCHAR(120),
    contact_number VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS hostel_room (
    room_id BIGSERIAL PRIMARY KEY,
    hostel_id BIGINT NOT NULL REFERENCES hostel(hostel_id) ON DELETE CASCADE,
    room_number VARCHAR(20) NOT NULL,
    floor_no SMALLINT NOT NULL,
    bed_capacity SMALLINT NOT NULL CHECK (bed_capacity > 0),
    room_type VARCHAR(20) NOT NULL CHECK (room_type IN ('single', 'double', 'triple')),
    CONSTRAINT uq_hostel_room UNIQUE (hostel_id, room_number)
);

CREATE TABLE IF NOT EXISTS section (
    section_id BIGSERIAL PRIMARY KEY,
    course_id BIGINT NOT NULL REFERENCES course(course_id) ON DELETE RESTRICT,
    semester_id BIGINT NOT NULL REFERENCES semester(semester_id) ON DELETE RESTRICT,
    faculty_id BIGINT NOT NULL REFERENCES faculty(faculty_id) ON DELETE RESTRICT,
    section_code VARCHAR(20) NOT NULL,
    room_no VARCHAR(20),
    schedule_pattern VARCHAR(120),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    delivery_mode VARCHAR(20) NOT NULL CHECK (delivery_mode IN ('offline', 'online', 'hybrid')),
    CONSTRAINT uq_section UNIQUE (course_id, semester_id, section_code)
);

CREATE TABLE IF NOT EXISTS enrollment (
    enrollment_id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
    section_id BIGINT NOT NULL REFERENCES section(section_id) ON DELETE CASCADE,
    enrollment_date DATE NOT NULL,
    enrollment_status VARCHAR(20) NOT NULL CHECK (enrollment_status IN ('enrolled', 'dropped', 'completed', 'waitlisted')),
    attendance_pct NUMERIC(5,2) CHECK (attendance_pct BETWEEN 0 AND 100),
    final_grade_letter VARCHAR(2),
    final_grade_points NUMERIC(4,2) CHECK (final_grade_points BETWEEN 0 AND 10),
    CONSTRAINT uq_enrollment UNIQUE (student_id, section_id)
);

CREATE TABLE IF NOT EXISTS assessment (
    assessment_id BIGSERIAL PRIMARY KEY,
    section_id BIGINT NOT NULL REFERENCES section(section_id) ON DELETE CASCADE,
    title VARCHAR(120) NOT NULL,
    assessment_type VARCHAR(20) NOT NULL CHECK (assessment_type IN ('exam', 'assignment')),
    max_marks NUMERIC(6,2) NOT NULL CHECK (max_marks > 0),
    weightage_pct NUMERIC(5,2) NOT NULL CHECK (weightage_pct > 0 AND weightage_pct <= 100),
    due_date DATE
);

CREATE TABLE IF NOT EXISTS exam (
    exam_id BIGINT PRIMARY KEY REFERENCES assessment(assessment_id) ON DELETE CASCADE,
    exam_mode VARCHAR(20) NOT NULL CHECK (exam_mode IN ('offline', 'online')),
    exam_date DATE NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    exam_hall VARCHAR(40)
);

CREATE TABLE IF NOT EXISTS assignment (
    assignment_id BIGINT PRIMARY KEY REFERENCES assessment(assessment_id) ON DELETE CASCADE,
    release_date DATE NOT NULL,
    submission_mode VARCHAR(20) NOT NULL CHECK (submission_mode IN ('portal', 'email', 'classroom')),
    max_attempts SMALLINT NOT NULL DEFAULT 1 CHECK (max_attempts >= 1)
);

CREATE TABLE IF NOT EXISTS exam_result (
    exam_id BIGINT NOT NULL REFERENCES exam(exam_id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
    marks_obtained NUMERIC(6,2) NOT NULL CHECK (marks_obtained >= 0),
    grade_letter VARCHAR(2),
    evaluated_at TIMESTAMPTZ,
    remarks TEXT,
    PRIMARY KEY (exam_id, student_id)
);

CREATE TABLE IF NOT EXISTS assignment_submission (
    assignment_id BIGINT NOT NULL REFERENCES assignment(assignment_id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
    attempt_no SMALLINT NOT NULL CHECK (attempt_no >= 1),
    submitted_at TIMESTAMPTZ,
    score NUMERIC(6,2) CHECK (score >= 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'submitted', 'graded', 'missing')),
    feedback TEXT,
    PRIMARY KEY (assignment_id, student_id, attempt_no)
);

CREATE TABLE IF NOT EXISTS fee_invoice (
    invoice_id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
    semester_id BIGINT NOT NULL REFERENCES semester(semester_id) ON DELETE RESTRICT,
    invoice_number VARCHAR(40) NOT NULL UNIQUE,
    invoice_date DATE NOT NULL,
    tuition_amount NUMERIC(12,2) NOT NULL DEFAULT 0.00 CHECK (tuition_amount >= 0),
    hostel_amount NUMERIC(12,2) NOT NULL DEFAULT 0.00 CHECK (hostel_amount >= 0),
    scholarship_amount NUMERIC(12,2) NOT NULL DEFAULT 0.00 CHECK (scholarship_amount >= 0),
    penalty_amount NUMERIC(12,2) NOT NULL DEFAULT 0.00 CHECK (penalty_amount >= 0),
    total_amount NUMERIC(12,2) NOT NULL CHECK (total_amount >= 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('unpaid', 'partial', 'paid', 'overdue')),
    due_date DATE NOT NULL,
    CONSTRAINT uq_fee_invoice UNIQUE (student_id, semester_id)
);

CREATE TABLE IF NOT EXISTS fee_payment (
    payment_id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL REFERENCES fee_invoice(invoice_id) ON DELETE CASCADE,
    payment_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    amount_paid NUMERIC(12,2) NOT NULL CHECK (amount_paid > 0),
    payment_method VARCHAR(30) NOT NULL CHECK (payment_method IN ('upi', 'card', 'netbanking', 'cash')),
    transaction_ref VARCHAR(80) NOT NULL UNIQUE,
    payment_status VARCHAR(20) NOT NULL CHECK (payment_status IN ('initiated', 'success', 'failed', 'reversed'))
);

CREATE TABLE IF NOT EXISTS hostel_allotment (
    allotment_id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
    room_id BIGINT NOT NULL REFERENCES hostel_room(room_id) ON DELETE RESTRICT,
    semester_id BIGINT NOT NULL REFERENCES semester(semester_id) ON DELETE RESTRICT,
    allotted_from DATE NOT NULL,
    allotted_to DATE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'completed', 'cancelled')),
    CONSTRAINT chk_hostel_allotment_dates CHECK (allotted_to IS NULL OR allotted_to >= allotted_from)
);

CREATE OR REPLACE VIEW student_transcript AS
SELECT
    s.student_id,
    p.first_name || ' ' || p.last_name AS student_name,
    s.roll_number,
    c.course_code,
    c.course_title,
    sem.academic_year,
    sem.term_name,
    e.final_grade_letter,
    e.final_grade_points,
    e.attendance_pct
FROM enrollment AS e
JOIN student AS s ON s.student_id = e.student_id
JOIN person AS p ON p.person_id = s.student_id
JOIN section AS sec ON sec.section_id = e.section_id
JOIN course AS c ON c.course_id = sec.course_id
JOIN semester AS sem ON sem.semester_id = sec.semester_id;

CREATE OR REPLACE VIEW faculty_load AS
SELECT
    f.faculty_id,
    p.first_name || ' ' || p.last_name AS faculty_name,
    d.department_name,
    sem.academic_year,
    sem.term_name,
    COUNT(sec.section_id) AS sections_taught,
    COALESCE(SUM(sec.capacity), 0) AS total_capacity
FROM faculty AS f
JOIN person AS p ON p.person_id = f.faculty_id
JOIN department AS d ON d.department_id = f.department_id
LEFT JOIN section AS sec ON sec.faculty_id = f.faculty_id
LEFT JOIN semester AS sem ON sem.semester_id = sec.semester_id
GROUP BY f.faculty_id, p.first_name, p.last_name, d.department_name, sem.academic_year, sem.term_name;

CREATE OR REPLACE VIEW department_summary AS
SELECT
    d.department_id,
    d.department_name,
    COUNT(DISTINCT s.student_id) AS student_count,
    COUNT(DISTINCT f.faculty_id) AS faculty_count,
    COUNT(DISTINCT c.course_id) AS course_count,
    ROUND(AVG(s.cgpa), 2) AS avg_cgpa
FROM department AS d
LEFT JOIN student AS s ON s.department_id = d.department_id
LEFT JOIN faculty AS f ON f.department_id = d.department_id
LEFT JOIN course AS c ON c.department_id = d.department_id
GROUP BY d.department_id, d.department_name;

CREATE INDEX IF NOT EXISTS idx_student_department_btree
    ON student USING btree (department_id);
-- Chosen because department-wise filtering and joins are frequent in dashboards and transcript lookups.

CREATE INDEX IF NOT EXISTS idx_enrollment_student_section_composite
    ON enrollment USING btree (student_id, section_id);
-- Chosen because enrollment validation and transcript reads commonly match on student and section together.

CREATE INDEX IF NOT EXISTS idx_section_semester_faculty_composite
    ON section USING btree (semester_id, faculty_id);
-- Chosen because faculty-load and semester scheduling queries group by current semester and instructor.

CREATE INDEX IF NOT EXISTS idx_fee_invoice_unpaid_partial
    ON fee_invoice USING btree (student_id, semester_id)
    WHERE status IN ('unpaid', 'partial', 'overdue');
-- Chosen as a partial index because payment workflows mostly target open invoices, not already paid ones.

-- Read-only execution roles are intentionally created in Phase 6 security setup,
-- not in Phase 1 schema DDL. This avoids committing database user passwords.
