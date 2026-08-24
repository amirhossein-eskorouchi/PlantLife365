# Security

PlantLife365 is a research/development software repository.

Detailed security boundaries and deployment limitations are documented in [docs/SECURITY.md](docs/SECURITY.md).

## Do Not Commit

Do not commit:

- `.env`
- `db.sqlite3`
- ESP32 `config.py`
- device secrets
- Wi-Fi credentials
- email credentials
- user databases
- private media
- workstation-specific configuration

## Reporting a Security Issue

For a private repository, report security concerns directly to the repository owner rather than opening a public issue containing credentials or exploit details.

## Production Deployment

The maintained repository should not be interpreted as a fully hardened internet-facing deployment.

Production deployment requires additional infrastructure-level controls described in `docs/SECURITY.md`.
