-- QueryMind Phase 3.2: PostgreSQL OLAP queries.

-- ROLLUP: total grade points by department -> by semester -> grand total.
SELECT
    dd.department_name,
    dt.academic_year,
    dt.term_name,
    SUM(fe.grade_points) AS total_grade_points,
    GROUPING(dd.department_name) AS department_grouping,
    GROUPING(dt.term_name) AS semester_grouping
FROM analytics.fact_enrollments AS fe
JOIN analytics.dim_department AS dd ON dd.department_key = fe.department_key
JOIN analytics.dim_time AS dt ON dt.time_key = fe.time_key
GROUP BY ROLLUP (dd.department_name, dt.academic_year, dt.term_name)
ORDER BY dd.department_name NULLS LAST, dt.academic_year NULLS LAST, dt.term_name NULLS LAST;

-- CUBE: cross-analysis of average grades by department, faculty, and semester.
SELECT
    dd.department_name,
    df.full_name AS faculty_name,
    dt.term_name,
    ROUND(AVG(fe.grade_points), 2) AS avg_grade_points,
    COUNT(*) AS enrollment_count
FROM analytics.fact_enrollments AS fe
JOIN analytics.dim_department AS dd ON dd.department_key = fe.department_key
JOIN analytics.dim_faculty AS df ON df.faculty_key = fe.faculty_key
JOIN analytics.dim_time AS dt ON dt.time_key = fe.time_key
GROUP BY CUBE (dd.department_name, df.full_name, dt.term_name)
ORDER BY dd.department_name NULLS LAST, df.full_name NULLS LAST, dt.term_name NULLS LAST;

-- GROUPING SETS: flexible aggregation for a dashboard.
SELECT
    dd.department_name,
    dc.course_title,
    dt.term_name,
    COUNT(*) AS enrollment_count,
    ROUND(AVG(fe.attendance_pct), 2) AS avg_attendance_pct,
    ROUND(SUM(fe.fees_paid), 2) AS fees_paid
FROM analytics.fact_enrollments AS fe
JOIN analytics.dim_department AS dd ON dd.department_key = fe.department_key
JOIN analytics.dim_course AS dc ON dc.course_key = fe.course_key
JOIN analytics.dim_time AS dt ON dt.time_key = fe.time_key
GROUP BY GROUPING SETS (
    (dd.department_name),
    (dd.department_name, dc.course_title),
    (dt.term_name),
    ()
)
ORDER BY dd.department_name NULLS LAST, dc.course_title NULLS LAST, dt.term_name NULLS LAST;
