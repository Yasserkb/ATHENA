# Semantic relationship fixture

This fixture contains two cross-language HTTP contracts:

- TypeScript client to Python/FastAPI `GET /users/{}`;
- Go client to Java/Spring `GET /health`.

It is intentionally small and deterministic so parser, contract-normalization, and incremental
derivation tests can assert exact graph relationships.
