# Data, Database, Privacy, and Cryptography Security Playbook

## 1. Data classification

Classify:

- public;
- internal;
- confidential;
- personal;
- financial;
- regulated;
- authentication secret;
- cryptographic material.

---

## 2. Data minimization

Collect, process, retain, and expose only what is required.

---

## 3. Access

Review:

- application roles;
- administrator roles;
- reporting access;
- tenant isolation;
- row/column controls;
- service accounts;
- break-glass;
- audit.

---

## 4. Database security

Review:

- network exposure;
- TLS;
- authentication;
- least privilege;
- schema ownership;
- migration privilege;
- dangerous extensions/functions;
- backup access;
- audit;
- injection protection;
- destructive operation safeguards.

---

## 5. Encryption

Document:

- data at rest;
- data in transit;
- fields requiring application-level encryption;
- keys;
- rotation;
- separation of duties;
- backup encryption;
- revocation;
- recovery.

Do not invent custom cryptography.

---

## 6. Logging and telemetry

Prevent sensitive data in:

- application logs;
- traces;
- metrics labels;
- error responses;
- audit exports;
- test results.

---

## 7. Non-production

Use:

- synthetic data;
- irreversible masking;
- tokenization;
- minimized extracts;
- controlled access.

---

## 8. Retention and deletion

Deletion must account for:

- primary storage;
- indexes;
- cache;
- exports;
- backups;
- logs;
- replicas;
- downstream datasets.

---

## 9. Data integrity

Protect:

- business keys;
- constraints;
- transactions;
- signatures/checksums where needed;
- audit history;
- reconciliation.

---

## 10. Privacy review

Consider:

- purpose;
- consent/legal basis;
- transparency;
- access;
- correction;
- deletion;
- cross-border transfer;
- third parties;
- automated decisions.
