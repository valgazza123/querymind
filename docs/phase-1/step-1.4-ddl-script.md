# QueryMind Phase 1.4: PostgreSQL DDL Script

## Output Files

The canonical Phase 1 DDL is split into three executable files:

- `backend/sql/ddl/01_schema.sql`
- `backend/sql/ddl/02_views.sql`
- `backend/sql/ddl/03_indexes.sql`

This split keeps the database boot order explicit:

1. Create tables, primary keys, foreign keys, weak entities, checks, and uniqueness constraints.
2. Create views after all base tables exist.
3. Create indexes after all referenced tables and columns exist.

## Schema Coverage

The normalized OLTP schema includes the following core tables:

- `department`
- `person`
- `student`
- `faculty`
- `staff`
- `semester`
- `course`
- `course_prerequisite`
- `hostel`
- `hostel_room`
- `section`
- `enrollment`
- `assessment`
- `exam`
- `assignment`
- `exam_result`
- `assignment_submission`
- `fee_invoice`
- `fee_payment`
- `hostel_allotment`

## Constraint Coverage

The DDL includes:

- Primary keys on every base table.
- Shared primary-key foreign keys for table-per-type generalization:
  - `student.student_id -> person.person_id`
  - `faculty.faculty_id -> person.person_id`
  - `staff.staff_id -> person.person_id`
  - `exam.exam_id -> assessment.assessment_id`
  - `assignment.assignment_id -> assessment.assessment_id`
- Composite primary keys for weak entities:
  - `exam_result(exam_id, student_id)`
  - `assignment_submission(assignment_id, student_id, attempt_no)`
- Foreign keys with intentional delete behavior:
  - `ON DELETE CASCADE` where child rows cannot exist without the parent.
  - `ON DELETE RESTRICT` where deletion should be blocked to protect academic history.
  - `ON DELETE SET NULL` where a parent deletion should preserve the child row but clear optional ownership.
- `CHECK` constraints for bounded numeric fields and enumerated domain values.
- `UNIQUE` constraints for natural identifiers like department code, email, roll number, course code, invoice number, and candidate keys.

## Views

The DDL defines three required views in `backend/sql/ddl/02_views.sql`:

- `student_transcript`: joins students, courses, sections, semesters, and enrollments for transcript queries.
- `faculty_load`: summarizes teaching load and total section capacity by faculty and semester.
- `department_summary`: summarizes students, faculty, courses, and average CGPA per department.

These views are intentionally useful for the later NL2SQL agent because common natural-language questions can target a readable view instead of requiring the LLM to build a long join every time.

## Indexes

The DDL defines four required indexes in `backend/sql/ddl/03_indexes.sql`:

- `idx_student_department_btree` on `student(department_id)`.
  This B-tree index supports department-wise filtering and joins.
- `idx_enrollment_student_section_composite` on `enrollment(student_id, section_id)`.
  This composite B-tree index supports transcript lookup and enrollment validation.
- `idx_section_semester_faculty_composite` on `section(semester_id, faculty_id)`.
  This composite B-tree index supports faculty-load and schedule queries.
- `idx_fee_invoice_unpaid_partial` on `fee_invoice(student_id, semester_id)` where status is open.
  This partial B-tree index keeps payment workflows fast by excluding already-paid invoices.

Security-role creation is intentionally excluded from Phase 1 DDL. Read-only execution users and secret-managed passwords belong in Phase 6.
