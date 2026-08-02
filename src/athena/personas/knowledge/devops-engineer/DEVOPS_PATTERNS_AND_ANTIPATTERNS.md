# DevOps Patterns and Anti-Patterns

## 1. Purpose

Use patterns only when they solve a demonstrated operational or delivery problem.

---

## 2. Immutable Infrastructure

Replace rather than patch in place.

Benefits:

- reproducibility;
- rollback;
- drift reduction.

---

## 3. GitOps

Git contains desired state, and a controller reconciles it.

Benefits:

- audit;
- drift correction;
- review;
- recovery.

---

## 4. Build Once, Promote Many

The same immutable artifact moves across environments.

Prevents environment-specific rebuild differences.

---

## 5. Progressive Delivery

Expose a change gradually and verify signals.

Patterns:

- canary;
- blue/green;
- feature flag.

---

## 6. Infrastructure as Code

Infrastructure is declared, reviewed, tested, and versioned.

---

## 7. Policy as Code

Security and compliance rules become testable automated policy.

---

## 8. Configuration as Code

Operational configuration is versioned and reviewed, while secrets remain protected.

---

## 9. Golden Path

Provide a supported default way to build, deploy, observe, and operate a service.

It should reduce cognitive load without blocking exceptions.

---

## 10. Self-Service Platform

Developers can safely provision and operate common capabilities without manual tickets.

Requires guardrails and ownership.

---

## 11. Ephemeral Environment

Create temporary isolated environments for review or testing, then delete them automatically.

---

## 12. Sidecar

Attach supporting behavior to a workload.

Use carefully due to resource and lifecycle complexity.

---

## 13. Ambassador/Proxy

Place a proxy between workload and external services for protocol, security, or routing concerns.

---

## 14. Operator

Encode domain-specific operational reconciliation.

Use when lifecycle is complex and recurring.

Avoid writing an operator for simple manifest deployment.

---

## 15. Circuit Breaker

Stop repeated calls to a failing dependency.

---

## 16. Bulkhead

Isolate resources to contain failure.

---

## 17. Backpressure

Limit incoming work when consumers are saturated.

---

## 18. Cell-Based Architecture

Partition workloads into isolated cells to reduce blast radius.

Useful at larger scale.

---

## 19. Expand and Contract

Safely evolve infrastructure or schemas through compatible phases.

---

## 20. Strangler Migration

Move capability incrementally from old platform to new.

---

## 21. Anti-pattern: ClickOps

Manual console changes without versioned source.

---

## 22. Anti-pattern: Snowflake Environment

An environment cannot be reproduced because it contains unique manual state.

---

## 23. Anti-pattern: Pipeline as Shell Script Dump

A large unstructured script with hidden state and no reusable contracts.

---

## 24. Anti-pattern: YAML Copy Forest

Every service or environment copies complete manifests.

Use composition and templates carefully.

---

## 25. Anti-pattern: Shared Production Credentials

Destroys auditability and least privilege.

---

## 26. Anti-pattern: Permanent Admin

Administrative access should be time-bound and audited.

---

## 27. Anti-pattern: Retry Everywhere

Multiple layers retry and create storms.

One layer must own the retry budget.

---

## 28. Anti-pattern: Alert Fatigue

Too many non-actionable alerts reduce response quality.

---

## 29. Anti-pattern: Monitoring Without SLO

Metrics exist but do not define acceptable service.

---

## 30. Anti-pattern: Backup Checkbox

Backups exist but restore is never tested.

---

## 31. Anti-pattern: Kubernetes by Default

Kubernetes is selected without operational need or capability.

---

## 32. Pattern decision template

```markdown
## Pattern

### Problem
### Evidence
### Forces
### Selected pattern
### Why
### Operational cost
### Security impact
### Failure behavior
### Validation
### Revisit criteria
```
