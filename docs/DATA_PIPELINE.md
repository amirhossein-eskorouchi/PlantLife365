# PlantLife365 Data Pipeline

## Purpose

Batch 4 establishes a consistent data boundary for live monitoring,
historical visualization, daily statistics, CSV export, and dashboard
alerts.

The maintained rule is:

User -> Owned Active Devices -> Sensor Readings

A user-facing endpoint must not access telemetry belonging to another
user's hardware device.

## Telemetry storage

Each SensorReading stores:

- temperature
- humidity
- light
- water level
- gas
- device ID
- optional image
- timestamp

The device ID connects incoming telemetry to an active HardwareDevice.

## Live dashboard

The live sensor API returns the most recent reading across the
authenticated user's active devices.

The API no longer contains ad hoc machine-learning training logic.

Prediction fields remain null placeholders so the existing dashboard
interface stays compatible until the analytics layer is rebuilt in
Batch 5.

## Historical telemetry

Supported historical windows are:

- 1 hour
- 1 day
- 1 week

Historical responses are capped through uniform downsampling to prevent
unbounded chart payloads.

The newest point is retained after downsampling.

## Rolling statistics

The daily statistics API uses a rolling 24-hour window.

For each sensor, the database calculates:

- minimum
- average
- maximum

The response also reports the number of readings used.

## CSV export

CSV export is restricted to:

- the authenticated user
- active devices owned by that user
- one explicitly requested calendar date

The exported columns are:

- timestamp
- device ID
- temperature
- humidity
- water level
- light
- gas

No private database or raw development dataset is distributed.

## Alerts and logs

The historical SystemLog table was global.

Batch 4 introduces explicit log ownership.

A dashboard alert created by a user is associated with that user.
Reading, marking, deleting, or clearing logs is restricted to the
authenticated owner.

The historical delete-by-username API was removed because authorization
must not be inferred from arbitrary text inside a log message.

Legacy logs from a private historical database may have no owner.
Those records are not automatically exposed to users.

## Threshold alerts

The existing dashboard currently evaluates configurable thresholds in
the browser and submits generated alerts to the backend.

Batch 4 keeps that behavior but makes backend storage and mutation
user-scoped and validated.

A future server-side alert engine may be added separately if required.

## Machine learning boundary

Machine-learning forecasting is intentionally not implemented in the
Batch 4 live-data endpoint.

The former ad hoc live-model logic is separated from the core telemetry
pipeline.

Machine-learning analytics and prediction semantics are handled in
Batch 5.
