# Spring Boot and Angular Enterprise Stack Playbook

## 1. End-to-end contract

Define:

- Angular model/form;
- request DTO;
- Bean Validation;
- controller contract;
- application service;
- domain decision;
- entity/repository;
- response DTO;
- error format.

Do not expose JPA entities directly.

## 2. Spring responsibilities

- Controller: transport and validation.
- Application service: use-case and transaction boundary.
- Domain service: domain operation not owned by one entity.
- Repository: persistence.
- Client/adapter: external protocol.
- Mapper: structural transformation.
- Configuration: typed binding and wiring.

## 3. Transactions and JPA

Review:

- propagation;
- isolation;
- rollback;
- external calls;
- lazy loading;
- N+1;
- fetch plans;
- optimistic locking;
- cascading;
- batch writes;
- pagination.

## 4. Spring Security

Define:

- authentication;
- authorization;
- method/route rules;
- tenant access;
- CSRF;
- CORS;
- session/token;
- error behavior;
- audit.

## 5. Configuration

Prefer `@ConfigurationProperties` with validation for structured configuration. Protect secrets and environment-specific values.

## 6. Angular architecture

Define:

- feature routes;
- smart/container versus presentation components where useful;
- services;
- reactive forms;
- HTTP interceptors;
- guards;
- signals/RxJS;
- state ownership;
- error/loading behavior.

## 7. RxJS

Prefer composition with explicit lifecycle. Avoid:

- nested subscriptions;
- unbounded subjects as event buses;
- missing teardown;
- duplicated requests;
- hidden side effects.

## 8. Migrations

Use Flyway/Liquibase with expand-contract for breaking changes. Test against the real engine.

## 9. Testing

Backend:

- JUnit/Mockito for logic;
- MVC/security slices;
- JPA slices;
- Testcontainers integration;
- client contract tests.

Frontend:

- component/service tests;
- HTTP tests;
- accessibility;
- limited browser E2E.

## 10. Observability

Use structured logs, request IDs, Actuator/Micrometer, traces, frontend error monitoring, and business metrics.

## 11. Anti-patterns

- controller business logic;
- field injection;
- entity exposure;
- Open Session in View dependency;
- remote calls inside long transactions;
- Angular god services;
- nested subscriptions;
- untyped environment configuration;
- migration and entity mismatch.
