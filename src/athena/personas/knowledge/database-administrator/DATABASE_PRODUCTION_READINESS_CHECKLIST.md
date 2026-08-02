# Database Production Readiness Checklist

## Ownership and requirements

- [ ] Database owner exists.
- [ ] Application owner exists.
- [ ] Data owner exists.
- [ ] Engine and version are documented.
- [ ] Workload is classified.
- [ ] Availability target exists.
- [ ] RTO and RPO exist.
- [ ] Maintenance window exists.

## Schema

- [ ] Primary keys exist.
- [ ] Business uniqueness is enforced.
- [ ] Foreign keys are justified and present.
- [ ] Nullability is intentional.
- [ ] Check constraints protect critical rules.
- [ ] Naming is consistent.
- [ ] Retention is defined.
- [ ] Tenant isolation is defined.

## Queries and indexes

- [ ] Critical queries are identified.
- [ ] Plans are reviewed.
- [ ] Indexes match workload.
- [ ] Write cost is understood.
- [ ] N+1/unbounded access is controlled.
- [ ] Pagination is safe.
- [ ] Statistics are maintained.

## Transactions

- [ ] Transaction boundaries are explicit.
- [ ] Isolation is appropriate.
- [ ] Long transactions are controlled.
- [ ] External calls are outside transactions where possible.
- [ ] Deadlock retry ownership is defined.
- [ ] Lock timeouts/statement timeouts are configured appropriately.

## Connections

- [ ] Pool limits are defined.
- [ ] Database maximum is protected.
- [ ] Timeouts exist.
- [ ] Failover/reconnect behavior is tested.
- [ ] Pooling mode semantics are understood.

## Security

- [ ] Application is not superuser.
- [ ] Roles are least privilege.
- [ ] Human access uses managed identity/process.
- [ ] Secrets are externalized and rotated.
- [ ] TLS is enabled.
- [ ] Encryption at rest is enabled.
- [ ] Audit is configured.
- [ ] Sensitive non-production data is masked.

## Backup and recovery

- [ ] Backup schedule exists.
- [ ] Retention is defined.
- [ ] Backups are encrypted.
- [ ] Backups are stored outside primary failure domain.
- [ ] Restore is tested.
- [ ] PITR is tested where required.
- [ ] Actual restore time is known.
- [ ] Recovery runbook exists.

## HA and replication

- [ ] Topology is documented.
- [ ] Replication mode is understood.
- [ ] Lag is monitored.
- [ ] Failover is tested.
- [ ] Fencing/split-brain protection exists.
- [ ] Client reconnection is tested.
- [ ] Capacity after failure is sufficient.

## Migrations

- [ ] Migration framework is used.
- [ ] Applied migrations are immutable.
- [ ] Production-size test exists.
- [ ] Lock/rewrite impact is known.
- [ ] Deployment order is defined.
- [ ] Rollback or forward-fix exists.
- [ ] Replication/log/storage impact is known.
- [ ] Validation queries exist.

## Observability

- [ ] Availability is monitored.
- [ ] Connections are monitored.
- [ ] Query latency is monitored.
- [ ] Top queries are visible.
- [ ] Locks/deadlocks are monitored.
- [ ] Replication lag is monitored.
- [ ] Backup failures alert.
- [ ] Disk and growth alert.
- [ ] Runbooks are linked.

## Capacity and maintenance

- [ ] Growth forecast exists.
- [ ] Storage headroom exists.
- [ ] Log/WAL/binlog growth is controlled.
- [ ] Maintenance tasks are scheduled.
- [ ] Vacuum/statistics/index policies are engine-appropriate.
- [ ] Upgrade plan exists.
- [ ] Cost is understood.

## Change readiness

- [ ] Prechecks exist.
- [ ] Exact execution order exists.
- [ ] Stop conditions exist.
- [ ] Monitoring during change exists.
- [ ] Post-validation exists.
- [ ] Rollback trigger exists.
- [ ] Residual risks have owners.
