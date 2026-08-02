# Cloud Production Readiness Checklist

## Requirements

- [ ] Workload criticality is classified.
- [ ] Availability target is defined.
- [ ] Latency and throughput are defined.
- [ ] RTO and RPO are defined.
- [ ] Data residency is known.
- [ ] Budget and owner are known.

## Foundation

- [ ] Correct account/subscription/project is used.
- [ ] Environment is isolated.
- [ ] Resource ownership is tagged.
- [ ] Audit logging is enabled.
- [ ] Policy baseline is applied.
- [ ] Budget alerts exist.

## Identity

- [ ] Human access uses SSO and MFA.
- [ ] Workload identity is used.
- [ ] CI/CD uses short-lived identity.
- [ ] Least privilege is reviewed.
- [ ] Break-glass exists and is monitored.
- [ ] Access review process exists.

## Network

- [ ] CIDR is approved.
- [ ] Public exposure is justified.
- [ ] Private endpoints are considered.
- [ ] Ingress is protected.
- [ ] Egress is controlled.
- [ ] DNS is owned and monitored.
- [ ] TLS is valid and renewable.
- [ ] Flow logs exist where required.

## Compute

- [ ] Compute model fits the workload.
- [ ] Capacity and quotas are sufficient.
- [ ] Scaling bounds exist.
- [ ] Patching/upgrades are owned.
- [ ] Graceful shutdown is defined.
- [ ] Images/artifacts are immutable.

## Data

- [ ] Data service fits access patterns.
- [ ] Encryption is enabled.
- [ ] Backup is configured.
- [ ] Restore is tested.
- [ ] Retention is configured.
- [ ] Replication semantics are understood.
- [ ] Database connection limits are considered.

## Security

- [ ] Data classification is applied.
- [ ] Secrets are in managed storage.
- [ ] Key ownership is clear.
- [ ] Security posture monitoring exists.
- [ ] Vulnerability process exists.
- [ ] Compliance evidence is mapped.
- [ ] Incident escalation exists.

## Reliability

- [ ] Failure domains are documented.
- [ ] Zone/region strategy matches requirements.
- [ ] Critical dependencies are analyzed.
- [ ] Capacity during failure is sufficient.
- [ ] Failover is tested.
- [ ] DR runbook exists.
- [ ] DR exercise frequency is defined.

## Observability

- [ ] Application metrics exist.
- [ ] Platform metrics exist.
- [ ] Logs are centralized.
- [ ] Audit logs are protected.
- [ ] Alerts are actionable.
- [ ] SLO dashboard exists.
- [ ] Cost dashboard exists.

## Operations

- [ ] Operational owner exists.
- [ ] Runbooks exist.
- [ ] Maintenance is planned.
- [ ] Quotas are monitored.
- [ ] Support process exists.
- [ ] Deployment and rollback are tested.

## FinOps

- [ ] Cost allocation is complete.
- [ ] Forecast and anomaly alerts exist.
- [ ] Egress is estimated.
- [ ] Observability retention is controlled.
- [ ] Commitment decisions are justified.
- [ ] Cleanup lifecycle exists.

## Exit and recovery

- [ ] Rollback is defined.
- [ ] Data export is possible.
- [ ] Provider dependencies are documented.
- [ ] Decommissioning plan exists.
- [ ] Residual risks have owners.
