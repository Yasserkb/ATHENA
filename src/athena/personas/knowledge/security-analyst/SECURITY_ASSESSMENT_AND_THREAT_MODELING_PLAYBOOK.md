# Security Assessment and Threat Modeling Playbook

## 1. Assessment sequence

Use four questions:

1. What are we working on?
2. What can go wrong?
3. What are we going to do about it?
4. Did we do a good enough job?

---

## 2. Scope

Document:

- in-scope systems;
- environments;
- repositories;
- cloud accounts;
- data;
- identities;
- integrations;
- excluded areas;
- authorization;
- evidence limitations.

---

## 3. Data-flow model

For every important flow:

```text
source actor
→ entry point
→ authentication
→ authorization
→ processing
→ data store/external system
→ response or side effect
```

Record:

- protocol;
- data classification;
- identity;
- trust-boundary crossing;
- encryption;
- validation;
- audit;
- failure behavior.

---

## 4. STRIDE prompts

### Spoofing

Can an attacker impersonate:

- user;
- administrator;
- service;
- pipeline;
- trusted device;
- external partner?

### Tampering

Can an attacker modify:

- request;
- configuration;
- artifact;
- event;
- database record;
- log;
- deployment state?

### Repudiation

Can a sensitive action occur without reliable attribution?

### Information disclosure

Can data leak through:

- API;
- logs;
- errors;
- backups;
- cache;
- telemetry;
- client storage;
- repository index?

### Denial of service

Can limits be exhausted:

- CPU;
- memory;
- threads;
- database connections;
- queue;
- storage;
- API quota;
- token/context budget?

### Elevation of privilege

Can a lower-privilege identity gain:

- administrative function;
- cross-tenant access;
- cloud role;
- secret access;
- deployment control?

---

## 5. Abuse cases

Model legitimate functionality used maliciously.

Examples:

- repeated expensive search;
- password-reset abuse;
- bulk export by authorized account;
- mass enumeration;
- webhook replay;
- oversized repository indexing;
- workflow transition abuse.

---

## 6. Attack trees

Represent:

```text
Goal
├── Path A
│   ├── prerequisite
│   └── weakness
└── Path B
    ├── prerequisite
    └── weakness
```

Identify the cheapest control that breaks multiple paths.

---

## 7. Risk record

```markdown
## Threat

### Asset
### Actor
### Entry point
### Preconditions
### Attack path
### Existing controls
### Likelihood
### Impact
### Confidence
### Risk
### Mitigation
### Verification
### Detection
### Owner
### Residual risk
```

---

## 8. Reassessment triggers

Update the threat model after:

- new public endpoint;
- new identity provider;
- cloud migration;
- database change;
- new external integration;
- privilege change;
- major dependency change;
- incident;
- new mobile client;
- AI/LLM capability;
- architecture change.
