# DevOps Production Readiness Checklist

## Ownership

- [ ] Technical owner exists.
- [ ] Operational owner exists.
- [ ] Escalation path exists.
- [ ] Runbooks are linked.

## Source and artifacts

- [ ] Source is reviewed.
- [ ] Artifact is immutable.
- [ ] Artifact maps to a commit.
- [ ] SBOM exists where required.
- [ ] Vulnerability policy is satisfied.
- [ ] Signature/provenance is verified where required.

## Configuration and secrets

- [ ] Configuration is validated.
- [ ] Secrets are externalized.
- [ ] Rotation is defined.
- [ ] No sensitive value appears in logs or artifacts.

## Runtime

- [ ] Resources are defined.
- [ ] Health probes are correct.
- [ ] Graceful shutdown is implemented.
- [ ] Autoscaling bounds exist.
- [ ] Disruption behavior is known.
- [ ] Storage behavior is known.

## Networking

- [ ] Ingress is justified.
- [ ] Egress is controlled.
- [ ] TLS is valid.
- [ ] DNS is owned.
- [ ] Timeouts are defined.
- [ ] Firewall rules are least privilege.

## Security

- [ ] Workload identity is least privilege.
- [ ] RBAC/IAM reviewed.
- [ ] Container runs non-root where possible.
- [ ] Policy checks pass.
- [ ] Audit evidence exists.
- [ ] Tenant boundaries are protected.

## Reliability

- [ ] Failure modes are documented.
- [ ] Retry is bounded and safe.
- [ ] Dependency timeout exists.
- [ ] Rollback is tested.
- [ ] Backup and restore are validated.
- [ ] RPO/RTO are defined where relevant.

## Observability

- [ ] Metrics exist.
- [ ] Logs are structured.
- [ ] Traces exist where useful.
- [ ] Dashboard exists.
- [ ] Alerts are actionable.
- [ ] SLO exists for critical service.

## Deployment

- [ ] Deployment strategy is defined.
- [ ] Database compatibility is verified.
- [ ] Migration order is defined.
- [ ] Smoke tests exist.
- [ ] Success and failure signals exist.
- [ ] Observation window exists.
- [ ] Rollback trigger exists.

## Capacity and cost

- [ ] Capacity is estimated.
- [ ] Quotas are sufficient.
- [ ] Saturation signals exist.
- [ ] Cost impact is understood.
- [ ] Retention policies exist.

## Compliance

- [ ] Data classification is known.
- [ ] Retention/deletion rules are satisfied.
- [ ] Required approvals exist.
- [ ] Audit requirements are met.

## Definition of ready

Production readiness is approved only when unresolved items have:

- explicit risk;
- owner;
- deadline;
- accepted mitigation.
