# T4 Universal Web and Native Stack Playbook

## 1. Scope

This playbook uses the T4 universal stack definition built around shared TypeScript applications for web and native platforms.

Reference capabilities:

- Next.js web;
- Expo/React Native native apps;
- Tamagui shared UI;
- Solito navigation patterns;
- tRPC and TanStack Query;
- Bun;
- Hono and Cloudflare Workers;
- D1/SQLite with Drizzle;
- shared authentication.

Confirm actual repository dependencies before applying a rule.

## 2. Monorepo/package boundaries

Typical packages:

- web app;
- native app;
- shared UI;
- API/contracts;
- database;
- configuration;
- tooling.

Define dependency direction and prevent platform-only dependencies from contaminating shared packages.

## 3. Shared UI

Share:

- design tokens;
- primitives;
- visual components;
- validation;
- domain logic.

Allow platform variants for:

- navigation;
- hover/pointer behavior;
- accessibility APIs;
- keyboard;
- file/media access;
- layout constraints.

## 4. Navigation

Define route parity and deliberate divergence between Next.js and Expo navigation. Handle deep links and authentication consistently.

## 5. Data fetching

Coordinate:

- tRPC contracts;
- TanStack Query keys;
- caching;
- retries;
- offline behavior;
- mutation invalidation;
- platform network lifecycle.

## 6. Edge backend

For Hono/Workers, review:

- Web API compatibility;
- CPU and execution limits;
- streaming;
- environment bindings;
- secret handling;
- connection limitations;
- background tasks;
- observability.

## 7. D1 and Drizzle

Address:

- SQLite semantics;
- migrations;
- transaction limits;
- indexes;
- geographic behavior;
- consistency;
- local development parity;
- backup/export strategy.

## 8. Authentication

Ensure one coherent identity model across browser, native, and API. Protect token storage and refresh behavior per platform.

## 9. Testing

- shared package unit tests;
- web component/browser tests;
- native component/device tests;
- API/edge tests;
- database migration tests;
- cross-platform contract tests.

## 10. Anti-patterns

- forced 100% UI sharing;
- platform checks scattered everywhere;
- browser storage assumptions on native;
- native secrets bundled in code;
- Node-only packages in edge runtime;
- one cache policy for incompatible lifecycle models.
