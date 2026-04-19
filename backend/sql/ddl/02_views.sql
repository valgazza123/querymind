-- QueryMind Phase 1.4: views used by NL2SQL and dashboard queries.
-- View 1: student_transcript.
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
