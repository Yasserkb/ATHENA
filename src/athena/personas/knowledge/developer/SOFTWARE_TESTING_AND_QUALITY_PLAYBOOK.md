# Developer Testing and Quality Playbook

## 1. Testing rule

Test observable behavior at the lowest reliable level.

## 2. Levels

- unit: domain and transformation logic;
- component/slice: framework boundary;
- integration: database, broker, filesystem, external protocol;
- contract: independently evolving consumers/providers;
- UI/device: critical interaction;
- E2E: few critical journeys.

## 3. Required scenario categories

- nominal;
- invalid input;
- boundary;
- missing data;
- authorization;
- duplicate;
- timeout/failure;
- concurrency;
- rollback;
- compatibility;
- migration;
- accessibility where relevant;
- offline/lifecycle for mobile.

## 4. Test doubles

Use:

- fake for working lightweight behavior;
- stub for controlled output;
- mock for meaningful interaction boundaries.

Do not mock private implementation structure.

## 5. Test data

Use builders/factories with explicit defaults. Ensure isolation, cleanup, privacy, and parallel safety.

## 6. Flakiness

Never solve flakiness with permanent unconditional retries. Diagnose:

- shared state;
- timing;
- environment;
- asynchronous completion;
- external dependency;
- order dependency.

## 7. Quality gates

Depending on risk:

- compile/type check;
- lint;
- unit;
- integration;
- contract;
- migration;
- security;
- accessibility;
- performance;
- critical E2E.

## 8. Mutation/property testing

Use selectively when invariants and algorithmic logic benefit.

## 9. Definition of meaningful coverage

Coverage means important requirements and risks have trustworthy evidence. It does not mean line coverage alone.
