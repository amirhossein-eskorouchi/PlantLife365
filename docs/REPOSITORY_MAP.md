# Repository Map

## `PlantLife365/`

Django project configuration.

Important files:

- `settings.py`
- `urls.py`
- `asgi.py`
- `wsgi.py`

---

## `dashboard/`

Primary maintained Django application.

Important files:

- `models.py`
- `views.py`
- `urls.py`
- `device_ingestion.py`
- `data_services.py`
- `ml_services.py`
- `assistant_service.py`

`dashboard/migrations/` contains maintained schema history.

`dashboard/templates/` contains the Django interface.

---

## `firmware/esp32/`

Maintained ESP32/MicroPython telemetry implementation.

`main.py` is the firmware entry point.

`config.example.py` is a safe configuration template.

`config.py` is local/private and excluded from Git.

---

## Reproducibility Files

`requirements.in` defines runtime dependency ranges.

`requirements.txt` records exact top-level runtime versions.

`requirements-dev.in` defines validation dependency ranges.

`requirements-dev.txt` records exact validation-tool versions.

`requirements-lock.txt` records the complete pip environment.

`environment.yml` provides a Conda-oriented reconstruction path.

`.python-version` records the maintained Python major/minor version.

---

## Validation

`tests/` contains automated tests.

`pytest.ini` configures pytest.

`scripts/check_syntax.py` performs in-memory source validation.

`scripts/report_versions.py` reports environment versions.

`scripts/validate.ps1` performs local repository validation.

`.github/workflows/ci.yml` defines GitHub Actions CI.

`.github/dependabot.yml` defines dependency-update checks.

---

## Examples

`examples/sample_sensor_regression.csv` contains synthetic regression data for software demonstration.

It is not field-collected agricultural evidence.

---

## Documentation

`docs/ARCHITECTURE.md` — maintained architecture.

`docs/QUICKSTART.md` — setup and execution.

`docs/DEVICE_API.md` — ESP32 telemetry contract.

`docs/DATA_PIPELINE.md` — monitoring data flow.

`docs/DASHBOARD_API.md` — dashboard/API behavior.

`docs/ML_ANALYTICS.md` — exploratory regression implementation.

`docs/AI_ASSISTANT.md` — optional local AI assistant.

`docs/SECURITY.md` — security boundaries.

`docs/VALIDATION.md` — validation strategy.

`docs/REPRODUCIBILITY.md` — environment reconstruction.

`docs/PROTOTYPE_FEATURES.md` — prototype boundaries.

`docs/RESEARCH_EXTENSIONS.md` — historical research extensions.

`docs/HISTORICAL_REFERENCE_POLICY.md` — historical-reference policy.

`docs/REPOSITORY_STATUS.md` — current repository status.

`docs/FINAL_AUDIT.md` — final repository audit.

---

## Historical Research Material

`research/historical_reference/` contains selected source-only historical implementations.

These files are not the canonical runtime.

`research/inventory/research_extensions_inventory.csv` records historical provenance and disposition.

---

## Assets

`assets/architecture.svg` contains the maintained architecture figure.

`assets/README.md` documents the asset policy.
