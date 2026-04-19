-- QueryMind Phase 2.1: 20 PostgreSQL demonstration queries.
-- All queries target the canonical Phase 1 schema in public.*.

-- Q01 | Natural language: Show active students with CGPA above 8, highest first.
-- Concept: SELECT, WHERE, ORDER BY, LIMIT.
SELECT p.first_name || ' ' || p.last_name AS student_name, s.roll_number, s.cgpa
FROM student AS s
JOIN person AS p ON p.person_id = s.student_id
WHERE s.status = 'active' AND s.cgpa > 8
ORDER BY s.cgpa DESC, s.roll_number
LIMIT 10;

-- Q02 | Natural language: Count students by department, but only show departments with more than 20 students.
-- Concept: GROUP BY and HAVING.
SELECT d.department_name, COUNT(*) AS student_count, ROUND(AVG(s.cgpa), 2) AS avg_cgpa
FROM department AS d
JOIN student AS s ON s.department_id = d.department_id
GROUP BY d.department_id, d.department_name
HAVING COUNT(*) > 20
ORDER BY student_count DESC;

-- Q03 | Natural language: Show each completed enrollment with student, course, faculty, semester, and grade.
-- Concept: INNER JOIN across a normalized schema.
SELECT
    p.first_name || ' ' || p.last_name AS student_name,
    c.course_code,
    c.course_title,
    fp.first_name || ' ' || fp.last_name AS faculty_name,
    sem.academic_year,
    sem.term_name,
    e.final_grade_letter,
    e.final_grade_points
FROM enrollment AS e
JOIN student AS s ON s.student_id = e.student_id
JOIN person AS p ON p.person_id = s.student_id
JOIN section AS sec ON sec.section_id = e.section_id
JOIN course AS c ON c.course_id = sec.course_id
JOIN faculty AS f ON f.faculty_id = sec.faculty_id
JOIN person AS fp ON fp.person_id = f.faculty_id
JOIN semester AS sem ON sem.semester_id = sec.semester_id
WHERE e.enrollment_status = 'completed'
ORDER BY sem.start_date DESC, c.course_code;

-- Q04 | Natural language: List all courses, including courses that currently have no sections.
-- Concept: LEFT JOIN.
SELECT c.course_code, c.course_title, COUNT(sec.section_id) AS section_count
FROM course AS c
LEFT JOIN section AS sec ON sec.course_id = c.course_id
GROUP BY c.course_id, c.course_code, c.course_title
ORDER BY section_count DESC, c.course_code;

-- Q05 | Natural language: Show all departments, including departments with zero active students.
-- Concept: RIGHT JOIN.
SELECT d.department_name, COUNT(s.student_id) AS active_students
FROM student AS s
RIGHT JOIN department AS d
    ON d.department_id = s.department_id
   AND s.status = 'active'
GROUP BY d.department_id, d.department_name
ORDER BY active_students DESC, d.department_name;

-- Q06 | Natural language: Compare sections offered in Monsoon vs Winter terms.
-- Concept: FULL OUTER JOIN.
WITH monsoon AS (
    SELECT c.course_id, c.course_code, COUNT(*) AS monsoon_sections
    FROM section AS sec
    JOIN semester AS sem ON sem.semester_id = sec.semester_id
    JOIN course AS c ON c.course_id = sec.course_id
    WHERE sem.term_name = 'Monsoon'
    GROUP BY c.course_id, c.course_code
),
winter AS (
    SELECT c.course_id, c.course_code, COUNT(*) AS winter_sections
    FROM section AS sec
    JOIN semester AS sem ON sem.semester_id = sec.semester_id
    JOIN course AS c ON c.course_id = sec.course_id
    WHERE sem.term_name = 'Winter'
    GROUP BY c.course_id, c.course_code
)
SELECT
    COALESCE(m.course_code, w.course_code) AS course_code,
    COALESCE(m.monsoon_sections, 0) AS monsoon_sections,
    COALESCE(w.winter_sections, 0) AS winter_sections
FROM monsoon AS m
FULL OUTER JOIN winter AS w ON w.course_id = m.course_id
ORDER BY course_code;

-- Q07 | Natural language: Find course pairs in the same department with the same credit count.
-- Concept: SELF JOIN.
SELECT c1.course_code AS course_a, c2.course_code AS course_b, d.department_name, c1.credits
FROM course AS c1
JOIN course AS c2
  ON c1.department_id = c2.department_id
 AND c1.credits = c2.credits
 AND c1.course_id < c2.course_id
JOIN department AS d ON d.department_id = c1.department_id
ORDER BY d.department_name, c1.credits DESC;

-- Q08 | Natural language: Show students whose CGPA is above the university average.
-- Concept: Non-correlated scalar subquery.
SELECT p.first_name || ' ' || p.last_name AS student_name, s.roll_number, s.cgpa
FROM student AS s
JOIN person AS p ON p.person_id = s.student_id
WHERE s.cgpa > (SELECT AVG(cgpa) FROM student WHERE cgpa IS NOT NULL)
ORDER BY s.cgpa DESC;

-- Q09 | Natural language: Show the top student within each department.
-- Concept: Correlated subquery.
SELECT d.department_name, p.first_name || ' ' || p.last_name AS student_name, s.cgpa
FROM student AS s
JOIN person AS p ON p.person_id = s.student_id
JOIN department AS d ON d.department_id = s.department_id
WHERE s.cgpa = (
    SELECT MAX(s2.cgpa)
    FROM student AS s2
    WHERE s2.department_id = s.department_id
);

-- Q10 | Natural language: Which students have at least one hostel allotment?
-- Concept: EXISTS subquery.
SELECT s.roll_number, p.first_name || ' ' || p.last_name AS student_name
FROM student AS s
JOIN person AS p ON p.person_id = s.student_id
WHERE EXISTS (
    SELECT 1 FROM hostel_allotment AS ha WHERE ha.student_id = s.student_id
)
ORDER BY s.roll_number;

-- Q11 | Natural language: Which courses have no prerequisites?
-- Concept: NOT EXISTS subquery.
SELECT c.course_code, c.course_title
FROM course AS c
WHERE NOT EXISTS (
    SELECT 1 FROM course_prerequisite AS cp WHERE cp.course_id = c.course_id
)
ORDER BY c.course_code;

-- Q12 | Natural language: List people who are either students or faculty in a single result set.
-- Concept: UNION.
SELECT p.email, 'student' AS role FROM person AS p JOIN student AS s ON s.student_id = p.person_id
UNION
SELECT p.email, 'faculty' AS role FROM person AS p JOIN faculty AS f ON f.faculty_id = p.person_id
ORDER BY email;

-- Q13 | Natural language: Which students are both enrolled and have a fee invoice?
-- Concept: INTERSECT.
SELECT student_id FROM enrollment
INTERSECT
SELECT student_id FROM fee_invoice
ORDER BY student_id;

-- Q14 | Natural language: Which students have invoices but no successful payments?
-- Concept: EXCEPT.
SELECT student_id FROM fee_invoice
EXCEPT
SELECT fi.student_id
FROM fee_invoice AS fi
JOIN fee_payment AS fp ON fp.invoice_id = fi.invoice_id
WHERE fp.payment_status = 'success'
ORDER BY student_id;

-- Q15 | Natural language: Rank students by CGPA within each department.
-- Concept: RANK window function.
SELECT
    d.department_name,
    s.roll_number,
    s.cgpa,
    RANK() OVER (PARTITION BY d.department_id ORDER BY s.cgpa DESC NULLS LAST) AS dept_rank
FROM student AS s
JOIN department AS d ON d.department_id = s.department_id
ORDER BY d.department_name, dept_rank;

-- Q16 | Natural language: Show the top three students per department without gaps in rank.
-- Concept: DENSE_RANK and ROW_NUMBER over partitions.
WITH ranked AS (
    SELECT
        d.department_name,
        s.roll_number,
        s.cgpa,
        DENSE_RANK() OVER (PARTITION BY d.department_id ORDER BY s.cgpa DESC NULLS LAST) AS dense_rank,
        ROW_NUMBER() OVER (PARTITION BY d.department_id ORDER BY s.cgpa DESC NULLS LAST, s.roll_number) AS row_num
    FROM student AS s
    JOIN department AS d ON d.department_id = s.department_id
)
SELECT * FROM ranked WHERE row_num <= 3 ORDER BY department_name, row_num;

-- Q17 | Natural language: Compare each student's grade to their previous enrolled course grade.
-- Concept: LAG window function.
SELECT
    s.roll_number,
    c.course_code,
    sem.term_name,
    e.final_grade_points,
    LAG(e.final_grade_points) OVER (
        PARTITION BY s.student_id ORDER BY sem.start_date, c.course_code
    ) AS previous_grade_points
FROM enrollment AS e
JOIN student AS s ON s.student_id = e.student_id
JOIN section AS sec ON sec.section_id = e.section_id
JOIN course AS c ON c.course_id = sec.course_id
JOIN semester AS sem ON sem.semester_id = sec.semester_id
ORDER BY s.roll_number, sem.start_date, c.course_code;

-- Q18 | Natural language: Show cumulative fee payments per invoice over time.
-- Concept: SUM window function.
SELECT
    invoice_id,
    payment_date,
    amount_paid,
    SUM(amount_paid) OVER (
        PARTITION BY invoice_id ORDER BY payment_date ROWS UNBOUNDED PRECEDING
    ) AS running_paid_total
FROM fee_payment
WHERE payment_status = 'success'
ORDER BY invoice_id, payment_date;

-- Q19 | Natural language: Find prerequisite chains for every course.
-- Concept: Recursive CTE.
WITH RECURSIVE prereq_chain AS (
    SELECT
        c.course_id,
        c.course_code,
        p.course_id AS prerequisite_id,
        p.course_code AS prerequisite_code,
        1 AS depth,
        ARRAY[c.course_code, p.course_code] AS path
    FROM course AS c
    JOIN course_prerequisite AS cp ON cp.course_id = c.course_id
    JOIN course AS p ON p.course_id = cp.prerequisite_course_id
    UNION ALL
    SELECT
        pc.course_id,
        pc.course_code,
        p.course_id,
        p.course_code,
        pc.depth + 1,
        pc.path || p.course_code
    FROM prereq_chain AS pc
    JOIN course_prerequisite AS cp ON cp.course_id = pc.prerequisite_id
    JOIN course AS p ON p.course_id = cp.prerequisite_course_id
    WHERE NOT p.course_code = ANY(pc.path)
)
SELECT course_code, prerequisite_code, depth, array_to_string(path, ' -> ') AS prerequisite_path
FROM prereq_chain
ORDER BY course_code, depth;

-- Q20 | Natural language: Show grade-point totals by department and semester with subtotals.
-- Concept: ROLLUP.
SELECT
    d.department_name,
    sem.academic_year,
    sem.term_name,
    SUM(e.final_grade_points) AS total_grade_points
FROM enrollment AS e
JOIN student AS s ON s.student_id = e.student_id
JOIN department AS d ON d.department_id = s.department_id
JOIN section AS sec ON sec.section_id = e.section_id
JOIN semester AS sem ON sem.semester_id = sec.semester_id
GROUP BY ROLLUP (d.department_name, sem.academic_year, sem.term_name)
ORDER BY d.department_name NULLS LAST, sem.academic_year NULLS LAST, sem.term_name NULLS LAST;

-- Bonus OLAP | Natural language: Cross-analyze average grades by department, faculty, and semester.
-- Concept: CUBE.
SELECT
    d.department_name,
    fp.first_name || ' ' || fp.last_name AS faculty_name,
    sem.term_name,
    ROUND(AVG(e.final_grade_points), 2) AS avg_grade_points
FROM enrollment AS e
JOIN section AS sec ON sec.section_id = e.section_id
JOIN faculty AS f ON f.faculty_id = sec.faculty_id
JOIN person AS fp ON fp.person_id = f.faculty_id
JOIN student AS s ON s.student_id = e.student_id
JOIN department AS d ON d.department_id = s.department_id
JOIN semester AS sem ON sem.semester_id = sec.semester_id
GROUP BY CUBE (d.department_name, fp.first_name || ' ' || fp.last_name, sem.term_name);
