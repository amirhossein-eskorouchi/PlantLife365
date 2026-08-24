# PlantLife365

[![PlantLife365 CI](https://github.com/amirhossein-eskorouchi/PlantLife365/actions/workflows/ci.yml/badge.svg)](https://github.com/amirhossein-eskorouchi/PlantLife365/actions/workflows/ci.yml)

**IoT-enabled agricultural monitoring and decision-support platform integrating ESP32 sensing, imaging, web dashboards, and analytics.**

PlantLife365 is a research-oriented full-stack monitoring platform connecting an ESP32-based sensing node with a Django web application. The maintained repository focuses on authenticated telemetry ingestion, user-scoped monitoring, historical visualization, data export, exploratory regression analytics, and an optional local AI assistant.

Historical research and prototype material is preserved separately so the repository documents the project's technical evolution without presenting experimental branches as active production functionality.

---

## System Overview

![PlantLife365 maintained architecture](assets/architecture.svg)

The maintained system has four primary layers:

1. **Edge sensing** — ESP32/MicroPython firmware acquires environmental measurements and optional imagery.
2. **Authenticated ingestion** — registered hardware devices authenticate before telemetry is accepted.
3. **Monitoring and data services** — Django provides current conditions, history, statistics, logs, and export while enforcing user ownership.
4. **Analytics and assistance** — bounded regression analytics and an optional local Ollama-compatible assistant extend the monitoring interface.

A detailed architectural description is available in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Maintained Capabilities

### ESP32 sensing and imaging

The maintained firmware entry point is `firmware/esp32/main.py`.

Private device configuration is externalized through `firmware/esp32/config.py`, which is excluded from Git.

A safe configuration template is provided at `firmware/esp32/config.example.py`.

### Authenticated telemetry ingestion

PlantLife365 does not treat a device identifier alone as sufficient authorization.

The maintained ingestion workflow uses a per-device secret. Server-side device secrets are protected at rest, and uploads are authenticated before telemetry is stored.

Incoming measurements are validated for required fields, numeric representation, finite values, and application-level ranges.

See [docs/DEVICE_API.md](docs/DEVICE_API.md).

### User-scoped monitoring

Data services restrict monitoring queries to devices associated with the authenticated user.

Maintained functionality includes:

- current sensor readings
- historical readings
- rolling and daily statistics
- date-based queries
- CSV export
- user-owned alerts and logs
- hardware registration and ownership

See [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) and [docs/DASHBOARD_API.md](docs/DASHBOARD_API.md).

### Exploratory regression analytics

PlantLife365 includes a bounded tabular regression workflow for research exploration.

Supported algorithms include:

- Linear Regression
- Random Forest Regression
- Gradient Boosting Regression
- Support Vector Regression
- K-Nearest Neighbors Regression

Reported outputs include:

- Mean Absolute Error
- Root Mean Squared Error
- R-squared
- actual-versus-predicted diagnostics
- model-specific descriptive feature scores when available

This functionality is presented as exploratory analysis, not as a validated agronomic forecasting or recommendation model.

See [docs/ML_ANALYTICS.md](docs/ML_ANALYTICS.md).

### Optional local AI assistant

The maintained application includes an optional Ollama-compatible assistant.

By default, the application allows loopback Ollama endpoints only.

The assistant receives a compact authenticated-user context containing current monitoring information and recent user-owned logs.

Generated responses are not treated as verified agronomic recommendations.

See [docs/AI_ASSISTANT.md](docs/AI_ASSISTANT.md).

---

## Repository Structure

    PlantLife365/
    ├── .github/
    │   ├── workflows/
    │   │   └── ci.yml
    │   └── dependabot.yml
    ├── PlantLife365/
    │   └── Django project configuration
    ├── dashboard/
    │   ├── migrations/
    │   ├── templates/
    │   ├── assistant_service.py
    │   ├── data_services.py
    │   ├── device_ingestion.py
    │   ├── ml_services.py
    │   ├── models.py
    │   ├── urls.py
    │   └── views.py
    ├── docs/
    ├── examples/
    ├── firmware/
    │   └── esp32/
    ├── research/
    │   ├── historical_reference/
    │   └── inventory/
    ├── scripts/
    ├── tests/
    ├── .env.example
    ├── .python-version
    ├── environment.yml
    ├── manage.py
    ├── pytest.ini
    ├── requirements.in
    ├── requirements.txt
    ├── requirements-dev.in
    ├── requirements-dev.txt
    └── requirements-lock.txt

See [docs/REPOSITORY_MAP.md](docs/REPOSITORY_MAP.md).

---

## Quick Start

Maintained environment:

- Python 3.11.15
- Django 5.2.17

Create an isolated environment:

    conda create --prefix .venv python=3.11 pip -y

Install dependencies:

    .\.venv\python.exe -m pip install --upgrade pip
    .\.venv\python.exe -m pip install -r requirements.txt
    .\.venv\python.exe -m pip install -r requirements-dev.txt

Create local configuration:

    Copy-Item .env.example .env

Create the local development database:

    .\.venv\python.exe manage.py migrate

Start Django:

    .\.venv\python.exe manage.py runserver

For the complete setup sequence, see [docs/QUICKSTART.md](docs/QUICKSTART.md).

---

## Validation

Run:

    powershell -ExecutionPolicy Bypass -File scripts/validate.ps1

Validation covers:

- Python source syntax
- dependency consistency
- Django system configuration
- migration consistency
- automated tests
- Git whitespace

The test suite covers device-secret handling, telemetry validation, authenticated ingestion, user data isolation, exploratory analytics, fixed-seed reproducibility, and local AI endpoint restrictions.

GitHub Actions executes the core validation workflow on pushes and pull requests involving `main`.

See [docs/VALIDATION.md](docs/VALIDATION.md).

---

## Reproducibility

PlantLife365 maintains several dependency records for different purposes:

- `requirements.in` — maintained runtime dependency ranges
- `requirements.txt` — exact top-level runtime versions
- `requirements-dev.in` — validation dependency ranges
- `requirements-dev.txt` — exact validation versions
- `requirements-lock.txt` — complete pip environment
- `environment.yml` — Conda-oriented reconstruction specification
- `.python-version` — maintained Python major/minor version

See [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

---

## Example Data

`examples/sample_sensor_regression.csv` is deliberately synthetic.

It exists only to exercise the software analytics workflow.

It is not field-collected agricultural data, a benchmark dataset, experimental evidence, or evidence of real-world predictive accuracy.

---

## Historical Research Extensions

The original development archive contains experimental directions associated with:

- Smart Delta Trap concepts
- YOLO and object-detection experiments
- offline monitoring
- MPCA and image-compression experiments
- Jetson and edge deployment
- earlier Dash and Kivy interfaces
- conference-era development branches

Selected reviewed source-level material is preserved under `research/historical_reference/`.

These files are historical/reference implementations only and are not automatically active PlantLife365 features.

The machine-readable historical inventory is stored at `research/inventory/research_extensions_inventory.csv`.

See [docs/RESEARCH_EXTENSIONS.md](docs/RESEARCH_EXTENSIONS.md) and [docs/HISTORICAL_REFERENCE_POLICY.md](docs/HISTORICAL_REFERENCE_POLICY.md).

---

## Important Research Boundaries

The maintained repository does not claim that PlantLife365 currently provides:

- a validated pest-detection model
- a validated agricultural forecasting model
- production payment processing
- secure arbitrary Python execution
- guaranteed agronomic recommendations from a language model

Historical prototypes related to these concepts are documented separately where appropriate.

See [docs/PROTOTYPE_FEATURES.md](docs/PROTOTYPE_FEATURES.md).

---

## Security and Privacy

The maintained repository includes safeguards that were not consistently present in historical prototypes:

- environment-based Django configuration
- ignored local secrets
- protected hardware-device secrets
- authenticated device uploads
- bounded telemetry validation
- user-scoped monitoring queries
- user-scoped logs
- disabled arbitrary server-side Python execution
- local-only AI endpoint policy by default
- ignored runtime database and media artifacts

PlantLife365 remains a research/development system rather than a hardened production deployment.

See [docs/SECURITY.md](docs/SECURITY.md) and [SECURITY.md](SECURITY.md).

---

## Historical Provenance

The canonical historical development archive is preserved outside this Git repository.

Recorded archive SHA-256:

    B5198A53ADA405E522835DFDA8594DDF6DBDEDA52A3F9B1C8F0B582F7FDEF638

The repository explicitly distinguishes among:

- original historical source
- sanitized maintained implementation
- historical reference implementations

---

## Documentation

| Topic | Document |
|---|---|
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Quick start | [docs/QUICKSTART.md](docs/QUICKSTART.md) |
| Device API | [docs/DEVICE_API.md](docs/DEVICE_API.md) |
| Dashboard API | [docs/DASHBOARD_API.md](docs/DASHBOARD_API.md) |
| Data pipeline | [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) |
| ML analytics | [docs/ML_ANALYTICS.md](docs/ML_ANALYTICS.md) |
| AI assistant | [docs/AI_ASSISTANT.md](docs/AI_ASSISTANT.md) |
| Reproducibility | [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) |
| Validation | [docs/VALIDATION.md](docs/VALIDATION.md) |
| Security | [docs/SECURITY.md](docs/SECURITY.md) |
| Prototype boundaries | [docs/PROTOTYPE_FEATURES.md](docs/PROTOTYPE_FEATURES.md) |
| Research extensions | [docs/RESEARCH_EXTENSIONS.md](docs/RESEARCH_EXTENSIONS.md) |
| Historical-reference policy | [docs/HISTORICAL_REFERENCE_POLICY.md](docs/HISTORICAL_REFERENCE_POLICY.md) |
| Repository map | [docs/REPOSITORY_MAP.md](docs/REPOSITORY_MAP.md) |
| Repository status | [docs/REPOSITORY_STATUS.md](docs/REPOSITORY_STATUS.md) |
| Final audit | [docs/FINAL_AUDIT.md](docs/FINAL_AUDIT.md) |

---

## Project Status

The maintained repository provides a reproducible research-software baseline for PlantLife365.

Physical ESP32 hardware integration and camera behavior still require hardware-specific validation and are not fully emulated by continuous integration.

Historical research extensions remain separated from the canonical runtime.

---

## License

No license file is currently included. Review licensing before public release or redistribution.
