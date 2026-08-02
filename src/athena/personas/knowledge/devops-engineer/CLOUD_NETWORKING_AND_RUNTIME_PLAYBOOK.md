# Cloud Networking and Runtime Playbook

## 1. Scope

This playbook covers:

- DNS;
- IP/CIDR;
- routing;
- load balancing;
- ingress;
- egress;
- firewalls/security groups;
- proxies;
- TLS;
- mTLS;
- service discovery;
- connectivity diagnostics.

---

## 2. Network design questions

- Who initiates?
- What destination?
- Which protocol and port?
- Public or private?
- Which identity?
- What encryption?
- What timeout?
- What volume?
- What failure behavior?
- Who owns the rule?

---

## 3. DNS

Define:

- authoritative zone;
- record type;
- TTL;
- health behavior;
- split horizon;
- certificate dependency;
- change/rollback.

Remember DNS changes are not instantaneous.

---

## 4. Load balancing

Choose:

- layer 4;
- layer 7;
- internal;
- external;
- global;
- regional.

Define health checks, draining, affinity, timeout, and limits.

---

## 5. TLS

Define:

- issuer;
- trust;
- hostname;
- protocol;
- cipher policy;
- renewal;
- rotation;
- revocation;
- monitoring.

Never disable verification as a production fix.

---

## 6. mTLS

Use when mutual workload identity and encryption are required.

Account for:

- certificate issuance;
- rotation;
- trust distribution;
- revocation;
- debugging;
- performance;
- failure mode.

---

## 7. Egress

Control external access.

Use:

- allowlists;
- proxy/NAT;
- DNS policy;
- monitoring;
- cost tracking.

---

## 8. Troubleshooting

```text
name resolution
→ route
→ firewall
→ listener
→ TLS
→ proxy/load balancer
→ application
→ response
```

Use evidence:

- DNS lookup;
- route;
- socket;
- certificate;
- packet/flow logs;
- proxy logs;
- service metrics.

---

## 9. Anti-patterns

- allow all;
- undocumented firewall;
- public database;
- disabled TLS verify;
- static host entry;
- overlapping CIDR;
- missing timeout;
- unlimited connections;
- direct pod IP dependency.
