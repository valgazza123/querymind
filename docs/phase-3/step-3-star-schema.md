# QueryMind Phase 3: Star Schema and OLAP

## Star Schema

Central fact table:
- `analytics.fact_enrollments`
  - measures: `grade_points`, `fees_paid`, `attendance_pct`

Dimensions:
- `analytics.dim_student`
- `analytics.dim_course`
- `analytics.dim_faculty`
- `analytics.dim_department`
- `analytics.dim_time`

## Why this is de-normalized

The OLTP schema is optimized for correctness and transactional updates. Analytics queries would otherwise join:
- `enrollment`
- `section`
- `course`
- `student`
- `faculty`
- `department`
- `semester`
- fee tables

The star schema duplicates descriptive attributes into dimensions so dashboards can:
- group quickly by department, faculty, course, and semester
- compute rollups with fewer joins
- separate historical reporting from transactional workload

Tradeoff:
- more storage
- ETL complexity
- occasional controlled redundancy

## OLAP Queries

### ROLLUP
```sql
SELECT
    dd.department_name,
    dt.term_name,
    SUM(fe.grade_points) AS total_grade_points
FROM analytics.fact_enrollments AS fe
JOIN analytics.dim_department AS dd ON dd.department_key = fe.department_key
JOIN analytics.dim_time AS dt ON dt.time_key = fe.time_key
GROUP BY ROLLUP (dd.department_name, dt.term_name)
ORDER BY dd.department_name NULLS LAST, dt.term_name NULLS LAST;
```

### CUBE
```sql
SELECT
    dd.department_name,
    df.full_name AS faculty_name,
    dt.term_name,
    ROUND(AVG(fe.grade_points), 2) AS avg_grade_points
FROM analytics.fact_enrollments AS fe
JOIN analytics.dim_department AS dd ON dd.department_key = fe.department_key
JOIN analytics.dim_faculty AS df ON df.faculty_key = fe.faculty_key
JOIN analytics.dim_time AS dt ON dt.time_key = fe.time_key
GROUP BY CUBE (dd.department_name, df.full_name, dt.term_name)
ORDER BY dd.department_name NULLS LAST, faculty_name NULLS LAST, dt.term_name NULLS LAST;
```

### GROUPING SETS
```sql
SELECT
    dd.department_name,
    df.full_name AS faculty_name,
    dt.term_name,
    COUNT(*) AS enrollment_count,
    ROUND(AVG(fe.attendance_pct), 2) AS avg_attendance
FROM analytics.fact_enrollments AS fe
JOIN analytics.dim_department AS dd ON dd.department_key = fe.department_key
JOIN analytics.dim_faculty AS df ON df.faculty_key = fe.faculty_key
JOIN analytics.dim_time AS dt ON dt.time_key = fe.time_key
GROUP BY GROUPING SETS (
    (dd.department_name),
    (dd.department_name, dt.term_name),
    (df.full_name, dt.term_name),
    ()
)
ORDER BY dd.department_name NULLS LAST, faculty_name NULLS LAST, dt.term_name NULLS LAST;
```

