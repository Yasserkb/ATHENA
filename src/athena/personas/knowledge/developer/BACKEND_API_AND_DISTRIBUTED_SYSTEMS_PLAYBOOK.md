# Backend, API, and Distributed Systems Playbook

## 1. Contract design

Define:

- transport;
- endpoint/event name;
- request/schema;
- validation;
- response;
- error model;
- authentication;
- authorization;
- idempotency;
- pagination;
- versioning;
- rate and payload limits.

## 2. Layer ownership

- Transport maps protocol.
- Application service orchestrates use cases.
- Domain logic owns business rules.
- Repository owns persistence access.
- Adapter/client owns external protocol translation.
- Mapper transforms structure without hiding business rules.

## 3. Transactions

Define:

- atomic boundary;
- isolation;
- external calls;
- rollback;
- retry;
- optimistic/pessimistic concurrency;
- outbox or reconciliation when crossing systems.

## 4. Idempotency

Use:

- request key;
- natural unique constraint;
- processed-event record;
- state-transition guard;
- deduplication window.

## 5. Remote dependencies

Specify:

- connection/read/total timeout;
- retryable failures;
- bounded attempts;
- backoff and jitter;
- circuit breaker;
- concurrency limit;
- error mapping;
- correlation;
- sensitive-data policy.

## 6. Messaging

Define:

- producer and consumer;
- schema and version;
- key and ordering;
- delivery semantics;
- retries;
- dead-letter handling;
- replay;
- idempotency;
- observability.

## 7. Caching

Only after a measured need. Define:

- key;
- source of truth;
- TTL;
- invalidation;
- stampede control;
- consistency;
- fallback;
- metrics.

## 8. Background and scheduled work

Define:

- scheduler/queue;
- ownership;
- concurrency;
- overlap;
- checkpoint;
- timeout;
- retries;
- shutdown;
- observability.

## 9. Backend security

Review:

- authentication;
- object and tenant authorization;
- injection;
- SSRF;
- path traversal;
- deserialization;
- file upload;
- secret handling;
- audit;
- rate limits.

## 10. Backend testing

Use:

- unit tests for rules;
- slice/component tests for framework behavior;
- integration tests for database/broker/protocol;
- contract tests for independent services;
- limited E2E for critical workflows.

## 11. Anti-patterns

- controllers with business logic;
- repositories orchestrating use cases;
- generic service layers;
- retries at multiple layers;
- network calls inside long transactions;
- events with no schema ownership;
- shared database as integration API;
- infinite queues;
- catch-all error conversion.
