# Backup, Restore, PITR, High Availability, and Disaster Recovery Playbook

## 1. Recovery requirements

Define:

- RPO;
- RTO;
- retention;
- legal requirements;
- failure domains;
- recovery location;
- ownership.

---

## 2. Backup types

Depending on engine:

- logical;
- physical/base;
- full;
- incremental;
- differential;
- snapshot;
- transaction/WAL/binlog/archive-log.

Each has different restore and consistency properties.

---

## 3. Backup controls

Require:

- encryption;
- access control;
- immutability;
- offsite/cross-region;
- monitoring;
- retention;
- deletion policy;
- checksum/integrity.

---

## 4. Restore testing

Test:

- full restore;
- point-in-time restore;
- object-level recovery where needed;
- application validation;
- credentials/keys;
- duration;
- runbook.

---

## 5. PITR

PITR requires:

- base backup;
- continuous log/archive retention;
- timeline/position;
- storage capacity;
- restore procedure;
- target validation.

---

## 6. Replication

Replication can support:

- availability;
- read scaling;
- DR.

It can also replicate:

- bad writes;
- deletes;
- corruption;
- privilege mistakes.

---

## 7. Failover

Define:

- trigger;
- health evidence;
- promotion;
- fencing;
- DNS/connection change;
- application retry;
- old-primary handling;
- data-loss estimate;
- failback.

---

## 8. DR models

- backup/restore;
- warm standby;
- hot standby;
- active/passive;
- active/active where engine/application supports it.

---

## 9. Exercises

Run:

- tabletop;
- restore;
- replica promotion;
- zone failure;
- region recovery.

Record actual RTO/RPO.

---

## 10. Anti-patterns

- backup on same host only;
- replica treated as backup;
- restore credentials unavailable;
- failover never tested;
- no fencing;
- PITR logs missing;
- RTO/RPO invented by engineering alone.
