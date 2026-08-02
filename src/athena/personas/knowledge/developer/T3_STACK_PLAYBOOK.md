# T3 Stack Engineering Playbook

## 1. Scope

Treat T3 as a modular approach, not a rigid framework. Confirm which technologies exist in the repository.

Typical capabilities:

- Next.js and React;
- TypeScript;
- Tailwind CSS;
- tRPC;
- Prisma or Drizzle;
- Auth.js/NextAuth;
- runtime validation.

## 2. Server and client boundaries

Identify:

- server components;
- client components;
- route handlers;
- server actions;
- tRPC server/client;
- server-only modules;
- environment exposure.

Never import database, secret, or privileged server modules into client code.

## 3. tRPC

Define:

- router ownership;
- public/protected procedures;
- input schema;
- output/error contract;
- authorization;
- context lifecycle;
- batching;
- invalidation;
- subscriptions if present.

Type safety does not replace runtime input validation.

## 4. Authentication

Review:

- provider;
- session strategy;
- callbacks;
- token fields;
- authorization;
- CSRF/cookie behavior;
- server enforcement;
- account linking;
- logout and revocation.

## 5. ORM and database

For Prisma or Drizzle, inspect:

- schema;
- generated types;
- migration workflow;
- transaction boundaries;
- connection lifecycle;
- serverless/edge compatibility;
- query count;
- indexes.

## 6. Rendering and caching

Define:

- static/dynamic behavior;
- data cache;
- request memoization;
- route cache;
- revalidation;
- client query cache;
- mutation invalidation.

Avoid contradictory caches.

## 7. Testing

- pure/domain unit tests;
- router/procedure tests;
- database integration;
- component tests;
- authentication/authorization tests;
- selected browser journeys.

## 8. Deployment

Verify:

- Node versus edge runtime;
- database connectivity;
- environment variables;
- migrations;
- image/serverless packaging;
- observability;
- background work constraints.

## 9. Anti-patterns

- assuming compile-time types validate the network;
- client-only authorization;
- leaking server code;
- one giant tRPC router;
- N+1 ORM access;
- cache invalidation by full-page refresh;
- rebuilding database clients per request incorrectly.
