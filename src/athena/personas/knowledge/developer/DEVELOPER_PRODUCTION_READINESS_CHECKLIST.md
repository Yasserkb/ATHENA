# Developer Production Readiness Checklist

## Requirement and ownership

- [ ] User/business outcome is clear.
- [ ] Acceptance criteria are testable.
- [ ] Owner exists.
- [ ] Non-goals are explicit.
- [ ] Risk is classified.

## Architecture

- [ ] Correct stack/persona was selected.
- [ ] Repository conventions are followed.
- [ ] Responsibilities are cohesive.
- [ ] Contracts are explicit.
- [ ] No speculative abstraction was added.

## Frontend/mobile

- [ ] Loading, empty, error, offline, and authorization states are handled.
- [ ] Accessibility is validated.
- [ ] Responsive/device behavior is understood.
- [ ] Secrets are not bundled.
- [ ] Performance budget is respected.
- [ ] Lifecycle and upgrade behavior are handled where relevant.

## Backend

- [ ] Validation and authorization are server-side.
- [ ] Transactions are deliberate.
- [ ] Duplicate/idempotent behavior is defined.
- [ ] Timeouts and remote failures are handled.
- [ ] Errors are mapped safely.
- [ ] Graceful shutdown/resource lifecycle is defined.

## Data

- [ ] Schema and constraints match invariants.
- [ ] Migration is safe and compatible.
- [ ] Index/query impact is understood.
- [ ] Retention and sensitive data are handled.
- [ ] Rollback or forward-fix exists.

## Security

- [ ] Authentication and authorization are tested.
- [ ] Tenant/object isolation is protected.
- [ ] Inputs are validated.
- [ ] Secrets and sensitive logs are protected.
- [ ] Dependency/security findings are reviewed.

## Reliability and performance

- [ ] Failure modes are documented.
- [ ] Retries are bounded and idempotent.
- [ ] Concurrency is analyzed.
- [ ] Performance claims are measured.
- [ ] Capacity/resource limits are understood.

## Testing

- [ ] Lowest reliable test levels are used.
- [ ] Critical integration boundaries are tested.
- [ ] Negative/boundary/concurrency cases exist.
- [ ] Tests are deterministic.
- [ ] Flakiness is not hidden.

## Observability

- [ ] Logs are structured and safe.
- [ ] Metrics expose outcome and failure.
- [ ] Correlation exists across boundaries.
- [ ] Frontend/mobile errors are observable.
- [ ] Alerts/runbooks exist for critical behavior.

## Delivery

- [ ] Build and configuration are reproducible.
- [ ] Migration/deployment order is defined.
- [ ] Feature flag/progressive rollout is considered.
- [ ] Smoke checks exist.
- [ ] Observation window exists.
- [ ] Rollback trigger and procedure exist.
- [ ] Residual risks have owners.
