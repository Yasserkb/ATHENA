# Senior Developer Design Patterns Playbook

## 1. Purpose

This playbook helps the Senior Developer persona select, apply, review, and reject design patterns.

A design pattern is a reusable design approach to a recurring problem. It is not a mandatory template and is not proof of seniority.

The correct question is not:

> Which pattern can be added?

The correct question is:

> Which recurring force or variation needs to be isolated, and what is the simplest design that does so safely?

---

## 2. Pattern-selection rules

Before using a pattern, answer:

1. What concrete problem repeats?
2. What changes independently?
3. What coupling is harmful?
4. What direct solution was considered?
5. What complexity will the pattern add?
6. Does the repository already use a compatible pattern?
7. How will the pattern be tested?
8. How will future developers recognize it?
9. When should it be removed or simplified?

Reject a pattern when:

- there is only one stable implementation;
- the variation is hypothetical;
- the abstraction hides rather than clarifies;
- framework capability already solves the problem;
- the team cannot operate it safely;
- the added indirection exceeds the value.

---

## 3. Foundational principles

Patterns should support:

- single responsibility;
- explicit dependencies;
- high cohesion;
- low coupling;
- dependency inversion at real boundaries;
- encapsulation;
- composition over inheritance;
- tell, do not ask;
- information hiding;
- stable contracts;
- local reasoning.

SOLID is guidance, not a scoring system. Applying every principle mechanically can produce excessive abstraction.

---

# Part I — Creational patterns

## 4. Factory Method

### Problem

Object creation depends on type, configuration, protocol, or runtime choice.

### Use when

- creation logic is complex;
- callers should depend on a contract;
- implementation selection is centralized;
- external clients vary by tenant/provider.

### Java/Spring mapping

- `@Bean` factory methods;
- provider registries;
- client factories;
- parser registries.

### Avoid when

- direct construction is clear;
- only one stable implementation exists;
- the factory merely wraps `new`.

### Review questions

- Is selection deterministic?
- Are unsupported types rejected?
- Is lifecycle ownership clear?
- Is configuration validated?

---

## 5. Abstract Factory

### Problem

A family of related objects must be created consistently.

### Use when

- one provider requires matching client, mapper, validator, and configuration;
- environment-specific families exist;
- mixed families would be invalid.

### Avoid when

- only one object varies;
- factory hierarchy becomes more complex than creation.

---

## 6. Builder

### Problem

Construction has many optional or validated values.

### Use when

- immutable objects have many fields;
- test data requires readable construction;
- construction order and validation matter.

### Java mapping

- explicit builder;
- Lombok builder with care;
- test-data builder.

### Risks

- bypassed invariants;
- invalid partial objects;
- builders for simple two-field DTOs.

---

## 7. Prototype

### Problem

New instances are efficiently derived from an existing configured instance.

### Use sparingly

Useful for complex templates or immutable configuration snapshots.

Avoid mutable shallow-copy traps.

---

# Part II — Structural patterns

## 8. Adapter

### Problem

An external or incompatible interface must fit an internal contract.

### Use when

- integrating external APIs;
- isolating SDK changes;
- translating protocol errors;
- protecting domain code.

### Spring example

```text
Application port
    ← adapter
        ← Feign/WebClient/SDK
```

### Benefits

- external details remain at the boundary;
- easier testing;
- normalized failure model;
- replaceable provider.

### Risks

- leaking provider DTOs through the port;
- hiding important provider semantics.

---

## 9. Facade

### Problem

A complex subsystem needs a simpler entry point.

### Use when

- callers should not coordinate many low-level services;
- a use case spans several components;
- a stable public boundary is valuable.

### Avoid when

The facade becomes a god service.

A facade should simplify access, not own every business rule.

---

## 10. Decorator

### Problem

Add behavior around an object without changing its core implementation.

### Use for

- metrics;
- caching;
- authorization;
- tracing;
- retry wrappers;
- audit.

### Spring mapping

- explicit decorators;
- filters;
- interceptors;
- AOP where semantics remain visible.

### Risks

- hidden order;
- repeated execution;
- proxy limitations;
- difficult debugging.

Use explicit composition when order and behavior matter.

---

## 11. Proxy

### Problem

Control access to another object.

### Spring examples

- `@Transactional`;
- method security;
- lazy initialization;
- AOP proxies.

### Important warning

Self-invocation can bypass Spring proxies. The persona must inspect proxy boundaries before relying on annotations.

---

## 12. Facade versus Adapter versus Decorator

| Pattern | Main purpose |
|---|---|
| Adapter | Change an interface |
| Facade | Simplify a subsystem |
| Decorator | Add behavior |
| Proxy | Control access |

Do not use the names interchangeably.

---

## 13. Composite

### Problem

Treat individual objects and groups uniformly.

### Use for

- rule trees;
- validation groups;
- nested document structures;
- permission hierarchies.

### Risks

- unclear lifecycle;
- expensive recursive traversal;
- mixed semantics.

---

## 14. Bridge

### Problem

Two dimensions vary independently.

Example:

```text
notification type × delivery provider
```

Use only when both dimensions genuinely vary.

---

# Part III — Behavioral patterns

## 15. Strategy

### Problem

One behavior has multiple algorithms or policies.

### Use when

- provider-specific behavior varies;
- pricing, validation, routing, or retry policy differs;
- conditionals are expanding.

### Java/Spring mapping

```text
interface Strategy
multiple @Component implementations
registry/factory selects strategy
```

### Avoid when

- there are only two tiny stable branches;
- selection logic becomes hidden.

---

## 16. Template Method

### Problem

A process has stable steps with controlled variation.

### Use when

- workflow skeleton is shared;
- subclasses vary a few steps;
- ordering must remain fixed.

### Risks

- inheritance coupling;
- fragile base class;
- hidden hooks.

Prefer composition/strategy when variation is broad.

---

## 17. Command

### Problem

Represent an operation as an object.

### Use for

- queued work;
- audit;
- retry;
- scheduling;
- undo where practical;
- use-case objects.

### Risks

- class explosion;
- command objects with no value beyond one method call.

---

## 18. Chain of Responsibility

### Problem

A request passes through ordered handlers.

### Use for

- validation;
- security filters;
- enrichment;
- processing pipelines;
- rule evaluation.

### Requirements

- order must be explicit;
- stop/continue behavior must be clear;
- failures must be owned;
- each handler must remain cohesive.

---

## 19. Observer

### Problem

Multiple consumers react to an event.

### Spring mapping

- application events;
- domain events;
- message broker consumers.

### Distinguish

- in-process Spring event;
- durable external event.

Do not treat an in-memory event as reliable messaging.

---

## 20. State

### Problem

Behavior depends on lifecycle state and transitions are significant.

### Use for

- workflows;
- orders;
- contact plans;
- controls;
- remediation states.

### Benefits

- valid transitions become explicit;
- state-specific behavior is localized.

### Avoid when

A simple enum and validated transition table are sufficient.

---

## 21. Specification

### Problem

Business predicates must be composed and reused.

### Use for

- eligibility;
- search criteria;
- policy;
- validation;
- repository queries.

### Spring/JPA mapping

- JPA `Specification`;
- explicit domain specifications.

### Risks

- mixing database and domain concerns;
- unreadable generic combinators;
- hidden query performance.

---

## 22. Mediator

### Problem

Many components communicate through complex relationships.

Use carefully. A mediator can reduce coupling, but a central mediator can become a god service.

---

# Part IV — Architectural patterns

## 23. Layered architecture

Typical flow:

```text
Controller
→ Application Service
→ Repository/Client
```

### Good for

- clear responsibilities;
- ordinary enterprise applications;
- consistent development.

### Risks

- business logic in controllers;
- god services;
- repositories exposed directly;
- layer-by-layer DTO duplication without value.

---

## 24. Hexagonal architecture

Core:

```text
Application/domain
    ↔ ports
        ↔ adapters
```

### Use when

- external systems change;
- domain logic deserves isolation;
- multiple adapters exist;
- testability across boundaries is valuable.

### Avoid when

A small CRUD module would gain only ceremony.

---

## 25. Clean architecture

Use the dependency rule:

```text
outer layers depend inward
```

Do not interpret it as “create five modules for every feature.”

---

## 26. Modular monolith

### Use when

- one deployable unit is operationally preferable;
- boundaries can be enforced in code;
- strong local transactions matter;
- teams do not need independent deployment.

### Requirements

- explicit module ownership;
- restricted dependencies;
- public module interfaces;
- no shared-table free-for-all.

Often the best default before microservices.

---

## 27. Microservices

Choose only when independent ownership/deployment/scaling justifies:

- network failure;
- distributed tracing;
- eventual consistency;
- operational overhead;
- schema/event versioning.

A distributed monolith is worse than a well-structured monolith.

---

## 28. Domain-Driven Design

Use DDD strategically.

Useful building blocks:

- bounded context;
- aggregate;
- entity;
- value object;
- domain service;
- repository;
- domain event;
- anti-corruption layer.

Avoid tactical DDD ceremony when the domain is simple.

---

## 29. CQRS

Separate command and query models when:

- read and write needs differ materially;
- complex projections are justified;
- independent scaling matters;
- domain commands require strong modeling.

Do not use CQRS for standard CRUD.

---

## 30. Event-driven architecture

Use when temporal decoupling and independent reactions are valuable.

Define:

- event ownership;
- schema;
- versioning;
- ordering;
- idempotency;
- retry;
- replay;
- dead-letter handling.

---

# Part V — Data and integration patterns

## 31. Repository

Use as a collection-like persistence boundary for aggregates or meaningful domain objects.

Avoid:

- one generic repository abstraction over every database;
- leaking query technology everywhere;
- business orchestration in repositories.

Spring Data already supplies much of the mechanism.

---

## 32. Data Mapper

Separates persistence representation from domain representation.

MapStruct can implement structural mapping, but business decisions should remain explicit.

---

## 33. Unit of Work

JPA’s persistence context already behaves like a Unit of Work.

Do not reimplement it unless using a different persistence model with a concrete need.

---

## 34. Transactional Outbox

### Problem

Database state and event publication must not diverge.

### Flow

```text
business update + outbox insert
    in one transaction

publisher reads outbox
    → publishes event
    → marks processed
```

### Requirements

- idempotent consumer;
- cleanup;
- ordering policy;
- monitoring;
- replay strategy.

---

## 35. Saga

Coordinates a distributed workflow through local transactions and compensation.

Use when a business operation crosses independent transactional boundaries.

### Types

- orchestration;
- choreography.

### Risks

- compensation complexity;
- partial states;
- difficult debugging;
- event coupling.

---

## 36. Anti-Corruption Layer

Protects one domain model from another system’s concepts.

Useful for legacy and external integrations.

---

## 37. Strangler Fig

Incrementally replace a legacy capability by routing portions to a new implementation.

Requires:

- clear boundary;
- compatibility;
- observability;
- traffic control;
- removal plan.

---

# Part VI — Resilience patterns

## 38. Timeout

Every remote call requires a finite timeout.

Separate:

- connection timeout;
- read/response timeout;
- total deadline.

---

## 39. Retry

Use only for transient failures and idempotent/safe operations.

Define:

- retryable errors;
- attempts;
- backoff;
- jitter;
- deadline;
- observability.

Never retry validation, authentication, or permanent business failures by default.

---

## 40. Circuit Breaker

Use when repeated calls to a failing dependency cause resource waste or cascading failure.

Track:

- closed;
- open;
- half-open.

Do not use a circuit breaker as a substitute for timeout.

---

## 41. Bulkhead

Isolate resource pools so one dependency cannot exhaust the entire application.

Examples:

- separate thread pools;
- connection pools;
- concurrency limits.

---

## 42. Rate Limiter

Protect:

- application;
- downstream;
- tenant fairness;
- external quotas.

Define response behavior and observability.

---

## 43. Idempotency

Required when duplicate commands are possible.

Approaches:

- idempotency key;
- natural unique constraint;
- processed-message table;
- state-transition guard.

---

## 44. Backpressure

When producers can outpace consumers, use:

- bounded queues;
- rejection;
- throttling;
- batching;
- demand signaling;
- load shedding.

Unbounded queues delay failure and risk memory exhaustion.

---

# Part VII — Concurrency patterns

## 45. Optimistic locking

Use when collisions are possible but uncommon.

JPA:

```text
@Version
```

Handle retry or conflict explicitly.

---

## 46. Pessimistic locking

Use when conflict is expected and correctness requires exclusive access.

Minimize lock scope and duration.

---

## 47. Per-key serialization

Use when operations for the same business key must be ordered while different keys may execute in parallel.

Define:

- key;
- queue/lock;
- cleanup;
- timeout;
- multi-instance behavior.

---

## 48. Immutable data

Prefer immutability for shared state and messages.

It reduces accidental concurrency defects.

---

# Part VIII — Testing patterns

## 49. Test Data Builder

Use for readable valid test objects with targeted overrides.

Prefer over giant constructors and repeated fixtures.

---

## 50. Object Mother

Provides common object presets.

Use carefully; excessive hidden defaults can make tests unclear.

---

## 51. Fake

A working lightweight implementation, such as an in-memory repository.

Useful when behavior matters more than interaction.

---

## 52. Stub

Returns controlled data.

Use for dependency outcomes.

---

## 53. Mock

Verifies important interaction at an external or orchestration boundary.

Avoid mocking internal implementation details.

---

## 54. Contract Test

Verifies that consumer and provider agree on:

- schema;
- endpoint;
- status;
- semantics.

Critical for independently deployed services.

---

# Part IX — Common anti-patterns

## 55. God Service

Symptoms:

- many dependencies;
- unrelated methods;
- broad transactions;
- every feature edits the same class.

Correction:

- split by use case or domain responsibility;
- retain a thin orchestration boundary.

---

## 56. Anemic orchestration everywhere

Not every domain requires rich entities, but business rules should not be scattered across controllers, mappers, and repositories.

Place rules where ownership is clearest.

---

## 57. Service Locator

Hidden dependency lookup harms:

- testability;
- visibility;
- lifecycle;
- static analysis.

Use constructor injection.

---

## 58. Generic abstraction too early

Examples:

- `GenericService<T>`;
- universal client wrapper;
- universal repository;
- generic workflow engine for one workflow.

Wait for real repeated structure.

---

## 59. Boolean-flag method

```text
process(data, true, false, true)
```

Flags often hide multiple behaviors.

Use explicit operations or a meaningful options object.

---

## 60. Retry storm

Multiple layers retry the same failing call.

Define one retry owner and total deadline.

---

## 61. Distributed monolith

Services deploy separately but require coordinated changes and synchronous chains.

Improve boundaries or return to a modular monolith.

---

## 62. Shared database as integration API

Independent services writing each other’s tables destroy ownership.

Use contracts, events, or explicit APIs.

---

## 63. Transactional spaghetti

Symptoms:

- unclear transaction ownership;
- remote calls inside transactions;
- nested propagation;
- unexpected rollback.

Define one application-level transaction boundary.

---

## 64. Exception swallowing

Catching and logging without resolution makes failures invisible to callers and recovery logic.

---

## 65. Cache-as-truth accident

A cache becomes required for correctness without durability or recovery design.

---

# Part X — Pattern decision matrix

| Problem | Consider first | Avoid first |
|---|---|---|
| Multiple algorithms | Strategy | large conditional tree |
| External API mismatch | Adapter | provider DTO leakage |
| Complex subsystem entry | Facade | god service |
| Cross-cutting behavior | Decorator/interceptor | hidden global AOP |
| Ordered processing | Chain of Responsibility | implicit unordered handlers |
| Lifecycle-dependent behavior | State | scattered switch statements |
| Reusable predicates | Specification | duplicated conditions |
| DB + event atomicity | Transactional Outbox | direct publish after commit |
| Distributed workflow | Saga | fake distributed transaction |
| Transient remote failure | Timeout + bounded Retry | infinite retry |
| Competing updates | Optimistic locking | last-write-wins silently |
| Same-key ordering | Per-key serialization | global lock |
| Legacy replacement | Strangler | big-bang rewrite |

---

## 66. Pattern documentation template

When applying a meaningful pattern, document:

```markdown
## Pattern: <Name>

### Problem

### Forces

### Selected pattern

### Why it fits

### Repository precedent

### Responsibilities

### Failure behavior

### Testing

### Trade-offs

### Revisit criteria
```

---

## 67. Final pattern checklist

- [ ] A concrete recurring problem exists.
- [ ] The direct solution was considered.
- [ ] The pattern matches repository conventions.
- [ ] Responsibilities are clearer after applying it.
- [ ] Failure behavior remains explicit.
- [ ] Tests verify behavior.
- [ ] Operational complexity is acceptable.
- [ ] The pattern name is used correctly.
- [ ] Future developers can understand it.
- [ ] There is no simpler complete design.
