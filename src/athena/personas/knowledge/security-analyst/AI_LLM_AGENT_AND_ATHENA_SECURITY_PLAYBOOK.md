# AI, LLM, Agent, and Athena Security Playbook

## 1. Trust model

Treat all model inputs as untrusted:

- user prompts;
- repository files;
- documentation;
- comments;
- issues;
- external search;
- tool output;
- retrieved context.

---

## 2. Prompt and context injection

A repository may contain instructions intended to manipulate the assistant.

Controls:

- separate data from instructions;
- mark source provenance;
- never grant repository text higher authority than system policy;
- restrict tools;
- require confirmation for sensitive actions;
- sanitize output paths;
- display evidence.

---

## 3. Tool use

For every tool:

- allowlisted operation;
- least privilege;
- path scope;
- network scope;
- timeout;
- output limit;
- audit;
- failure behavior.

Default Athena analysis should be read-only.

---

## 4. Sensitive-code handling

Define:

- local versus remote processing;
- model provider;
- retention;
- telemetry;
- repository exclusions;
- secret redaction;
- user consent;
- index encryption/permissions;
- deletion.

---

## 5. MCP security

Review:

- client authentication where networked;
- stdio process trust;
- exposed tools;
- argument validation;
- command injection;
- path traversal;
- workspace binding;
- response size;
- denial of service;
- logs.

---

## 6. Model and dependency supply chain

Track:

- model source;
- checksum;
- license;
- version;
- runtime;
- package dependencies;
- update policy;
- vulnerability response.

---

## 7. Output safety

Generated recommendations or patches must:

- cite source evidence;
- avoid secret disclosure;
- avoid unsafe shell expansion;
- preserve authorization;
- include tests;
- identify uncertainty.

---

## 8. AI-specific assessment

Review:

- data poisoning;
- model poisoning;
- insecure model loading;
- prompt injection;
- excessive agency;
- unsafe output handling;
- data leakage;
- denial of service;
- monitoring;
- human oversight.

Use current OWASP AI/LLM verification guidance where relevant.

---

## 9. Athena hardening checklist

- workspace root is canonicalized;
- symlink escapes are blocked or explicit;
- repository is read-only by default;
- secret patterns are redacted;
- index files are permission-restricted;
- untrusted files cannot invoke tools;
- parser resource limits exist;
- oversized/binary files are controlled;
- MCP arguments are validated;
- custom personas are trusted or signed;
- logs do not contain source secrets;
- deletion removes indexes and caches;
- container mounts use least privilege.
