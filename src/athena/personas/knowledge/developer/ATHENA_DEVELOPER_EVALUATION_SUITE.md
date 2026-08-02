# Athena Developer Persona Evaluation Suite

## 1. Goals

Measure whether the suite improves:

- routing accuracy;
- retrieval recall;
- context precision;
- token use;
- latency;
- answer usefulness;
- implementation correctness.

## 2. Dataset format

Each task should contain:

```yaml
id: spring-001
task: Add an authenticated paginated endpoint and Angular table.
expected_persona: spring-angular-developer
expected_files:
  - backend controller
  - backend service
  - repository/entity
  - Angular route/component
  - Angular API service
  - tests
forbidden_or_low_value:
  - unrelated deployment files
risk_tags: [authorization, pagination, persistence]
```

## 3. Minimum task set

Create at least:

- 15 frontend tasks;
- 15 backend tasks;
- 10 mobile tasks;
- 10 MERN tasks;
- 10 T3 tasks;
- 10 T4 tasks;
- 20 Spring/Angular tasks;
- 15 Python tasks;
- 10 cross-stack tasks.

## 4. Routing metrics

- exact persona accuracy;
- specialist-family accuracy;
- fallback rate;
- confidence calibration;
- confusion matrix.

Targets for a mature suite:

- specialist-family accuracy ≥ 90%;
- exact persona accuracy ≥ 85%;
- generic fallback on clearly classified tasks ≤ 5%.

## 5. Retrieval metrics

- expected-file recall@K;
- context precision;
- MRR for primary symbol;
- duplicate-token ratio;
- test-evidence recall;
- contract/data/config evidence recall.

Suggested targets:

- expected-file recall ≥ 90%;
- context precision ≥ 70%;
- duplicate source tokens < 3%;
- budget violations = 0.

## 6. Token profiles

Suggested budgets:

- focused/local change: 2,500–3,500;
- normal specialist task: 4,000–5,200;
- deep cross-stack design: 6,000–8,000 through an explicit profile, not default.

## 7. Quality evaluation

For each generated answer, score:

- evidence correctness;
- architecture consistency;
- contract completeness;
- security;
- test completeness;
- absence of invented files/symbols;
- implementation success;
- test pass rate.

## 8. Regression gates

A persona or router change must not merge when it causes:

- >3 percentage-point routing regression;
- >5 percentage-point expected-file recall regression;
- >10% median-token growth without quality gain;
- new budget violations;
- increased hallucinated file/symbol rate.

## 9. Real repository validation

Use representative repositories:

- large Java/Spring + Angular enterprise project;
- MERN app;
- T3 app;
- T4 universal app;
- Python API;
- React Native/Expo app.

Include both greenfield features and incident/debug tasks.
