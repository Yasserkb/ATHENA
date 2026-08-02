# Cloud IAM, Security, and Compliance Playbook

## 1. Identity domains

Separate:

- workforce;
- workload;
- CI/CD;
- customer identity;
- privileged administration;
- emergency access.

---

## 2. Human access

Require:

- federated SSO;
- MFA;
- group-based access;
- role assumption;
- short sessions for privileged roles;
- access review;
- automated offboarding.

---

## 3. Workload identity

Use native workload identities.

Avoid:

- static access keys;
- credentials in environment files;
- shared service principals;
- broad reusable roles.

---

## 4. Authorization

Design permissions from tasks.

Use:

- least privilege;
- resource scope;
- condition;
- permission boundaries;
- separation of duties;
- deny guardrails where appropriate.

---

## 5. Secrets

Use a managed secret store.

Define:

- owner;
- consumer;
- encryption;
- rotation;
- access;
- audit;
- revocation;
- reload behavior.

---

## 6. Encryption

Define:

### At rest

- provider-managed or customer-managed keys;
- key ownership;
- rotation;
- deletion protection;
- separation.

### In transit

- TLS;
- certificate lifecycle;
- mTLS where justified;
- private connectivity.

---

## 7. Key management

Consider:

- KMS/HSM;
- key hierarchy;
- regionality;
- cross-account access;
- rotation;
- backup;
- deletion waiting period;
- audit.

---

## 8. Data protection

Apply:

- classification;
- minimization;
- masking;
- tokenization;
- residency;
- retention;
- deletion;
- audit.

---

## 9. Security posture

Use:

- configuration assessment;
- vulnerability findings;
- threat detection;
- audit analytics;
- network findings;
- identity findings.

Centralize ownership and triage.

---

## 10. Compliance

Provider certifications support compliance but do not make the workload compliant.

Map:

- control;
- implementation;
- evidence;
- owner;
- review frequency.

---

## 11. Break-glass

Emergency access must be:

- limited;
- protected;
- monitored;
- tested;
- documented;
- reviewed after use.

---

## 12. Provider mapping

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| IAM | IAM / IAM Identity Center | Entra ID / Azure RBAC | Cloud IAM / Cloud Identity |
| Secrets | Secrets Manager | Key Vault | Secret Manager |
| Key management | KMS / CloudHSM | Key Vault / Managed HSM | Cloud KMS / Cloud HSM |
| Security posture | Security Hub | Defender for Cloud | Security Command Center |
| Audit | CloudTrail | Activity Log | Cloud Audit Logs |
| Policy | Organizations SCP / Config | Azure Policy | Organization Policy |
