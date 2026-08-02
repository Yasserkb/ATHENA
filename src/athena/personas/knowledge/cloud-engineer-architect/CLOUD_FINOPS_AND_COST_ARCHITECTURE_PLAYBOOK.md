# Cloud FinOps and Cost Architecture Playbook

## 1. Principle

Cloud cost is a shared engineering and business responsibility.

Optimize value, not only spend.

---

## 2. Allocation

Require:

- owner;
- application;
- environment;
- cost center;
- product;
- lifecycle.

Use tags/labels and account boundaries.

---

## 3. Cost model

Estimate:

- compute;
- storage;
- database;
- requests;
- data transfer;
- load balancing;
- NAT;
- observability;
- security;
- backups;
- support.

Include growth and failure capacity.

---

## 4. Unit economics

Useful measures:

- cost per customer;
- cost per transaction;
- cost per environment;
- cost per GB processed;
- cost per deployment;
- cost per model inference.

---

## 5. Budgets and forecasts

Set:

- monthly budget;
- forecast alert;
- anomaly alert;
- owner;
- escalation.

---

## 6. Optimization sequence

1. remove unused;
2. stop idle;
3. right-size;
4. tune storage and retention;
5. reduce egress;
6. improve architecture;
7. buy commitments after baseline stability.

---

## 7. Commitments

Reserved capacity/savings plans/commitments trade flexibility for discount.

Evaluate:

- baseline usage;
- term;
- scope;
- growth;
- migration risk;
- utilization;
- break-even.

---

## 8. Storage cost

Manage:

- lifecycle;
- versioning;
- snapshots;
- logs;
- backups;
- replication;
- retrieval fees;
- deletion.

---

## 9. Network cost

Track:

- internet egress;
- inter-zone;
- inter-region;
- NAT;
- private endpoints;
- CDN;
- data movement.

Network design is often a major hidden cost.

---

## 10. Observability cost

Control:

- log volume;
- cardinality;
- trace sampling;
- retention;
- indexing;
- archive.

Do not remove required evidence blindly.

---

## 11. Cost optimization guardrails

Every optimization must preserve:

- SLO;
- security;
- recovery;
- capacity;
- compliance.

---

## 12. Anti-patterns

- commitments before usage baseline;
- budgets with no owner;
- missing allocation;
- idle preview environments;
- indefinite log retention;
- cross-region traffic by accident;
- cost optimization that breaks recovery.
