# Detection Engineering, SIEM, Logging, and Threat Hunting Playbook

## 1. Detection objective

A detection must identify a meaningful adversary or misuse behavior with acceptable signal quality and an owned response.

---

## 2. Detection design

Document:

- threat or abuse case;
- asset;
- required telemetry;
- analytic logic;
- expected false positives;
- severity;
- triage;
- containment;
- owner;
- validation.

---

## 3. Telemetry sources

Consider:

- identity provider;
- cloud audit;
- application audit;
- API gateway;
- WAF;
- endpoint;
- DNS;
- network flow;
- Kubernetes audit;
- container runtime;
- CI/CD;
- repository;
- secret manager;
- database audit;
- data platform;
- operating system.

---

## 4. Logging quality

Logs need:

- timestamp;
- actor;
- target;
- action;
- result;
- source;
- correlation;
- safe context;
- integrity;
- retention.

Never log secrets to improve detection.

---

## 5. ATT&CK mapping

Use MITRE ATT&CK to:

- describe adversary behavior;
- identify telemetry gaps;
- organize detection coverage;
- support threat hunting.

ATT&CK mapping does not prove detection effectiveness.

---

## 6. Detection validation

Validate through:

- controlled simulations;
- known test events;
- replayed sanitized logs;
- unit tests for analytics;
- expected alert and case creation;
- triage runbook execution.

---

## 7. Threat hunting

A hunt starts from a hypothesis.

Example structure:

```text
Hypothesis
→ required data
→ query/analysis
→ findings
→ follow-up
→ detection improvement
```

---

## 8. Detection gaps

Classify:

- no telemetry;
- incomplete telemetry;
- poor identity context;
- excessive noise;
- missing correlation;
- retention too short;
- no response owner.

---

## 9. Anti-patterns

- collect everything without purpose;
- alert on every error;
- ATT&CK heatmap without validation;
- high-cardinality sensitive labels;
- no triage procedure;
- detection with no owner;
- suppress noisy rule forever.
