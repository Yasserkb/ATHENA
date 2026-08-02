# Python Engineering Playbook

## 1. Project structure

Define:

- `pyproject.toml`;
- package source layout;
- entry points;
- runtime dependencies;
- dev dependencies;
- lock strategy;
- supported Python versions;
- test configuration;
- lint/type tools.

## 2. Typing and validation

Use type hints for design and tooling. Use runtime validation for:

- HTTP;
- messages;
- files;
- environment;
- database input;
- external services.

## 3. Framework boundaries

### FastAPI

Separate routes, schemas, dependencies, services, repositories, and background work. Own database session lifecycle explicitly.

### Django

Use apps and domain boundaries deliberately. Avoid signals for hidden critical workflows. Review ORM queries and transaction behavior.

### Flask

Create explicit application factories, extensions, configuration, service boundaries, and error handling.

## 4. Concurrency

Choose based on workload:

- synchronous I/O;
- asyncio;
- threads;
- processes;
- task queue.

Do not call blocking libraries in an event loop without isolation.

## 5. Persistence

For SQLAlchemy or Django ORM, inspect:

- session/unit-of-work;
- transaction;
- eager/lazy behavior;
- N+1;
- migrations;
- pooling;
- async-driver compatibility.

## 6. Background work

For Celery/RQ/etc., define:

- queue;
- idempotency;
- retry;
- timeout;
- acknowledgement;
- result handling;
- dead letter/failure store;
- observability.

## 7. Errors and logging

Use specific exceptions, preserve causes, map errors at boundaries, and use structured logging with redaction.

## 8. Security

Review:

- unsafe deserialization;
- command execution;
- path traversal;
- dependency vulnerabilities;
- secret handling;
- template escaping;
- authorization;
- file upload.

## 9. Performance

Measure:

- CPU profiles;
- allocations;
- I/O;
- event-loop delay;
- query count;
- serialization;
- worker concurrency;
- memory.

## 10. Testing

Use pytest with:

- focused fixtures;
- test-data factories;
- parametrization;
- property-based testing where useful;
- integration containers;
- async tests;
- contract tests.

Avoid giant session-scoped mutable fixtures.
