# QA and Test Automation Patterns and Anti-Patterns

## 1. Test Pyramid

Many fast lower-level tests, fewer broad tests.

Use as guidance, not dogma.

---

## 2. Test Trophy

Emphasizes integration tests where application behavior emerges from component interaction.

---

## 3. Test Data Builder

Creates readable valid test objects with targeted overrides.

---

## 4. Object Mother

Provides common presets.

Avoid hidden defaults that make tests unclear.

---

## 5. Fixture

Provides controlled setup and cleanup.

---

## 6. Fake

A lightweight working implementation.

---

## 7. Stub

Returns controlled responses.

---

## 8. Mock

Verifies important interaction.

Avoid mocking internal implementation details.

---

## 9. Consumer-Driven Contract

Consumer expectations are verified against provider behavior.

---

## 10. Page Object

Encapsulates UI interaction.

Do not turn it into a giant assertion container.

---

## 11. Screenplay

Models actors, abilities, tasks, and questions.

Useful for complex reusable journeys; excessive for simple suites.

---

## 12. Robot Pattern

Encapsulates UI actions around intent.

---

## 13. Golden Master

Captures existing behavior for legacy refactoring.

Review snapshot changes carefully.

---

## 14. Characterization Test

Documents current behavior before modifying poorly understood code.

---

## 15. Property-Based Testing

Generates inputs to verify invariants.

---

## 16. Mutation Testing

Measures whether tests detect deliberate code changes.

Use selectively due to cost.

---

## 17. Model-Based Testing

Generates scenarios from state or behavior models.

---

## 18. Service Virtualization

Simulates external systems.

---

## 19. Hermetic Test

Controls all dependencies and avoids external variation.

---

## 20. Anti-pattern: Ice-Cream Cone

Too many manual/UI tests and too little lower-level coverage.

---

## 21. Anti-pattern: Selenium Everywhere

UI automation used for logic and API behavior.

---

## 22. Anti-pattern: Sleep-Driven Testing

Fixed delays replace state synchronization.

---

## 23. Anti-pattern: Retry Until Green

Flakiness is hidden.

---

## 24. Anti-pattern: Shared Mutable Fixture

Tests influence one another.

---

## 25. Anti-pattern: Assertion Roulette

Many assertions fail without diagnostic context.

---

## 26. Anti-pattern: Mystery Guest

Test depends on hidden external data/resource.

---

## 27. Anti-pattern: Fragile Test

Minor implementation changes break behaviorally valid tests.

---

## 28. Anti-pattern: Test-Code Duplication

Setup and actions are copied broadly.

---

## 29. Anti-pattern: Coverage Theater

High line coverage is presented as complete quality evidence.

---

## 30. Anti-pattern: Manual Regression Forever

Repeated stable checks remain manual without reason.

---

## 31. Pattern documentation template

```markdown
## Pattern

### Risk or problem
### Why direct testing is insufficient
### Selected pattern
### Test level
### Data and isolation
### Diagnostics
### Maintenance cost
### Validation
### Revisit criteria
```
