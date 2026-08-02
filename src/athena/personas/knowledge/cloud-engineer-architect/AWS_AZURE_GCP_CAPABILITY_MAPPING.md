# AWS, Azure, and GCP Capability Mapping

## 1. Purpose

This mapping helps translate provider-neutral architecture into cloud-specific services.

It is not a recommendation to use every service listed.

Always validate:

- regional availability;
- quotas;
- pricing;
- feature maturity;
- compliance;
- networking;
- support;
- current provider documentation.

---

## 2. Foundation and governance

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| Organization hierarchy | Organizations | Management Groups | Organization/Folders |
| Account boundary | Account | Subscription | Project |
| Landing-zone accelerator | Control Tower | Azure Landing Zones | Cloud Foundation Fabric / Enterprise Foundations |
| Policy | SCP / AWS Config | Azure Policy | Organization Policy |
| Audit | CloudTrail | Activity Log | Cloud Audit Logs |
| Cost | Cost Explorer/Budgets | Cost Management | Cloud Billing/Budgets |

---

## 3. Identity and security

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| Workforce identity | IAM Identity Center | Entra ID | Cloud Identity |
| Resource IAM | IAM | Azure RBAC | Cloud IAM |
| Secrets | Secrets Manager | Key Vault | Secret Manager |
| Keys | KMS/CloudHSM | Key Vault/Managed HSM | Cloud KMS/Cloud HSM |
| Security posture | Security Hub | Defender for Cloud | Security Command Center |
| WAF | AWS WAF | Azure WAF | Cloud Armor |

---

## 4. Network

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| Virtual network | VPC | VNet | VPC |
| Transit | Transit Gateway | Virtual WAN | Network Connectivity Center |
| Private endpoint | PrivateLink | Private Link | Private Service Connect |
| DNS | Route 53 | Azure DNS | Cloud DNS |
| Dedicated connectivity | Direct Connect | ExpressRoute | Cloud Interconnect |
| CDN | CloudFront | Front Door/CDN | Cloud CDN |

---

## 5. Compute

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| VM | EC2 | Virtual Machines | Compute Engine |
| Kubernetes | EKS | AKS | GKE |
| Containers | ECS/Fargate/App Runner | Container Apps | Cloud Run |
| Functions | Lambda | Functions | Cloud Functions |
| Batch | AWS Batch | Azure Batch | Batch |

---

## 6. Data and integration

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| Object storage | S3 | Blob Storage | Cloud Storage |
| Relational | RDS/Aurora | Azure SQL/Managed PostgreSQL/MySQL | Cloud SQL/AlloyDB/Spanner |
| NoSQL | DynamoDB/DocumentDB | Cosmos DB | Firestore/Bigtable |
| Cache | ElastiCache | Azure Managed Redis | Memorystore |
| Queue | SQS | Service Bus Queue | Pub/Sub |
| Event bus | EventBridge | Event Grid | Eventarc |
| Streaming | Kinesis/MSK | Event Hubs | Pub/Sub/Dataflow |
| Warehouse | Redshift | Synapse/Fabric | BigQuery |

---

## 7. Observability

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| Metrics/logs | CloudWatch | Azure Monitor/Log Analytics | Cloud Monitoring/Logging |
| Tracing | X-Ray | Application Insights | Cloud Trace |
| Managed Prometheus | AMP | Azure Monitor managed Prometheus | Managed Service for Prometheus |

---

## 8. Decision rule

Select a provider service only after documenting:

- capability;
- workload fit;
- failure behavior;
- availability;
- network path;
- security;
- operational burden;
- cost;
- quota;
- lock-in;
- exit plan.
