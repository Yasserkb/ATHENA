# Data Quality, Reconciliation, and Observability Playbook

## 1. Quality dimensions

- completeness;
- uniqueness;
- validity;
- consistency;
- timeliness;
- accuracy;
- integrity.

---

## 2. Rule design

Each rule needs:

- dataset/field;
- expectation;
- threshold;
- severity;
- owner;
- failure behavior;
- evidence;
- remediation.

---

## 3. Schema checks

Validate:

- fields;
- types;
- nullability;
- constraints;
- compatibility;
- unexpected columns;
- missing columns.

---

## 4. Volume checks

Track:

- row count;
- event count;
- file count;
- bytes;
- partition count;
- distribution.

Use historical and expected ranges.

---

## 5. Freshness

Measure from the consumer perspective:

```text
current time - latest valid business/event time
```

Job completion time alone can be misleading.

---

## 6. Reconciliation

Compare source and target using:

- counts;
- sums;
- hashes;
- keys;
- status distribution;
- control totals;
- sample records.

For financial data, define tolerances explicitly.

---

## 7. Quarantine

Invalid data may be quarantined when continuing is safe.

Quarantine requires:

- reason;
- secure storage;
- owner;
- alert;
- correction;
- replay;
- retention.

---

## 8. Data observability

Monitor:

- freshness;
- volume;
- schema;
- quality;
- lineage;
- distribution;
- job health;
- downstream impact.

---

## 9. Incident classification

Distinguish:

- source issue;
- pipeline issue;
- infrastructure;
- schema;
- business rule;
- consumer misuse;
- quality rule defect.

---

## 10. Anti-patterns

- job success equals data success;
- threshold with no owner;
- warning forever;
- quarantine with no replay;
- no source reconciliation;
- quality only at final table.
