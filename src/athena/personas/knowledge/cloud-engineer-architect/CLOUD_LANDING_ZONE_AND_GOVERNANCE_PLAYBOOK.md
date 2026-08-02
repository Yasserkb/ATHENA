# Cloud Landing Zone and Governance Playbook

## 1. Purpose

A landing zone provides the governed foundation for cloud adoption.

It includes:

- organization hierarchy;
- accounts/subscriptions/projects;
- identity;
- networking;
- logging;
- security;
- policy;
- budgets;
- automation;
- shared services.

---

## 2. Organization structure

Design based on:

- environment;
- business unit;
- workload criticality;
- compliance;
- ownership;
- billing;
- lifecycle.

Avoid mirroring the organization chart too literally if it creates technical coupling.

---

## 3. Core accounts or subscriptions

Typical capabilities:

- management;
- audit;
- security;
- central logging;
- network;
- shared services;
- identity;
- development;
- testing;
- production.

Exact structure must remain proportional.

---

## 4. Identity federation

Use enterprise identity as the human access source.

Define:

- groups;
- roles;
- MFA;
- session duration;
- privileged access;
- access reviews;
- break-glass;
- offboarding.

---

## 5. Guardrails

Use preventive and detective controls.

### Preventive

- policy;
- organization restrictions;
- admission rules;
- IAM boundaries;
- allowed regions;
- encryption requirements.

### Detective

- posture checks;
- audit;
- configuration monitoring;
- drift;
- security findings;
- budget alerts.

---

## 6. Central logging

Centralize:

- administrative audit;
- authentication;
- network flow;
- security findings;
- resource configuration;
- critical workload logs.

Protect logs from workload administrators where separation is required.

---

## 7. Network foundation

Define:

- hub-and-spoke or transit;
- shared network;
- routing;
- DNS;
- inspection;
- internet ingress;
- internet egress;
- private connectivity;
- hybrid connectivity.

---

## 8. Shared services

Examples:

- DNS;
- certificate authority;
- artifact registry;
- secret management;
- observability;
- identity integration;
- bastion or zero-trust access;
- backup.

Avoid centralizing capabilities that create an unnecessary single bottleneck.

---

## 9. Resource standards

Require:

- naming;
- tags/labels;
- owner;
- environment;
- data classification;
- cost center;
- lifecycle;
- repository reference.

---

## 10. Account vending

New accounts/subscriptions/projects should be created through automation.

The process should apply:

- baseline policy;
- logging;
- network;
- IAM;
- budgets;
- security;
- ownership;
- inventory.

---

## 11. Exceptions

Every exception needs:

- business reason;
- risk;
- owner;
- compensating control;
- expiry;
- review.

---

## 12. Anti-patterns

- one shared account for all workloads;
- manual account creation;
- local users instead of federation;
- no central audit;
- guardrails with no exception process;
- production administrators owning audit logs;
- unmanaged regions;
- shared static credentials.
