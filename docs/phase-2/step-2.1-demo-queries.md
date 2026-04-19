# QueryMind Phase 2.1: 20 Demonstration SQL Queries

## 1. Students with GPA above 8.5
Natural language question: Show all students with CGPA above 8.5 ordered by highest GPA.
```sql
SELECT roll_number, cgpa
FROM student
WHERE cgpa > 8.50
ORDER BY cgpa DESC, roll_number ASC;
```
Concept: `SELECT`, `WHERE`, `ORDER BY`

## 2. Student count by department
Natural language question: Count active students in each department.
```sql
SELECT d.department_name, COUNT(*) AS student_count
FROM department AS d
JOIN student AS s ON s.department_id = d.department_id
WHERE s.status = 'active'
GROUP BY d.department_name
ORDER BY student_count DESC;
```
Concept: `GROUP BY`, aggregation

## 3. Departments with average CGPA above 8
Natural language question: Which departments have an average CGPA above 8?
```sql
SELECT d.department_name, ROUND(AVG(s.cgpa), 2) AS avg_cgpa
FROM department AS d
JOIN student AS s ON s.department_id = d.department_id
GROUP BY d.department_name
HAVING AVG(s.cgpa) > 8.0
ORDER BY avg_cgpa DESC;
```
Concept: `HAVING`

## 4. Inner join for enrolled students and courses
Natural language question: Show students and the course codes they are enrolled in.
```sql
SELECT s.roll_number, c.course_code
FROM enrollment AS e
JOIN student AS s ON s.student_id = e.student_id
JOIN section AS sec ON sec.section_id = e.section_id
JOIN course AS c ON c.course_id = sec.course_id
ORDER BY s.roll_number, c.course_code;
```
Concept: `INNER JOIN`

## 5. Left join for all departments with student counts
Natural language question: Show all departments, even those with no students yet.
```sql
SELECT d.department_name, COUNT(s.student_id) AS student_count
FROM department AS d
LEFT JOIN student AS s ON s.department_id = d.department_id
GROUP BY d.department_name
ORDER BY d.department_name;
```
Concept: `LEFT JOIN`

## 6. Right join for all semester sections
Natural language question: Show all sections and their faculty names, including sections that may not yet be assigned.
```sql
SELECT sec.section_code, p.first_name || ' ' || p.last_name AS faculty_name
FROM faculty AS f
RIGHT JOIN section AS sec ON sec.faculty_id = f.faculty_id
LEFT JOIN person AS p ON p.person_id = f.faculty_id
ORDER BY sec.section_code;
```
Concept: `RIGHT JOIN`

## 7. Full outer join for student-hostel coverage
Natural language question: Compare students and hostel allotments, including unmatched records on either side.
```sql
SELECT s.roll_number, ha.allotment_id
FROM student AS s
FULL OUTER JOIN hostel_allotment AS ha ON ha.student_id = s.student_id
ORDER BY s.roll_number NULLS LAST, ha.allotment_id NULLS LAST;
```
Concept: `FULL OUTER JOIN`

## 8. Self join on course prerequisites
Natural language question: Show each course with its prerequisite course code.
```sql
SELECT c.course_code, pre.course_code AS prerequisite_code
FROM course_prerequisite AS cp
JOIN course AS c ON c.course_id = cp.course_id
JOIN course AS pre ON pre.course_id = cp.prerequisite_course_id
ORDER BY c.course_code, prerequisite_code;
```
Concept: `SELF JOIN`

## 9. Non-correlated subquery
Natural language question: Show students whose CGPA is above the overall average.
```sql
SELECT roll_number, cgpa
FROM student
WHERE cgpa > (SELECT AVG(cgpa) FROM student)
ORDER BY cgpa DESC;
```
Concept: non-correlated subquery

## 10. Correlated subquery
Natural language question: Show faculty members who teach more sections than the average for their department.
```sql
SELECT f.faculty_id, p.first_name || ' ' || p.last_name AS faculty_name
FROM faculty AS f
JOIN person AS p ON p.person_id = f.faculty_id
WHERE (
    SELECT COUNT(*)
    FROM section AS sec
    WHERE sec.faculty_id = f.faculty_id
) > (
    SELECT AVG(section_count)
    FROM (
        SELECT COUNT(*) AS section_count
        FROM faculty AS f2
        LEFT JOIN section AS sec2 ON sec2.faculty_id = f2.faculty_id
        WHERE f2.department_id = f.department_id
        GROUP BY f2.faculty_id
    ) AS dept_counts
);
```
Concept: correlated subquery

## 11. UNION
Natural language question: Show all unique IDs of people who are either students or faculty.
```sql
SELECT student_id AS person_ref FROM student
UNION
SELECT faculty_id AS person_ref FROM faculty
ORDER BY person_ref;
```
Concept: `UNION`

## 12. INTERSECT
Natural language question: Which students are both hostel residents and fee defaulters?
```sql
SELECT DISTINCT student_id
FROM hostel_allotment
WHERE status = 'active'
INTERSECT
SELECT student_id
FROM fee_invoice
WHERE status IN ('unpaid', 'overdue');
```
Concept: `INTERSECT`

## 13. EXCEPT
Natural language question: Which students have enrollments but no hostel allotment?
```sql
SELECT DISTINCT student_id
FROM enrollment
EXCEPT
SELECT DISTINCT student_id
FROM hostel_allotment
WHERE status = 'active';
```
Concept: `EXCEPT`

## 14. Window function with RANK
Natural language question: Rank students by GPA within each department.
```sql
SELECT
    d.department_name,
    s.roll_number,
    s.cgpa,
    RANK() OVER (PARTITION BY d.department_name ORDER BY s.cgpa DESC) AS dept_rank
FROM student AS s
JOIN department AS d ON d.department_id = s.department_id
ORDER BY d.department_name, dept_rank;
```
Concept: `RANK() OVER (PARTITION BY ...)`

## 15. Window function with DENSE_RANK
Natural language question: Dense-rank courses by enrollment size within each semester.
```sql
SELECT
    sem.academic_year,
    sem.term_name,
    c.course_code,
    COUNT(e.enrollment_id) AS enrollment_count,
    DENSE_RANK() OVER (
        PARTITION BY sem.semester_id
        ORDER BY COUNT(e.enrollment_id) DESC
    ) AS dense_rank_in_semester
FROM section AS sec
JOIN semester AS sem ON sem.semester_id = sec.semester_id
JOIN course AS c ON c.course_id = sec.course_id
LEFT JOIN enrollment AS e ON e.section_id = sec.section_id
GROUP BY sem.semester_id, sem.academic_year, sem.term_name, c.course_code
ORDER BY sem.academic_year, sem.term_name, dense_rank_in_semester;
```
Concept: `DENSE_RANK`

## 16. Window function with ROW_NUMBER
Natural language question: Show the latest fee payment per invoice.
```sql
WITH ranked_payments AS (
    SELECT
        fp.*,
        ROW_NUMBER() OVER (
            PARTITION BY fp.invoice_id
            ORDER BY fp.payment_date DESC, fp.payment_id DESC
        ) AS rn
    FROM fee_payment AS fp
)
SELECT invoice_id, payment_date, amount_paid, payment_status
FROM ranked_payments
WHERE rn = 1;
```
Concept: `ROW_NUMBER`, CTE

## 17. Recursive CTE for prerequisite chains
Natural language question: Show the prerequisite chain for a given course.
```sql
WITH RECURSIVE prereq_chain AS (
    SELECT
        cp.course_id,
        cp.prerequisite_course_id,
        1 AS depth
    FROM course_prerequisite AS cp
    WHERE cp.course_id = 5

    UNION ALL

    SELECT
        pc.course_id,
        cp.prerequisite_course_id,
        pc.depth + 1
    FROM prereq_chain AS pc
    JOIN course_prerequisite AS cp
      ON cp.course_id = pc.prerequisite_course_id
)
SELECT course_id, prerequisite_course_id, depth
FROM prereq_chain
ORDER BY depth;
```
Concept: recursive CTE

## 18. Transcript view usage
Natural language question: Show transcript rows for a student roll number.
```sql
SELECT *
FROM student_transcript
WHERE roll_number = 'MPSTME2024001'
ORDER BY academic_year, term_name, course_code;
```
Concept: view usage

## 19. ROLLUP aggregation
Natural language question: Show total grade points by department, by semester, and grand total.
```sql
SELECT
    d.department_name,
    sem.term_name,
    SUM(e.final_grade_points) AS total_grade_points
FROM enrollment AS e
JOIN student AS s ON s.student_id = e.student_id
JOIN department AS d ON d.department_id = s.department_id
JOIN section AS sec ON sec.section_id = e.section_id
JOIN semester AS sem ON sem.semester_id = sec.semester_id
GROUP BY ROLLUP (d.department_name, sem.term_name)
ORDER BY d.department_name NULLS LAST, sem.term_name NULLS LAST;
```
Concept: `ROLLUP`

## 20. CUBE aggregation
Natural language question: Cross-analyze average grade points by department, faculty, and semester.
```sql
SELECT
    d.department_name,
    p.first_name || ' ' || p.last_name AS faculty_name,
    sem.term_name,
    ROUND(AVG(e.final_grade_points), 2) AS avg_grade_points
FROM enrollment AS e
JOIN section AS sec ON sec.section_id = e.section_id
JOIN faculty AS f ON f.faculty_id = sec.faculty_id
JOIN person AS p ON p.person_id = f.faculty_id
JOIN department AS d ON d.department_id = f.department_id
JOIN semester AS sem ON sem.semester_id = sec.semester_id
GROUP BY CUBE (d.department_name, faculty_name, sem.term_name)
ORDER BY d.department_name NULLS LAST, faculty_name NULLS LAST, sem.term_name NULLS LAST;
```
Concept: `CUBE`

