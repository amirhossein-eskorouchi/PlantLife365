# Initial Source Classification

This classification records the **initial audit state** before source
migration. It does not mean every listed file will ultimately be
published.

## A. Canonical-system candidates

These are the strongest candidates for the maintained PlantLife365
implementation and require file-by-file verification:

- `PlantLife365/`
- `dashboard/`
- `manage.py`
- `main.py`
- `requirements.txt`
- `Documentation/`

Expected role:

- Django web application
- device/user management
- environmental telemetry
- image ingestion
- dashboard/history
- analytics
- ESP32 communication

## B. Firmware candidates

Requires canonical-version selection:

- `Firmware/`
- ESP32 camera firmware generations
- Arduino sketches
- MicroPython firmware variants

Goal:

Retain one clearly supported firmware workflow and preserve only
scientifically/usefully relevant historical variants.

## C. Research-extension candidates

Review separately from the maintained application:

- IISE 2026 material
- Smart Delta Trap work
- Ultralytics/YOLO experiments
- offline monitoring
- MPCA/image-compression experiments
- related sensing experiments

These must not be described as maintained PlantLife365 capabilities
unless the final repository actually implements them.

## D. Historical deployment/reference material

Historical application generations may include:

- Dash prototypes
- Kivy prototypes
- OpenCV/IP-camera workflows
- earlier real-time monitoring servers
- workstation-specific launch scripts

These are provenance/reference material, not automatically maintained
source code.

## E. Private / prohibited repository material

The following must remain outside the maintained Git repository:

- `db.sqlite3`
- runtime SQLite databases
- user/account records
- device PINs/secrets
- Wi-Fi passwords
- email/application credentials
- raw runtime `media/`
- local logs
- caches
- `__pycache__/`
- `.pyc` files
- Windows `.lnk` shortcuts
- machine-specific local configuration
- complete raw research archives

## F. Important scientific-description boundaries

The historical material includes generic object-detection experiments.
Existing YOLO results must not be presented as a custom agricultural
pest detector unless the corresponding trained dataset/model and
evaluation actually support that statement.

Likewise, demonstration overlays or mock prediction outputs must not be
described as genuine AI inference.

Subscription-tier prototypes must not be described as a production
payment implementation unless a real payment workflow is present.

Final claims in the README will be tied directly to maintained source
code and reproducible evidence.

## G. Batch 6 research-reference disposition

Research-extension candidates from the historical archive are now
tracked under:

`research/historical_reference/`

and:

`research/inventory/research_extensions_inventory.csv`

These materials are historical/reference implementations only.

The following extension families are intentionally separated from the
canonical maintained application:

- Smart Delta Trap work
- YOLO/object-detection experiments
- offline-monitoring prototypes
- MPCA/image-compression experiments
- Jetson/edge deployment work
- historical Dash/Kivy interfaces
- IISE 2026 research material
- January 2026 historical generations

Binary artifacts, datasets, runtime state, credentials, and unsafe
historical files remain private-archive-only.
