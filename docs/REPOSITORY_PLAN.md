# Repository Reconstruction Plan

PlantLife365 is being reconstructed from a mixed historical archive
containing maintained application code, firmware generations,
experiments, runtime files, and research prototypes.

The work is organized into eight accelerated batches.

## Batch 1 — Provenance + repository bootstrap

- preserve the original archive outside Git
- record source-archive integrity
- establish repository boundaries
- classify major source families
- create safe repository scaffolding

## Batch 2 — Security + canonical Django/ESP32 system

- identify canonical Django application
- identify canonical firmware
- remove credentials and local paths
- externalize configuration
- exclude private/runtime state
- establish clean application structure

## Batch 3 — IoT ingestion + device authentication

- document telemetry schema
- clean device registration
- authenticate device uploads
- validate sensor/image payloads
- improve error handling
- create simulated-device workflow

## Batch 4 — Dashboard + data pipeline

- historical sensor data
- live monitoring
- charts and statistics
- image monitoring
- exports
- logs
- threshold/alert behavior

## Batch 5 — Analytics + AI functionality

- modularize analytics
- clean preprocessing/regression workflows
- distinguish exploration from prediction
- clean local Ollama integration
- remove misleading demonstration AI output
- disable or isolate unsafe arbitrary-code execution

## Batch 6 — Research extensions

Evaluate and selectively preserve:

- smart delta-trap work
- YOLO/COCO experiments
- offline-monitoring prototypes
- MPCA/image-compression experiments
- earlier Dash/Kivy deployment generations

Historical experiments must remain clearly separated from maintained
product capabilities.

## Batch 7 — Reproducibility + tests + CI

- freeze actual environment
- installation procedure
- safe example/synthetic data
- device simulator
- Django/API tests
- analytics tests
- privacy/path validator
- GitHub Actions

## Batch 8 — Documentation + portfolio release audit

- professional README
- system architecture
- hardware/firmware documentation
- screenshots and diagrams
- limitations
- licensing
- citation metadata
- acknowledgments
- clean-environment validation
- GitHub description/topics
- final release audit
