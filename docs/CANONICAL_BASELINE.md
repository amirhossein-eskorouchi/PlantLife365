# Canonical Baseline

## Purpose

Batch 2 establishes the first maintained PlantLife365 application
baseline from the historical AgricultureMonitoring archive.

No historical directory was copied wholesale into Git.

## Canonical source mapping

The initial maintained application is derived from:

| Historical source | Maintained location | Role |
| --- | --- | --- |
| `PlantLife365/` | `PlantLife365/` | Django project configuration |
| `dashboard/` | `dashboard/` | Core Django application |
| `manage.py` | `manage.py` | Django command entry point |
| root `main.py` | `firmware/esp32/main.py` | ESP32/MicroPython telemetry firmware |

The following were intentionally **not** imported in Batch 2:

- `db.sqlite3`
- `media/`
- cache/bytecode files
- deployment prototypes
- Smart Delta Trap experiments
- Ultralytics training outputs
- IISE 2026 research experiments
- January 2026 historical generations
- Jetson migration work
- Windows launch artifacts
- raw detection logs
- firmware binaries
- Arduino library archives

Those remain available in the private historical baseline.

## Security changes applied during migration

The maintained baseline differs intentionally from the raw historical
application in several safety-critical ways:

1. Django `SECRET_KEY`, debug mode, and allowed hosts are environment
   driven.
2. ESP32 deployment credentials are moved to an ignored device-local
   `config.py`.
3. workstation-specific reference-dataset paths are removed.
4. the demonstration image overlay that displayed synthetic AI
   detection labels is removed.
5. arbitrary server-side execution of uploaded Python code is disabled.
6. Ollama endpoint/model selection is configurable through environment
   variables.
7. the historical synthetic reference-dataset demonstration is disabled
   until it can be represented reproducibly and accurately.

## Known deferred items

These are **not considered finished in Batch 2**:

- telemetry authentication
- secure treatment of device credentials
- input validation/rate limiting
- analytics modularization
- subscription prototype cleanup
- ML prediction semantics
- environment/version freeze
- production deployment security
- automated tests

These belong to later reconstruction batches.

## Dependency-status warning

The historical `requirements.txt` specifies:

`Django>=4.2,<5.0`

while the recovered Django project header states that it was generated
using Django 6.0.1.

Because those records conflict, Batch 2 preserves the historical
requirements under:

`docs/provenance/historical_requirements.txt`

but does not silently declare either version canonical.

The executable environment will be resolved and frozen during the
reproducibility batch.
