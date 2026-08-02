# Kubernetes and Container Platform Playbook

## 1. Workload requirements

Before Kubernetes, verify the workload needs:

- orchestration;
- scaling;
- scheduling;
- self-healing;
- multi-service platform.

Do not choose Kubernetes only for fashion.

---

## 2. Container image

Requirements:

- trusted minimal base;
- non-root;
- multi-stage;
- pinned digest/version;
- no secrets;
- signal handling;
- read-only filesystem where possible;
- vulnerability scanning;
- SBOM and provenance.

---

## 3. Workload resources

Define:

- Deployment/StatefulSet/Job/CronJob;
- replicas;
- strategy;
- resources;
- probes;
- termination grace;
- lifecycle;
- service account;
- security context.

---

## 4. Probes

### Startup

Use for slow initialization.

### Readiness

Answers: should this instance receive traffic?

### Liveness

Answers: is the process irrecoverably stuck?

Do not make liveness depend on a remote dependency that can trigger mass restarts.

---

## 5. Resources

Requests affect scheduling.

Limits affect enforcement.

Set from measurements.

Watch:

- CPU throttling;
- OOM kill;
- node pressure;
- QoS class.

---

## 6. Scheduling

Use:

- affinity;
- anti-affinity;
- topology spread;
- taints/tolerations;
- priorities;
- disruption budgets.

Distribute replicas across failure domains where availability requires it.

---

## 7. Networking

Define:

- Service;
- ingress/gateway;
- network policy;
- DNS;
- egress;
- TLS;
- mTLS if justified.

Default-deny policies should be introduced with tested allow rules.

---

## 8. Security

Use:

- restricted pod security;
- non-root;
- dropped capabilities;
- seccomp;
- read-only root;
- workload identity;
- least-privilege RBAC;
- image verification;
- admission policy.

---

## 9. Configuration and secrets

Use ConfigMaps for non-sensitive configuration.

Use approved secret mechanisms for secrets.

Plan rotation and reload behavior.

---

## 10. Autoscaling

HPA requires:

- correct metrics;
- requests;
- bounds;
- stabilization;
- workload behavior.

Cluster autoscaling requires:

- schedulable pending pods;
- node-group capacity;
- disruption analysis.

---

## 11. Storage

Define:

- access mode;
- class;
- zone;
- backup;
- restore;
- expansion;
- retention;
- reclaim policy.

---

## 12. Helm

Charts should:

- provide safe defaults;
- validate values;
- avoid excessive templates;
- keep naming stable;
- support rendering tests;
- separate secret references.

Pin chart dependencies.

---

## 13. Kustomize

Use for declarative overlays and patches.

Avoid giant overlays that duplicate bases.

---

## 14. Upgrades

Plan:

- API deprecations;
- control-plane version;
- node version;
- CNI/CSI;
- ingress;
- operators;
- workload compatibility;
- rollback.

---

## 15. Troubleshooting model

```text
desired object
→ controller status
→ events
→ pod scheduling
→ image/startup
→ probes
→ service/endpoints
→ DNS/network
→ dependency
→ application signals
```

---

## 16. Anti-patterns

- `latest`;
- no resources;
- privileged by default;
- wildcard RBAC;
- application data in image;
- stateful app without backup;
- liveness restart storm;
- every service publicly exposed;
- manual `kubectl edit`;
- production-only manifests.
