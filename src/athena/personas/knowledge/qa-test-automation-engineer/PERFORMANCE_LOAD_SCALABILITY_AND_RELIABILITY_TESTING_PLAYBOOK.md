# Performance, Load, Scalability, and Reliability Testing Playbook

## 1. Requirements first

Define:

- workload;
- concurrency;
- request rate;
- data size;
- latency target;
- throughput;
- error threshold;
- duration;
- growth;
- resource limits.

---

## 2. Test types

### Baseline

Single-user or low-load behavior.

### Load

Expected load.

### Stress

Beyond expected capacity.

### Spike

Sudden increase.

### Soak

Long duration.

### Capacity

Maximum supported within SLO.

### Scalability

Behavior as resources or instances increase.

### Failover

Performance during component loss.

---

## 3. Workload model

Base on:

- production analytics;
- expected traffic;
- business flow;
- think time;
- arrival rate;
- read/write mix;
- data distribution;
- authentication.

---

## 4. Environment

A meaningful environment should match relevant:

- topology;
- instance size;
- database;
- network;
- data volume;
- configuration.

State limitations explicitly.

---

## 5. Metrics

Collect:

- latency percentiles;
- throughput;
- error;
- CPU;
- memory;
- GC;
- threads;
- connections;
- queue;
- database;
- network;
- saturation.

Average latency is insufficient.

---

## 6. Analysis

Correlate:

```text
load
→ latency
→ errors
→ saturation
→ bottleneck
```

---

## 7. Reliability tests

Test:

- timeout;
- dependency latency;
- dependency outage;
- retry;
- circuit breaker;
- queue backlog;
- node loss;
- resource exhaustion;
- recovery.

---

## 8. Test hygiene

Use:

- warm-up;
- controlled data;
- repeatability;
- versioned script;
- result archive;
- baseline comparison.

---

## 9. Anti-patterns

- unrealistic zero-think-time load;
- testing only average;
- load generator bottleneck;
- tiny database;
- no warm-up;
- no server metrics;
- performance claim from one run;
- production stress without controls.
