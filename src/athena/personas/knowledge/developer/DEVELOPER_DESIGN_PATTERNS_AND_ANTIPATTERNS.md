# Developer Design Patterns and Anti-Patterns

## Selection rule

Use a pattern only when a concrete recurring force exists and the direct solution is insufficient.

## Core patterns

### Adapter

Translate an external or incompatible interface into an internal contract.

### Strategy

Isolate multiple real algorithms or policies.

### Factory

Centralize meaningful construction or implementation selection.

### Builder

Create complex immutable values with validation.

### Facade

Expose a simpler boundary over a complex subsystem.

### Decorator

Add explicit behavior such as metrics, caching, or authorization around a contract.

### Chain of Responsibility

Apply ordered handlers with explicit stop/continue behavior.

### State

Model state-dependent behavior and valid transitions.

### Specification

Compose reusable predicates or query criteria.

### Repository

Encapsulate meaningful persistence access without hiding all database capability.

### Ports and Adapters

Protect application/domain logic from infrastructure when the boundary has real value.

### Transactional Outbox

Coordinate database state and event publication.

### Saga

Coordinate distributed local transactions and compensation.

### Cache-Aside

Load and invalidate cache explicitly around a source of truth.

### Backend for Frontend

Use when web and mobile have materially different aggregation or protocol needs.

### Offline-First

Use local state plus synchronization when mobile/network requirements demand it.

### Strangler

Replace legacy capability incrementally.

## Frontend patterns

- controlled forms;
- container/presentation separation when useful;
- compound components;
- renderless/headless components;
- query cache;
- route-level boundaries;
- design-system primitives.

## Anti-patterns

- god component/service;
- generic repository/service for every entity;
- global mutable state;
- prop drilling solved immediately with a global store;
- boolean-flag APIs;
- distributed monolith;
- event bus for ordinary function calls;
- retry everywhere;
- shared database integration;
- premature microservices;
- premature generic framework;
- client-only authorization;
- ORM entities as public APIs;
- hardcoded platform checks throughout universal code;
- inheritance for code reuse where composition is clearer.

## Pattern record

```markdown
## Pattern: <Name>
### Problem and evidence
### Forces
### Direct option considered
### Why the pattern fits
### Responsibilities
### Failure behavior
### Security/performance cost
### Tests
### Revisit criteria
```
