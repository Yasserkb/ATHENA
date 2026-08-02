# Application, API, Web, and Backend Security Playbook

## 1. Architecture review

Inspect:

- entry points;
- authentication;
- authorization;
- session;
- validation;
- serialization;
- persistence;
- files;
- external requests;
- business workflows;
- errors;
- logging.

---

## 2. Access control

Verify authorization for every protected action and object.

Review:

- object-level authorization;
- function-level authorization;
- property/field authorization;
- tenant boundaries;
- administrator boundaries;
- indirect object references;
- default-deny behavior.

Do not rely on UI visibility as authorization.

---

## 3. Authentication and sessions

Review:

- credential storage;
- MFA where required;
- token issuer/audience;
- expiration;
- revocation;
- session fixation;
- refresh tokens;
- logout;
- brute-force controls;
- recovery flows.

---

## 4. Input and injection

Trace untrusted input into:

- SQL;
- shell/process;
- templates;
- expression languages;
- file paths;
- XML;
- LDAP;
- NoSQL;
- logs;
- redirects;
- HTTP headers.

Prefer safe APIs, parameterization, allowlists, and strict schemas.

---

## 5. API security

Review:

- BOLA/BFLA;
- mass/property assignment;
- rate and resource limits;
- sensitive business-flow abuse;
- SSRF;
- inventory/versioning;
- unsafe third-party API consumption;
- pagination and bulk export;
- error disclosure;
- idempotency.

---

## 6. Browser security

Review:

- XSS;
- CSRF;
- CORS;
- CSP;
- clickjacking;
- cookie flags;
- client-side secrets;
- local storage;
- DOM sinks;
- third-party scripts;
- dependency integrity.

---

## 7. File security

Review:

- type validation;
- extension;
- content;
- size;
- filename/path;
- archive extraction;
- malware scanning;
- storage isolation;
- access control;
- download headers;
- lifecycle.

---

## 8. External requests

Protect against:

- SSRF;
- DNS rebinding;
- unsafe redirects;
- certificate validation failures;
- credential forwarding;
- response-size abuse;
- timeout exhaustion.

---

## 9. Business logic

Review:

- state transitions;
- duplicate/replay;
- race conditions;
- price/quantity;
- approval;
- cancellation;
- account recovery;
- batch operations;
- workflow bypass.

---

## 10. Verification

Use:

- unit security tests;
- API authorization matrices;
- negative integration tests;
- contract tests;
- controlled DAST;
- dependency and SAST signals;
- manual code review.

Automation does not replace business-logic analysis.
