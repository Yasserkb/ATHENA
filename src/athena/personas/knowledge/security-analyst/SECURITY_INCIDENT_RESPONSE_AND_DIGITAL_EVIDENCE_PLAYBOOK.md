# Security Incident Response and Digital Evidence Playbook

## 1. Priorities

1. protect people and data;
2. establish incident command;
3. contain harmful activity;
4. preserve evidence;
5. restore safe service;
6. communicate;
7. determine scope and cause;
8. improve controls.

---

## 2. Incident roles

- incident commander;
- security lead;
- operations lead;
- application/cloud specialist;
- communications lead;
- evidence scribe;
- legal/privacy contact where required.

---

## 3. Initial triage

Determine:

- what happened;
- when;
- affected assets;
- active threat;
- compromised identities;
- data impact;
- operational impact;
- scope uncertainty;
- required escalation.

---

## 4. Evidence preservation

Preserve:

- timestamps;
- logs;
- cloud audit;
- identity activity;
- affected artifacts;
- configuration;
- network evidence;
- volatile state where authorized;
- chain of custody where required.

Avoid destructive troubleshooting before evidence capture.

---

## 5. Containment

Prefer reversible actions:

- revoke/rotate credential;
- isolate workload;
- block route;
- disable account;
- pause pipeline;
- remove public exposure;
- quarantine artifact;
- increase logging safely.

---

## 6. Eradication and recovery

Address:

- entry point;
- persistence;
- affected credentials;
- vulnerable component;
- malicious artifact;
- configuration;
- data integrity;
- recovery validation.

---

## 7. Communication

Report:

- confirmed impact;
- current scope;
- actions;
- user guidance;
- next update.

Do not present speculation as fact.

---

## 8. Post-incident review

Document:

- timeline;
- root causes;
- contributing conditions;
- detection gaps;
- response gaps;
- recovery gaps;
- security debt;
- actions;
- owners;
- deadlines.

---

## 9. Lessons for Athena

Athena can support incident review by mapping:

- vulnerable code;
- callers;
- configuration;
- deployment;
- tests;
- ownership.

It must not modify or contaminate evidence repositories during analysis.
