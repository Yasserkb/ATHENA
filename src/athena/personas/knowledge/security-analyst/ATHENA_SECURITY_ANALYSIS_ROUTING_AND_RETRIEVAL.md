# Athena Security Analysis Routing and Retrieval Upgrade

## 1. Goal

The `security-analyst` persona must be selected for cross-system defensive-security work and must retrieve security-relevant evidence across code, infrastructure, data, and operations.

---

## 2. Routing precedence

Recommended precedence:

```text
explicit --persona
→ security-specific specialist
→ stack/domain specialist
→ generic reviewer/debugger/developer
```

Examples that should select `security-analyst`:

- “Threat-model the complete platform.”
- “Review this Spring API and Kubernetes deployment for security.”
- “Analyze IAM, secrets, database permissions, and attack paths.”
- “Triage these SAST and dependency findings.”
- “Find missing detections for this incident.”
- “Check Athena for prompt injection and unsafe MCP tool use.”

---

## 3. Co-operation with other personas

Security Analyst owns:

- threat model;
- attack paths;
- security risk;
- remediation requirements;
- security verification;
- detection.

Domain personas may provide implementation depth:

- developer;
- DevOps;
- cloud;
- QA;
- data engineer;
- DBA.

Future Athena orchestration can combine:

```text
security-analyst
+ relevant domain persona
→ consolidated evidence package
```

The security persona remains responsible for final risk classification.

---

## 4. Retrieval sequence

Recommended retrieval order:

```text
security terms and exact identifiers
→ entry points
→ authentication and authorization
→ secrets and configuration
→ sensitive data stores
→ external calls
→ infrastructure and IAM
→ pipelines and dependencies
→ logs, alerts, and tests
→ graph expansion across trust boundaries
```

---

## 5. Security node types

Future Athena parsers should add:

- identity;
- role;
- permission;
- trust policy;
- secret reference;
- sensitive field;
- security control;
- ingress;
- egress;
- network rule;
- image;
- dependency;
- artifact;
- pipeline permission;
- audit event;
- detection rule;
- vulnerability finding;
- trust boundary;
- data flow.

---

## 6. Security relations

Recommended relationships:

- AUTHENTICATES_WITH;
- AUTHORIZES;
- ASSUMES_ROLE;
- GRANTS;
- READS_SECRET;
- WRITES_SECRET;
- EXPOSES_PUBLICLY;
- SENDS_DATA_TO;
- STORES_SENSITIVE_DATA;
- CROSSES_TRUST_BOUNDARY;
- DEPLOYS;
- BUILDS_ARTIFACT;
- SIGNED_BY;
- DETECTED_BY;
- LOGGED_BY;
- PROTECTED_BY;
- VULNERABLE_TO;
- MITIGATES;
- AFFECTS_ASSET.

---

## 7. Evidence provenance

Every security finding should retain:

- repository path;
- line range;
- parser/extractor;
- runtime source if any;
- timestamp;
- confidence;
- hash;
- environment;
- redaction status.

---

## 8. Context budget

The persona uses a larger context budget because attack paths cross layers.

Still prefer:

- high-value security evidence;
- one or two chunks per control;
- summarized architecture;
- explicit missing evidence.

Do not dump all security configuration or entire manifests.

---

## 9. Future assessment command

Recommended Athena command:

```bash
athena security-assess \
  --root . \
  --scope application,cloud,pipeline,data \
  --format markdown \
  --persona security-analyst
```

Possible outputs:

- system security model;
- attack paths;
- findings;
- evidence;
- remediation plan;
- standards mapping;
- machine-readable JSON/SARIF.

---

## 10. Security of Athena execution

Security analysis should run:

- read-only by default;
- without external network by default;
- with bounded file and parser resources;
- with secret redaction;
- with explicit permission before sending context to remote models;
- with a clear data-deletion command.
