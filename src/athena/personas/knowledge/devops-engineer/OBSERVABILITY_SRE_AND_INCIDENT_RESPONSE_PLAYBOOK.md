# Observability, SRE, and Incident Response Playbook

## 1. Service level model

Define:

- SLI;
- SLO;
- error budget.

Examples:

- availability;
- latency;
- correctness;
- freshness;
- durability.

---

## 2. Metrics

Use the four golden signals:

- latency;
- traffic;
- errors;
- saturation.

Add business signals.

Metrics need:

- owner;
- unit;
- labels;
- cardinality control;
- retention.

---

## 3. Logs

Logs must be:

- structured;
- leveled;
- correlated;
- safe;
- actionable.

Avoid high-cardinality or sensitive fields.

---

## 4. Tracing

Trace critical cross-service flows.

Propagate context through:

- HTTP;
- messaging;
- async executors;
- scheduled jobs.

---

## 5. Dashboards

A dashboard should answer a specific operational question.

Recommended views:

- service overview;
- dependency health;
- release comparison;
- capacity;
- business flow;
- SLO.

---

## 6. Alerting

Alerts need:

- user impact;
- urgency;
- owner;
- runbook;
- deduplication;
- suppression;
- recovery notification.

Prefer multi-window burn-rate alerts for SLOs.

---

## 7. Capacity

Track:

- CPU;
- memory;
- storage;
- connections;
- queue;
- thread pools;
- rate limits;
- quotas.

Maintain headroom based on failure and growth.

---

## 8. Incident roles

- incident commander;
- operations lead;
- communications lead;
- subject-matter expert;
- scribe.

Small incidents may combine roles, but ownership must remain clear.

---

## 9. Incident lifecycle

```text
detect
→ acknowledge
→ assess
→ contain
→ mitigate
→ recover
→ verify
→ review
```

---

## 10. Severity

Define severity through:

- user impact;
- data/security impact;
- scope;
- duration;
- workaround.

---

## 11. Communication

Provide regular updates with:

- impact;
- current status;
- actions;
- next update.

Do not speculate publicly.

---

## 12. Runbooks

A runbook must include:

- symptom;
- checks;
- safe mitigation;
- rollback;
- escalation;
- validation;
- evidence to collect.

---

## 13. Post-incident review

Use blameless analysis.

Document:

- timeline;
- root causes;
- contributing factors;
- detection gaps;
- response gaps;
- actions;
- owners;
- deadlines.

Action items should improve systems, not merely tell people to be more careful.

---

## 14. Backup and restore

Measure:

- backup success;
- age;
- size;
- restore success;
- restore duration.

Test restore regularly.

---

## 15. Chaos and resilience testing

Use controlled experiments for:

- dependency loss;
- pod/node failure;
- latency;
- DNS;
- queue backlog;
- certificate expiry;
- resource exhaustion.

Start in safe environments.

---

## 16. Anti-patterns

- alert on every error;
- dashboard without owner;
- logs only;
- metrics without units;
- untested runbook;
- backup without restore test;
- postmortem without actions;
- blaming operator;
- hiding incidents.
