# Full-Stack System Design Playbook

## 1. Design inputs

Document:

- users;
- business objective;
- critical journeys;
- functional requirements;
- latency and availability;
- data and retention;
- traffic and growth;
- security and compliance;
- offline/mobile needs;
- delivery and cost constraints.

## 2. Views

Provide:

- context view;
- frontend/mobile view;
- API/event view;
- domain/module view;
- data view;
- deployment view;
- security view;
- failure/recovery view.

## 3. Contract-first boundaries

Define contracts for:

- browser/mobile to backend;
- service to service;
- events;
- persistence;
- configuration;
- authentication;
- file/object flows.

## 4. State ownership

For each state item, define:

- source of truth;
- readers/writers;
- consistency;
- cache;
- lifecycle;
- recovery.

## 5. Cross-layer flow

For each critical journey:

```text
user action
→ UI state
→ request/event
→ validation/auth
→ use case/domain
→ transaction/data
→ external side effect
→ response/event
→ UI update
→ observability
```

## 6. Non-functional design

Cover:

- security;
- accessibility;
- performance;
- reliability;
- scalability;
- observability;
- recovery;
- maintainability;
- cost.

## 7. Migration

Use phased compatibility for:

- API changes;
- schema changes;
- event changes;
- client upgrades;
- mobile versions that cannot update immediately.

## 8. Architecture decision record

Record:

- context;
- options;
- decision;
- consequences;
- evidence;
- revisit trigger.

## 9. System-design template

```markdown
# Design: <Name>
## Executive summary
## Goals and non-goals
## Users and journeys
## Requirements and constraints
## Current architecture
## Proposed architecture
## Contracts
## State and data
## Critical flows
## Security and privacy
## Performance and capacity
## Reliability and recovery
## Observability
## Testing
## Deployment and migration
## Alternatives and trade-offs
## Risks and open decisions
## Definition of done
```
