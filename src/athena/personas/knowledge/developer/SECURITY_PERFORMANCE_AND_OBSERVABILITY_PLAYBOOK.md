# Developer Security, Performance, and Observability Playbook

## 1. Security review

Review:

- authentication;
- authorization;
- tenant/object isolation;
- validation;
- injection;
- XSS/CSRF;
- SSRF;
- file/path handling;
- secrets;
- sensitive data;
- dependency risk;
- logging and analytics;
- mobile local storage;
- browser/server boundaries.

Use negative tests for critical controls.

## 2. Performance workflow

```text
requirement
→ baseline
→ bottleneck
→ hypothesis
→ one change
→ remeasure
→ regression guard
```

Frontend/mobile:

- startup/render;
- interaction latency;
- bundle;
- network;
- memory;
- battery;
- cache.

Backend:

- latency percentiles;
- throughput;
- query count;
- allocation/GC;
- thread/event-loop saturation;
- queue depth;
- connection pools.

## 3. Observability

A production flow should expose:

- structured logs;
- correlation ID;
- metrics for traffic, errors, latency, saturation, and business result;
- traces across remote/async boundaries;
- frontend/mobile crash and error evidence;
- actionable alerts.

## 4. Sensitive evidence

Never log or report:

- passwords;
- tokens;
- private keys;
- full regulated identifiers;
- sensitive request bodies;
- unredacted database URLs.

## 5. Resilience

For remote dependencies, define:

- timeout;
- retry owner;
- idempotency;
- circuit/bulkhead if justified;
- degraded behavior;
- recovery;
- observability.

## 6. Production verification

After release, compare:

- error rate;
- latency;
- resource use;
- user/business success;
- logs/traces;
- client crash rate;
- database health.
