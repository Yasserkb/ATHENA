# Cloud Data, Storage, and Managed Services Playbook

## 1. Data requirements

Collect:

- data model;
- query pattern;
- consistency;
- transactions;
- volume;
- velocity;
- retention;
- durability;
- latency;
- availability;
- residency;
- backup;
- analytics.

---

## 2. Object storage

Use for:

- files;
- backups;
- archives;
- data lake;
- static content;
- large immutable objects.

Define:

- bucket/container ownership;
- encryption;
- versioning;
- lifecycle;
- replication;
- public-access block;
- access logs;
- retention;
- legal hold.

---

## 3. Block and file storage

Use block for instance-attached low-latency storage.

Use managed file systems when shared filesystem semantics are required.

Review:

- zone;
- throughput;
- IOPS;
- backup;
- expansion;
- mount identity;
- failure behavior.

---

## 4. Relational database

Use when:

- transactions;
- constraints;
- joins;
- relational integrity;
- SQL queries

are important.

Review:

- engine;
- version;
- HA;
- read replicas;
- backup;
- point-in-time recovery;
- connection limits;
- maintenance;
- storage growth;
- failover.

---

## 5. NoSQL

Choose based on access pattern.

Do not choose “NoSQL” as one generic category.

Consider:

- key-value;
- document;
- wide-column;
- graph;
- time-series.

---

## 6. Cache

Use when measured access patterns justify it.

Define:

- key;
- TTL;
- invalidation;
- eviction;
- consistency;
- failure fallback;
- warm-up;
- cost.

---

## 7. Messaging

Choose:

- queue;
- pub/sub;
- event stream;
- event bus.

Define:

- delivery;
- ordering;
- retention;
- retry;
- dead letter;
- replay;
- idempotency;
- schema.

---

## 8. Analytics

Separate operational and analytical workloads when needed.

Consider:

- warehouse;
- lake;
- lakehouse;
- ETL/ELT;
- stream processing;
- governance;
- catalog;
- lineage.

---

## 9. Provider mapping

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| Object storage | S3 | Blob Storage | Cloud Storage |
| Managed relational | RDS/Aurora | Azure SQL/PostgreSQL/MySQL | Cloud SQL/AlloyDB/Spanner |
| Key-value/document | DynamoDB/DocumentDB | Cosmos DB | Firestore/Bigtable |
| Cache | ElastiCache | Azure Managed Redis | Memorystore |
| Queue/pub-sub | SQS/SNS | Service Bus/Event Grid | Pub/Sub |
| Stream | Kinesis/MSK | Event Hubs | Pub/Sub/Dataflow |
| Warehouse | Redshift | Synapse/Fabric | BigQuery |
