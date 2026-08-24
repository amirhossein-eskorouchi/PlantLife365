# Research Extensions and Historical Implementations

## Batch 6 purpose

The original PlantLife365 development archive contains multiple
experimental and historical branches beyond the maintained
Django/ESP32 application.

Batch 6 preserves the technical history without allowing those
experiments to become ambiguous production claims.

## Historical archive

Immutable source archive:

`AgricultureMonitoring-aitools (1).zip`

SHA-256:

`B5198A53ADA405E522835DFDA8594DDF6DBDEDA52A3F9B1C8F0B582F7FDEF638`

The source archive remains outside Git.

## Discovery results

Total historical files scanned:

`209`

Research-extension candidate files:

`92`

Historical source references copied after safety review:

`44`

## Categories

- Smart Delta Trap: 7 candidates, 6 safe source references copied
- YOLO and Computer Vision Experiments: 27 candidates, 1 safe source references copied
- Offline Monitoring Prototypes: 3 candidates, 3 safe source references copied
- MPCA and Image Compression Experiments: 1 candidates, 1 safe source references copied
- Jetson and Edge Deployment Work: 1 candidates, 1 safe source references copied
- Historical Dash, Kivy, and UI Deployments: 0 candidates, 0 safe source references copied
- IISE 2026 Research Material: 12 candidates, 10 safe source references copied
- January 2026 Historical Generation: 41 candidates, 22 safe source references copied

## Reference-only policy

Material under:

`research/historical_reference/`

is historical/reference code.

It does not redefine the canonical PlantLife365 system.

Canonical maintained application functionality remains in the primary
Django, firmware, dashboard, analytics, and supporting service
directories.

## Computer-vision boundary

Historical YOLO or object-detection code is preserved only as research
evidence when safe to do so.

The repository must not claim that PlantLife365 currently includes a
validated agricultural pest detector unless the corresponding:

- task-specific dataset
- trained model
- evaluation protocol
- performance evidence
- reproducible inference pipeline

are present and documented.

Generic object-detection experiments alone are insufficient to make
that claim.

## Smart Delta Trap boundary

Historical Smart Delta Trap material may represent a research direction,
prototype, or integration experiment.

Its presence in the reference archive does not mean the feature is part
of the maintained PlantLife365 deployment.

## Offline-monitoring boundary

Historical offline or standalone monitoring implementations are
preserved for architecture/provenance purposes.

They are not necessarily compatible with the current authenticated
Django/ESP32 pipeline.

## MPCA and compression boundary

Historical MPCA, tensor, or image-compression experiments are preserved
as research extensions.

Their inclusion does not establish a production compression layer or
validated bandwidth-reduction claim in the maintained platform.

## Jetson / edge boundary

Historical Jetson and edge-deployment material is retained separately
from the canonical ESP32 firmware path.

Model binaries, deployment artifacts, generated engines, and private
runtime configuration remain excluded.

## Historical UI boundary

Earlier Dash, Kivy, OpenCV, IP-camera, or standalone-monitoring
interfaces may illustrate the project's development history.

They are not presented as current user interfaces unless explicitly
maintained elsewhere in the repository.

## Safety filtering

Historical candidates were excluded from Git when they were:

- runtime databases
- data directories
- logs
- generated runs
- model weights
- binary artifacts
- archives
- media files
- unsupported file types
- larger than the conservative source-reference limit
- unreadable as source text
- detected to contain obvious private configuration

The full original files remain available only in the private historical
archive.

## Machine-readable inventory

See:

`research/inventory/research_extensions_inventory.csv`

This inventory records the SHA-256 and disposition of every research
candidate discovered during Batch 6.
