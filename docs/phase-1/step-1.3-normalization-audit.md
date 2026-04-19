# QueryMind Phase 1.3: Normalization Audit

## Goal
Audit the initial University Management System schema for:
- 1NF issues
- 2NF issues using functional dependencies
- 3NF issues using transitive dependencies
- two intentional denormalizations for the analytics layer

This document is written as a project-report artifact: it shows what the initial design might contain, what the normalized correction is, and why.

## Initial Assumption
The relational schema from Step 1.2 is already close to normalized, but for DBMS coursework you usually need to:
1. demonstrate what common design mistakes would look like,
2. identify the violating dependencies,
3. show the corrected normalized structure.

So this audit treats a few attributes as if they were present in an earlier draft, then explains why the Step 1.2 schema fixes them.

---

## 1NF Audit

### 1NF Rule
First Normal Form requires:
- atomic attribute values
- no repeating groups
- each row-column intersection must contain a single value

### Likely 1NF Violations in an early draft

#### Violation A: `person.phone`
Problematic draft:
```text
Person(person_id, ..., phone)
```
If `phone` stores values like `"9876543210, 9988776655"` then it is multi-valued and violates 1NF.

Fix:
- keep `person.phone` as one primary contact only, or
- create a separate table:

```text
Person_Contact(contact_id PK, person_id FK, phone_number, contact_type)
```

Decision for QueryMind:
- keep one atomic `phone` value in `person`
- if multiple contacts are needed later, add `person_contact`

#### Violation B: `section.schedule_pattern`
Problematic draft:
```text
Section(..., schedule_pattern)
```
If it stores `"Mon 10-11, Wed 10-11, Fri 2-3"` it is a compound textual field, not properly atomic for scheduling queries.

Normalized fix:
```text
Section_Meeting(
    meeting_id PK,
    section_id FK,
    day_of_week,
    start_time,
    end_time,
    room_no
)
```

Decision for QueryMind:
- for the course project baseline, `schedule_pattern` may remain as display text
- for strict normalization, `section_meeting` is the correct design

#### Violation C: `assessment_type` mixed with subtype detail in one row
Problematic draft:
```text
Assessment(assessment_id, section_id, title, assessment_type, exam_date, exam_hall, submission_mode, max_attempts, ...)
```
This does not strictly violate 1NF by atomocity, but it creates sparse null-heavy rows and mixed semantics.

Fix:
- split into `assessment`, `exam`, and `assignment`
- already done in Step 1.2

### 1NF Conclusion
The Step 1.2 schema satisfies 1NF if:
- `phone` remains atomic
- `schedule_pattern` is treated as descriptive text only
- subtype-specific attributes remain separated into subtype tables

For a stricter design, `section_meeting` can be added later.

---

## 2NF Audit

### 2NF Rule
Second Normal Form requires:
- relation is already in 1NF
- every non-key attribute is fully functionally dependent on the whole primary key
- no partial dependency on only part of a composite key

### Relations with composite keys
The composite-key tables are:
- `exam_result(exam_id, student_id, ...)`
- `assignment_submission(assignment_id, student_id, attempt_no, ...)`
- `course_prerequisite(course_id, prerequisite_course_id)`

### Functional Dependencies Considered

#### A. `exam_result`
Current design:
```text
Exam_Result(exam_id, student_id, marks_obtained, grade_letter, evaluated_at, remarks)
PK = (exam_id, student_id)
```

Functional dependencies:
- `(exam_id, student_id) -> marks_obtained, grade_letter, evaluated_at, remarks`

No partial dependency:
- `marks_obtained` does not depend only on `exam_id`
- `marks_obtained` does not depend only on `student_id`

Result:
- `exam_result` is in 2NF

#### B. `assignment_submission`
Current design:
```text
Assignment_Submission(assignment_id, student_id, attempt_no, submitted_at, score, status, feedback)
PK = (assignment_id, student_id, attempt_no)
```

Functional dependencies:
- `(assignment_id, student_id, attempt_no) -> submitted_at, score, status, feedback`

No partial dependency:
- `submitted_at` is attempt-specific, so it depends on the full key

Result:
- `assignment_submission` is in 2NF

### Example of a 2NF violation in an early draft

Problematic draft:
```text
Enrollment(student_id, section_id, student_name, course_title, faculty_name, enrollment_date, attendance_pct)
PK = (student_id, section_id)
```

Functional dependencies:
- `student_id -> student_name`
- `section_id -> course_title, faculty_name`
- `(student_id, section_id) -> enrollment_date, attendance_pct`

Why this violates 2NF:
- `student_name` depends only on `student_id`
- `course_title` and `faculty_name` depend only on `section_id`
- these are partial dependencies on parts of a composite key

Fix:
- keep only relationship-specific attributes in `enrollment`
- move person/course/faculty attributes back to their own relations

Correct normalized form:
```text
Enrollment(enrollment_id, student_id, section_id, enrollment_date, enrollment_status, attendance_pct, final_grade_letter, final_grade_points)
```

### 2NF Conclusion
The Step 1.2 schema is in 2NF because:
- composite-key tables store only attributes dependent on the full key
- descriptive attributes like names, titles, and department info remain in their own base tables

---

## 3NF Audit

### 3NF Rule
Third Normal Form requires:
- relation is already in 2NF
- no transitive dependency from key -> non-key -> another non-key

### Common 3NF Risks in the university domain

#### Violation A: Department details inside student
Problematic draft:
```text
Student(student_id, roll_number, department_id, department_name, department_code, ...)
```

Functional dependencies:
- `student_id -> department_id`
- `department_id -> department_name, department_code`

Transitive dependency:
- `student_id -> department_id -> department_name, department_code`

Fix:
- store only `department_id` in `student`
- keep department descriptors in `department`

This is already fixed in Step 1.2.

#### Violation B: Course details inside section
Problematic draft:
```text
Section(section_id, course_id, course_code, course_title, credits, semester_id, faculty_id, ...)
```

Functional dependencies:
- `section_id -> course_id`
- `course_id -> course_code, course_title, credits`

Transitive dependency:
- `section_id -> course_id -> course_code, course_title, credits`

Fix:
- keep course descriptors only in `course`
- keep `section` limited to offering-specific attributes

Already fixed in Step 1.2.

#### Violation C: Invoice status derivable from payment totals
Problematic draft:
```text
Fee_Invoice(invoice_id, ..., total_amount, amount_paid_so_far, status)
```

If:
- `invoice_id -> total_amount`
- payments determine `amount_paid_so_far`
- `status` is derived from the comparison between amount paid and total amount

Then `status` can become a derived/transitively maintained attribute.

Design choice in QueryMind:
- `fee_invoice.status` is kept as an operational status field for workflow convenience
- strict normalization would compute it from payments
- in OLTP systems, this is often tolerated if controlled by transaction logic

#### Violation D: Faculty department name inside course
Problematic draft:
```text
Course(course_id, department_id, department_name, ...)
```

Functional dependencies:
- `course_id -> department_id`
- `department_id -> department_name`

Transitive dependency:
- `course_id -> department_id -> department_name`

Fix:
- keep `department_name` only in `department`

### 3NF Conclusion
The Step 1.2 schema is effectively in 3NF because:
- department descriptors are isolated in `department`
- course descriptors are isolated in `course`
- person descriptors are isolated in `person`
- section-specific data is separate from course-specific data

One borderline field remains:
- `fee_invoice.status`

This is acceptable for an operational system if enforced consistently via transactions, but in a theory-heavy answer you can mention that it is a controlled derived attribute.

---

## Final Normalized Schema Position

After 1NF, 2NF, and 3NF corrections, the key normalized principles are:
- atomic person, course, and academic attributes
- subtype decomposition via table-per-type
- relationship tables carrying only relationship attributes
- weak entities modeled with composite identifying keys
- lookup/descriptive attributes stored only in their determinant tables

The schema from Step 1.2 is therefore the normalized OLTP schema for QueryMind.

---

## Functional Dependency Summary

### department
- `department_id -> department_code, department_name, office_phone, office_email, building_name, budget, created_at`
- `department_code -> department_id, department_name, office_phone, office_email, building_name, budget, created_at`

### person
- `person_id -> first_name, last_name, date_of_birth, gender, email, phone, address_line, city, state, postal_code, person_type, created_at`
- `email -> person_id, first_name, last_name, date_of_birth, gender, phone, address_line, city, state, postal_code, person_type, created_at`

### student
- `student_id -> roll_number, department_id, admission_date, current_year, program_level, status, cgpa`
- `roll_number -> student_id, department_id, admission_date, current_year, program_level, status, cgpa`

### faculty
- `faculty_id -> employee_code, department_id, designation, hire_date, salary, specialization`
- `employee_code -> faculty_id, department_id, designation, hire_date, salary, specialization`

### course
- `course_id -> course_code, department_id, course_title, credits, course_level, course_type, description`
- `course_code -> course_id, department_id, course_title, credits, course_level, course_type, description`

### semester
- `semester_id -> academic_year, term_name, start_date, end_date, is_current`
- `(academic_year, term_name) -> semester_id, start_date, end_date, is_current`

### section
- `section_id -> course_id, semester_id, faculty_id, section_code, room_no, schedule_pattern, capacity, delivery_mode`
- `(course_id, semester_id, section_code) -> section_id, faculty_id, room_no, schedule_pattern, capacity, delivery_mode`

### enrollment
- `enrollment_id -> student_id, section_id, enrollment_date, enrollment_status, attendance_pct, final_grade_letter, final_grade_points`
- `(student_id, section_id) -> enrollment_id, enrollment_date, enrollment_status, attendance_pct, final_grade_letter, final_grade_points`

### assessment
- `assessment_id -> section_id, title, assessment_type, max_marks, weightage_pct, due_date`

### exam
- `exam_id -> exam_mode, exam_date, duration_minutes, exam_hall`

### assignment
- `assignment_id -> release_date, submission_mode, max_attempts`

### exam_result
- `(exam_id, student_id) -> marks_obtained, grade_letter, evaluated_at, remarks`

### assignment_submission
- `(assignment_id, student_id, attempt_no) -> submitted_at, score, status, feedback`

### fee_invoice
- `invoice_id -> student_id, semester_id, invoice_number, invoice_date, tuition_amount, hostel_amount, scholarship_amount, penalty_amount, total_amount, status, due_date`
- `invoice_number -> invoice_id, student_id, semester_id, invoice_date, tuition_amount, hostel_amount, scholarship_amount, penalty_amount, total_amount, status, due_date`
- `(student_id, semester_id) -> invoice_id, invoice_number, invoice_date, tuition_amount, hostel_amount, scholarship_amount, penalty_amount, total_amount, status, due_date`

### fee_payment
- `payment_id -> invoice_id, payment_date, amount_paid, payment_method, transaction_ref, payment_status`
- `transaction_ref -> payment_id, invoice_id, payment_date, amount_paid, payment_method, payment_status`

### hostel
- `hostel_id -> hostel_name, hostel_type, capacity, warden_name, contact_number`
- `hostel_name -> hostel_id, hostel_type, capacity, warden_name, contact_number`

### hostel_room
- `room_id -> hostel_id, room_number, floor_no, bed_capacity, room_type`
- `(hostel_id, room_number) -> room_id, floor_no, bed_capacity, room_type`

### hostel_allotment
- `allotment_id -> student_id, room_id, semester_id, allotted_from, allotted_to, status`

---

## Intentional De-normalization for Analytics Layer

The OLTP schema should remain normalized. However, for reporting and OLAP queries, limited de-normalization is beneficial.

### De-normalization 1: `fact_enrollments`
Proposed warehouse fact table:
```text
fact_enrollments(
    enrollment_key,
    student_key,
    course_key,
    faculty_key,
    department_key,
    time_key,
    grade_points,
    fees_paid,
    attendance_pct
)
```

Why de-normalize:
- avoids repeated joins across `enrollment`, `section`, `course`, `student`, `faculty`, `department`, `semester`, and fee tables
- improves dashboard performance
- makes `ROLLUP`, `CUBE`, and `GROUPING SETS` queries simpler

Tradeoff:
- duplicate dimension references and derived measures
- ETL maintenance required
- update anomalies are acceptable because warehouse tables are append/batch oriented, not transactional

### De-normalization 2: `dim_student` with department attributes embedded
Proposed dimension:
```text
dim_student(
    student_key,
    student_id,
    roll_number,
    full_name,
    department_name,
    program_level,
    admission_year,
    hostel_flag
)
```

Why de-normalize:
- dashboard filters should not require joins back to normalized OLTP tables
- department and program slicing is common in analytics
- dimensions are intentionally descriptive and query-friendly

Tradeoff:
- if a student changes department, historical handling becomes a Slowly Changing Dimension problem
- attribute duplication increases storage
- ETL complexity rises, but query latency drops

---

## Final Answer You Can Use in Submission

The operational QueryMind schema is normalized to 3NF:
- 1NF is satisfied by atomic attributes and separation of repeating groups
- 2NF is satisfied because composite-key relations contain only attributes dependent on the full key
- 3NF is satisfied because descriptive attributes are stored only in their determinant tables, avoiding transitive dependencies

Two deliberate denormalizations are reserved for the analytics layer:
- a `fact_enrollments` star-schema fact table
- descriptive dimensions such as `dim_student` with embedded reporting attributes

This separation keeps OLTP transactions clean while making OLAP queries fast and explainable.
