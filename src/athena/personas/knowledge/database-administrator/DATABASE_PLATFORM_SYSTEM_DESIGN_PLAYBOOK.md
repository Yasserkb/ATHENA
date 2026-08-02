# Database Platform System Design Playbook

## 1. Purpose

Use this playbook for:

- new production databases;
- managed database selection;
- database platform design;
- multi-tenant architecture;
- HA/DR;
- migration;
- consolidation;
- sharding;
- database modernization;
- operational governance.

---

## 2. Design template

```markdown
# Database Design: <Name>

## 1. Executive summary
## 2. Business objective
## 3. Workload and users
## 4. Goals and non-goals
## 5. Data classification
## 6. Functional requirements
## 7. Non-functional requirements
## 8. Scale and growth
## 9. Current architecture
## 10. Target architecture
## 11. Engine and deployment model
## 12. Schema and ownership
## 13. Transaction and consistency model
## 14. Indexing and access patterns
## 15. Connection architecture
## 16. Security and audit
## 17. Backup and recovery
## 18. HA and replication
## 19. Observability
## 20. Capacity and performance
## 21. Maintenance
## 22. Migration and cutover
## 23. Rollback
## 24. Cost
## 25. Alternatives and trade-offs
## 26. Risks and mitigations
## 27. Open decisions
## 28. Definition of done
```

---

## 3. Engine-selection criteria

Evaluate:

- transaction model;
- consistency;
- SQL features;
- workload;
- scale;
- availability;
- ecosystem;
- operations;
- licensing;
- cloud support;
- portability;
- team expertise;
- recovery;
- cost.

Do not select an engine from popularity alone.

---

## 4. Deployment models

### Self-managed

Maximum control; maximum operational responsibility.

### Managed database

Reduced operational burden; provider constraints and cost.

### Distributed SQL

Useful when scale, geographic distribution, and transactional consistency justify complexity.

### Serverless database

Useful for variable workloads when limits, cold behavior, and cost fit.

---

## 5. Multi-tenancy models

### Shared database, shared schema

Simple and efficient; strongest application-level isolation requirement.

### Shared database, schema per tenant

Improved logical separation; migration and object-count complexity.

### Database per tenant

Strong isolation; higher operational overhead.

Choose based on:

- isolation;
- scale;
- customization;
- compliance;
- operations;
- cost.

---

## 6. Connection architecture

Define:

- application pool;
- proxy/pooler;
- max connections;
- transaction pooling constraints;
- read/write routing;
- timeout;
- failover behavior.

---

## 7. Failure-domain analysis

Consider:

- process;
- host;
- storage;
- zone;
- region;
- network;
- DNS;
- identity;
- control plane;
- operator error.

---

## 8. Design checklist

- [ ] Data owner exists.
- [ ] Engine choice is justified.
- [ ] Growth is estimated.
- [ ] Transaction model is explicit.
- [ ] Schema boundaries are clear.
- [ ] Connection limits are safe.
- [ ] Backup restore is tested.
- [ ] HA failure modes are understood.
- [ ] Security is least privilege.
- [ ] Maintenance is owned.
- [ ] Migration is reversible where possible.
