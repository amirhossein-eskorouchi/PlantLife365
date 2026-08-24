# Examples

## Synthetic regression dataset

`sample_sensor_regression.csv` contains deliberately synthetic values
created for software demonstration and automated validation.

It is not:

- field-collected PlantLife365 telemetry
- experimental agricultural evidence
- a scientific benchmark dataset
- evidence of real-world prediction performance

Columns:

- temperature
- humidity
- light
- water_level
- gas
- target

The target is generated deterministically from the synthetic inputs.

The file allows the exploratory regression workflow to be exercised
without distributing private historical datasets.
