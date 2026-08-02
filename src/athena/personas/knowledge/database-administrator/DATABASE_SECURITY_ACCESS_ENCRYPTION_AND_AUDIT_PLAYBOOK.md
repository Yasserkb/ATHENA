# Database Security, Access Control, Encryption, and Audit Playbook

## 1. Identity separation

Use separate identities for:

- application runtime;
- migrations;
- read-only reporting;
- monitoring;
- backup;
- administration;
- break-glass.

---

## 2. Least privilege

Grant:

- specific database/schema;
- required objects;
- required operations;
- time-bound elevated access.

Avoid application ownership of the whole database.

---

## 3. Role design

Prefer roles/groups and inheritance over direct grants to individuals.

Review grants regularly.

---

## 4. Secrets

Store credentials in approved secret management.

Use:

- rotation;
- short-lived tokens where supported;
- workload identity;
- connection encryption;
- audit.

---

## 5. Encryption

Define:

- at rest;
- in transit;
- backup;
- replicas;
- keys;
- rotation;
- ownership.

---

## 6. Network access

Restrict:

- source network;
- private endpoints;
- firewall;
- port;
- administrative paths.

Public database exposure requires exceptional justification.

---

## 7. Row and column security

Use when:

- shared tables;
- tenant isolation;
- sensitive columns;
- policy enforcement

justify database-level controls.

Test carefully with application roles.

---

## 8. Masking

Non-production environments should use:

- synthetic data;
- irreversible masking;
- tokenization;
- minimized datasets.

---

## 9. Audit

Audit:

- login;
- privilege changes;
- schema changes;
- sensitive reads where required;
- data changes;
- failed access;
- backup/restore;
- administration.

Control audit volume and retention.

---

## 10. Anti-patterns

- shared admin account;
- plaintext connection string;
- public database;
- wildcard grants;
- production data copied to dev;
- disabled TLS verification;
- audit logs writable by the audited administrator.
