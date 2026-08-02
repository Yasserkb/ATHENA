# Security Architecture Patterns and Anti-Patterns

## 1. Defense in Depth

Multiple independent controls reduce single-point security failure.

---

## 2. Least Privilege

Grant only required actions, resources, conditions, and duration.

---

## 3. Default Deny

Access is denied unless explicitly allowed.

---

## 4. Zero Trust

Authenticate and authorize based on identity and context, not network location alone.

---

## 5. Complete Mediation

Every sensitive access is checked.

---

## 6. Separation of Duties

Critical actions require distinct responsibilities or approvals.

---

## 7. Workload Identity

Use short-lived platform identity rather than embedded credentials.

---

## 8. Secrets Broker

Centralize secret issuance, rotation, audit, and revocation.

---

## 9. Secure Gateway

Centralize appropriate edge controls without assuming it replaces service authorization.

---

## 10. Security Boundary Adapter

Normalize and validate data when crossing an external-system boundary.

---

## 11. Policy as Code

Version and test enforceable security policy.

---

## 12. Security Champion

Embed security knowledge in delivery teams with central support and governance.

---

## 13. Threat Modeling as Code

Version security models, assumptions, and findings near architecture.

---

## 14. Immutable Artifact

Build, verify, sign, and promote the same artifact.

---

## 15. Break Glass

Provide controlled emergency access with monitoring and review.

---

## 16. Honeytoken/Canary

Use non-production decoy signals to detect unauthorized access where appropriate.

---

## 17. Anti-pattern: Security by Obscurity

Hidden implementation is treated as the primary control.

---

## 18. Anti-pattern: Perimeter-Only Security

Internal identities and east-west paths are trusted broadly.

---

## 19. Anti-pattern: Authentication Equals Authorization

A valid identity is permitted to access any object or function.

---

## 20. Anti-pattern: Shared Administrator

Privileged actions cannot be attributed.

---

## 21. Anti-pattern: Permanent Exception

Risk acceptance has no expiry or review.

---

## 22. Anti-pattern: Scanner-Driven Security

Tool output replaces architecture and business analysis.

---

## 23. Anti-pattern: Encrypt Everything, Manage Nothing

Encryption is added without key ownership, rotation, recovery, or access design.

---

## 24. Anti-pattern: Log Everything

Sensitive data and unmanageable noise are collected without detection purpose.

---

## 25. Anti-pattern: Alert and Forget

A rule has no owner, runbook, validation, or response.

---

## 26. Anti-pattern: Compliance Equals Security

Passing a control checklist is treated as proof that attack paths are controlled.

---

## 27. Anti-pattern: Client-Side Trust

Mobile or browser checks are treated as server authorization.

---

## 28. Anti-pattern: Security Last Gate

Security is postponed until release and cannot influence design.

---

## 29. Pattern record

```markdown
## Pattern

### Security problem
### Assets and trust boundary
### Threat
### Selected pattern
### Preventive control
### Detective control
### Recovery control
### Trade-offs
### Verification
### Residual risk
```
