# Exploratory ML Analytics

## Purpose

PlantLife365 includes a controlled exploratory regression tool for
user-supplied tabular datasets.

The feature is intended for research exploration and demonstration.

It is not described as:

- a deployed forecasting engine
- an agronomic recommendation model
- a validated crop-management model
- a production AutoML platform

## Supported input

Accepted formats:

- CSV
- XLSX
- XLS

Default safety limits:

- maximum upload size: 5 MB
- maximum rows: 50,000
- maximum columns: 100
- maximum selected features: 20

## Analysis workflow

The user selects:

- one response variable
- one or more feature variables
- training percentage
- random seed
- one or more supported regression algorithms

Selected columns are converted to numeric values.

Rows containing unusable values in selected variables are removed.

A reproducible train/test split is then created.

## Supported models

The maintained exploratory tool supports:

- Linear Regression
- Random Forest Regression
- Gradient Boosting Regression
- Support Vector Regression
- K-Nearest Neighbors Regression

Scaling is applied through scikit-learn pipelines where appropriate.

## Metrics

The report includes:

- Mean Absolute Error
- Root Mean Squared Error
- R-squared

RMSE is calculated as the square root of mean squared error.

## Diagnostic visualization

Each successfully fitted model receives an actual-versus-predicted
diagnostic plot.

Tree feature importance or linear coefficients may also be displayed
when available.

These quantities are descriptive model properties and are not causal
effects.

## Security boundary

The historical Custom Python Editor submitted arbitrary Python code to
the Django server and executed it with exec().

That feature is removed from the maintained repository.

The maintained interface performs only explicitly implemented analysis
operations in dashboard/ml_services.py.

## Reproducibility

Exact environment and package versions will be finalized during the
reproducibility batch.
