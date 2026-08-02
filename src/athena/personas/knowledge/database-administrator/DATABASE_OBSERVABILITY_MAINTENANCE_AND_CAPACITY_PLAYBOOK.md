# Database Observability, Maintenance, and Capacity Planning Playbook

## 1. Core health

Monitor:

- availability;
- connections;
- active sessions;
- transaction age;
- query latency;
- error rate;
- lock waits;
- deadlocks;
- replication lag;
- storage;
- CPU;
- memory;
- I/O.

---

## 2. Workload visibility

Track:

- top total-time queries;
- top frequency;
- slowest;
- rows;
- temporary I/O;
- cache behavior;
- plan changes.

---

## 3. PostgreSQL maintenance

Review:

- autovacuum;
- analyze;
- bloat;
- frozen transaction age;
- checkpoints;
- WAL;
- replication slots;
- long transactions.

---

## 4. MySQL maintenance

Review:

- InnoDB buffer pool;
- redo/undo;
- binary logs;
- replication;
- slow query log;
- table/index statistics;
- purge lag.

---

## 5. Oracle maintenance

Review:

- AWR/ASH;
- wait events;
- tablespaces;
- undo;
- redo/archive;
- statistics;
- RMAN;
- Data Guard.

---

## 6. SQL Server maintenance

Review:

- Query Store;
- wait stats;
- tempdb;
- transaction log;
- statistics;
- index maintenance;
- Always On;
- backups.

---

## 7. Capacity model

Forecast:

- rows;
- table bytes;
- index bytes;
- transaction logs;
- backups;
- temp space;
- connections;
- IOPS;
- maintenance window.

---

## 8. Alerts

Alert on:

- failed backup;
- low disk;
- high replication lag;
- connection exhaustion;
- blocked workload;
- deadlock surge;
- long transaction;
- recovery failure;
- corruption signal.

---

## 9. Maintenance

Use measured policies for:

- vacuum/analyze;
- statistics;
- index rebuild/reorganize;
- partition maintenance;
- log cleanup;
- backup cleanup.

Do not run expensive maintenance blindly on every object.

---

## 10. Anti-patterns

- CPU-only monitoring;
- no query statistics;
- alert without runbook;
- index rebuild by schedule regardless of need;
- autovacuum disabled globally;
- unlimited log retention;
- capacity planning after disk alert.
