# Database Automation, Change Management, and Incident Response Playbook

## 1. Automation scope

Automate:

- backup;
- restore verification;
- health checks;
- maintenance;
- capacity reports;
- migration validation;
- replication checks;
- privilege review;
- failover exercises.

---

## 2. Safety controls

Automation requires:

- environment allowlist;
- explicit target;
- dry run;
- row/object estimate;
- timeout;
- concurrency bound;
- audit;
- stop condition;
- post-validation.

---

## 3. Change management

A production database change should include:

- ticket/record;
- owner;
- risk;
- prerequisites;
- script;
- peer review;
- test evidence;
- window;
- communication;
- rollback;
- validation.

---

## 4. Incident priorities

1. protect data;
2. stop harmful writes if necessary;
3. restore service;
4. preserve evidence;
5. communicate;
6. recover;
7. analyze.

---

## 5. Common incidents

- connection exhaustion;
- long-running query;
- lock chain;
- deadlock surge;
- replication lag;
- disk full;
- failed backup;
- corruption signal;
- bad migration;
- credential compromise;
- failover failure.

---

## 6. Incident evidence

Capture:

- timeline;
- topology;
- sessions;
- queries;
- locks;
- waits;
- resource metrics;
- logs;
- recent changes;
- replication;
- storage.

---

## 7. Safe mitigation

Prefer reversible controls:

- cancel query;
- terminate blocker with approval;
- throttle workload;
- disable job;
- redirect read traffic;
- scale capacity;
- rollback application;
- pause migration.

---

## 8. Post-incident review

Identify:

- trigger;
- root causes;
- contributing factors;
- detection gap;
- response gap;
- recovery gap;
- actions;
- owners.

---

## 9. Anti-patterns

- kill sessions randomly;
- restart database before evidence;
- disable durability;
- delete logs;
- run unreviewed repair;
- hide incident;
- no follow-up action.
