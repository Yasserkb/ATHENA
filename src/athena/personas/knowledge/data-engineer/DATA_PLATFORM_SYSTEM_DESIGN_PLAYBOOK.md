# Data Platform System Design Playbook

## 1. Purpose

Use this playbook for:

- enterprise data platforms;
- analytics platforms;
- lakehouses;
- warehouses;
- streaming platforms;
- operational data integration;
- migration;
- data products;
- ML feature platforms.

---

## 2. Design template

```markdown
# Data Platform Design: <Name>

## 1. Executive summary
## 2. Business objective
## 3. Consumers and use cases
## 4. Goals and non-goals
## 5. Sources and ownership
## 6. Data classification
## 7. Volume, velocity, variety
## 8. Freshness and latency
## 9. Quality and SLOs
## 10. Current architecture
## 11. Target architecture
## 12. Ingestion
## 13. Processing
## 14. Storage zones
## 15. Data modeling
## 16. Serving interfaces
## 17. Orchestration
## 18. Metadata, catalog, and lineage
## 19. Security and governance
## 20. Reliability and recovery
## 21. Observability
## 22. Performance and scaling
## 23. Cost model
## 24. Migration and backfill
## 25. Testing
## 26. Rollout and rollback
## 27. Alternatives and trade-offs
## 28. Risks and mitigations
## 29. Open decisions
## 30. Definition of done
```

---

## 3. Architecture layers

Typical capabilities:

```text
sources
→ ingestion
→ transport
→ raw/landing
→ processing
→ curated/conformed
→ serving
→ consumers
```

Cross-cutting:

- orchestration;
- metadata;
- lineage;
- quality;
- security;
- observability;
- governance;
- cost.

---

## 4. Architecture styles

### Warehouse-first

Good for:

- structured analytics;
- SQL users;
- governed reporting;
- managed operations.

### Data lake

Good for:

- diverse data;
- raw retention;
- large-scale files;
- open formats.

### Lakehouse

Combines lake storage with transactional table capabilities.

Use when the organization can operate table formats, catalogs, and compute engines coherently.

### Data mesh

Use as an organizational and ownership model when domain ownership and platform enablement are mature.

Do not use it as a synonym for distributed files.

### Lambda architecture

Batch plus separate speed layer.

Often complex; prefer a simpler unified model where possible.

### Kappa architecture

Stream-first processing and replay.

Use only when event log and streaming requirements justify it.

---

## 5. Storage-zone design

Possible zones:

- landing;
- raw;
- validated;
- standardized;
- conformed;
- curated;
- serving;
- quarantine.

Each zone must define:

- contract;
- owner;
- mutability;
- retention;
- access;
- quality;
- format.

---

## 6. Serving patterns

- warehouse tables;
- semantic layer;
- data marts;
- APIs;
- extracts;
- search indexes;
- feature store;
- reverse ETL.

Define consumer SLOs.

---

## 7. Reliability model

For each stage, define:

- checkpoint;
- retry;
- replay;
- duplicate handling;
- data loss detection;
- reconciliation;
- recovery time;
- storage durability.

---

## 8. Review checklist

- [ ] Source of truth is known.
- [ ] Dataset owners exist.
- [ ] Contracts are versioned.
- [ ] Grain is explicit.
- [ ] Late/duplicate data is handled.
- [ ] Backfills are supported.
- [ ] Quality is measurable.
- [ ] Lineage exists.
- [ ] Sensitive data is controlled.
- [ ] Recovery is tested.
- [ ] Cost drivers are known.
