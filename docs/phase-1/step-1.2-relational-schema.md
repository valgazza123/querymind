# QueryMind Phase 1.2: ER to Relational Schema Conversion

## Mapping Strategy

### Generalization Handling
For both specialization hierarchies, this design uses `table-per-type`:
- `Person` as the supertype table, with subtype tables `Student`, `Faculty`, `Staff`
- `Assessment` as the supertype table, with subtype tables `Exam`, `Assignment`

Reason:
- preserves normalization
- keeps subtype-specific attributes isolated
- supports clean foreign-key references
- makes DBMS theory explanation stronger for viva/project review

### Weak Entity Handling
- `Exam_Result` is implemented with composite primary key (`exam_id`, `student_id`)
- `Assignment_Submission` is implemented with composite primary key (`assignment_id`, `student_id`, `attempt_no`)

These tables cannot exist without their owner entities, so their identifying foreign keys are also part of the primary key.

## Relational Schema

## 1. department
```sql
department (
    department_id       BIGSERIAL PRIMARY KEY,
    department_code     VARCHAR(20) NOT NULL UNIQUE,
    department_name     VARCHAR(120) NOT NULL UNIQUE,
    office_phone        VARCHAR(20),
    office_email        VARCHAR(120) UNIQUE,
    building_name       VARCHAR(100),
    budget              NUMERIC(14,2) NOT NULL DEFAULT 0.00,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
```

## 2. person
```sql
person (
    person_id           BIGSERIAL PRIMARY KEY,
    first_name          VARCHAR(80) NOT NULL,
    last_name           VARCHAR(80) NOT NULL,
    date_of_birth       DATE NOT NULL,
    gender              VARCHAR(20),
    email               VARCHAR(150) NOT NULL UNIQUE,
    phone               VARCHAR(20),
    address_line        VARCHAR(255),
    city                VARCHAR(80),
    state               VARCHAR(80),
    postal_code         VARCHAR(20),
    person_type         VARCHAR(20) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
```

Constraint intent:
- `person_type IN ('student', 'faculty', 'staff')`

## 3. student
```sql
student (
    student_id          BIGINT PRIMARY KEY,
    roll_number         VARCHAR(30) NOT NULL UNIQUE,
    department_id       BIGINT NOT NULL,
    admission_date      DATE NOT NULL,
    current_year        SMALLINT NOT NULL,
    program_level       VARCHAR(20) NOT NULL,
    status              VARCHAR(20) NOT NULL,
    cgpa                NUMERIC(4,2),
    CONSTRAINT fk_student_person
        FOREIGN KEY (student_id) REFERENCES person(person_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_student_department
        FOREIGN KEY (department_id) REFERENCES department(department_id)
        ON DELETE RESTRICT
)
```

## 4. faculty
```sql
faculty (
    faculty_id          BIGINT PRIMARY KEY,
    employee_code       VARCHAR(30) NOT NULL UNIQUE,
    department_id       BIGINT NOT NULL,
    designation         VARCHAR(60) NOT NULL,
    hire_date           DATE NOT NULL,
    salary              NUMERIC(12,2) NOT NULL,
    specialization      VARCHAR(120),
    CONSTRAINT fk_faculty_person
        FOREIGN KEY (faculty_id) REFERENCES person(person_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_faculty_department
        FOREIGN KEY (department_id) REFERENCES department(department_id)
        ON DELETE RESTRICT
)
```

## 5. staff
```sql
staff (
    staff_id            BIGINT PRIMARY KEY,
    employee_code       VARCHAR(30) NOT NULL UNIQUE,
    department_id       BIGINT,
    job_title           VARCHAR(80) NOT NULL,
    hire_date           DATE NOT NULL,
    salary              NUMERIC(12,2) NOT NULL,
    CONSTRAINT fk_staff_person
        FOREIGN KEY (staff_id) REFERENCES person(person_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_staff_department
        FOREIGN KEY (department_id) REFERENCES department(department_id)
        ON DELETE SET NULL
)
```

## 6. course
```sql
course (
    course_id           BIGSERIAL PRIMARY KEY,
    course_code         VARCHAR(20) NOT NULL UNIQUE,
    department_id       BIGINT NOT NULL,
    course_title        VARCHAR(150) NOT NULL,
    credits             SMALLINT NOT NULL,
    course_level        SMALLINT NOT NULL,
    course_type         VARCHAR(30) NOT NULL,
    description         TEXT,
    CONSTRAINT fk_course_department
        FOREIGN KEY (department_id) REFERENCES department(department_id)
        ON DELETE RESTRICT
)
```

## 7. semester
```sql
semester (
    semester_id         BIGSERIAL PRIMARY KEY,
    academic_year       VARCHAR(9) NOT NULL,
    term_name           VARCHAR(20) NOT NULL,
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    is_current          BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_semester UNIQUE (academic_year, term_name)
)
```

## 8. section
```sql
section (
    section_id          BIGSERIAL PRIMARY KEY,
    course_id           BIGINT NOT NULL,
    semester_id         BIGINT NOT NULL,
    faculty_id          BIGINT NOT NULL,
    section_code        VARCHAR(20) NOT NULL,
    room_no             VARCHAR(20),
    schedule_pattern    VARCHAR(120),
    capacity            INTEGER NOT NULL,
    delivery_mode       VARCHAR(20) NOT NULL,
    CONSTRAINT uq_section UNIQUE (course_id, semester_id, section_code),
    CONSTRAINT fk_section_course
        FOREIGN KEY (course_id) REFERENCES course(course_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_section_semester
        FOREIGN KEY (semester_id) REFERENCES semester(semester_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_section_faculty
        FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id)
        ON DELETE RESTRICT
)
```

## 9. enrollment
```sql
enrollment (
    enrollment_id       BIGSERIAL PRIMARY KEY,
    student_id          BIGINT NOT NULL,
    section_id          BIGINT NOT NULL,
    enrollment_date     DATE NOT NULL,
    enrollment_status   VARCHAR(20) NOT NULL,
    attendance_pct      NUMERIC(5,2),
    final_grade_letter  VARCHAR(2),
    final_grade_points  NUMERIC(4,2),
    CONSTRAINT uq_enrollment UNIQUE (student_id, section_id),
    CONSTRAINT fk_enrollment_student
        FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_enrollment_section
        FOREIGN KEY (section_id) REFERENCES section(section_id)
        ON DELETE CASCADE
)
```

## 10. assessment
```sql
assessment (
    assessment_id       BIGSERIAL PRIMARY KEY,
    section_id          BIGINT NOT NULL,
    title               VARCHAR(120) NOT NULL,
    assessment_type     VARCHAR(20) NOT NULL,
    max_marks           NUMERIC(6,2) NOT NULL,
    weightage_pct       NUMERIC(5,2) NOT NULL,
    due_date            DATE,
    CONSTRAINT fk_assessment_section
        FOREIGN KEY (section_id) REFERENCES section(section_id)
        ON DELETE CASCADE
)
```

Constraint intent:
- `assessment_type IN ('exam', 'assignment')`

## 11. exam
```sql
exam (
    exam_id             BIGINT PRIMARY KEY,
    exam_mode           VARCHAR(20) NOT NULL,
    exam_date           DATE NOT NULL,
    duration_minutes    INTEGER NOT NULL,
    exam_hall           VARCHAR(40),
    CONSTRAINT fk_exam_assessment
        FOREIGN KEY (exam_id) REFERENCES assessment(assessment_id)
        ON DELETE CASCADE
)
```

## 12. assignment
```sql
assignment (
    assignment_id       BIGINT PRIMARY KEY,
    release_date        DATE NOT NULL,
    submission_mode     VARCHAR(20) NOT NULL,
    max_attempts        SMALLINT NOT NULL DEFAULT 1,
    CONSTRAINT fk_assignment_assessment
        FOREIGN KEY (assignment_id) REFERENCES assessment(assessment_id)
        ON DELETE CASCADE
)
```

## 13. exam_result
```sql
exam_result (
    exam_id             BIGINT NOT NULL,
    student_id          BIGINT NOT NULL,
    marks_obtained      NUMERIC(6,2) NOT NULL,
    grade_letter        VARCHAR(2),
    evaluated_at        TIMESTAMPTZ,
    remarks             TEXT,
    PRIMARY KEY (exam_id, student_id),
    CONSTRAINT fk_exam_result_exam
        FOREIGN KEY (exam_id) REFERENCES exam(exam_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_exam_result_student
        FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE
)
```

## 14. assignment_submission
```sql
assignment_submission (
    assignment_id       BIGINT NOT NULL,
    student_id          BIGINT NOT NULL,
    attempt_no          SMALLINT NOT NULL,
    submitted_at        TIMESTAMPTZ,
    score               NUMERIC(6,2),
    status              VARCHAR(20) NOT NULL,
    feedback            TEXT,
    PRIMARY KEY (assignment_id, student_id, attempt_no),
    CONSTRAINT fk_assignment_submission_assignment
        FOREIGN KEY (assignment_id) REFERENCES assignment(assignment_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_assignment_submission_student
        FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE
)
```

## 15. fee_invoice
```sql
fee_invoice (
    invoice_id          BIGSERIAL PRIMARY KEY,
    student_id          BIGINT NOT NULL,
    semester_id         BIGINT NOT NULL,
    invoice_number      VARCHAR(40) NOT NULL UNIQUE,
    invoice_date        DATE NOT NULL,
    tuition_amount      NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    hostel_amount       NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    scholarship_amount  NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    penalty_amount      NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    total_amount        NUMERIC(12,2) NOT NULL,
    status              VARCHAR(20) NOT NULL,
    due_date            DATE NOT NULL,
    CONSTRAINT uq_fee_invoice UNIQUE (student_id, semester_id),
    CONSTRAINT fk_fee_invoice_student
        FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_fee_invoice_semester
        FOREIGN KEY (semester_id) REFERENCES semester(semester_id)
        ON DELETE RESTRICT
)
```

## 16. fee_payment
```sql
fee_payment (
    payment_id          BIGSERIAL PRIMARY KEY,
    invoice_id          BIGINT NOT NULL,
    payment_date        TIMESTAMPTZ NOT NULL,
    amount_paid         NUMERIC(12,2) NOT NULL,
    payment_method      VARCHAR(30) NOT NULL,
    transaction_ref     VARCHAR(80) NOT NULL UNIQUE,
    payment_status      VARCHAR(20) NOT NULL,
    CONSTRAINT fk_fee_payment_invoice
        FOREIGN KEY (invoice_id) REFERENCES fee_invoice(invoice_id)
        ON DELETE CASCADE
)
```

## 17. hostel
```sql
hostel (
    hostel_id           BIGSERIAL PRIMARY KEY,
    hostel_name         VARCHAR(80) NOT NULL UNIQUE,
    hostel_type         VARCHAR(20) NOT NULL,
    capacity            INTEGER NOT NULL,
    warden_name         VARCHAR(120),
    contact_number      VARCHAR(20)
)
```

## 18. hostel_room
```sql
hostel_room (
    room_id             BIGSERIAL PRIMARY KEY,
    hostel_id           BIGINT NOT NULL,
    room_number         VARCHAR(20) NOT NULL,
    floor_no            SMALLINT NOT NULL,
    bed_capacity        SMALLINT NOT NULL,
    room_type           VARCHAR(20) NOT NULL,
    CONSTRAINT uq_hostel_room UNIQUE (hostel_id, room_number),
    CONSTRAINT fk_hostel_room_hostel
        FOREIGN KEY (hostel_id) REFERENCES hostel(hostel_id)
        ON DELETE CASCADE
)
```

## 19. hostel_allotment
```sql
hostel_allotment (
    allotment_id        BIGSERIAL PRIMARY KEY,
    student_id          BIGINT NOT NULL,
    room_id             BIGINT NOT NULL,
    semester_id         BIGINT NOT NULL,
    allotted_from       DATE NOT NULL,
    allotted_to         DATE,
    status              VARCHAR(20) NOT NULL,
    CONSTRAINT fk_hostel_allotment_student
        FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_hostel_allotment_room
        FOREIGN KEY (room_id) REFERENCES hostel_room(room_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_hostel_allotment_semester
        FOREIGN KEY (semester_id) REFERENCES semester(semester_id)
        ON DELETE RESTRICT
)
```

## Optional Supporting Table for Recursive SQL Demos

To support prerequisite-chain queries later:

## 20. course_prerequisite
```sql
course_prerequisite (
    course_id               BIGINT NOT NULL,
    prerequisite_course_id  BIGINT NOT NULL,
    PRIMARY KEY (course_id, prerequisite_course_id),
    CONSTRAINT fk_course_prereq_course
        FOREIGN KEY (course_id) REFERENCES course(course_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_course_prereq_prereq
        FOREIGN KEY (prerequisite_course_id) REFERENCES course(course_id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_no_self_prereq
        CHECK (course_id <> prerequisite_course_id)
)
```

This table is not mandatory for the ER model, but it is highly useful for:
- recursive CTE demonstrations
- prerequisite-path analytics
- richer NL2SQL examples

## Schema Notes for Viva / Report

### How weak entities are implemented
- `exam_result` uses a composite primary key from its owner entities
- `assignment_submission` uses a composite primary key plus `attempt_no`
- both are existence-dependent and use `ON DELETE CASCADE`

### How M:N relationships are implemented
- `student` and `section` are resolved by `enrollment`
- `student` and `hostel_room` over time are resolved by `hostel_allotment`
- `course` and `course` prerequisite relation is resolved by `course_prerequisite`

### How total participation appears in the schema
Total participation from the ER model becomes `NOT NULL` foreign keys in relational tables, for example:
- `student.department_id`
- `faculty.department_id`
- `course.department_id`
- `section.course_id`
- `section.semester_id`
- `section.faculty_id`
- `assessment.section_id`
- `fee_invoice.student_id`
- `fee_invoice.semester_id`

### Why table-per-type is preferable here
- cleaner subtype-specific constraints
- avoids many nullable columns in one supertable
- better conceptual alignment with DBMS syllabus content
- easier to explain supertype/subtype conversion in documentation

## Compact Relational Schema Listing

```text
Department(department_id PK, department_code UQ, department_name UQ, office_phone, office_email UQ, building_name, budget, created_at)

Person(person_id PK, first_name, last_name, date_of_birth, gender, email UQ, phone, address_line, city, state, postal_code, person_type)

Student(student_id PK/FK->Person.person_id, roll_number UQ, department_id FK->Department.department_id, admission_date, current_year, program_level, status, cgpa)

Faculty(faculty_id PK/FK->Person.person_id, employee_code UQ, department_id FK->Department.department_id, designation, hire_date, salary, specialization)

Staff(staff_id PK/FK->Person.person_id, employee_code UQ, department_id FK->Department.department_id NULL, job_title, hire_date, salary)

Course(course_id PK, course_code UQ, department_id FK->Department.department_id, course_title, credits, course_level, course_type, description)

Semester(semester_id PK, academic_year, term_name, start_date, end_date, is_current, UQ(academic_year, term_name))

Section(section_id PK, course_id FK->Course.course_id, semester_id FK->Semester.semester_id, faculty_id FK->Faculty.faculty_id, section_code, room_no, schedule_pattern, capacity, delivery_mode, UQ(course_id, semester_id, section_code))

Enrollment(enrollment_id PK, student_id FK->Student.student_id, section_id FK->Section.section_id, enrollment_date, enrollment_status, attendance_pct, final_grade_letter, final_grade_points, UQ(student_id, section_id))

Assessment(assessment_id PK, section_id FK->Section.section_id, title, assessment_type, max_marks, weightage_pct, due_date)

Exam(exam_id PK/FK->Assessment.assessment_id, exam_mode, exam_date, duration_minutes, exam_hall)

Assignment(assignment_id PK/FK->Assessment.assessment_id, release_date, submission_mode, max_attempts)

Exam_Result(exam_id PK/FK->Exam.exam_id, student_id PK/FK->Student.student_id, marks_obtained, grade_letter, evaluated_at, remarks)

Assignment_Submission(assignment_id PK/FK->Assignment.assignment_id, student_id PK/FK->Student.student_id, attempt_no PK, submitted_at, score, status, feedback)

Fee_Invoice(invoice_id PK, student_id FK->Student.student_id, semester_id FK->Semester.semester_id, invoice_number UQ, invoice_date, tuition_amount, hostel_amount, scholarship_amount, penalty_amount, total_amount, status, due_date, UQ(student_id, semester_id))

Fee_Payment(payment_id PK, invoice_id FK->Fee_Invoice.invoice_id, payment_date, amount_paid, payment_method, transaction_ref UQ, payment_status)

Hostel(hostel_id PK, hostel_name UQ, hostel_type, capacity, warden_name, contact_number)

Hostel_Room(room_id PK, hostel_id FK->Hostel.hostel_id, room_number, floor_no, bed_capacity, room_type, UQ(hostel_id, room_number))

Hostel_Allotment(allotment_id PK, student_id FK->Student.student_id, room_id FK->Hostel_Room.room_id, semester_id FK->Semester.semester_id, allotted_from, allotted_to, status)

Course_Prerequisite(course_id PK/FK->Course.course_id, prerequisite_course_id PK/FK->Course.course_id)
```
