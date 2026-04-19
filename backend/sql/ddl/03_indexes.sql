-- QueryMind Phase 1.4: index definitions and rationale.
-- Demonstrates B-tree, composite B-tree, and partial indexes.

CREATE INDEX IF NOT EXISTS idx_student_department_btree
    ON student USING btree (department_id);
-- Chosen because department-wise filtering and joins are frequent in dashboards and transcript lookups.

CREATE INDEX IF NOT EXISTS idx_enrollment_student_section_composite
    ON enrollment USING btree (student_id, section_id);
-- Chosen because enrollment validation and transcript reads commonly match on student and section together.

CREATE INDEX IF NOT EXISTS idx_section_semester_faculty_composite
    ON section USING btree (semester_id, faculty_id);
-- Chosen because faculty-load and semester scheduling queries group by current semester and instructor.

CREATE INDEX IF NOT EXISTS idx_fee_invoice_unpaid_partial
    ON fee_invoice USING btree (student_id, semester_id)
    WHERE status IN ('unpaid', 'partial', 'overdue');
-- Chosen as a partial index because payment workflows mostly target open invoices, not already paid ones.
