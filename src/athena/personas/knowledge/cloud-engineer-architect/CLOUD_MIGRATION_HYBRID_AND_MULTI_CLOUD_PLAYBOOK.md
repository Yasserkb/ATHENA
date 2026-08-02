# Cloud Migration, Hybrid, and Multi-Cloud Playbook

## 1. Discovery

Inventory:

- applications;
- dependencies;
- data;
- traffic;
- identity;
- network;
- licenses;
- operations;
- compliance;
- cost;
- lifecycle.

---

## 2. Migration classification

Use:

- rehost;
- replatform;
- refactor;
- repurchase;
- retain;
- retire;
- relocate.

Choose per workload, not for the entire portfolio.

---

## 3. Dependency mapping

Identify:

- synchronous calls;
- asynchronous calls;
- shared databases;
- file transfers;
- DNS;
- identity;
- certificates;
- batch windows;
- external partners.

---

## 4. Wave planning

Group workloads by:

- dependency;
- risk;
- business owner;
- data;
- readiness;
- rollback;
- learning value.

Start with representative low-risk workloads.

---

## 5. Foundation prerequisites

Before migration:

- landing zone;
- IAM;
- network;
- logging;
- security;
- backups;
- operations;
- cost controls;
- CI/CD.

---

## 6. Data migration

Define:

- volume;
- transfer mechanism;
- encryption;
- change capture;
- validation;
- freeze;
- cutover;
- rollback;
- reconciliation.

---

## 7. Cutover

Specify:

- entry criteria;
- change window;
- traffic shift;
- DNS TTL;
- data synchronization;
- smoke tests;
- observation;
- rollback trigger.

---

## 8. Hybrid

Define:

- connectivity;
- routing;
- DNS;
- identity;
- monitoring;
- latency;
- failure;
- security;
- support.

Avoid creating permanent hybrid complexity without ownership.

---

## 9. Multi-cloud

Define what is portable:

- source;
- container;
- API;
- data;
- identity;
- observability;
- IaC.

Perfect portability is expensive and often unrealistic.

---

## 10. Decommissioning

After migration:

- verify usage;
- retain evidence;
- revoke access;
- archive data;
- delete resources;
- stop licenses;
- update inventory;
- remove DNS and routes.

---

## 11. Migration exit criteria

- functional validation;
- performance validation;
- security validation;
- backup/restore;
- monitoring;
- owner acceptance;
- rollback period complete;
- cost reviewed;
- legacy dependency removed.
