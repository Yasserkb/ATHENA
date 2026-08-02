# Infrastructure as Code Playbook

## 1. Purpose

IaC manages infrastructure through reviewed, repeatable code.

It must provide:

- reproducibility;
- drift visibility;
- safe change;
- ownership;
- recovery.

---

## 2. Module design

A module should represent a coherent capability.

Good examples:

- network;
- Kubernetes cluster;
- database;
- object storage;
- IAM role;
- monitoring stack.

Avoid modules that hide every provider feature behind generic variables.

---

## 3. Inputs and outputs

Inputs must be:

- typed;
- documented;
- validated;
- minimal;
- safe by default.

Outputs should expose stable contracts, not internal implementation details.

---

## 4. State

Define:

- backend;
- encryption;
- locking;
- backup;
- access;
- separation;
- recovery;
- migration.

Never share one state file across unrelated trust or failure boundaries.

---

## 5. Environment composition

Prefer:

- reusable modules;
- small environment composition;
- explicit differences.

Avoid copy-paste full environments.

---

## 6. Plan and apply

Required process:

```text
format/lint
→ validate
→ security/policy scan
→ plan
→ review
→ approved apply
→ verify
```

Store plan evidence when policy requires.

---

## 7. Import and drift

Existing resources require controlled import.

After import:

- compare;
- normalize;
- prevent replacement;
- document ownership.

Run drift detection continuously or regularly.

---

## 8. Lifecycle controls

Use carefully:

- prevent destroy;
- create before destroy;
- ignore changes;
- replacement triggers.

`ignore_changes` can hide unmanaged drift and must have a documented reason.

---

## 9. Provider and module versions

Pin compatible versions.

Upgrade through:

- change log review;
- plan;
- test environment;
- migration;
- rollout.

---

## 10. Testing

Use:

- validation;
- policy tests;
- unit-style module tests;
- integration deployment;
- cost estimation;
- destructive-test environment where required.

---

## 11. Ansible and host configuration

Playbooks must be:

- idempotent;
- role-based;
- inventory-safe;
- secret-safe;
- check-mode aware where possible;
- tagged;
- tested.

Avoid uncontrolled shell commands when a module exists.

---

## 12. Anti-patterns

- manual changes after apply;
- giant root module;
- hardcoded secrets;
- shared state for everything;
- unpinned provider;
- automatic production apply without review;
- outputting secrets;
- circular module dependency;
- generic module that nobody understands.
