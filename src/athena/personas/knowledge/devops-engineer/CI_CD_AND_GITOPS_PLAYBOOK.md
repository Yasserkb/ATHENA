# CI/CD and GitOps Playbook

## 1. CI objectives

CI provides fast, trustworthy evidence that a change is buildable, testable, secure enough to progress, and reproducible.

Track:

- lead time;
- queue time;
- execution time;
- failure rate;
- flaky tests;
- cache efficiency.

---

## 2. Pipeline structure

Recommended order:

```text
validate
→ dependency restore
→ compile
→ unit test
→ static analysis
→ package
→ security scan
→ integration test
→ attest/sign
→ publish
```

Use parallelism only where stages are independent.

---

## 3. Deterministic builds

Control:

- base images;
- dependencies;
- plugin versions;
- build environment;
- locale/timezone;
- external downloads;
- generated timestamps;
- network access.

Store provenance.

---

## 4. Caching

Cache:

- dependency downloads;
- compiler caches;
- immutable tools.

Do not cache:

- secrets;
- untrusted branch artifacts across trust boundaries;
- outputs whose validity cannot be proven.

Use explicit cache keys and invalidation.

---

## 5. Runners

Separate runners by trust:

- untrusted pull request;
- trusted branch;
- privileged image build;
- production deployment.

Avoid privileged shared runners.

---

## 6. Security gates

Include:

- secret scan;
- dependency scan;
- SAST;
- IaC scan;
- container scan;
- policy validation;
- license policy;
- signature verification.

A finding policy must define:

- severity;
- blocking behavior;
- exception process;
- expiry;
- owner.

---

## 7. Artifact publication

Publish only after required checks.

Use:

- immutable tags;
- digest references;
- signatures;
- SBOM;
- provenance;
- retention.

---

## 8. Deployment pipeline

Separate:

- build;
- promotion;
- deployment.

Do not rebuild during deployment.

---

## 9. GitOps principles

Git stores desired state.

The controller:

- pulls;
- compares;
- reconciles;
- reports drift.

Avoid pipelines that push arbitrary mutable state directly to the cluster when GitOps is the declared model.

---

## 10. Repository strategies

### Monorepo

Benefits:

- atomic changes;
- shared policy;
- visibility.

Risks:

- scale;
- ownership;
- broad pipeline triggers.

### Multi-repo

Benefits:

- independent lifecycle;
- ownership.

Risks:

- coordinated changes;
- version management.

### Environment repository

Can separate application source from deployment state.

Define promotion ownership carefully.

---

## 11. Promotion

Options:

- commit/tag update;
- pull request;
- automated policy promotion;
- environment branch.

Prefer explicit auditable promotion.

---

## 12. Drift

Detect:

- manual changes;
- unmanaged resources;
- controller failure;
- ignored differences.

Policy:

- alert;
- reconcile;
- block;
- investigate.

---

## 13. Progressive delivery

Use metrics to control rollout:

- error rate;
- latency;
- saturation;
- business success.

Automated rollback requires trustworthy signals.

---

## 14. Rollback

Rollback must include:

- application;
- configuration;
- database compatibility;
- feature flags;
- traffic;
- state.

A previous image alone may not be a valid rollback after an irreversible migration.

---

## 15. Pipeline testing

Test pipeline logic through:

- linting;
- schema validation;
- local runner where possible;
- test repositories;
- fixture pipelines;
- dry runs;
- ephemeral environment.

---

## 16. Anti-patterns

- one giant pipeline;
- environment logic copied everywhere;
- rebuilding per environment;
- mutable tags;
- secrets in variables without scope;
- production deploy from unreviewed branch;
- disabled checks to meet deadline;
- deployment success without health verification;
- shared privileged runner;
- hidden manual step with no audit.
