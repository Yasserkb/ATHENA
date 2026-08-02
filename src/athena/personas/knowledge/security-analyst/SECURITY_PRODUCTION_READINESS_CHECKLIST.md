# Security Production Readiness Checklist

## Scope and ownership

- [ ] Security owner exists.
- [ ] Assets and trust boundaries are documented.
- [ ] Data classification exists.
- [ ] Public exposure is inventoried.
- [ ] Residual risks have business owners.

## Identity and access

- [ ] Human access uses managed identity and MFA where required.
- [ ] Workloads use dedicated identity.
- [ ] CI/CD uses short-lived identity.
- [ ] Least privilege is reviewed.
- [ ] Tenant boundaries are tested.
- [ ] Emergency access is controlled and audited.
- [ ] Inactive credentials are removed.

## Application and API

- [ ] Authorization is enforced server-side.
- [ ] Object and function access are tested.
- [ ] Input schemas and limits exist.
- [ ] Injection paths are controlled.
- [ ] SSRF and outbound requests are controlled.
- [ ] Sensitive workflows resist replay and abuse.
- [ ] Errors do not disclose sensitive information.
- [ ] Security tests exist.

## Web and mobile

- [ ] Browser security headers and cookie policy are correct.
- [ ] Client storage contains no unnecessary secrets.
- [ ] Deep links/WebViews are constrained.
- [ ] Mobile release signing is protected.
- [ ] Client checks are not trusted as server authorization.
- [ ] Privacy permissions are justified.

## Cloud and infrastructure

- [ ] Production is isolated.
- [ ] Public resources are justified.
- [ ] Network ingress and egress are controlled.
- [ ] Cloud audit is centralized.
- [ ] IAM escalation paths are reviewed.
- [ ] Security policies are automated.
- [ ] Backups and recovery are protected.

## Containers and Kubernetes

- [ ] Images use trusted sources.
- [ ] Images are scanned and traceable.
- [ ] Workloads run non-root where possible.
- [ ] Privileged access and capabilities are minimized.
- [ ] RBAC is least privilege.
- [ ] Network policy exists where required.
- [ ] Secrets are handled safely.
- [ ] Admission/image policy exists for critical environments.

## Supply chain

- [ ] Branches and releases are protected.
- [ ] Dependencies are locked and monitored.
- [ ] CI runners are isolated by trust.
- [ ] Artifacts are immutable.
- [ ] SBOM/provenance exists where required.
- [ ] Signing and verification are used where required.
- [ ] Vulnerability exceptions expire.

## Data and database

- [ ] Sensitive data is minimized.
- [ ] Encryption and key ownership are defined.
- [ ] Database roles are least privilege.
- [ ] Non-production data is synthetic or masked.
- [ ] Logs do not contain secrets or personal data.
- [ ] Retention and deletion cover downstream copies.
- [ ] Data-integrity controls exist.

## Detection and response

- [ ] Security-relevant logs exist.
- [ ] Logs contain identity and correlation context.
- [ ] Critical attack paths have detections or compensating monitoring.
- [ ] Alerts have owners and runbooks.
- [ ] Incident contacts and roles exist.
- [ ] Credential-revocation procedures exist.
- [ ] Recovery and evidence procedures are tested.

## Athena and AI tooling

- [ ] Repository content is treated as untrusted.
- [ ] Workspace access is read-only by default.
- [ ] Path and symlink boundaries are enforced.
- [ ] Secrets are redacted.
- [ ] Remote model use is explicit.
- [ ] MCP tools are allowlisted and validated.
- [ ] Parser and context resource limits exist.
- [ ] Index deletion and retention are defined.

## Release decision

- [ ] No unresolved unacceptable attack path exists.
- [ ] High-risk findings have mitigations and owners.
- [ ] Security verification passed.
- [ ] Detection coverage is sufficient.
- [ ] Rollback is possible.
- [ ] Accepted risks have expiry and approval.
