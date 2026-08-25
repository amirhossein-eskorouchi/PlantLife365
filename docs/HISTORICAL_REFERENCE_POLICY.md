# Historical Reference Policy

## Purpose

Historical code is retained only when it provides useful evidence of:

- prototype evolution
- research exploration
- alternative architectures
- earlier deployment strategies
- experimental analysis workflows

## Canonical versus historical

A historical file is not canonical.

Canonical source must be:

- intentionally maintained
- documented as part of the current system
- safe for the repository
- consistent with the current architecture
- testable or otherwise reproducible where applicable

Historical-reference source may instead be incomplete, superseded, or
experiment-specific.

## Allowed reference material

Examples of source material that may be retained:

- Python scripts
- notebooks
- Arduino / ESP32 source
- configuration examples without credentials
- Markdown documentation
- safe experiment metadata
- source-level HTML/JavaScript/CSS

## Excluded reference material

Do not publish historical:

- runtime SQLite databases
- user records
- credentials
- Wi-Fi passwords
- API keys
- email passwords
- device secrets
- private media
- large datasets
- model weights
- trained checkpoints
- generated inference runs
- binary firmware
- workstation-specific launch artifacts
- raw archives

## Claims

Historical reference code may support statements such as:

"An object-detection experiment was explored."

It does not by itself support statements such as:

"PlantLife365 provides a validated pest-detection model."

Claims must match the actual maintained implementation and available
evaluation evidence.
## Workstation-path sanitization

Historical source references selected for public preservation must not
expose private account identifiers or workstation-specific project
roots.

When such a path is present, the public historical copy may replace
only the private root with a descriptive portable placeholder. Each
transformation must preserve:

- the public destination;
- the original archive-derived SHA-256;
- the sanitized public SHA-256;
- the number and type of replacements; and
- the historical-reference disposition.

PlantLife365 records these transformations in
`research/inventory/historical_sanitization_manifest.csv`.

This sanitization does not convert historical reference code into
maintained application code.
