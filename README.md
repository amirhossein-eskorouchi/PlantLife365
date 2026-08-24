# PlantLife365

**PlantLife365** is an IoT-enabled agricultural monitoring and
decision-support platform that integrates ESP32-based sensing, imaging,
a Django web application, historical environmental monitoring, data
visualization, and exploratory analytics.

> **Repository status:** private reconstruction in progress. The
> historical research archive is being audited before canonical source
> files are migrated into the maintained repository.

## Intended maintained scope

The repository is being organized around the following core system:

- ESP32 environmental sensing and image acquisition
- device-to-server telemetry
- Django-based device and user management
- temperature, humidity, light, water, and gas measurements
- historical sensor visualization
- daily descriptive statistics
- CSV export
- camera/image monitoring
- analytics and machine-learning utilities
- local AI-assisted interaction
- reproducible local deployment

## Research extensions

Historical development material also contains research and prototype
extensions involving:

- smart agricultural monitoring
- computer-vision experiments
- smart delta-trap concepts
- offline monitoring
- edge/image-compression experiments
- alternative deployment architectures

These extensions are being evaluated separately and will not be
presented as production capabilities unless supported by the maintained
implementation.

## Repository boundaries

The public-facing source repository will **not** contain:

- the original SQLite runtime database
- user/account information
- device secrets or Wi-Fi credentials
- private runtime media
- workstation-specific configuration
- raw logs
- cache files
- the complete historical development archive

The untouched source archive is preserved separately for provenance.

## Development status

Repository reconstruction is being performed in controlled batches:

1. provenance and repository bootstrap
2. security and canonical Django/ESP32 system
3. IoT ingestion and device authentication
4. dashboard and data pipeline
5. analytics and AI functionality
6. research extensions
7. reproducibility, testing, and CI
8. documentation, visual portfolio, and release audit

Canonical application source code will be added only after the
provenance and security review is complete.
