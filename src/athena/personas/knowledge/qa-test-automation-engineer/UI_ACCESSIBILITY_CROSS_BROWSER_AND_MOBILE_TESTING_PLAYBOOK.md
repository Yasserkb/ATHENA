# UI, Accessibility, Cross-Browser, and Mobile Testing Playbook

## 1. UI risk areas

Test:

- critical journeys;
- navigation;
- form validation;
- state;
- error recovery;
- permissions;
- responsive behavior;
- accessibility;
- localization;
- browser compatibility.

---

## 2. Automation scope

Automate:

- stable critical flows;
- high-value regression;
- deterministic behavior.

Use exploratory testing for:

- usability;
- visual coherence;
- unexpected interaction;
- new workflows.

---

## 3. Selectors

Prefer:

- semantic role;
- accessible name;
- stable test ID when necessary.

Avoid:

- generated CSS;
- brittle XPath;
- text that changes frequently.

---

## 4. Synchronization

Wait for:

- element state;
- network state;
- application event;
- route;
- observable completion.

Do not use fixed sleeps.

---

## 5. Accessibility

Review:

- keyboard;
- focus;
- semantics;
- labels;
- contrast;
- screen reader;
- error messages;
- zoom;
- motion.

Automated accessibility checks are necessary but not sufficient.

---

## 6. Cross-browser

Select browsers from:

- user analytics;
- product support;
- risk.

Do not test every browser version blindly.

---

## 7. Visual testing

Use visual regression for:

- stable components;
- design system;
- critical layout.

Control:

- viewport;
- font;
- animation;
- data;
- time.

---

## 8. Mobile

Cover:

- OS versions;
- device sizes;
- permissions;
- offline;
- poor network;
- interruption;
- background/foreground;
- upgrade;
- deep links;
- push notifications;
- battery;
- orientation.

---

## 9. Mobile automation

Balance:

- unit;
- component;
- API;
- emulator/simulator;
- real device.

Real devices remain important for hardware and OS behavior.

---

## 10. Anti-patterns

- automating every UI detail;
- ignoring accessibility;
- one browser only without evidence;
- emulator-only confidence;
- fixed sleeps;
- shared user state;
- visual baseline approved blindly.
