# PostgreSQL, MySQL, Oracle, and SQL Server Operational Mapping

## 1. Purpose

This file maps common DBA capabilities across engines.

Always validate against the exact engine version and deployment model.

---

## 2. Query plans

| Capability | PostgreSQL | MySQL | Oracle | SQL Server |
|---|---|---|---|---|
| Explain | EXPLAIN | EXPLAIN | EXPLAIN PLAN | Estimated execution plan |
| Actual execution | EXPLAIN ANALYZE | EXPLAIN ANALYZE | SQL Monitor/trace | Actual execution plan |
| Query history | pg_stat_statements | Performance Schema | AWR/ASH | Query Store |

---

## 3. Replication and HA

| Capability | PostgreSQL | MySQL | Oracle | SQL Server |
|---|---|---|---|---|
| Physical replication | Streaming replication | InnoDB/GTID replication | Data Guard | Always On AG/log shipping |
| Logical replication | Logical replication | Binlog-based tools | GoldenGate | CDC/replication |
| HA orchestration | Patroni/repmgr/managed | InnoDB Cluster/managed | Data Guard Broker/RAC | WSFC/Always On |

---

## 4. Backup and PITR

| Capability | PostgreSQL | MySQL | Oracle | SQL Server |
|---|---|---|---|---|
| Logical | pg_dump | mysqldump/mysqlpump | Data Pump | BACPAC/export tools |
| Physical | pg_basebackup/tools | physical backup tools | RMAN | Full/diff backup |
| Log recovery | WAL archive | binlog | archive redo | transaction log |

---

## 5. Maintenance

| Area | PostgreSQL | MySQL | Oracle | SQL Server |
|---|---|---|---|---|
| Statistics | ANALYZE | ANALYZE TABLE | DBMS_STATS | UPDATE STATISTICS |
| Space/version cleanup | VACUUM | purge/optimize selectively | segment/undo management | index/ghost cleanup |
| Top query tooling | pg_stat_statements | Performance Schema | AWR/ASH | Query Store/DMVs |

---

## 6. Online changes

Engine support differs by:

- version;
- edition;
- storage engine;
- managed provider.

Never use a generic online-DDL claim without verification.

---

## 7. Connection pooling

- PostgreSQL commonly uses PgBouncer or provider proxies.
- MySQL commonly uses ProxySQL/provider proxies.
- Oracle commonly uses application pools, DRCP, or connection managers.
- SQL Server commonly relies on driver/application pools and managed gateways.

Pooling mode can change transaction/session semantics.
