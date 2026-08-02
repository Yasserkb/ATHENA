# Batch, Streaming, CDC, and Event Processing Playbook

## 1. Selection framework

Choose based on:

- freshness;
- event rate;
- processing complexity;
- ordering;
- state;
- replay;
- cost;
- operations.

### Batch

Use when data can be processed in windows.

### Micro-batch

Use when near-real-time is sufficient and batch semantics are simpler.

### Streaming

Use when low latency or continuous event processing is required.

---

## 2. Batch design

Define:

- window;
- partition;
- source completeness;
- dependency;
- idempotency;
- output commit;
- rerun;
- late arrival;
- backfill.

---

## 3. Stream design

Define:

- event schema;
- key;
- partition;
- ordering;
- timestamp;
- watermark;
- allowed lateness;
- state;
- checkpoint;
- retry;
- poison event;
- replay.

---

## 4. Delivery semantics

### At most once

Possible loss, no duplicates.

### At least once

No intentional loss, duplicates possible.

### Exactly once

Requires coordinated source, processing state, sink behavior, and recovery.

Be explicit whether this means:

- processing exactly once;
- sink transaction exactly once;
- business effect exactly once.

---

## 5. Event-time processing

Use event time for business chronology.

Define:

- watermark;
- lateness;
- late-event correction;
- window type;
- trigger.

---

## 6. Partitioning

Choose keys that balance:

- ordering;
- locality;
- throughput;
- skew.

Hot keys can destroy scalability.

---

## 7. Schema management

Use:

- version;
- compatibility policy;
- registry/catalog;
- consumer testing;
- deprecation.

---

## 8. CDC

CDC should preserve:

- source position;
- key;
- operation;
- before/after where required;
- transaction ordering;
- delete behavior.

---

## 9. Replay

Replay requires:

- retained input;
- deterministic code;
- versioned logic;
- isolated output or overwrite policy;
- reconciliation;
- capacity.

---

## 10. Dead-letter handling

Dead-letter queues require:

- reason;
- payload protection;
- owner;
- alert;
- replay;
- retention.

They must not become permanent data graveyards.

---

## 11. Anti-patterns

- streaming without latency requirement;
- random partition key;
- no replay plan;
- no schema compatibility;
- ignoring late data;
- unbounded state;
- “exactly once” marketing claim;
- CDC used as a domain event.
