# Research Extensions

This directory preserves selected historical research and prototype
source files from the PlantLife365 development archive.

## Critical boundary

The maintained PlantLife365 application consists primarily of the
sanitized Django application, authenticated ESP32 telemetry workflow,
dashboard/data pipeline, exploratory analytics service, and optional
local AI assistant.

Files under:

`research/historical_reference/`

are **historical/reference implementations**.

They are not automatically:

- maintained application features
- production-ready modules
- validated research results
- active deployment components
- current firmware
- current computer-vision models

## Why preserve them?

The original development archive contains multiple exploratory branches
and research directions.

Selected source files are retained here so the repository documents the
technical evolution of the project without mixing experimental code
into the maintained runtime application.

## Extension families

Batch 6 searches the historical archive for material related to:

- Smart Delta Trap concepts
- YOLO / object-detection experiments
- offline monitoring
- MPCA / image-compression work
- Jetson / edge deployment
- historical Dash / Kivy / monitoring interfaces
- IISE 2026 research material
- January 2026 historical generations

## Safety policy

Historical files are copied only when they pass a conservative source
audit.

The repository does not import historical:

- databases
- runtime media
- model weights
- trained checkpoints
- binary firmware
- archives
- datasets
- generated runs
- workstation-specific source files
- files containing obvious embedded secrets

Files excluded by this audit remain preserved in the private historical
archive.

## Inventory

The machine-readable discovery record is:

`research/inventory/research_extensions_inventory.csv`

Each discovered file records:

- category
- historical relative path
- extension
- file size
- SHA-256
- disposition
- copied reference location, when applicable

## Provenance

The immutable historical baseline remains outside this Git repository.

Its archive SHA-256 is:

`B5198A53ADA405E522835DFDA8594DDF6DBDEDA52A3F9B1C8F0B582F7FDEF638`

No historical source file should be treated as canonical merely because
it appears in this reference area.
## Public-release sanitization

Before the first public release, reviewed historical source references
were scanned for workstation-specific paths.

Five historical files contained a private Linux document root. That
root was replaced with the portable placeholder `PROJECT_ROOT`. No
maintained runtime behavior was changed.

The transformation is recorded in:

`research/inventory/historical_sanitization_manifest.csv`

The manifest preserves both the original archive-derived SHA-256 and
the sanitized public-file SHA-256 for each transformed historical
reference.

The original unsanitized files remain available only in the immutable
private source archive identified in `docs/PROVENANCE.md`.
