# Repository Status

## Maintained Baseline

PlantLife365 has completed the accelerated repository reconstruction workflow.

Current maintained layers include:

- ESP32/MicroPython firmware
- authenticated telemetry ingestion
- Django device and user management
- user-scoped sensor access
- user-scoped system logs
- monitoring dashboard
- historical visualization
- statistics
- CSV export
- exploratory regression analytics
- optional local AI assistant
- automated testing
- continuous integration
- historical-reference preservation

## Reproducibility Baseline

Python:

`3.11.15`

Django:

`5.2.17`

Dependency definitions:

- `requirements.in`
- `requirements.txt`
- `requirements-dev.in`
- `requirements-dev.txt`
- `requirements-lock.txt`
- `environment.yml`

## Repository Boundaries

The following are intentionally excluded:

- private historical database
- private runtime media
- local `.env`
- ESP32 private configuration
- user credentials
- unrelated historical model weights
- raw development archives

## Historical Extensions

Experimental Smart Delta Trap, computer-vision, MPCA/compression, offline-monitoring, edge-deployment, and historical UI material is tracked separately as reference source where safe.

## Remaining Physical Validation

Automated CI cannot fully replace validation involving:

- physical sensors
- ESP32 networking
- ESP32 camera hardware
- hardware-specific serial interfaces
- field-deployment conditions

These remain physical integration-validation activities.
