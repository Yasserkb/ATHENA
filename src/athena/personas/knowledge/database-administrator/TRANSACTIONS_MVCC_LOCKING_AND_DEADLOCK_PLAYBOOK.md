# Transactions, MVCC, Locking, and Deadlock Playbook

## 1. Transaction design

Define:

- business operation;
- isolation;
- read set;
- write set;
- duration;
- retry;
- external calls;
- failure behavior.

---

## 2. Isolation levels

Understand engine-specific behavior for:

- read uncommitted;
- read committed;
- repeatable read;
- snapshot;
- serializable.

Do not select serializable or weaker isolation without workload analysis.

---

## 3. MVCC

MVCC can reduce reader/writer blocking but creates:

- version cleanup;
- vacuum/undo pressure;
- long-transaction impact;
- storage overhead.

---

## 4. Lock investigation

Capture:

- blocked session;
- blocker;
- lock type;
- object/key;
- transaction age;
- statement;
- application name;
- user.

---

## 5. Deadlocks

A deadlock requires a cycle.

Prevent through:

- consistent resource ordering;
- smaller transactions;
- proper indexes;
- fewer touched rows;
- retry at the correct application layer.

---

## 6. Long transactions

Long transactions may cause:

- lock retention;
- version bloat;
- vacuum delay;
- replication lag;
- log growth;
- recovery complexity.

---

## 7. Optimistic concurrency

Use version/timestamp checks when conflicts are uncommon and application retry is acceptable.

---

## 8. Pessimistic locking

Use when conflicts are expected and exclusive access is necessary.

Keep scope short.

---

## 9. Advisory/application locks

Use only with:

- clear key;
- ownership;
- timeout;
- cleanup;
- multi-instance semantics.

---

## 10. Anti-patterns

- remote API inside long transaction;
- retry whole request blindly after deadlock;
- raising lock timeout indefinitely;
- no transaction timeout;
- batch update without commits/checkpoints;
- hidden autocommit assumptions.
