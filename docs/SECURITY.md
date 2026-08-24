# Security Boundary

PlantLife365 is currently a research/development system.

## Removed from the maintained repository

The maintained source tree must not contain:

- runtime SQLite databases
- user accounts
- device secret values
- Wi-Fi credentials
- email credentials
- private runtime images
- workstation-specific paths
- arbitrary executable uploaded Python code
- synthetic AI labels presented as real inference

## Local configuration

Use `.env` for Django/server settings and `firmware/esp32/config.py`
for device-specific ESP32 configuration.

Both are ignored by Git.

## Current limitation

The historical `/upload` telemetry interface identifies devices by
`device_id`, but authenticated per-device telemetry is not yet
implemented.

That is the primary security task for Batch 3.

Until then, the current ingestion interface should be treated as a
local research/development interface rather than a hardened
internet-facing API.
