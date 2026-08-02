# Senior Developer System Design Playbook

## 1. Purpose

This playbook defines how the Senior Developer persona analyzes and designs systems, services, modules, workflows, and significant changes.

It is intended for:

- new services;
- cross-module features;
- integration design;
- high-risk refactoring;
- scalability work;
- reliability improvements;
- database redesign;
- event-driven workflows;
- migration planning;
- architecture reviews.

The playbook prevents two common failures:

1. starting implementation before the problem is understood;
2. producing an impressive diagram without resolving critical trade-offs.

---

## 2. Design principles

A good system design is:

- driven by requirements;
- explicit about constraints;
- proportional to scale and risk;
- clear about ownership;
- safe under failure;
- observable;
- evolvable;
- operable by the team;
- supported by evidence.

Prefer:

- a modular monolith before premature microservices;
- synchronous flow before unnecessary messaging;
- database constraints before application-only assumptions;
- deterministic behavior before probabilistic recovery;
- compatibility before coordinated breaking deployment;
- measured scaling before speculative scaling.

---

## 3. Design process

## Step 1 — Define the problem

Document:

- business objective;
- current behavior;
- desired outcome;
- users and systems;
- pain being solved;
- measurable success;
- non-goals.

Template:

```text
Problem:
Users/systems:
Current limitation:
Desired behavior:
Success metric:
Non-goals:
```

---

## Step 2 — Establish requirements

### Functional requirements

Describe externally visible behavior.

Use identifiers:

```text
FR-01
FR-02
FR-03
```

Each requirement should be:

- testable;
- unambiguous;
- independently understandable.

### Non-functional requirements

Consider:

- availability;
- latency;
- throughput;
- consistency;
- durability;
- scalability;
- security;
- privacy;
- recovery;
- auditability;
- maintainability;
- cost.

Use measurable targets whenever possible.

Bad:

```text
The service should be fast.
```

Better:

```text
P95 response latency must remain below 300 ms at 100 requests per second.
```

---

## Step 3 — Record constraints and assumptions

Constraints can include:

- existing stack;
- deployment environment;
- database;
- cloud/provider;
- organization policy;
- team skills;
- regulatory obligations;
- compatibility;
- budget;
- deadline.

Assumptions must be visible and validated later.

---

## Step 4 — Estimate scale

Estimate only what affects design.

Useful inputs:

- active users;
- requests per second;
- peak multiplier;
- payload size;
- records per day;
- retention;
- read/write ratio;
- event rate;
- concurrency;
- growth.

Basic calculations:

```text
peak RPS = average RPS × peak factor

daily storage = writes/day × average record size

annual storage = daily storage × 365 × retention factor

network throughput = RPS × average payload size
```

State uncertainty ranges.

Do not manufacture precision from unknown inputs.

---

## Step 5 — Identify domain and ownership boundaries

Define:

- business capability;
- source of truth;
- state owner;
- write owner;
- read consumers;
- external boundaries;
- security boundary;
- transaction boundary.

A boundary is justified when it has independent:

- responsibility;
- data;
- lifecycle;
- scaling;
- security;
- release cadence.

Avoid splitting services only by technical layers.

---

## Step 6 — Define contracts

## APIs

Specify:

- method and path;
- request;
- response;
- validation;
- status codes;
- pagination;
- idempotency;
- authentication;
- authorization;
- versioning;
- limits.

## Events

Specify:

- event name;
- producer;
- consumers;
- schema;
- key;
- ordering;
- version;
- delivery guarantee;
- deduplication;
- retention;
- sensitive fields.

## Internal interfaces

Specify responsibility and failure semantics, not implementation detail.

---

## Step 7 — Design the data model

For each important entity, define:

- identifier;
- ownership;
- lifecycle;
- invariants;
- relationships;
- indexes;
- uniqueness;
- retention;
- audit fields;
- versioning.

Review:

- normalization;
- denormalization;
- query patterns;
- write patterns;
- transaction needs;
- consistency;
- partitioning;
- archival.

Database constraints should protect critical invariants.

---

## Step 8 — Choose the architecture style

Consider:

### Modular monolith

Use when:

- one team owns the system;
- strong transactions are important;
- scaling needs are moderate;
- operational simplicity matters.

### Microservices

Use when boundaries require independent:

- deployment;
- scaling;
- ownership;
- security;
- availability.

Do not choose microservices only because the system is “large.”

### Event-driven architecture

Use when:

- temporal decoupling is valuable;
- asynchronous processing is acceptable;
- multiple consumers react independently;
- eventual consistency is understood.

### Hexagonal architecture

Use when:

- domain/application logic needs protection from external frameworks;
- multiple adapters are expected;
- testing through ports has clear value.

### CQRS

Use when read and write models have materially different needs.

Do not use CQRS for ordinary CRUD.

---

## Step 9 — Model critical flows

For each critical flow, document:

1. entry point;
2. validation;
3. authentication/authorization;
4. state read;
5. decision;
6. state write;
7. external call;
8. event;
9. response;
10. failure handling.

Include sequence diagrams where helpful.

---

## Step 10 — Define consistency and transactions

Choose intentionally:

- strong consistency;
- eventual consistency;
- read-your-writes;
- monotonic reads;
- best effort.

For each multi-step operation, define:

- atomic boundary;
- partial-failure behavior;
- compensation;
- retry;
- idempotency;
- deduplication.

Avoid distributed transactions unless they are truly required and supported.

Prefer patterns such as:

- transactional outbox;
- idempotency key;
- saga;
- reconciliation.

---

## Step 11 — Design failure handling

List dependencies and failure modes:

| Dependency | Failure | Detection | Response | Recovery |
|---|---|---|---|---|
| Database | timeout | exception/metric | fail request | retry/recover |
| External API | 5xx | response | bounded retry | alert/replay |
| Queue | unavailable | publish failure | persist/outbox | retry |
| Cache | miss/down | error | database fallback | restore |

Consider:

- timeout;
- retry;
- backoff;
- jitter;
- circuit breaker;
- bulkhead;
- fallback;
- degraded mode;
- replay;
- dead-letter queue;
- reconciliation.

---

## Step 12 — Design concurrency and ordering

Define:

- concurrency unit;
- ordering key;
- maximum parallelism;
- shared state;
- lock strategy;
- duplicate handling;
- queue capacity;
- backpressure;
- multi-instance behavior.

Examples:

- serialize operations per customer ID;
- allow different customers in parallel;
- use optimistic locking for competing updates;
- use idempotency keys for repeated commands.

---

## Step 13 — Design caching

Use caching only after identifying:

- expensive source;
- read frequency;
- acceptable staleness;
- invalidation strategy;
- failure behavior.

Define:

- cache key;
- value;
- TTL;
- eviction;
- invalidation;
- consistency;
- stampede prevention;
- fallback;
- observability.

Do not use a cache as the source of truth unless explicitly designed that way.

---

## Step 14 — Design scalability

Scale only the bottleneck.

Consider:

- horizontal application scaling;
- database indexes;
- query optimization;
- pagination;
- connection pools;
- queues;
- partitioning;
- sharding;
- batch processing;
- asynchronous work;
- payload reduction.

For each scaling mechanism, state the new complexity introduced.

---

## Step 15 — Design security

Document:

- trust boundaries;
- authentication;
- authorization;
- tenant isolation;
- data classification;
- encryption;
- key management;
- secrets;
- audit;
- retention;
- deletion;
- abuse prevention;
- dependency risk.

Use least privilege.

Threat-model critical flows.

---

## Step 16 — Design observability

Define:

### Logs

- structured fields;
- safe identifiers;
- result;
- duration;
- failure category;
- correlation ID.

### Metrics

- request count;
- success/failure;
- latency;
- queue depth;
- retries;
- circuit state;
- business outcome;
- resource saturation.

### Traces

Trace:

- entry point;
- database;
- remote calls;
- messaging;
- asynchronous boundaries.

### Alerts

Alert on user impact and exhausted recovery, not every transient error.

---

## Step 17 — Design deployment and operations

Define:

- runtime topology;
- replicas;
- resource requests/limits;
- health checks;
- readiness;
- graceful shutdown;
- configuration;
- secret delivery;
- rollout;
- rollback;
- feature flags;
- disaster recovery.

---

## Step 18 — Design migration

For existing systems, define:

- compatibility period;
- deployment order;
- data migration;
- backfill;
- dual read/write if needed;
- traffic switch;
- verification;
- rollback;
- cleanup.

Prefer reversible steps.

---

## Step 19 — Design testing

Include:

- unit;
- integration;
- contract;
- end-to-end;
- migration;
- security;
- resilience;
- performance;
- concurrency;
- rollback.

Map every major requirement and risk to a verification method.

---

## Step 20 — Evaluate cost

Consider:

- infrastructure;
- storage;
- network;
- external APIs;
- operations;
- on-call burden;
- development complexity;
- maintenance.

The cheapest infrastructure is not always the cheapest system.

---

## 4. Trade-off framework

For each important decision, record:

```text
Decision:
Problem:
Options:
Selected option:
Why:
Benefits:
Costs:
Risks:
Revisit when:
Evidence:
```

Common trade-offs:

- consistency versus availability;
- latency versus durability;
- simplicity versus flexibility;
- synchronous versus asynchronous;
- normalized versus denormalized;
- local transaction versus distributed workflow;
- build versus buy;
- modular monolith versus microservices;
- exact retrieval versus semantic retrieval.

---

## 5. Architecture decision record

Use an ADR when a decision:

- affects multiple modules;
- changes a public contract;
- introduces infrastructure;
- creates a long-term constraint;
- is expensive to reverse;
- has meaningful alternatives.

ADR structure:

```markdown
# ADR-NNN: Title

## Status

## Context

## Decision

## Alternatives considered

## Consequences

## Risks

## Validation

## Revisit criteria
```

---

## 6. System-design response template

```markdown
# Design: <Name>

## 1. Executive summary

## 2. Problem and goals

## 3. Non-goals

## 4. Requirements

### Functional

### Non-functional

## 5. Constraints and assumptions

## 6. Capacity and scale

## 7. Current architecture

## 8. Proposed architecture

## 9. Components and responsibilities

## 10. APIs and events

## 11. Data model

## 12. Critical flows

## 13. Consistency and transactions

## 14. Failure handling and resilience

## 15. Concurrency and ordering

## 16. Performance and scaling

## 17. Security and privacy

## 18. Observability

## 19. Deployment and operations

## 20. Migration and rollout

## 21. Testing strategy

## 22. Alternatives and trade-offs

## 23. Risks and mitigations

## 24. Open questions

## 25. Definition of done
```

---

## 7. Design review checklist

### Problem

- [ ] Is the business problem clear?
- [ ] Are goals measurable?
- [ ] Are non-goals explicit?

### Requirements

- [ ] Are functional requirements testable?
- [ ] Are NFRs measurable?
- [ ] Are constraints visible?

### Architecture

- [ ] Are boundaries justified?
- [ ] Is ownership clear?
- [ ] Is complexity proportional?

### Data

- [ ] Are invariants protected?
- [ ] Are indexes based on queries?
- [ ] Is migration safe?

### Reliability

- [ ] Are timeouts defined?
- [ ] Are retries bounded and safe?
- [ ] Is partial failure handled?
- [ ] Is recovery possible?

### Security

- [ ] Are trust boundaries defined?
- [ ] Is authorization explicit?
- [ ] Are secrets and sensitive data protected?

### Operations

- [ ] Is behavior observable?
- [ ] Is rollback possible?
- [ ] Are resource limits defined?
- [ ] Is graceful shutdown handled?

### Verification

- [ ] Does testing cover the largest risks?
- [ ] Are performance claims measured?
- [ ] Are compatibility claims tested?
