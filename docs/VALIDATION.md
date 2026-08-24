# Validation

PlantLife365 uses layered automated validation.

## Python source validation

`scripts/check_syntax.py`

compiles maintained Python source in memory.

The script does not intentionally create `.pyc` files.

## Dependency consistency

Validation runs:

`python -m pip check`

to detect incompatible installed packages.

## Django system validation

Validation runs:

`python manage.py check`

to inspect the Django application configuration.

## Migration consistency

Validation runs:

`python manage.py makemigrations --check --dry-run`

to verify that maintained models agree with committed migrations.

The private historical database is not migrated.

## Automated tests

pytest and pytest-django validate:

- device-secret hashing
- legacy plaintext-secret migration
- telemetry validation
- telemetry authentication
- sensor storage
- user-specific telemetry access
- user-specific statistics
- user-specific date queries
- user-specific logs
- exploratory ML execution
- fixed-seed ML reproducibility
- local AI-assistant endpoint restrictions

pytest-django may create a temporary test database.

## Hardware boundary

Automated tests do not emulate the complete physical ESP32 sensor and
camera stack.

Physical hardware validation remains a separate integration activity.

## Local validation

Run:

`powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`

## Continuous integration

`.github/workflows/ci.yml`

runs the core repository checks through GitHub Actions.
