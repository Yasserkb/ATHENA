# Git, Code Review, and Delivery Playbook

## 1. Change structure

A change should be:

- focused;
- reviewable;
- buildable;
- testable;
- reversible where feasible.

## 2. Commits

Use coherent commits that explain intent. Do not hide generated or unrelated changes.

## 3. Review priorities

1. security/data loss;
2. incorrect behavior;
3. concurrency/transactions;
4. compatibility;
5. reliability;
6. performance;
7. maintainability;
8. readability/style.

Each finding needs evidence, impact, and a concrete correction.

## 4. Pull request content

Include:

- problem;
- solution;
- important decisions;
- affected contracts/data;
- tests;
- screenshots for UI;
- migration/deployment;
- rollback;
- risk.

## 5. CI

Run cheap checks first. Promote the same artifact. Protect secrets and privileged runners.

## 6. Release

Define:

- artifact;
- configuration;
- database migration;
- feature flag;
- rollout;
- health check;
- observation window;
- rollback.

## 7. Documentation

Update documentation when behavior, contract, configuration, architecture, or operations change.
