# Database Patterns and Anti-Patterns

## 1. Primary Key

Stable row identity.

Prefer immutable keys.

---

## 2. Natural Key

Business-meaningful unique key.

Often useful as a unique constraint even when a surrogate primary key exists.

---

## 3. Surrogate Key

Database-generated identity independent of business meaning.

---

## 4. Foreign Key

Protects referential integrity.

---

## 5. Check Constraint

Protects domain invariants close to the data.

---

## 6. Covering Index

Includes required columns to reduce table lookups.

---

## 7. Partial or Filtered Index

Indexes a useful subset of rows.

---

## 8. Expression or Function Index

Indexes a computed expression used by queries.

---

## 9. Partitioning

Splits large logical tables for manageability and pruning.

Requires partition-aligned queries and maintenance.

---

## 10. Materialized View

Stores derived query results for faster reads.

Requires refresh and freshness policy.

---

## 11. Read Replica

Scales reads or supports recovery.

Replication lag affects consistency.

---

## 12. Connection Pool

Reuses database connections and limits concurrency.

---

## 13. Expand and Contract

Safely evolves schema across application versions.

---

## 14. Online Index Build

Reduces blocking where engine support allows.

---

## 15. Queue Table / Outbox

Persists work or events transactionally.

Requires cleanup, locking, retries, and idempotency.

---

## 16. Audit Table

Preserves controlled change history.

Not a substitute for full database audit where required.

---

## 17. Soft Delete

Marks records deleted instead of removing them.

Adds query, uniqueness, retention, and privacy complexity.

---

## 18. Temporal/Bitemporal Modeling

Tracks valid time and system time.

Useful for historical/regulatory requirements.

---

## 19. Anti-pattern: Entity-Attribute-Value Everywhere

Flexible schema creates weak constraints and difficult queries.

Use only for genuinely sparse dynamic attributes.

---

## 20. Anti-pattern: Index Every Column

Harms writes, storage, and maintenance.

---

## 21. Anti-pattern: Missing Foreign Keys for Performance

Integrity is moved into fragile application assumptions.

---

## 22. Anti-pattern: SELECT Star

Reads unnecessary columns and creates compatibility risk.

---

## 23. Anti-pattern: Unbounded Query

Large results consume memory, network, locks, and time.

---

## 24. Anti-pattern: Long Transaction

Retains locks/versions/logs and harms maintenance.

---

## 25. Anti-pattern: Shared Superuser

Destroys least privilege and auditability.

---

## 26. Anti-pattern: One Giant Table

Multiple entities and grains are mixed without clear constraints.

---

## 27. Anti-pattern: ORM-Only Schema Governance

Production schema reality is assumed from entity definitions.

---

## 28. Anti-pattern: Replica as Backup

Logical mistakes replicate immediately.

---

## 29. Anti-pattern: Retry Every Database Error

Permanent and integrity errors are retried incorrectly.

---

## 30. Pattern documentation template

```markdown
## Pattern

### Database problem
### Workload evidence
### Selected pattern
### Engine behavior
### Data integrity
### Concurrency
### Performance
### Recovery
### Operational cost
### Validation
### Revisit criteria
```
