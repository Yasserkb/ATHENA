# Developer Skills and Stack Catalog

## 1. Core computer-science and engineering skills

Athena should expect a senior developer to reason about:

- algorithms and complexity;
- data structures;
- type systems;
- object-oriented, functional, and event-driven design;
- concurrency and asynchronous execution;
- networking and HTTP;
- relational and non-relational data;
- transactions and consistency;
- security fundamentals;
- testing and debugging;
- observability;
- operating systems and processes;
- build systems, packaging, and dependency management;
- Git and delivery workflows;
- architecture and trade-offs.

---

## 2. Frontend web skills

- HTML semantics;
- CSS layout, responsive design, container queries, design tokens;
- JavaScript and TypeScript;
- React and Angular;
- Next.js rendering and routing;
- forms and validation;
- client, server, URL, and local state;
- accessibility;
- browser security;
- performance and Core Web Vitals;
- testing with unit/component/browser tools;
- internationalization;
- analytics and error monitoring.

---

## 3. Backend skills

- REST, GraphQL, gRPC, WebSocket, SSE;
- domain and application services;
- API versioning;
- authentication and authorization;
- transaction boundaries;
- database access and migrations;
- messaging and event processing;
- idempotency;
- resilience;
- caching;
- scheduled/background jobs;
- observability;
- performance and capacity.

---

## 4. Mobile skills

- iOS and Android lifecycle;
- React Native/Expo, Flutter, native Kotlin/Swift concepts;
- navigation;
- offline-first and synchronization;
- local secure storage;
- permissions;
- deep links;
- push notifications;
- background work;
- device fragmentation;
- performance, battery, and memory;
- app signing and store rollout;
- mobile analytics and crash reporting.

---

## 5. MERN stack

### MongoDB

- document modeling from access patterns;
- indexes;
- aggregation;
- transactions when needed;
- schema validation;
- pagination and projections;
- replication and connection lifecycle.

### Express

- middleware ordering;
- routing;
- validation;
- authorization;
- error handling;
- timeouts;
- rate limits;
- observability.

### React

- component and state architecture;
- server-state libraries;
- forms;
- accessibility;
- performance;
- testing.

### Node.js

- event loop;
- streams;
- worker threads/processes;
- package boundaries;
- runtime security;
- graceful shutdown.

---

## 6. T3 stack

Core:

- TypeScript;
- Next.js;
- React.

Common modular additions:

- Tailwind CSS;
- tRPC;
- Prisma or Drizzle;
- Auth.js/NextAuth;
- runtime schemas such as Zod.

Athena must inspect the repository rather than assuming all modules exist.

---

## 7. T4 universal stack

For this suite, T4 means the universal TypeScript web/native starter ecosystem centered around:

- Next.js for web;
- Expo/React Native for native;
- Tamagui for shared UI;
- Solito for shared navigation patterns;
- tRPC and TanStack Query;
- Bun;
- Hono and Cloudflare Workers;
- D1/SQLite and Drizzle;
- authentication such as Supabase in the reference stack.

Athena must allow repository-specific substitutions.

---

## 8. Spring and Angular stack

### Spring

- Java 17/21+ concepts;
- Spring Boot;
- Spring MVC/WebFlux when justified;
- Spring Security;
- validation;
- JPA/Hibernate;
- transactions;
- MapStruct;
- Flyway/Liquibase;
- scheduling and async;
- external clients;
- Actuator and observability;
- testing with JUnit, Mockito, Spring slices, Testcontainers.

### Angular

- standalone components/modules according to repository version;
- signals and RxJS;
- router;
- reactive forms;
- HTTP interceptors;
- guards;
- state management when justified;
- Angular Material/design systems;
- testing and accessibility.

---

## 9. Python stack

- Python language and typing;
- packaging with `pyproject.toml`;
- virtual environments and lock files;
- FastAPI, Django, or Flask;
- Pydantic;
- SQLAlchemy and migrations;
- pytest;
- asyncio;
- Celery/RQ/background workers;
- data processing when relevant;
- logging and metrics;
- security and dependency management;
- performance profiling.

---

## 10. Skill evidence Athena should retrieve

For a requested stack, retrieve:

- package/build manifests;
- framework configuration;
- entry points;
- routing;
- dependency injection or composition;
- API contracts;
- persistence;
- tests;
- environment configuration;
- deployment runtime;
- repository conventions.

Do not infer a stack from one dependency alone.
