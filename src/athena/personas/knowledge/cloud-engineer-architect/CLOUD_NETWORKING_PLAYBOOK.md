# Cloud Networking Playbook

## 1. Design inputs

Collect:

- regions;
- environments;
- expected growth;
- hybrid connectivity;
- public entry points;
- egress destinations;
- compliance;
- latency;
- tenancy;
- DNS;
- inspection requirements.

---

## 2. Address planning

Define CIDRs with growth space.

Avoid:

- overlap;
- excessively large networks without segmentation;
- tiny subnets that prevent scaling;
- provider-reserved address mistakes.

Maintain an IP allocation registry.

---

## 3. Topologies

### Hub-and-spoke

Useful for centralized:

- routing;
- inspection;
- hybrid connectivity;
- shared services.

### Full mesh

Becomes operationally complex.

### Shared network

Can improve central control but may increase coupling.

### Service networking

Private endpoints and service-to-service constructs reduce public exposure.

---

## 4. Segmentation

Segment by:

- environment;
- trust;
- workload;
- data;
- administration;
- shared services.

Do not rely only on subnets; enforce identity and policy too.

---

## 5. Ingress

Define:

- DNS;
- CDN;
- DDoS;
- WAF;
- load balancer;
- TLS;
- routing;
- authentication;
- origin protection;
- rate limiting.

---

## 6. Egress

Control:

- NAT;
- proxy;
- firewall;
- allowlists;
- DNS;
- private service access;
- data exfiltration;
- egress cost.

---

## 7. DNS

Design:

- public zones;
- private zones;
- split DNS;
- forwarding;
- hybrid resolution;
- service discovery;
- TTL;
- failover.

---

## 8. Hybrid connectivity

Options:

- site-to-site VPN;
- dedicated connection;
- SD-WAN;
- provider interconnect.

Define:

- bandwidth;
- redundancy;
- routing;
- encryption;
- monitoring;
- failover;
- provider diversity.

---

## 9. Private endpoints

Use for managed services when:

- public exposure is unnecessary;
- data policies require private paths;
- DNS and routing can be managed safely.

Review cost and DNS complexity.

---

## 10. Network security

Use:

- stateful firewall/security groups;
- stateless ACL where justified;
- network policy;
- WAF;
- DDoS protection;
- flow logs;
- service identity;
- TLS/mTLS.

---

## 11. Troubleshooting sequence

```text
DNS
→ route
→ firewall/policy
→ endpoint/listener
→ TLS
→ load balancer/proxy
→ application
→ dependency
```

---

## 12. Provider mapping

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| Virtual network | VPC | VNet | VPC |
| Transit | Transit Gateway | Virtual WAN / vHub | Network Connectivity Center |
| Private service access | PrivateLink | Private Link | Private Service Connect |
| DNS | Route 53 | Azure DNS | Cloud DNS |
| L7 load balancing | ALB / CloudFront | Application Gateway / Front Door | Cloud Load Balancing |
| WAF | AWS WAF | Azure WAF | Cloud Armor |
| Dedicated hybrid | Direct Connect | ExpressRoute | Cloud Interconnect |
