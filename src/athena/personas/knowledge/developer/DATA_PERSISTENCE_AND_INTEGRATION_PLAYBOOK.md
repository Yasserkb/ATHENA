# Developer Data, Persistence, and Integration Playbook

## 1. Data model

Define:

- identity;
- business key;
- ownership;
- lifecycle;
- invariants;
- relationships;
- retention;
- access patterns;
- indexes;
- audit.

## 2. Relational persistence

Review:

- constraints;
- transactions;
- migrations;
- N+1;
- pagination;
- locking;
- optimistic versioning;
- query plans;
- connection pools.

## 3. Document persistence

Review:

- embed/reference;
- document growth;
- atomic update;
- schema validation;
- indexes;
- query limits;
- aggregation;
- migration.

## 4. Migrations

Use expand-contract when clients or deployments overlap.

Define:

- precheck;
- DDL/data change;
- lock/rewrite risk;
- backfill;
- compatibility;
- validation;
- rollback/forward fix.

## 5. API integration

Define:

- contract;
- auth;
- timeout;
- retry;
- idempotency;
- rate limit;
- payload limit;
- error mapping;
- correlation;
- test strategy.

## 6. File/SFTP/object flows

Define:

- naming;
- path;
- encoding;
- atomic publish;
- duplicate;
- checksum;
- permission;
- cleanup;
- retry;
- remote failure;
- audit.

## 7. Events

Differentiate:

- domain event;
- integration event;
- CDC record;
- notification.

Define schema, compatibility, key, ordering, delivery, replay, and ownership.
