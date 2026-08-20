# Changelog

This project follows [Semantic Versioning](https://semver.org/). Because Athena is pre-1.0, minor
releases may include documented interface changes.

## [Unreleased]

## [0.2.0] - 2026-08-20

### Added

- Economy-mode repository context and bounded clarification.
- Persistent native watcher with polling fallback and repository-scoped incremental Git scans.
- Multi-repository Observatory, benchmark gates, container health checks, SBOM, and provenance.
- Public contribution, validation, conduct, and security policies.
- Guarded `athena sync` workflow with upstream verification.

### Changed

- Expanded specialist persona routing and representative regression coverage.
- Hardened Docker publishing, base-image maintenance, vulnerability reporting, and local-state
  exclusions.
- Synchronized package, CLI, container, Compose, and release version metadata.

### Security

- Containers run as a non-root user with a read-only filesystem, dropped capabilities, bounded
  resources, and no network for the repository daemon.
- Local assistant settings, runtime databases, environment files, and credentials are excluded from
  Git and Docker build contexts.

[Unreleased]: https://github.com/Yasserkb/ATHENA/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Yasserkb/ATHENA/releases/tag/v0.2.0
