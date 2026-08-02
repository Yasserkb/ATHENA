# Security Testing and Abuse-Case Playbook

## 1. Scope

Security testing supports, but does not replace, secure design.

Cover:

- authentication;
- authorization;
- input;
- session;
- secrets;
- data;
- tenant isolation;
- file handling;
- external calls;
- logging;
- dependencies;
- configuration.

---

## 2. Threat-based testing

Identify:

- asset;
- actor;
- entry point;
- trust boundary;
- abuse case;
- control;
- test evidence.

---

## 3. Authentication

Test:

- invalid credential;
- expiration;
- revocation;
- MFA where applicable;
- brute force/rate limit;
- session fixation;
- logout;
- token audience/issuer.

---

## 4. Authorization

Test:

- horizontal escalation;
- vertical escalation;
- tenant isolation;
- direct object access;
- hidden endpoint;
- role change;
- default deny.

---

## 5. Input and injection

Test relevant:

- SQL;
- command;
- template;
- LDAP;
- header;
- path traversal;
- SSRF;
- XSS;
- deserialization;
- file upload.

---

## 6. Sensitive data

Verify:

- no secret in logs;
- masking;
- encryption;
- retention;
- export;
- error response;
- cache;
- test report.

---

## 7. API abuse

Test:

- replay;
- duplicate;
- oversized payload;
- enumeration;
- rate limit;
- resource exhaustion;
- malformed content.

---

## 8. Security tooling

Use:

- SAST;
- dependency scan;
- DAST;
- secret scan;
- IaC scan;
- container scan.

Manual risk-driven testing remains necessary.

---

## 9. Reporting

Security findings need:

- severity;
- exploitability;
- impact;
- evidence;
- affected scope;
- remediation;
- retest.

---

## 10. Anti-patterns

- security scan only;
- authorization tested only through UI;
- real secret in test;
- disabled TLS verification;
- vulnerability accepted without owner/expiry;
- sensitive payload in report.
