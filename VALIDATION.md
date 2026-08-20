# Release Validation

Athena `0.2.0` is a public beta intended for local, single-user repository intelligence. It is not
an authenticated multi-tenant service. The following gates define a releasable build.

## Automated gates

- Ruff lint and format checks pass for `src`, `tests`, and `scripts`.
- Strict mypy passes for `src/athena`.
- Tests pass on Python 3.11, 3.12, and 3.13 with at least 80% branch-aware coverage.
- Persona and generated-adapter checks pass.
- The representative benchmark meets every threshold in `benchmarks/representative.yaml`.
- The Python wheel and source distribution build successfully.
- The container runs as UID/GID `10001:10001`, passes CLI, scan, daemon, and health checks, and is
  built for Linux AMD64 and ARM64.
- Container scans report all findings and block fixable critical vulnerabilities.
- Published images include an SBOM, provenance, immutable digest, and keyless signature.

## Manual release checklist

1. Confirm `CHANGELOG.md`, package metadata, CLI output, Docker labels, and the Git tag agree.
2. Confirm all GitHub Actions jobs are green on the release commit.
3. Review the complete vulnerability report and document accepted unfixed base-image risk.
4. Confirm the public tree and history contain no secrets, local state, or private source content.
5. Verify installation and first-run instructions on a clean Windows and Linux environment.
6. Publish a non-prerelease GitHub Release and verify the Docker Hub digest and signature.

## Current evidence

The launch audit on 2026-08-20 passed 123 tests at 82.6% branch-aware coverage and the expanded
ten-case representative benchmark gate with 100% routing accuracy, 100% recall, zero forbidden hits,
and 0.432 file precision. These metrics are regression gates, not a guarantee for every language or
repository.
