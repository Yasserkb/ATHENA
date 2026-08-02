# Cloud Architecture System Design Playbook

## 1. Purpose

Use this playbook for:

- new cloud platforms;
- workload cloud architecture;
- cloud migration;
- landing zones;
- hybrid and multi-cloud;
- regional expansion;
- resilience redesign;
- data-platform cloud design;
- cloud security architecture.

---

## 2. Design template

```markdown
# Cloud Architecture: <Name>

## 1. Executive summary
## 2. Business objective
## 3. Users and workload
## 4. Goals and non-goals
## 5. Functional requirements
## 6. Non-functional requirements
## 7. Constraints and assumptions
## 8. Data classification and compliance
## 9. Scale and capacity
## 10. Current architecture
## 11. Target provider-neutral architecture
## 12. Provider mapping
## 13. Organization and account structure
## 14. Identity and access
## 15. Network topology
## 16. Compute
## 17. Data and storage
## 18. Integration and messaging
## 19. Security controls
## 20. Availability and disaster recovery
## 21. Observability
## 22. Deployment and operations
## 23. Cost and FinOps
## 24. Migration and cutover
## 25. Rollback and exit strategy
## 26. Alternatives and trade-offs
## 27. Risks and mitigations
## 28. Open decisions
## 29. Definition of done
```

---

## 3. Architecture views

Provide views based on audience.

### Context view

Shows:

- users;
- external systems;
- cloud boundary;
- data movement.

### Logical view

Shows:

- application;
- data;
- integration;
- security;
- platform capabilities.

### Deployment view

Shows:

- account/subscription/project;
- region;
- zone;
- network;
- runtime;
- storage.

### Security view

Shows:

- trust boundaries;
- identity;
- encryption;
- ingress/egress;
- audit.

### Failure view

Shows:

- failure domains;
- redundancy;
- failover;
- recovery.

### Cost view

Shows:

- major cost drivers;
- allocation;
- scaling behavior.

---

## 4. Architecture decision framework

For each service choice:

```text
Capability:
Requirements:
Candidate options:
Selected option:
Why:
Operational responsibility:
Availability:
Scalability:
Security:
Cost:
Lock-in:
Exit path:
Quotas:
Failure modes:
Validation:
```

---

## 5. Well-architected dimensions

Review:

- operational excellence;
- security;
- reliability;
- performance efficiency;
- cost optimization;
- sustainability.

Provider frameworks may name these differently, but the underlying questions remain useful.

---

## 6. Dependency failure analysis

For every dependency:

| Dependency | Scope | Failure mode | Detection | Degraded mode | Recovery |
|---|---|---|---|---|---|
| Identity | global/regional | authentication unavailable | metrics/health | existing session only | failover/manual |
| DNS | global | lookup failure | synthetic check | cached resolution | secondary DNS |
| Database | zonal/regional | unavailable | connection errors | read-only/queue | failover |
| Object storage | regional | request failure | error metric | buffer locally | retry/reconcile |

---

## 7. Architecture review checklist

### Requirements

- [ ] Availability is measurable.
- [ ] Latency is measurable.
- [ ] RTO and RPO are defined.
- [ ] Data residency is known.
- [ ] Cost constraints are known.

### Boundaries

- [ ] Account structure is justified.
- [ ] Environment isolation is clear.
- [ ] Ownership is clear.
- [ ] Trust boundaries are visible.

### Identity

- [ ] SSO and MFA exist.
- [ ] Workload identity is used.
- [ ] Privileged access is limited.
- [ ] CI uses federation or short-lived credentials.

### Network

- [ ] CIDRs do not overlap.
- [ ] Public exposure is justified.
- [ ] Egress is controlled.
- [ ] DNS ownership is clear.
- [ ] Private endpoints are considered.

### Data

- [ ] Database fits access patterns.
- [ ] Encryption is defined.
- [ ] Backup and restore are tested.
- [ ] Retention is defined.
- [ ] Replication semantics are understood.

### Reliability

- [ ] Failure domains are identified.
- [ ] Capacity during failure is sufficient.
- [ ] Dependencies match availability target.
- [ ] Failover is tested.

### Operations

- [ ] Metrics and logs exist.
- [ ] Audit logs are centralized.
- [ ] Alerts are actionable.
- [ ] Runbooks and ownership exist.

### Cost

- [ ] Major cost drivers are known.
- [ ] Budgets and alerts exist.
- [ ] Egress and observability cost are included.
- [ ] Commitment risk is evaluated.
