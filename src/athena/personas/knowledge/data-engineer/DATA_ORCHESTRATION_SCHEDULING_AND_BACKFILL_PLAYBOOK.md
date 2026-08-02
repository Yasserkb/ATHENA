# Data Orchestration, Scheduling, and Backfill Playbook

## 1. Orchestration responsibilities

Orchestration manages:

- dependency;
- schedule;
- retries;
- timeout;
- parameters;
- backfill;
- observability;
- ownership;
- alerting.

Business transformation logic should not be hidden in orchestration definitions.

---

## 2. DAG design

A task should have:

- clear input;
- clear output;
- idempotency;
- bounded runtime;
- retry policy;
- owner;
- diagnostics.

Avoid one giant task and thousands of tiny tasks without reason.

---

## 3. Scheduling

Define:

- timezone;
- business date;
- calendar;
- source readiness;
- SLA;
- catch-up;
- missed runs.

---

## 4. Dependencies

Prefer data-aware readiness where possible rather than arbitrary clock delays.

---

## 5. Retries

Retry only transient failures.

Define:

- attempts;
- delay;
- backoff;
- deadline;
- cleanup.

Do not retry deterministic data-quality failures indefinitely.

---

## 6. Backfill

A backfill plan must define:

- date/key range;
- logic version;
- source availability;
- target isolation;
- capacity;
- throttling;
- validation;
- reconciliation;
- consumer impact;
- rollback.

---

## 7. Partial failure

Define:

- failed partition;
- successful partitions;
- commit semantics;
- resume point;
- duplicate prevention.

---

## 8. Dynamic pipelines

Dynamic tasks require bounds and observability.

Unbounded fan-out can overload scheduler and infrastructure.

---

## 9. Tool selection

Evaluate orchestrators such as Airflow, Dagster, Prefect, managed schedulers, or native workflow systems based on:

- workload;
- language;
- scale;
- backfill;
- assets/data awareness;
- operations;
- ecosystem.

---

## 10. Anti-patterns

- sleep-based dependency;
- orchestration containing all transformation code;
- no backfill capability;
- unbounded retries;
- hidden business date;
- rerun duplicates output;
- no ownership.
