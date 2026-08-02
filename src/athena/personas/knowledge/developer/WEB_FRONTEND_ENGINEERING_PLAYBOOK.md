# Web and Frontend Engineering Playbook

## 1. User-state matrix

For each page or component, cover:

- initial;
- loading;
- success;
- empty;
- partial;
- validation error;
- authorization failure;
- server failure;
- offline;
- stale;
- retry;
- disabled/read-only.

## 2. Rendering and routing

For Next.js or similar frameworks, choose deliberately among:

- static rendering;
- server rendering;
- streaming;
- client rendering;
- incremental regeneration;
- route handlers/server actions.

Protect server/client boundaries and hydration consistency.

For Angular, inspect:

- route configuration;
- guards;
- resolvers;
- lazy boundaries;
- standalone/module structure;
- change detection;
- signals/RxJS ownership.

## 3. Component architecture

A component should own one coherent UI responsibility.

Separate:

- presentation;
- data orchestration;
- domain transformation;
- reusable primitives;
- page/layout composition.

Avoid components that fetch, authorize, transform, render, and persist everything.

## 4. State model

Classify state:

- server cache;
- URL/navigation;
- form;
- local interaction;
- cross-feature client state;
- persisted browser state.

Use global stores only for genuinely shared state.

## 5. Forms

Define:

- schema;
- initial values;
- client validation;
- server validation;
- field and form errors;
- duplicate submission;
- unsaved changes;
- accessibility;
- optimistic behavior.

## 6. Data fetching

Address:

- cache key;
- freshness;
- cancellation;
- race conditions;
- retries;
- pagination;
- optimistic update;
- invalidation;
- errors;
- authorization.

## 7. Accessibility

Require:

- semantic elements;
- accessible names;
- keyboard operation;
- focus management;
- error announcement;
- contrast;
- reduced motion;
- zoom and reflow;
- screen-reader verification for critical flows.

## 8. Browser security

Review:

- XSS;
- CSRF;
- CSP;
- clickjacking;
- unsafe HTML;
- token storage;
- CORS misconceptions;
- open redirects;
- third-party scripts;
- sensitive data in storage or analytics.

## 9. Performance

Measure:

- LCP;
- INP;
- CLS;
- bundle size;
- route payload;
- image behavior;
- font loading;
- render count;
- network waterfalls;
- cache effectiveness.

## 10. Testing

Use:

- unit tests for transformations;
- component tests for behavior;
- contract/API tests for data boundaries;
- limited browser tests for critical journeys;
- accessibility checks;
- visual regression selectively.

## 11. Frontend anti-patterns

- global state for every value;
- nested subscriptions;
- fetching in presentation primitives;
- client-side authorization as the only control;
- fixed sleeps in browser tests;
- div-based semantics;
- disabling type checks;
- giant page components;
- premature memoization;
- direct environment secrets in browser code.
