# Data Performance, Scaling, and Cost Optimization Playbook

## 1. Measure first

Collect:

- input size;
- output size;
- duration;
- CPU;
- memory;
- shuffle;
- spill;
- scanned bytes;
- partition count;
- skew;
- file size;
- concurrency;
- queue time;
- cost.

---

## 2. Partition pruning

Ensure queries and jobs filter on partition-aware fields.

Verify with query plans and scanned data.

---

## 3. Join strategy

Evaluate:

- broadcast;
- shuffle;
- sort-merge;
- partition alignment;
- skew;
- filter pushdown.

---

## 4. Data skew

Detect hot keys and uneven partitions.

Options:

- salting;
- pre-aggregation;
- custom partitioning;
- split heavy keys;
- broadcast small side.

---

## 5. File sizing

Aim for engine-appropriate file sizes.

Avoid both tiny-file explosion and excessively large files.

---

## 6. Caching

Cache only when repeated access and invalidation justify it.

Avoid memory pressure and stale results.

---

## 7. Incremental processing

Prefer incremental transformations when correct and substantially cheaper.

Define:

- watermark;
- changed key;
- merge;
- deletion;
- late correction;
- rebuild.

---

## 8. Warehouse optimization

Consider:

- clustering;
- sorting;
- partition;
- materialization;
- aggregate tables;
- workload management;
- concurrency.

---

## 9. Cost drivers

Track:

- compute time;
- scanned bytes;
- storage;
- replication;
- streaming retention;
- network;
- orchestration;
- observability;
- idle clusters.

---

## 10. Optimization rule

Every optimization must preserve:

- correctness;
- recovery;
- quality;
- lineage;
- security.

---

## 11. Anti-patterns

- repartition blindly;
- cache everything;
- full reload forever;
- optimize without baseline;
- large cluster for small job;
- permanent idle cluster;
- performance test with tiny data.
