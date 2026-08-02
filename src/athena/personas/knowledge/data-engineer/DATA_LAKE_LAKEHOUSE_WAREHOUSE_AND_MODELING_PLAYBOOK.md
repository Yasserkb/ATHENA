# Data Lake, Lakehouse, Warehouse, and Modeling Playbook

## 1. Storage selection

Evaluate:

- access pattern;
- data shape;
- volume;
- update frequency;
- concurrency;
- latency;
- governance;
- cost;
- engine compatibility.

---

## 2. File formats

Common analytical formats:

- Parquet;
- ORC;
- Avro.

Choose based on:

- columnar reads;
- schema evolution;
- interoperability;
- streaming;
- compression.

---

## 3. Table formats

Lakehouse table formats can add:

- ACID transactions;
- snapshots;
- schema evolution;
- partition evolution;
- time travel;
- incremental reads.

Examples include:

- Apache Iceberg;
- Delta Lake;
- Apache Hudi.

Select based on engine support, catalog, operations, and migration—not popularity.

---

## 4. Partitioning

Partition by commonly filtered, reasonably distributed fields.

Avoid:

- excessive cardinality;
- tiny partitions;
- immutable bad partition choices;
- ingestion-time partitions when business-date queries dominate.

---

## 5. Small files

Small files increase:

- metadata overhead;
- planning time;
- storage operations.

Use compaction with clear scheduling and cost controls.

---

## 6. Dimensional modeling

Define:

- business process;
- grain;
- dimensions;
- facts;
- measures;
- keys;
- SCD type;
- conformed dimensions.

---

## 7. Slowly changing dimensions

### Type 1

Overwrite current value.

### Type 2

Preserve history with effective dates/current flag.

### Type 3

Limited previous value.

Choose based on analytical need and policy.

---

## 8. Data Vault

Useful for auditable historical integration across many sources.

Adds modeling and operational complexity.

---

## 9. Wide tables

Can simplify consumption but create:

- duplication;
- slow evolution;
- unclear ownership.

Use intentionally.

---

## 10. Semantic layer

A semantic layer defines consistent:

- metrics;
- dimensions;
- joins;
- access.

It reduces duplicated business logic.

---

## 11. Anti-patterns

- no explicit grain;
- mixed fact grains;
- partition by every field;
- raw JSON forever;
- one giant curated table;
- data lake without catalog;
- SCD2 without stable business key;
- lakehouse with incompatible engines.
