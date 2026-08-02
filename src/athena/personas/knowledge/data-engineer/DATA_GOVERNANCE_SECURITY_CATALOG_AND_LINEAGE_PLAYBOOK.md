# Data Governance, Security, Privacy, Catalog, and Lineage Playbook

## 1. Governance roles

Define:

- data owner;
- data steward;
- platform owner;
- pipeline owner;
- consumer;
- security/privacy owner.

---

## 2. Catalog

Catalog entries should include:

- name;
- description;
- owner;
- source;
- schema;
- classification;
- freshness;
- quality;
- lineage;
- consumers;
- retention.

---

## 3. Lineage

Capture:

- source;
- transformation;
- output;
- column-level lineage where necessary;
- code version;
- job;
- timestamp.

Lineage should come from execution and metadata, not only documentation.

---

## 4. Access control

Use:

- least privilege;
- groups/roles;
- row/column policies;
- masking;
- purpose-based access;
- time-bound access;
- audit.

---

## 5. Sensitive data

Identify:

- PII;
- financial;
- health;
- authentication;
- regulated identifiers.

Apply:

- minimization;
- masking;
- tokenization;
- encryption;
- restricted zones;
- audit;
- retention;
- deletion.

---

## 6. Data sharing

Define:

- contract;
- consumer;
- purpose;
- fields;
- SLA;
- access;
- retention;
- revocation.

---

## 7. Retention and deletion

Policy must cover:

- raw;
- curated;
- backups;
- logs;
- caches;
- extracts;
- downstream copies.

---

## 8. Residency

Track where data is:

- stored;
- processed;
- backed up;
- replicated;
- accessed.

---

## 9. Data contracts

A contract includes:

- schema;
- semantics;
- ownership;
- compatibility;
- quality;
- freshness;
- deprecation;
- support.

---

## 10. Anti-patterns

- unknown owner;
- catalog without freshness;
- lineage only in diagrams;
- full sensitive data in dev;
- permanent broad access;
- deletion only from primary table;
- contract with no compatibility policy.
