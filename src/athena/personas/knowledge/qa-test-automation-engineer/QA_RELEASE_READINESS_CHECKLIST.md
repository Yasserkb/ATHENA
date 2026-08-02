# QA Release Readiness Checklist

## Requirements

- [ ] Acceptance criteria are testable.
- [ ] Ambiguities are resolved or documented.
- [ ] In-scope and out-of-scope are clear.
- [ ] Critical user journeys are identified.

## Risk

- [ ] Product risks are prioritized.
- [ ] Security and data risks are included.
- [ ] Integration and migration risks are included.
- [ ] Recovery risk is understood.
- [ ] Residual risks have owners.

## Functional evidence

- [ ] Nominal paths are covered.
- [ ] Negative paths are covered.
- [ ] Boundaries are covered.
- [ ] State transitions are covered.
- [ ] Permissions are covered.
- [ ] Configuration variants are covered where relevant.

## Automation

- [ ] Tests use the correct level.
- [ ] Tests are deterministic.
- [ ] No unexplained flakiness exists.
- [ ] Test data is isolated.
- [ ] Failures provide diagnostics.
- [ ] Execution time is acceptable.
- [ ] Ownership exists.

## API and integration

- [ ] Contracts are validated.
- [ ] External failures are tested.
- [ ] Timeouts are tested.
- [ ] Duplicate/idempotent behavior is tested.
- [ ] Persistence is verified.
- [ ] Migrations are tested.

## UI/mobile

- [ ] Critical journeys are tested.
- [ ] Accessibility is reviewed.
- [ ] Supported browsers/devices are covered.
- [ ] Error recovery is tested.
- [ ] Network/interruption behavior is tested where relevant.

## Non-functional

- [ ] Performance thresholds are met.
- [ ] Resource saturation is understood.
- [ ] Security findings are addressed.
- [ ] Recovery behavior is tested.
- [ ] Reliability mechanisms are validated.

## Environment and data

- [ ] Environment version is known.
- [ ] Dependencies are healthy.
- [ ] Test data is controlled.
- [ ] Production-sensitive data is protected.
- [ ] Environment limitations are documented.

## Defects

- [ ] Blocker defects are closed.
- [ ] Critical defects are resolved or accepted explicitly.
- [ ] Deferred defects have owners.
- [ ] Fixes are retested.
- [ ] Regression coverage exists.

## Release

- [ ] Artifact is traceable.
- [ ] Smoke tests exist.
- [ ] Rollback is possible.
- [ ] Production signals are defined.
- [ ] Observation window exists.
- [ ] Release recommendation is explicit.

## Decision

Release readiness is approved only when untested or failed areas have:

- known impact;
- explicit owner;
- accepted risk;
- mitigation;
- follow-up date.
