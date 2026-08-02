# Athena Developer Routing and Retrieval Upgrade

## 1. Why a router upgrade is needed

Athena 0.1 gives the generic `developer` persona an implementation bonus. A task such as:

```text
Implement an Angular form
```

can therefore route to generic `developer` even when `spring-angular-developer` matched `angular`.

Specialist personas remain usable through explicit `--persona`, but automatic routing should classify stack/domain first and use generic developer only as fallback.

---

## 2. Recommended routing order

1. explicit persona supplied by the caller;
2. specialist stack/domain match;
3. task-purpose persona such as reviewer/debugger/tester;
4. generic developer fallback.

For implementation tasks, combine domain and purpose:

```text
implement + angular → spring-angular-developer
implement + mobile → mobile-developer
implement + mongodb + react → mern-developer
implement + t3 → t3-developer
implement + python → python-developer
implement with no domain signal → developer
```

---

## 3. Scoring model

Recommended score channels:

- exact multi-word trigger: 2.0;
- exact single trigger: 1.0;
- repository stack evidence: 0.4–1.2;
- task-purpose signal: 0.8;
- generic fallback: 0.25;
- negative conflict: -0.5.

Do not give generic developer a larger bonus than a specialist exact match.

---

## 4. Repository stack evidence

Athena should detect stack evidence from manifests and paths:

| Evidence | Stack signal |
|---|---|
| `pom.xml`, `build.gradle`, Spring imports | Spring |
| `angular.json`, `@angular/*` | Angular |
| `next.config.*`, `next` dependency | Next.js |
| `create-t3-app`, `@trpc/*` | T3 |
| Tamagui + Expo + Solito/Hono | T4 |
| MongoDB/Mongoose + Express + React | MERN |
| `pyproject.toml`, FastAPI/Django/Flask | Python |
| Expo/React Native/Android/iOS files | Mobile |

Stack evidence must not override explicit user selection.

---

## 5. Requested-tag expansion

Athena 0.1 only boosts a few task tags. Expand requested tags for:

- frontend/component/form/accessibility;
- backend/api/event/transaction;
- mobile/offline/navigation/push;
- React/Angular/Next.js;
- Spring/JPA/Flyway;
- Python/FastAPI/Django;
- MERN/MongoDB/Express;
- T3/tRPC/Prisma/Drizzle;
- T4/Tamagui/Expo/Hono/Cloudflare.

The included patch demonstrates a minimal implementation.

---

## 6. Parser upgrade priority

Persona quality cannot exceed index quality. Athena 0.1's generic parser detects only a small set of TypeScript/Python declarations and does not build framework-specific relations.

Recommended parser roadmap:

### Priority 1 — TypeScript/JavaScript

Extract:

- imports/exports;
- functions, classes, interfaces, types, enums;
- React components/hooks;
- Next.js routes and server actions;
- Express/Hono routes;
- tRPC routers/procedures;
- Angular components/services/routes;
- call and dependency relations.

### Priority 2 — Python

Extract:

- modules/imports;
- classes/functions;
- decorators;
- FastAPI/Flask/Django routes;
- Pydantic models;
- SQLAlchemy models;
- Celery tasks;
- call/dependency relations.

### Priority 3 — Mobile

Extract:

- Expo/React Native screens;
- navigation routes;
- native modules;
- Android activities/services;
- iOS views/services;
- permissions and deep-link configuration.

Tree-sitter is a suitable first parser layer; framework semantic passes should derive higher-level nodes and edges.

---

## 7. New node kinds

Recommended kinds:

- component;
- hook;
- screen;
- route;
- server_action;
- api_procedure;
- middleware;
- schema;
- model;
- state_store;
- mobile_permission;
- background_task;
- event_handler;
- build_target;
- package;

---

## 8. New relations

Recommended relations:

- IMPORTS;
- EXPORTS;
- RENDERS;
- USES_HOOK;
- FETCHES;
- HANDLES_ROUTE;
- VALIDATES_WITH;
- AUTHORIZED_BY;
- PERSISTS_WITH;
- NAVIGATES_TO;
- SHARES_PACKAGE_WITH;
- RUNS_ON;
- EMITS_EVENT;
- CONSUMES_EVENT;
- MIGRATED_BY;

---

## 9. Context planning

Before packing chunks, create a task evidence plan.

Examples:

### Frontend feature

- route/page;
- component;
- API client;
- schema/form;
- style/design primitive;
- tests.

### Backend feature

- endpoint;
- service/use case;
- repository/entity;
- migration/configuration;
- caller/client;
- tests.

### Mobile feature

- screen/navigation;
- state/store;
- API/local storage;
- permissions/lifecycle;
- tests/build config.

This prevents high-scoring duplicate implementation chunks from consuming the full budget.

---

## 10. Evaluation requirement

Do not call the suite an improvement until the evaluation file demonstrates:

- higher persona-routing accuracy;
- higher expected-file recall;
- lower irrelevant context;
- stable token budget;
- better implementation/test success.
