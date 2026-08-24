# Reproducibility

## Maintained environment

PlantLife365 uses an isolated repository-local Python environment:

`.venv/`

The environment is excluded from Git.

Canonical runtime:

- Python 3.11.15
- Django 5.2.17

The PlantLife365 environment is independent of other research
environments on the workstation.

The existing `tf` environment is not modified by this repository
setup.

## Historical dependency conflict

Historical development files contained conflicting Django references.

The maintained repository therefore defines a new explicit supported
environment instead of treating either historical dependency record as
canonical.

## Exact top-level application packages

- Django: 5.2.17
- django-cors-headers: 4.9.0
- djangorestframework: 3.18.0
- python-dotenv: 1.2.3
- Pillow: 12.3.0
- numpy: 2.4.6
- pandas: 2.3.3
- matplotlib: 3.11.1
- seaborn: 0.13.2
- scikit-learn: 1.9.0
- openpyxl: 3.1.5
- xlrd: 2.0.2
- requests: 2.34.2
- pyserial: 3.5

## Validation packages

- pytest: 8.4.2
- pytest-django: 4.14.0
- coverage: 7.15.4

## Dependency files

`requirements.in`

Maintained application dependency ranges.

`requirements.txt`

Exact top-level application versions from the validated Batch 7
environment.

`requirements-dev.in`

Validation dependency ranges.

`requirements-dev.txt`

Exact validation package versions.

`requirements-lock.txt`

Complete pip environment including transitive dependencies.

`environment.yml`

Conda-oriented reconstruction specification.

`.python-version`

Maintained Python major/minor declaration.

## Conda solver note

The workstation Conda installation may contain an incompatible
`conda-libmamba-solver` plugin.

The Batch 7 creation workflow therefore requests Conda's built-in
classic solver and disables external plugins only for the environment
creation command.

It does not change the user's global Conda configuration.

## Local validation

Run:

`powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`

Validation checks:

1. Python syntax
2. dependency consistency
3. Django system configuration
4. migration consistency
5. automated tests
6. Git whitespace

## Tests

Automated tests cover:

- device-secret hashing
- historical plaintext-secret migration
- telemetry payload validation
- sensor-range validation
- authenticated telemetry ingestion
- invalid telemetry authentication
- per-user telemetry isolation
- per-user rolling-statistics isolation
- per-user date-query isolation
- per-user system-log isolation
- exploratory regression execution
- fixed-seed regression reproducibility
- local AI-endpoint policy

## Temporary database boundary

The private historical PlantLife365 database is not migrated by this
validation process.

pytest-django may create a temporary test database during test
execution.

## Synthetic example data

`examples/sample_sensor_regression.csv` contains synthetic software
validation data.

It is not field-collected agricultural data and does not represent
real-world model performance.

## Continuous integration

GitHub Actions runs the maintained validation workflow for pushes and
pull requests involving `main`.

Environment freeze date:

`2026-08-24`
