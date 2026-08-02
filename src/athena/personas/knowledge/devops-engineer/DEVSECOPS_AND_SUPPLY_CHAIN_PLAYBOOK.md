# DevSecOps and Software Supply-Chain Playbook

## 1. Security model

Security is integrated into:

- source;
- dependencies;
- build;
- artifacts;
- registry;
- deployment;
- runtime;
- operations.

---

## 2. Threat modeling

Identify:

- assets;
- actors;
- entry points;
- trust boundaries;
- abuse cases;
- mitigations;
- residual risk.

---

## 3. Source security

Use:

- branch protection;
- review;
- CODEOWNERS;
- secret scanning;
- signed releases;
- audit logs.

---

## 4. Dependency security

Maintain:

- lock files;
- update automation;
- vulnerability scanning;
- license policy;
- exception expiry;
- provenance.

Do not blindly upgrade production dependencies without compatibility validation.

---

## 5. Build security

Use:

- isolated runners;
- minimal permissions;
- ephemeral credentials;
- pinned actions/plugins;
- trusted builders;
- reproducible builds;
- network restrictions where possible.

---

## 6. SBOM

Generate and retain an SBOM for release artifacts.

Use it for:

- vulnerability response;
- license review;
- provenance;
- customer requirements.

---

## 7. Signing and provenance

Sign artifacts and attest:

- source commit;
- builder;
- workflow;
- dependencies;
- tests;
- identity.

Verify before deployment.

---

## 8. Registry security

Use:

- immutable tags;
- access control;
- retention;
- vulnerability policy;
- replication;
- audit;
- signature verification.

---

## 9. IaC and policy

Scan:

- Terraform;
- Kubernetes;
- Dockerfile;
- Helm;
- cloud policy.

Use policy as code for mandatory controls.

---

## 10. Runtime security

Include:

- least privilege;
- workload identity;
- network policy;
- admission control;
- runtime detection;
- audit;
- secret rotation;
- patching.

---

## 11. Secret lifecycle

```text
create
→ store
→ distribute
→ use
→ rotate
→ revoke
→ audit
```

Never expose secrets in:

- logs;
- command arguments;
- build artifacts;
- Docker layers;
- Git history.

---

## 12. Vulnerability policy

Define:

- severity;
- exploitability;
- exposure;
- SLA;
- exception owner;
- expiry;
- compensating control.

CVSS alone is not enough.

---

## 13. Incident response

Security incidents require:

- containment;
- credential revocation;
- evidence;
- scope;
- notification;
- recovery;
- lessons.

---

## 14. Anti-patterns

- security only at final stage;
- privileged CI runner;
- long-lived cloud key;
- ignored scan forever;
- unsigned mutable images;
- secrets in environment dump;
- public admin interface;
- wildcard IAM;
- disabled TLS verification.
