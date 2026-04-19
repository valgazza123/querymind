-- QueryMind Phase 3: analytics star schema and OLAP queries.
-- The normalized OLTP schema lives in public.*. This warehouse is deliberately
-- denormalized so dashboard queries avoid repeated 7-table joins.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.dim_department (
    department_key BIGSERIAL PRIMARY KEY,
    department_id BIGINT NOT NULL UNIQUE,
    department_code VARCHAR(20) NOT NULL,
    department_name VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_student (
    student_key BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL UNIQUE,
    roll_number VARCHAR(30) NOT NULL,
    full_name VARCHAR(161) NOT NULL,
    department_name VARCHAR(120) NOT NULL,
    program_level VARCHAR(20) NOT NULL,
    admission_year INTEGER NOT NULL,
    hostel_flag BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS analytics.dim_faculty (
    faculty_key BIGSERIAL PRIMARY KEY,
    faculty_id BIGINT NOT NULL UNIQUE,
    employee_code VARCHAR(30) NOT NULL,
    full_name VARCHAR(161) NOT NULL,
    designation VARCHAR(60) NOT NULL,
    department_name VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_course (
    course_key BIGSERIAL PRIMARY KEY,
    course_id BIGINT NOT NULL UNIQUE,
    course_code VARCHAR(20) NOT NULL,
    course_title VARCHAR(150) NOT NULL,
    credits SMALLINT NOT NULL,
    course_type VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_time (
    time_key BIGSERIAL PRIMARY KEY,
    semester_id BIGINT NOT NULL UNIQUE,
    academic_year VARCHAR(9) NOT NULL,
    term_name VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.fact_enrollments (
    fact_enrollment_key BIGSERIAL PRIMARY KEY,
    enrollment_id BIGINT NOT NULL UNIQUE,
    student_key BIGINT NOT NULL REFERENCES analytics.dim_student(student_key),
    course_key BIGINT NOT NULL REFERENCES analytics.dim_course(course_key),
    faculty_key BIGINT NOT NULL REFERENCES analytics.dim_faculty(faculty_key),
    department_key BIGINT NOT NULL REFERENCES analytics.dim_department(department_key),
    time_key BIGINT NOT NULL REFERENCES analytics.dim_time(time_key),
    grade_points NUMERIC(4,2),
    fees_paid NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    attendance_pct NUMERIC(5,2),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fact_enrollments_dimensions
    ON analytics.fact_enrollments (department_key, faculty_key, time_key);

CREATE INDEX IF NOT EXISTS idx_fact_enrollments_student_time
    ON analytics.fact_enrollments (student_key, time_key);

-- ROLLUP: total grade points by department -> semester -> grand total.
-- SELECT
--     dd.department_name,
--     dt.academic_year,
--     dt.term_name,
--     SUM(fe.grade_points) AS total_grade_points,
--     GROUPING(dd.department_name) AS is_department_total,
--     GROUPING(dt.term_name) AS is_semester_total
-- FROM analytics.fact_enrollments AS fe
-- JOIN analytics.dim_department AS dd ON dd.department_key = fe.department_key
-- JOIN analytics.dim_time AS dt ON dt.time_key = fe.time_key
-- GROUP BY ROLLUP (dd.department_name, dt.academic_year, dt.term_name);

-- CUBE: cross-analysis of average grades by department, faculty, and semester.
-- SELECT
--     dd.department_name,
--     df.full_name AS faculty_name,
--     dt.term_name,
--     ROUND(AVG(fe.grade_points), 2) AS avg_grade_points
-- FROM analytics.fact_enrollments AS fe
-- JOIN analytics.dim_department AS dd ON dd.department_key = fe.department_key
-- JOIN analytics.dim_faculty AS df ON df.faculty_key = fe.faculty_key
-- JOIN analytics.dim_time AS dt ON dt.time_key = fe.time_key
-- GROUP BY CUBE (dd.department_name, df.full_name, dt.term_name);

-- GROUPING SETS: flexible dashboard aggregations in one scan.
-- SELECT
--     dd.department_name,
--     dc.course_title,
--     dt.term_name,
--     COUNT(*) AS enrollments,
--     ROUND(AVG(fe.attendance_pct), 2) AS avg_attendance_pct
-- FROM analytics.fact_enrollments AS fe
-- JOIN analytics.dim_department AS dd ON dd.department_key = fe.department_key
-- JOIN analytics.dim_course AS dc ON dc.course_key = fe.course_key
-- JOIN analytics.dim_time AS dt ON dt.time_key = fe.time_key
-- GROUP BY GROUPING SETS (
--     (dd.department_name),
--     (dd.department_name, dc.course_title),
--     (dt.term_name),
--     ()
-- );
