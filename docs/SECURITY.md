# Security Boundary

PlantLife365 is currently a research/development system.

## Repository protections

The maintained repository excludes:

- runtime SQLite databases
- user-account records
- plaintext deployment credentials
- Wi-Fi credentials
- email credentials
- private runtime images
- workstation-specific paths
- arbitrary uploaded Python execution
- synthetic AI labels presented as genuine inference

## Server configuration

Django configuration is externalized through environment variables.

Real `.env` files are excluded from Git.

## ESP32 configuration

Device-specific values live in:

`firmware/esp32/config.py`

The real file is excluded from Git.

Only:

`firmware/esp32/config.example.py`

is committed.

## Device authentication

The historical application allowed telemetry submission using a known
active device ID without authenticating the physical sender.

The maintained Batch 3 implementation requires:

- an active `device_id`
- the corresponding per-device shared secret

The ESP32 sends the secret through:

`X-PlantLife365-Token`

New device secrets are stored using Django password hashing.

## Historical PIN migration

A private historical database may contain plaintext device PINs.

The maintained model supports plaintext comparison only for controlled
migration.

After successful verification, the historical PIN is upgraded to the
hashed representation.

No historical database is distributed by this repository.

## Input validation

The canonical telemetry endpoint validates:

- JSON structure
- device ID format
- finite numeric sensor values
- application-level sensor ranges
- JPEG MIME type
- JPEG structure
- maximum image size

## Removed historical endpoint

The historical standalone unauthenticated image-upload endpoint is not
part of the maintained application.

The canonical firmware sends telemetry and its optional JPEG through
the authenticated `/upload` endpoint.

## Future production hardening

A future internet-facing production deployment should consider:

- HTTPS/TLS
- rate limiting
- replay protection
- token rotation
- secret revocation
- certificate-based device identity
- secure provisioning
- reverse-proxy and firewall controls

These are future hardening opportunities rather than claims about the
current research prototype.
