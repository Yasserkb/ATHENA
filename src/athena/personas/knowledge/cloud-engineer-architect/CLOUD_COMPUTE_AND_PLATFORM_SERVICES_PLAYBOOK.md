# Cloud Compute and Platform Services Playbook

## 1. Selection criteria

Evaluate:

- runtime;
- execution duration;
- traffic shape;
- startup latency;
- state;
- portability;
- network;
- security;
- operations;
- scaling;
- cost;
- team capability.

---

## 2. Virtual machines

Choose VMs for:

- legacy;
- OS-specific;
- specialized drivers;
- licensing;
- host-level control.

Requirements:

- image pipeline;
- patching;
- autoscaling;
- backup;
- monitoring;
- identity;
- immutable replacement where possible.

---

## 3. Managed containers

Good when container packaging is desired but cluster operations are not.

Evaluate:

- task limits;
- networking;
- scaling;
- storage;
- startup;
- observability;
- pricing.

---

## 4. Kubernetes

Use when platform-level benefits justify:

- control-plane complexity;
- upgrades;
- networking;
- policy;
- observability;
- workload standards.

Decide between:

- managed control plane;
- autopilot/serverless Kubernetes;
- standard managed cluster.

---

## 5. Serverless functions

Good for:

- events;
- short tasks;
- burst;
- glue logic.

Review:

- timeout;
- concurrency;
- cold start;
- package size;
- networking;
- state;
- retries;
- idempotency;
- cost at scale.

---

## 6. Managed application platforms

Useful for web/API services with standard runtime needs.

Trade off:

- speed and operations;
- platform constraints and portability.

---

## 7. Batch

Use managed batch or scheduled container platforms for:

- queued work;
- resource-specific jobs;
- large parallel computation.

Define:

- queue;
- retries;
- timeout;
- priority;
- cost model;
- checkpointing.

---

## 8. GPU and specialized compute

Evaluate:

- availability;
- quotas;
- utilization;
- scheduling;
- data locality;
- cost;
- fallback.

---

## 9. Provider mapping

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| VM | EC2 | Virtual Machines | Compute Engine |
| Managed Kubernetes | EKS | AKS | GKE |
| Managed containers | ECS/Fargate/App Runner | Container Apps | Cloud Run |
| Functions | Lambda | Azure Functions | Cloud Functions |
| PaaS app | Elastic Beanstalk/App Runner | App Service | App Engine |
| Batch | AWS Batch | Azure Batch | Batch |
