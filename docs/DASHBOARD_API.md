# Dashboard Data APIs

All user-facing dashboard endpoints operate within the authenticated
user's device boundary.

## Live telemetry

Endpoint:

GET /api/data/

Purpose:

Return the newest telemetry available from the user's active devices.

Machine-learning prediction fields are currently null placeholders and
will be addressed in Batch 5.

## Historical telemetry

Endpoint:

GET /api/sensor-history/?period=1h

Supported period values:

- live
- 1h
- 1d
- 1w

Historical responses are bounded to approximately 100 points.

## Daily statistics

Endpoint:

GET /api/daily-stats/

The response contains rolling 24-hour minimum, average, and maximum
values for:

- temperature
- humidity
- water level
- light
- gas

## CSV export

Endpoint:

GET /api/export-csv/?date=YYYY-MM-DD

Only readings from active devices owned by the authenticated user are
included.

## Alerts

List alerts:

GET /api/logs/

Mark one alert as read:

POST /api/logs/read/<log_id>/

Delete one alert:

POST /api/logs/delete/<log_id>/

Delete all current-user alerts:

POST /api/logs/delete_all/

Create one dashboard alert:

POST /api/logs/create/

The create endpoint accepts:

- level
- message
- optional device_id

Accepted levels:

- INFO
- WARNING
- CRITICAL

Every log mutation is restricted to the authenticated owner.
