# Security Standards and Framework Reference Map

## 1. Purpose

Frameworks support consistency and communication. They do not replace system-specific analysis.

Use versioned requirement identifiers where possible.

---

## 2. Governance and enterprise risk

### NIST Cybersecurity Framework 2.0

Use its functions:

- Govern;
- Identify;
- Protect;
- Detect;
- Respond;
- Recover.

Use for program-level outcomes and communication.

### CIS Controls v8.1

Use as prioritized defensive safeguards across enterprise assets, software, cloud, mobile, data, logging, vulnerability management, and incident response.

---

## 3. Secure development

### NIST SSDF

Use for secure software development practices integrated into the SDLC.

The latest final baseline is SP 800-218 SSDF 1.1. A version 1.2 revision was published as a draft; do not describe a draft as final.

### OpenSSF guidance

Use for secure software and open-source supply-chain practices.

---

## 4. Application and API

### OWASP ASVS 5.0

Use testable application-security verification requirements.

### OWASP Top 10:2025

Use as web-application security awareness, not a complete verification standard.

### OWASP API Security Top 10:2023

Use for API-specific awareness and review prompts.

### OWASP Cheat Sheet Series

Use for implementation guidance.

---

## 5. Mobile and client

### OWASP MASVS

Use for mobile security verification.

### OWASP MASTG

Use for mobile testing guidance.

### OWASP TCASVS

Use for thick-client verification where relevant.

---

## 6. Threats and detection

### MITRE ATT&CK

Use real-world adversary tactics and techniques to organize:

- threat models;
- telemetry requirements;
- detection coverage;
- threat hunts.

Do not use ATT&CK mapping as proof that controls work.

---

## 7. AI-enabled systems

Use current OWASP AI and LLM security verification standards when Athena or another system:

- retrieves untrusted context;
- invokes tools;
- processes private data;
- uses models or agents;
- creates automated actions.

---

## 8. Framework mapping rule

A finding may include:

```text
technical evidence
→ system-specific risk
→ remediation
→ verification
→ optional framework mapping
```

Never reverse the order and start from a checklist item without system evidence.
