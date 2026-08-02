# SQL Query Tuning and Execution Plan Playbook

## 1. Tuning workflow

```text
identify slow workload
→ capture query and parameters
→ measure frequency and impact
→ inspect actual plan
→ identify bottleneck
→ change one thing
→ remeasure
→ protect with regression evidence
```

---

## 2. Evidence

Collect:

- normalized query;
- parameter values/distribution;
- duration;
- rows;
- buffers/I/O;
- CPU;
- waits;
- plan;
- frequency;
- concurrency;
- cache state.

---

## 3. Plan analysis

Review:

- estimated versus actual rows;
- scan type;
- join order;
- join algorithm;
- sort;
- aggregate;
- filter placement;
- partition pruning;
- spills;
- parallelism;
- memory grant;
- loops.

Large estimate errors often indicate statistics or correlation problems.

---

## 4. Sargability

Write predicates that can use indexes.

Avoid unnecessary functions or casts on indexed columns when equivalent searchable forms exist.

---

## 5. Indexing

Possible indexes:

- B-tree;
- hash where supported/useful;
- GIN/GiST;
- bitmap;
- full-text;
- spatial;
- partial/filtered;
- expression/function;
- covering/include.

Use engine-specific evidence.

---

## 6. Join tuning

Check:

- keys;
- data types;
- indexes;
- row estimates;
- skew;
- duplicate multiplication;
- filter timing.

---

## 7. Pagination

Offset pagination degrades at large offsets.

Consider keyset/seek pagination for stable ordered access.

---

## 8. ORM-generated SQL

Inspect actual SQL.

Watch:

- N+1;
- unnecessary columns;
- eager joins;
- duplicate selects;
- unbounded collections;
- incorrect pagination;
- implicit casts.

---

## 9. Parameter-sensitive plans

Some engines may reuse plans poorly across parameter distributions.

Use engine-specific mechanisms only after confirming the issue.

---

## 10. Anti-patterns

- add index before plan analysis;
- optimize one query while harming writes;
- compare plans with different cache conditions unknowingly;
- rely on average duration only;
- force hints permanently without revisit criteria;
- ignore parameter distribution.
