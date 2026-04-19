# QueryMind Phase 4: Transaction Management

## 1. Student Enrollment Transaction

Isolation level: `SERIALIZABLE`

Why:
- seat availability is a shared mutable resource
- concurrent enrollments can oversubscribe a section if read/write races are allowed

Failure scenario:
- two students attempt the last seat at the same time
- one transaction commits first
- the other sees a serialization failure and rolls back cleanly

Conflict schedule:
- `T1: R(capacity_used), W(enrollment), W(fee_invoice)`
- `T2: R(capacity_used), W(enrollment), W(fee_invoice)`
- conflicting writes on the same logical seat inventory create edges `T1 -> T2` or `T2 -> T1`
- serializable execution prevents a cycle by aborting one transaction

## 2. Grade Submission Transaction

Isolation level: `REPEATABLE READ`

Why:
- a faculty submission should see a stable set of enrollment rows while writing grades
- GPA recalculation must not mix old and new versions during the same transaction

Failure scenario:
- two faculty members attempt to modify the same grade row
- row-level locking or transaction conflict causes one update to wait or fail
- rollback preserves previous valid grades

Conflict graph:
- `T1 -> T2` if `T1` writes `exam_result(student, exam)` and `T2` reads or writes the same tuple before commit
- with proper locking, schedules remain conflict-serializable

## 3. Fee Payment Transaction

Isolation level: `SERIALIZABLE`

Why:
- concurrent payments against the same invoice can double-apply funds
- the payment status and outstanding balance must remain consistent

Failure scenario:
- two payment requests hit the same unpaid invoice simultaneously
- both read the same outstanding amount
- one commit succeeds, the other is rolled back and retried

Conflict graph:
- `T1` reads invoice balance, `T2` reads invoice balance
- `T1` writes payment row and invoice status
- `T2` writes payment row and invoice status
- write-write conflict on the invoice creates a cycle unless serialized

## Django / psycopg transaction code

See [transactions.py](/Users/apple/querymind/backend/core/transactions.py) for full typed implementations.

