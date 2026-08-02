# Mobile, Desktop, and Client Security Playbook

## 1. Client trust model

Assume the client device and client code can be inspected and modified.

Never rely on client-only enforcement for server authorization or business integrity.

---

## 2. Local storage

Review:

- tokens;
- personal data;
- cached API responses;
- logs;
- files;
- backups;
- screenshots;
- clipboard;
- keychain/keystore usage.

---

## 3. Network

Require:

- TLS validation;
- safe certificate handling;
- no debug proxy trust in production;
- secure API authentication;
- replay protection where needed;
- safe WebView configuration.

Certificate pinning is a trade-off and requires rotation/recovery design.

---

## 4. Platform integration

Review:

- deep links;
- URL schemes;
- intents;
- exported components;
- permissions;
- push notifications;
- background tasks;
- biometric use;
- application updates;
- inter-process communication.

---

## 5. Code and build

Review:

- debug flags;
- development endpoints;
- signing;
- build variants;
- symbols;
- hardcoded secrets;
- dependency provenance;
- tamper detection where justified.

---

## 6. WebView and browser components

Review:

- JavaScript bridges;
- navigation allowlists;
- mixed content;
- file access;
- untrusted URLs;
- origin validation.

---

## 7. Privacy

Review:

- permissions;
- tracking;
- analytics;
- identifiers;
- consent;
- data minimization;
- deletion.

---

## 8. Testing

Use authorized:

- static analysis;
- runtime inspection;
- local storage review;
- network review;
- platform configuration tests;
- server authorization tests.

Map mobile controls to OWASP MASVS where useful.
