# DevSecOps, CI/CD, and Software Supply-Chain Security Playbook

## 1. Source integrity

Review:

- branch protection;
- required reviews;
- CODEOWNERS;
- signed releases;
- repository access;
- secret scanning;
- protected tags;
- audit.

---

## 2. CI identities

Use:

- workload federation/OIDC;
- short-lived credentials;
- environment-specific roles;
- least privilege;
- protected deployment contexts.

Avoid long-lived cloud keys.

---

## 3. Runner security

Separate:

- untrusted pull requests;
- trusted builds;
- privileged image builds;
- production deployment.

Prefer ephemeral isolated runners for high-risk work.

---

## 4. Dependency security

Review:

- lockfiles;
- trusted registries;
- package names;
- dependency confusion;
- typosquatting;
- update policy;
- vulnerability triage;
- license;
- provenance;
- maintainer risk.

---

## 5. Build integrity

Use:

- pinned build tools/actions;
- controlled network;
- clean environments;
- reproducible or verifiable builds;
- artifact checksums;
- provenance;
- SBOM;
- signatures.

---

## 6. Artifact registry

Require:

- immutable artifacts;
- least privilege;
- retention;
- scanning;
- signature verification;
- audit;
- promotion rather than rebuild.

---

## 7. Deployment protection

Review:

- approval;
- artifact identity;
- environment isolation;
- GitOps controls;
- admission policy;
- rollback;
- deployment audit.

---

## 8. Secrets

Prevent secrets in:

- source;
- logs;
- build cache;
- artifacts;
- image layers;
- command arguments;
- test reports.

---

## 9. Vulnerability gating

A gate needs:

- severity and exploitability policy;
- asset exposure;
- exception owner;
- expiry;
- compensating control;
- revalidation.

Do not block or accept solely from CVSS.

---

## 10. Supply-chain incident readiness

Maintain:

- component inventory;
- SBOM;
- affected-version lookup;
- artifact provenance;
- revocation process;
- rebuild process;
- customer communication.
