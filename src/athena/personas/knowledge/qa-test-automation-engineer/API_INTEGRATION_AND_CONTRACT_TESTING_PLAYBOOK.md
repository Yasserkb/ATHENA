# API, Integration, and Contract Testing Playbook

## 1. API coverage

Validate:

- method/path;
- authentication;
- authorization;
- headers;
- validation;
- status;
- body;
- schema;
- pagination;
- filtering;
- sorting;
- idempotency;
- rate limits;
- errors;
- compatibility.

---

## 2. Negative testing

Include:

- missing field;
- invalid type;
- malformed payload;
- boundary;
- unauthorized;
- forbidden;
- missing resource;
- conflict;
- duplicate;
- unsupported media;
- timeout;
- dependency failure.

---

## 3. Contract testing

Use contract tests when consumers and providers evolve independently.

Cover:

- request;
- response;
- schema;
- optional fields;
- enum evolution;
- error;
- event;
- version.

---

## 4. Integration testing

Use real dependencies where behavior matters:

- database;
- message broker;
- object storage;
- SFTP;
- cache;
- filesystem.

Use containers or controlled environments.

---

## 5. External service virtualization

Use mocks/stubs for:

- rare errors;
- latency;
- unavailable sandbox;
- deterministic tests.

Do not let virtualization replace all real integration validation.

---

## 6. Event testing

Validate:

- schema;
- key;
- ordering;
- delivery;
- duplicates;
- retry;
- dead-letter;
- replay;
- idempotency;
- consumer compatibility.

---

## 7. Database validation

Check:

- persisted state;
- constraints;
- transaction rollback;
- migration;
- indexes when performance relevant;
- concurrency;
- cleanup.

---

## 8. SFTP/file flows

Validate:

- naming;
- encoding;
- path;
- permissions;
- partial upload;
- duplicate;
- checksum;
- retry;
- cleanup;
- remote failure;
- file size.

---

## 9. Anti-patterns

- only happy-path status check;
- test against shared mutable external sandbox only;
- provider DTO copied as internal contract;
- no timeout testing;
- no compatibility testing;
- ignoring duplicate delivery.
