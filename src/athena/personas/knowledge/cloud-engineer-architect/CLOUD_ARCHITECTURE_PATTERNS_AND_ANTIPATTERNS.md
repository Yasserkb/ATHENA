# Cloud Architecture Patterns and Anti-Patterns

## 1. Landing Zone

Creates governed cloud foundations before workload scale.

---

## 2. Hub-and-Spoke Network

Centralizes shared connectivity and inspection while segmenting workloads.

---

## 3. Shared Services

Centralizes capabilities such as DNS, identity integration, observability, or registries.

Avoid creating a fragile central bottleneck.

---

## 4. Multi-Account / Multi-Subscription

Uses administrative boundaries for isolation, ownership, quotas, and billing.

---

## 5. Private Endpoint

Connects to managed services without public internet exposure.

---

## 6. Workload Identity

Uses platform identity instead of static credentials.

---

## 7. Cell Architecture

Partitions workloads and customers into independent cells to reduce blast radius.

---

## 8. Bulkhead

Separates capacity and failure domains.

---

## 9. Queue-Based Load Leveling

Buffers bursty demand and decouples processing.

---

## 10. Competing Consumers

Scales parallel processing from a queue.

Requires idempotency and ordering analysis.

---

## 11. Retry with Backoff

Handles transient failure with bounded attempts and jitter.

---

## 12. Circuit Breaker

Stops calls to an unhealthy dependency.

---

## 13. Cache-Aside

Application loads data into cache on miss.

Requires invalidation and fallback.

---

## 14. Materialized View

Builds read-optimized projections.

---

## 15. Transactional Outbox

Coordinates database state and event publication.

---

## 16. Event Sourcing

Stores state changes as events.

Use only when audit/history/reconstruction benefits justify complexity.

---

## 17. Strangler Migration

Moves capability incrementally.

---

## 18. Anti-Corruption Layer

Protects a domain from external or legacy models.

---

## 19. Active/Passive

Keeps one environment ready to take over.

---

## 20. Active/Active

Serves traffic from multiple locations.

Requires data and conflict strategy.

---

## 21. Anti-pattern: Cloud Washing

Moving VMs without changing operations but claiming cloud-native benefits.

---

## 22. Anti-pattern: Lift-and-Shift Forever

Rehosting is sometimes valid, but temporary compromises must have optimization ownership.

---

## 23. Anti-pattern: Public by Default

Resources receive public endpoints without explicit requirement.

---

## 24. Anti-pattern: One Giant Account

Destroys isolation, ownership, quotas, and billing clarity.

---

## 25. Anti-pattern: Static Cloud Keys

Long-lived credentials increase compromise risk and operational burden.

---

## 26. Anti-pattern: Multi-Cloud by PowerPoint

Multi-cloud is declared without deployable, operable, and tested equivalence.

---

## 27. Anti-pattern: Kubernetes for Everything

Cluster complexity is introduced where a managed platform would suffice.

---

## 28. Anti-pattern: Managed-Service Blindness

A managed service is selected without quota, networking, lock-in, or failure analysis.

---

## 29. Anti-pattern: Backup Without Restore

Backup success is mistaken for recovery capability.

---

## 30. Anti-pattern: Cost Afterthought

Architecture is deployed before ownership, allocation, and budgets exist.

---

## 31. Pattern documentation template

```markdown
## Pattern

### Problem
### Workload evidence
### Forces
### Selected pattern
### Provider-neutral design
### Provider implementation
### Security
### Reliability
### Operations
### Cost
### Lock-in and exit
### Validation
### Revisit criteria
```
