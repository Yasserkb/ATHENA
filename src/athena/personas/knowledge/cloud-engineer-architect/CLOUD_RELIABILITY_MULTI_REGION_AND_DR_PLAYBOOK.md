# Cloud Reliability, Multi-Region, Backup, and DR Playbook

## 1. Reliability requirements

Define:

- availability target;
- SLO;
- RTO;
- RPO;
- critical dependencies;
- failure domains;
- degraded mode;
- operational capability.

---

## 2. Availability patterns

### Single zone

Acceptable for:

- development;
- disposable;
- low-criticality workloads.

### Multi-zone

Common production baseline where supported.

### Multi-region

Use only for requirements that justify added complexity.

---

## 3. Multi-region models

### Backup and restore

Lowest cost, highest recovery time.

### Pilot light

Critical foundation remains ready.

### Warm standby

Reduced-capacity secondary environment.

### Active/passive

Secondary can assume traffic.

### Active/active

Both regions serve traffic.

Requires the greatest application and data complexity.

---

## 4. Data replication

Understand:

- synchronous/asynchronous;
- lag;
- conflict;
- failover;
- split brain;
- write ownership;
- data-loss window.

---

## 5. Backup

Define:

- resource scope;
- schedule;
- retention;
- immutability;
- encryption;
- cross-account;
- cross-region;
- monitoring.

---

## 6. Restore

Test:

- data;
- infrastructure;
- identity;
- DNS;
- secrets;
- application order;
- external dependencies.

Measure restore duration.

---

## 7. Dependency alignment

The system availability cannot exceed critical dependencies without a degraded strategy.

Review:

- identity;
- DNS;
- certificate;
- network;
- registry;
- database;
- messaging;
- external API.

---

## 8. Capacity during failure

Ensure remaining zones/regions can carry required load.

---

## 9. DR exercises

Run:

- tabletop;
- component restore;
- regional simulation;
- full recovery where justified.

Record actual RTO/RPO.

---

## 10. Anti-patterns

- multi-region database without conflict strategy;
- backup in same failure domain only;
- DNS failover never tested;
- active/active with hidden single-region dependency;
- DR documents without owner;
- RTO/RPO chosen without business input.
