# Schema Design, DDL, Migration, and Data Correction Playbook

## 1. Migration principles

A migration must be:

- versioned;
- repeatable or safely one-time;
- reviewed;
- observable;
- compatible;
- reversible where feasible;
- tested at realistic scale.

---

## 2. Expand and contract

Preferred for breaking changes:

1. add new compatible structure;
2. deploy code supporting old and new;
3. backfill;
4. switch reads/writes;
5. verify;
6. remove old structure later.

---

## 3. Online DDL

Evaluate engine-specific support for:

- concurrent index build;
- online table change;
- metadata-only change;
- lock duration;
- rewrite behavior.

Never assume `ALTER TABLE` is cheap.

---

## 4. Large-table changes

For large tables:

- estimate rows and bytes;
- inspect lock behavior;
- test duration;
- batch data changes;
- monitor replication;
- control WAL/log growth;
- set timeouts;
- provide stop criteria.

---

## 5. Data corrections

A correction plan must define:

- exact predicate;
- expected row count;
- preview query;
- transaction strategy;
- batching;
- audit copy;
- validation;
- rollback.

Use explicit safeguards against broad updates/deletes.

---

## 6. Backfill

Define:

- range;
- batch size;
- ordering;
- concurrency;
- throttling;
- retry;
- checkpoint;
- replication impact;
- validation;
- completion.

---

## 7. Constraint introduction

Before adding a constraint:

- detect violations;
- correct/quarantine data;
- validate safely;
- add enforcement.

Where supported, add constraint without immediate full validation, then validate separately.

---

## 8. Column changes

Review:

- nullability;
- default;
- type conversion;
- application compatibility;
- table rewrite;
- index;
- replication;
- ORM mapping.

---

## 9. Object naming

Use consistent names for:

- primary keys;
- foreign keys;
- unique constraints;
- checks;
- indexes;
- sequences.

Named constraints improve diagnostics and rollback.

---

## 10. Migration-framework standards

For Flyway/Liquibase:

- immutable applied migrations;
- no version reuse;
- environment consistency;
- checksum handling;
- repair policy;
- transactional behavior;
- callbacks used carefully.

---

## 11. Anti-patterns

- editing an applied migration;
- unbounded production update;
- drop column in same release as code change;
- adding not-null with unknown existing data;
- index creation without lock analysis;
- data fix with no preview count;
- rollback assumed but not scripted.
