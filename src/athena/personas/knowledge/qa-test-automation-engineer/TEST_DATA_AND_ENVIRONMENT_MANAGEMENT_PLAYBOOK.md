# Test Data and Environment Management Playbook

## 1. Test-data strategy

Define:

- data types;
- ownership;
- source;
- privacy;
- creation;
- uniqueness;
- cleanup;
- retention;
- refresh;
- masking;
- reproducibility.

---

## 2. Data approaches

### Synthetic

Best for privacy and control.

### Masked production-derived

Use only with approved transformation and controls.

### Generated fixtures

Useful for deterministic automation.

### On-demand API creation

Good when public setup APIs exist.

### Database seeding

Useful for controlled integration environments.

---

## 3. Data isolation

Use:

- unique IDs;
- tenant;
- namespace;
- transaction rollback;
- ephemeral database;
- cleanup jobs.

---

## 4. Privacy

Never copy production data casually.

Protect:

- personal information;
- credentials;
- financial data;
- health data;
- identifiers.

---

## 5. Environment inventory

Track:

- purpose;
- owner;
- version;
- configuration;
- data;
- dependencies;
- availability;
- limitations.

---

## 6. Ephemeral environments

Useful for:

- pull request;
- integration;
- isolated test.

Define:

- creation;
- seed;
- URL;
- identity;
- TTL;
- cleanup;
- cost.

---

## 7. Service virtualization

Use for unavailable or unstable dependencies.

Maintain contract fidelity.

---

## 8. Environment health

Validate before test execution:

- deployment;
- database;
- queues;
- external stubs;
- DNS;
- certificates;
- test data;
- capacity.

---

## 9. Anti-patterns

- shared global test account;
- manual database edits;
- environment unknown version;
- production data copied directly;
- cleanup ignored;
- test failure caused by stale environment.
