# Cloud, IAM, Network, Container, and Kubernetes Security Playbook

## 1. Identity

Review:

- federated human access;
- MFA;
- workload identity;
- CI federation;
- role scope;
- trust policies;
- privilege escalation paths;
- emergency access;
- inactive identities;
- access reviews.

---

## 2. Cloud organization

Review:

- account/subscription/project separation;
- production isolation;
- central audit;
- policy guardrails;
- allowed regions;
- security ownership;
- budgets and anomaly alerts.

---

## 3. Network exposure

Identify:

- public IPs;
- load balancers;
- ingress;
- databases;
- management ports;
- egress;
- private endpoints;
- DNS;
- peering/transit;
- firewall rules.

Public access requires a documented reason and compensating controls.

---

## 4. Storage and data services

Review:

- public-access blocks;
- encryption;
- key access;
- backups;
- versioning;
- retention;
- replication;
- logging;
- database authentication;
- private connectivity.

---

## 5. Containers

Review:

- trusted minimal base;
- non-root;
- capabilities;
- seccomp;
- read-only filesystem;
- secrets;
- image signing;
- SBOM;
- vulnerability status;
- exposed ports;
- health behavior.

---

## 6. Kubernetes

Review:

- RBAC;
- service accounts;
- pod security;
- admission policy;
- network policy;
- namespaces;
- secrets;
- ingress;
- egress;
- host access;
- privileged workloads;
- image verification;
- audit;
- etcd/control-plane protection;
- operator permissions.

---

## 7. Zero-trust reasoning

Authorize based on:

- verified identity;
- device/workload context;
- explicit policy;
- least privilege;
- continuous evidence.

Do not treat network location alone as trust.

---

## 8. Availability attacks

Review:

- autoscaling limits;
- quotas;
- connection pools;
- queue growth;
- expensive endpoints;
- storage exhaustion;
- log flooding;
- regional dependencies;
- recovery.

---

## 9. Verification

Use:

- IaC scanning;
- cloud configuration inventory;
- IAM graph analysis;
- policy tests;
- network reachability analysis;
- container manifest review;
- cluster posture checks;
- runtime audit.
