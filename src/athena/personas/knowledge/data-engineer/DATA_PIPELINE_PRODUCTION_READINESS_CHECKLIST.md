# Data Pipeline Production Readiness Checklist

## Ownership and contracts

- [ ] Source owner exists.
- [ ] Pipeline owner exists.
- [ ] Dataset owner/steward exists.
- [ ] Consumers are known.
- [ ] Schema and semantics are documented.
- [ ] Compatibility policy exists.
- [ ] Freshness and quality SLOs exist.

## Source and ingestion

- [ ] Source of truth is identified.
- [ ] Incremental or watermark logic is defined.
- [ ] Deletes are handled.
- [ ] Duplicates are handled.
- [ ] Schema changes are detected.
- [ ] Source outage behavior is defined.
- [ ] Rate limits and authentication are handled.

## Processing

- [ ] Processing model is justified.
- [ ] Jobs are idempotent.
- [ ] Jobs are restartable.
- [ ] Partial failure is handled.
- [ ] Late and out-of-order data are handled.
- [ ] Checkpoints are protected.
- [ ] Replays are safe.

## Storage and modeling

- [ ] Dataset grain is explicit.
- [ ] Keys are defined.
- [ ] Partitioning is justified.
- [ ] File/table format is supported.
- [ ] Retention is configured.
- [ ] History behavior is defined.
- [ ] Consumer queries are supported.

## Quality

- [ ] Schema tests exist.
- [ ] Critical field rules exist.
- [ ] Volume and freshness checks exist.
- [ ] Reconciliation exists.
- [ ] Threshold owners exist.
- [ ] Quarantine/recovery exists.
- [ ] Quality failures are visible.

## Security and governance

- [ ] Data classification is applied.
- [ ] Sensitive fields are protected.
- [ ] Access is least privilege.
- [ ] Encryption is enabled.
- [ ] Catalog metadata exists.
- [ ] Lineage exists.
- [ ] Retention/deletion is complete.
- [ ] Audit requirements are met.

## Orchestration

- [ ] Schedule and timezone are defined.
- [ ] Dependencies are explicit.
- [ ] Retries are bounded.
- [ ] Timeouts exist.
- [ ] Backfill is supported.
- [ ] Missed-run behavior is defined.
- [ ] Ownership and alerting exist.

## Testing

- [ ] Unit/transformation tests exist.
- [ ] Contract tests exist.
- [ ] Integration tests exist.
- [ ] Edge data is covered.
- [ ] Failure/recovery is tested.
- [ ] Migration/backfill is tested.
- [ ] Performance is validated at realistic scale.

## Observability

- [ ] Job health is monitored.
- [ ] Freshness is monitored.
- [ ] Volume is monitored.
- [ ] Quality is monitored.
- [ ] Schema change is monitored.
- [ ] Lag/checkpoint is monitored.
- [ ] Cost is monitored.
- [ ] Downstream impact is visible.

## Reliability

- [ ] Backup/restore is defined.
- [ ] Raw/replay data is retained as required.
- [ ] RTO/RPO are defined.
- [ ] Capacity for backfill is known.
- [ ] Disaster recovery is tested where required.
- [ ] Runbook exists.

## Release

- [ ] Deployment order is defined.
- [ ] Schema compatibility is validated.
- [ ] Consumer migration is planned.
- [ ] Dual-run/shadow comparison is used where needed.
- [ ] Rollback is possible.
- [ ] Post-release reconciliation is planned.
- [ ] Residual risks have owners.
