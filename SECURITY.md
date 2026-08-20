# Security Policy

## Supported versions

Athena CodeGraph is pre-1.0 software. Security fixes are provided for the latest `0.2.x` release
and the `main` branch. Older snapshots are not supported.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's **Report a vulnerability**
button on the repository Security page to submit a private security advisory. Include affected
versions, reproduction steps, impact, and any suggested mitigation.

Maintainers will acknowledge a complete report within seven days, validate severity, coordinate a
fix and disclosure, and credit reporters who request attribution. Never include credentials,
private repository contents, or personal information in a report.

## Scope and operating assumptions

Athena is local-first and its MCP transport is STDIO. The Observatory binds to loopback by default
and has no authentication layer; do not expose it to an untrusted network. Repository contents are
untrusted input. Secret redaction is defense in depth and is not a substitute for keeping secrets
out of source control or using a dedicated secret scanner.

Container releases include provenance and an SBOM. CI reports all known image vulnerabilities and
blocks release when a critical vulnerability with an available fix remains unapplied.
