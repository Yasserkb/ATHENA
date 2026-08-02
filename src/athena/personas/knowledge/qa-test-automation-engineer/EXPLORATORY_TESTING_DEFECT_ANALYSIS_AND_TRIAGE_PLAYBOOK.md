# Exploratory Testing, Defect Analysis, and Triage Playbook

## 1. Exploratory testing

Exploratory testing combines:

- learning;
- design;
- execution.

Use charters.

Example:

```text
Explore contact-plan recovery
with missing and restored contact data
to discover invalid state transitions and duplicate emissions.
```

---

## 2. Heuristics

Explore:

- inputs;
- boundaries;
- states;
- interruptions;
- timing;
- permissions;
- configuration;
- integration failure;
- repeated action;
- concurrency;
- recovery.

---

## 3. Session notes

Record:

- charter;
- environment;
- data;
- paths;
- observations;
- defects;
- questions;
- coverage;
- time.

---

## 4. Defect isolation

Use:

```text
reproduce
→ reduce
→ classify
→ collect evidence
→ compare expected
→ identify boundary
```

---

## 5. Defect categories

- requirement ambiguity;
- product logic;
- integration;
- data;
- migration;
- concurrency;
- configuration;
- infrastructure;
- observability;
- test automation;
- environment.

---

## 6. Severity

Assess:

- user impact;
- data/security;
- frequency;
- scope;
- workaround;
- recovery.

---

## 7. Triage

Decide:

- valid defect;
- duplicate;
- expected behavior;
- cannot reproduce;
- environment;
- deferred;
- blocker.

Document evidence.

---

## 8. Root-cause support

QA may identify likely boundaries but should not claim root cause without evidence.

Provide:

- first failing layer;
- request/response;
- log;
- trace;
- data;
- timing;
- configuration.

---

## 9. Retest and regression

After fix:

- reproduce original;
- verify fix;
- test neighboring behavior;
- add automated coverage at the lowest reliable level;
- monitor production risk.

---

## 10. Anti-patterns

- vague “does not work” defect;
- severity based on emotion;
- closing without retest;
- adding only UI regression;
- blaming environment without evidence;
- root-cause claim from symptom.
