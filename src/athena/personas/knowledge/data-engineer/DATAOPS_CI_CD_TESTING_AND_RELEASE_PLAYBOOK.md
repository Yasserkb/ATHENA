# DataOps, CI/CD, Testing, and Release Playbook

## 1. Version control

Version:

- pipeline code;
- SQL;
- models;
- schemas;
- contracts;
- quality rules;
- orchestration;
- infrastructure;
- dashboards;
- documentation.

---

## 2. CI stages

```text
format/lint
→ compile/parse
→ unit tests
→ schema/contract tests
→ transformation tests
→ quality tests
→ integration tests
→ security scan
→ package
```

---

## 3. Test categories

### Unit

- transformation function;
- parser;
- mapping;
- business rule.

### SQL/model

- not null;
- unique;
- relationship;
- accepted values;
- custom assertions.

### Integration

- database;
- broker;
- object storage;
- catalog;
- orchestrator.

### Contract

- source/consumer schema;
- compatibility.

### End-to-end

- limited critical pipeline.

### Reconciliation

- source-to-target controls.

---

## 4. Test data

Use:

- synthetic;
- masked;
- generated;
- bounded fixtures.

Include:

- null;
- duplicate;
- late;
- out-of-order;
- invalid;
- schema change;
- large key;
- deletion.

---

## 5. Deployment

Define:

- artifact;
- schema;
- job;
- schedule;
- infrastructure;
- order;
- compatibility;
- rollback.

---

## 6. Model migration

Use compatible phases:

1. add new model/field;
2. dual-run or populate;
3. compare;
4. migrate consumers;
5. switch;
6. remove old later.

---

## 7. Quality gates

Block for:

- schema incompatibility;
- failed critical quality rule;
- reconciliation failure;
- migration failure;
- unacceptable performance regression;
- security violation.

---

## 8. Promotion

Promote the same code and validated artifacts across environments.

Configuration may vary, logic should not.

---

## 9. Post-release

Verify:

- freshness;
- volume;
- quality;
- reconciliation;
- downstream success;
- cost;
- lag.

---

## 10. Anti-patterns

- SQL copied manually to production;
- no test data;
- pipeline release without schema review;
- quality warnings ignored;
- no rollback;
- production validation only by job status.
