# MERN Stack Engineering Playbook

## 1. Architecture

Recommended responsibility flow:

```text
React UI
→ client/domain API layer
→ Express route
→ validation and authorization
→ application/domain service
→ MongoDB repository/model
```

## 2. MongoDB modeling

Choose embed versus reference from:

- read patterns;
- update patterns;
- document growth;
- atomicity;
- lifecycle;
- cardinality.

Define indexes for real queries. Control projections and result sizes.

## 3. Mongoose or driver behavior

Review:

- schema validation;
- defaults;
- middleware;
- lean reads;
- population cost;
- sessions/transactions;
- ObjectId conversion;
- timestamps;
- model compilation in hot-reload/serverless environments.

## 4. Express

Define middleware order:

- request ID;
- security headers;
- body limits;
- authentication;
- routing;
- error handling;
- logging.

Use centralized error mapping without losing domain context.

## 5. React

Keep server state in a server-state abstraction. Use forms with runtime schemas shared only where coupling is intentional.

## 6. Node runtime

Address:

- event-loop blocking;
- streams;
- async error handling;
- graceful shutdown;
- connection lifecycle;
- worker processes/threads;
- memory limits.

## 7. Security

Review:

- NoSQL injection;
- mass assignment;
- query operator injection;
- JWT/session handling;
- CORS;
- CSRF where cookies are used;
- rate limits;
- password hashing;
- secret storage.

## 8. Performance

Measure:

- slow queries;
- index usage;
- aggregation stages;
- document size;
- pagination;
- connection-pool saturation;
- response payload;
- React bundle/render behavior.

## 9. Testing

- domain/unit;
- Express route integration;
- MongoDB integration through disposable instances;
- API contract;
- React component;
- limited E2E.
