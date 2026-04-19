# QueryMind Phase 1.1: ER Diagram Design

## Scope
University Management System ER model for the QueryMind demo database.

This design intentionally covers:
- strong entities
- weak entities
- identifying relationships
- total vs partial participation
- two specialization/generalization hierarchies
- enough academic and administrative breadth to support OLTP queries, OLAP queries, and NL2SQL demos

## Specialization / Generalization Hierarchies

### Hierarchy 1: Person -> Student, Faculty, Staff
- Supertype: `Person`
- Subtypes: `Student`, `Faculty`, `Staff`
- Constraint: `total, disjoint`
- Reason: every person recorded in the system belongs to exactly one operational role

### Hierarchy 2: Assessment -> Exam, Assignment
- Supertype: `Assessment`
- Subtypes: `Exam`, `Assignment`
- Constraint: `total, disjoint`
- Reason: each assessment event is either an exam or an assignment in this project model

## Entities

### 1. Department
Represents an academic department.

Attributes:
- `department_id` (PK)
- `department_code` (unique)
- `department_name`
- `office_phone`
- `office_email`
- `building_name`
- `budget`
- `created_at`

### 2. Person
Common supertype for all people in the university.

Attributes:
- `person_id` (PK)
- `first_name`
- `last_name`
- `date_of_birth`
- `gender`
- `email` (unique)
- `phone`
- `address_line`
- `city`
- `state`
- `postal_code`
- `person_type`
- `created_at`

### 3. Student
Subtype of `Person`.

Attributes:
- `student_id` (PK, also FK -> Person.person_id)
- `roll_number` (unique)
- `department_id` (FK -> Department)
- `admission_date`
- `current_year`
- `program_level`
- `status`
- `cgpa`

### 4. Faculty
Subtype of `Person`.

Attributes:
- `faculty_id` (PK, also FK -> Person.person_id)
- `employee_code` (unique)
- `department_id` (FK -> Department)
- `designation`
- `hire_date`
- `salary`
- `specialization`

### 5. Staff
Subtype of `Person`.

Attributes:
- `staff_id` (PK, also FK -> Person.person_id)
- `employee_code` (unique)
- `department_id` (FK -> Department, nullable because some staff may be central admin)
- `job_title`
- `hire_date`
- `salary`

### 6. Course
Represents a catalog course.

Attributes:
- `course_id` (PK)
- `course_code` (unique)
- `department_id` (FK -> Department)
- `course_title`
- `credits`
- `course_level`
- `course_type`
- `description`

### 7. Semester
Represents an academic term.

Attributes:
- `semester_id` (PK)
- `academic_year`
- `term_name`
- `start_date`
- `end_date`
- `is_current`

### 8. Section
Represents a specific offering of a course in a semester.

Attributes:
- `section_id` (PK)
- `course_id` (FK -> Course)
- `semester_id` (FK -> Semester)
- `faculty_id` (FK -> Faculty)
- `section_code`
- `room_no`
- `schedule_pattern`
- `capacity`
- `delivery_mode`

### 9. Enrollment
Associative entity between `Student` and `Section`.

Attributes:
- `enrollment_id` (PK)
- `student_id` (FK -> Student)
- `section_id` (FK -> Section)
- `enrollment_date`
- `enrollment_status`
- `attendance_pct`
- `final_grade_letter`
- `final_grade_points`

Candidate key:
- (`student_id`, `section_id`)

### 10. Assessment
Supertype for assessment events linked to a section.

Attributes:
- `assessment_id` (PK)
- `section_id` (FK -> Section)
- `title`
- `assessment_type`
- `max_marks`
- `weightage_pct`
- `due_date`

### 11. Exam
Subtype of `Assessment`.

Attributes:
- `exam_id` (PK, also FK -> Assessment.assessment_id)
- `exam_mode`
- `exam_date`
- `duration_minutes`
- `exam_hall`

### 12. Assignment
Subtype of `Assessment`.

Attributes:
- `assignment_id` (PK, also FK -> Assessment.assessment_id)
- `release_date`
- `submission_mode`
- `max_attempts`

### 13. Exam_Result
Weak entity dependent on `Exam` and `Student`.

Attributes:
- `exam_id` (partial key, FK -> Exam)
- `student_id` (partial key, FK -> Student)
- `marks_obtained`
- `grade_letter`
- `evaluated_at`
- `remarks`

Primary key:
- (`exam_id`, `student_id`)

Identification:
- identified by Exam + Student

### 14. Assignment_Submission
Weak entity dependent on `Assignment` and `Student`.

Attributes:
- `assignment_id` (partial key, FK -> Assignment)
- `student_id` (partial key, FK -> Student)
- `attempt_no` (partial key)
- `submitted_at`
- `score`
- `status`
- `feedback`

Primary key:
- (`assignment_id`, `student_id`, `attempt_no`)

### 15. Fee_Invoice
Represents billing generated for a student per semester.

Attributes:
- `invoice_id` (PK)
- `student_id` (FK -> Student)
- `semester_id` (FK -> Semester)
- `invoice_number` (unique)
- `invoice_date`
- `tuition_amount`
- `hostel_amount`
- `scholarship_amount`
- `penalty_amount`
- `total_amount`
- `status`
- `due_date`

### 16. Fee_Payment
Represents a payment against an invoice.

Attributes:
- `payment_id` (PK)
- `invoice_id` (FK -> Fee_Invoice)
- `payment_date`
- `amount_paid`
- `payment_method`
- `transaction_ref` (unique)
- `payment_status`

### 17. Hostel
Represents a hostel building.

Attributes:
- `hostel_id` (PK)
- `hostel_name`
- `hostel_type`
- `capacity`
- `warden_name`
- `contact_number`

### 18. Hostel_Room
Represents rooms inside a hostel.

Attributes:
- `room_id` (PK)
- `hostel_id` (FK -> Hostel)
- `room_number`
- `floor_no`
- `bed_capacity`
- `room_type`

Candidate key:
- (`hostel_id`, `room_number`)

### 19. Hostel_Allotment
Associative entity representing student room allotment over time.

Attributes:
- `allotment_id` (PK)
- `student_id` (FK -> Student)
- `room_id` (FK -> Hostel_Room)
- `semester_id` (FK -> Semester)
- `allotted_from`
- `allotted_to`
- `status`

## Relationships With Cardinality and Participation

### R1. Department employs/contains Faculty
- Relationship: `Department` -> `Faculty`
- Cardinality: `1 : N`
- Participation:
  - `Faculty`: total
  - `Department`: partial
- Meaning: every faculty member belongs to exactly one department; a department may have zero or more faculty members

### R2. Department admits Students
- Relationship: `Department` -> `Student`
- Cardinality: `1 : N`
- Participation:
  - `Student`: total
  - `Department`: partial
- Meaning: every student belongs to exactly one home department

### R3. Department offers Courses
- Relationship: `Department` -> `Course`
- Cardinality: `1 : N`
- Participation:
  - `Course`: total
  - `Department`: partial
- Meaning: every course is owned by one department

### R4. Person specialization into Student / Faculty / Staff
- Relationship: ISA
- Cardinality: supertype-subtype
- Participation:
  - `Person`: total in specialization
  - subtypes: disjoint
- Meaning: each person is exactly one of Student, Faculty, or Staff

### R5. Course offered as Sections
- Relationship: `Course` -> `Section`
- Cardinality: `1 : N`
- Participation:
  - `Section`: total
  - `Course`: partial
- Meaning: one course can have many semester-wise sections; each section belongs to one course

### R6. Semester contains Sections
- Relationship: `Semester` -> `Section`
- Cardinality: `1 : N`
- Participation:
  - `Section`: total
  - `Semester`: partial
- Meaning: each section is scheduled in exactly one semester

### R7. Faculty teaches Section
- Relationship: `Faculty` -> `Section`
- Cardinality: `1 : N`
- Participation:
  - `Section`: total
  - `Faculty`: partial
- Meaning: every section must have one instructor; a faculty member may teach zero or more sections

### R8. Student enrolls in Section
- Relationship: `Student` <-> `Section` resolved by `Enrollment`
- Cardinality: `M : N`
- Participation:
  - `Enrollment`: total to both `Student` and `Section`
  - `Student`: partial
  - `Section`: partial
- Meaning: students may enroll in many sections and sections may contain many students

### R9. Section has Assessments
- Relationship: `Section` -> `Assessment`
- Cardinality: `1 : N`
- Participation:
  - `Assessment`: total
  - `Section`: partial
- Meaning: an assessment belongs to one section; a section may have multiple assessments

### R10. Assessment specialization into Exam / Assignment
- Relationship: ISA
- Cardinality: supertype-subtype
- Participation:
  - `Assessment`: total in specialization
  - subtypes: disjoint
- Meaning: every assessment is either an exam or an assignment

### R11. Exam generates Exam_Result
- Relationship: `Exam` -> `Exam_Result`
- Cardinality: `1 : N`
- Participation:
  - `Exam_Result`: total
  - `Exam`: partial
- Meaning: an exam may produce many student-specific results

### R12. Student receives Exam_Result
- Relationship: `Student` -> `Exam_Result`
- Cardinality: `1 : N`
- Participation:
  - `Exam_Result`: total
  - `Student`: partial
- Meaning: result rows cannot exist without a student

### R13. Assignment produces Assignment_Submission
- Relationship: `Assignment` -> `Assignment_Submission`
- Cardinality: `1 : N`
- Participation:
  - `Assignment_Submission`: total
  - `Assignment`: partial

### R14. Student submits Assignment_Submission
- Relationship: `Student` -> `Assignment_Submission`
- Cardinality: `1 : N`
- Participation:
  - `Assignment_Submission`: total
  - `Student`: partial

### R15. Student receives Fee_Invoice
- Relationship: `Student` -> `Fee_Invoice`
- Cardinality: `1 : N`
- Participation:
  - `Fee_Invoice`: total
  - `Student`: partial

### R16. Semester scopes Fee_Invoice
- Relationship: `Semester` -> `Fee_Invoice`
- Cardinality: `1 : N`
- Participation:
  - `Fee_Invoice`: total
  - `Semester`: partial

### R17. Fee_Invoice paid by Fee_Payment
- Relationship: `Fee_Invoice` -> `Fee_Payment`
- Cardinality: `1 : N`
- Participation:
  - `Fee_Payment`: total
  - `Fee_Invoice`: partial
- Meaning: an invoice may be paid in installments

### R18. Hostel contains Hostel_Room
- Relationship: `Hostel` -> `Hostel_Room`
- Cardinality: `1 : N`
- Participation:
  - `Hostel_Room`: total
  - `Hostel`: partial

### R19. Student allotted Hostel_Room through Hostel_Allotment
- Relationship: `Student` <-> `Hostel_Room` resolved by `Hostel_Allotment`
- Cardinality: `M : N` over time
- Participation:
  - `Hostel_Allotment`: total to both parent entities
  - `Student`: partial
  - `Hostel_Room`: partial
- Meaning: a student may change rooms over semesters; a room serves different students over time

### R20. Semester scopes Hostel_Allotment
- Relationship: `Semester` -> `Hostel_Allotment`
- Cardinality: `1 : N`
- Participation:
  - `Hostel_Allotment`: total
  - `Semester`: partial

## Weak Entities Summary

### Weak Entity 1: Exam_Result
- Owner entities: `Exam`, `Student`
- Identifying relationship: result exists only for a specific student taking a specific exam
- Primary key: (`exam_id`, `student_id`)

### Weak Entity 2: Assignment_Submission
- Owner entities: `Assignment`, `Student`
- Identifying relationship: submission exists only for a specific student and assignment
- Primary key: (`assignment_id`, `student_id`, `attempt_no`)

## Participation Constraints to Show Explicitly in the Diagram

Mark these as `total participation`:
- `Student` in belongs-to `Department`
- `Faculty` in belongs-to `Department`
- `Course` in offered-by `Department`
- `Section` in of `Course`
- `Section` in during `Semester`
- `Section` in taught-by `Faculty`
- `Assessment` in belongs-to `Section`
- `Exam_Result` in identifying relationships with `Exam` and `Student`
- `Assignment_Submission` in identifying relationships with `Assignment` and `Student`
- `Fee_Invoice` in billed-to `Student` and for `Semester`
- `Fee_Payment` in against `Fee_Invoice`
- `Hostel_Room` in belongs-to `Hostel`
- `Hostel_Allotment` in links `Student`, `Hostel_Room`, and `Semester`

Mark these as `partial participation`:
- `Department` in most relationships
- `Course` in has-sections
- `Semester` in has-sections / invoices / allotments
- `Student` in enrollments, results, submissions, invoices, allotments
- `Faculty` in teaches-sections
- `Hostel` in contains-rooms

## Draw.io / dbdiagram Drawing Order

Use this order to draw cleanly:
1. Place `Department` at top center.
2. Place `Person` under it with ISA branches to `Student`, `Faculty`, `Staff`.
3. Place `Course`, `Semester`, and `Section` as the academic core.
4. Place `Assessment` under `Section`, then branch to `Exam` and `Assignment`.
5. Place weak entities `Exam_Result` and `Assignment_Submission` below those branches.
6. Place `Enrollment` between `Student` and `Section`.
7. Place `Fee_Invoice` and `Fee_Payment` on the right.
8. Place `Hostel`, `Hostel_Room`, and `Hostel_Allotment` on the left or bottom.

## Why This ER Model Is Good for QueryMind
- It supports simple SQL, advanced SQL, joins, views, and normalization exercises.
- It includes weak entities and ISA hierarchies for DBMS theory coverage.
- It supports transactional workflows: enrollment, grade submission, fee payment.
- It supports analytics later through denormalized warehouse facts and dimensions.
- It gives the NL2SQL engine enough schema richness to demonstrate schema-aware generation.
