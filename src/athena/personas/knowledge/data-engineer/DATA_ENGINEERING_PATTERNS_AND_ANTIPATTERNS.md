# Data Engineering Patterns and Anti-Patterns

## 1. ETL

Transform before loading.

Useful when target requires curated output or source data should not be loaded directly.

---

## 2. ELT

Load then transform in scalable analytical storage.

Useful for flexible transformations and SQL-centric teams.

---

## 3. Medallion Architecture

Organizes data into progressive quality zones.

Use as a responsibility model, not only bronze/silver/gold folder names.

---

## 4. Lambda Architecture

Batch plus speed layer.

Provides low latency and complete recomputation but duplicates logic.

---

## 5. Kappa Architecture

Stream-first processing with replay.

Use when event log and stream processing are central.

---

## 6. Data Lakehouse

Open/low-cost storage with table transactions and analytical semantics.

Requires coherent catalog and engine support.

---

## 7. Data Mesh

Domain ownership plus platform and governance.

Requires organizational maturity.

---

## 8. Data Vault

Historical, auditable integration model using hubs, links, and satellites.

---

## 9. Dimensional Modeling

Facts and dimensions optimized for analytics.

---

## 10. Change Data Capture

Captures database changes from logs or equivalent mechanisms.

---

## 11. Transactional Outbox

Publishes reliable events from transactional systems.

---

## 12. Event Sourcing

Stores domain changes as events.

Not a replacement for ordinary audit logging.

---

## 13. Idempotent Consumer

Processes duplicate messages without duplicate business effect.

---

## 14. Dead-Letter Queue

Separates unprocessable events for investigation and replay.

---

## 15. Quarantine Zone

Stores invalid records with reason and recovery path.

---

## 16. Incremental Materialization

Processes only changed data.

---

## 17. Snapshot

Captures dataset state at a point in time.

---

## 18. Slowly Changing Dimension

Preserves or updates dimension history according to analytical requirements.

---

## 19. Anti-pattern: Data Swamp

A lake lacks catalog, quality, ownership, and discoverability.

---

## 20. Anti-pattern: One Giant DAG

Every pipeline is coupled into one orchestration graph.

---

## 21. Anti-pattern: Full Reload Forever

Every run reprocesses all history without justification.

---

## 22. Anti-pattern: Streaming by Default

Streaming is selected despite batch-compatible freshness.

---

## 23. Anti-pattern: Exactly-Once Illusion

Broker or framework claims are treated as end-to-end business guarantees.

---

## 24. Anti-pattern: Schema-on-Read Chaos

Consumers independently interpret undocumented raw data.

---

## 25. Anti-pattern: Silent Data Loss

Invalid or late records disappear without evidence.

---

## 26. Anti-pattern: Metric Duplication

Different teams calculate the same business metric differently.

---

## 27. Anti-pattern: Backfill Without Reconciliation

Historical data is reprocessed without proving target correctness.

---

## 28. Anti-pattern: Partition Explosion

High-cardinality partitions create metadata and small-file problems.

---

## 29. Anti-pattern: Sensitive Data Everywhere

Raw personal or regulated data is copied across environments without controls.

---

## 30. Pattern documentation template

```markdown
## Pattern

### Data problem
### Requirements
### Forces
### Selected pattern
### Contract
### Correctness
### Recovery
### Quality
### Security
### Cost
### Validation
### Revisit criteria
```
