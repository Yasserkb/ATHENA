# Mobile Engineering Playbook

## 1. Platform matrix

Document:

- Android versions;
- iOS versions;
- device classes;
- phone/tablet;
- orientation;
- network conditions;
- accessibility settings;
- locale/timezone.

## 2. Lifecycle

Handle:

- cold start;
- warm start;
- background;
- foreground;
- termination;
- interruption;
- process recreation;
- session expiration;
- app upgrade.

## 3. Offline and synchronization

Define:

- local source of truth;
- cache versus durable data;
- pending operations;
- conflict policy;
- retry;
- ordering;
- duplicate handling;
- reconciliation;
- stale-state UX.

## 4. Navigation and deep links

Protect:

- authenticated routes;
- invalid links;
- link replay;
- notification routing;
- back-stack behavior;
- cold-start navigation.

## 5. Permissions

Request permission at the point of value. Handle:

- denied;
- permanently denied;
- revoked;
- limited access;
- platform differences.

## 6. Local security

Use platform secure storage for sensitive tokens. Review:

- screenshots;
- clipboard;
- backups;
- rooted/jailbroken risk;
- certificate validation;
- logging;
- analytics payloads.

## 7. Performance

Measure:

- startup;
- frame rate;
- memory;
- leaks;
- battery;
- network;
- image/cache;
- JS/native bridge where relevant;
- bundle size.

## 8. Native and cross-platform boundaries

Share:

- domain logic;
- validation;
- API contracts;
- design tokens;
- portable components.

Keep platform-specific:

- permissions;
- lifecycle integrations;
- notifications;
- native UI behavior;
- system services.

## 9. Testing

Use:

- unit;
- component/widget;
- API contract;
- emulator/simulator;
- selected real-device;
- critical end-to-end;
- upgrade and offline scenarios.

## 10. Release

Define:

- signing;
- environment configuration;
- version/build number;
- migration of local data;
- staged rollout;
- crash/error monitoring;
- rollback/hotfix constraints;
- store review.
