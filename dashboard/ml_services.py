"""
Safe exploratory machine-learning services for PlantLife365.

The maintained feature performs bounded regression analysis on a
user-supplied tabular dataset. It is not presented as a deployed
forecasting system or agronomic recommendation engine.
"""

import base64
import io
import math
import os
from pathlib import Path


ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}

SUPPORTED_MODELS = {
    "linear": "Linear Regression",
    "random_forest": "Random Forest",
    "gbm": "Gradient Boosting",
    "svr": "Support Vector Regression",
    "knn": "K-Nearest Neighbors",
}

DEFAULT_MAX_FILE_BYTES = 5_000_000
DEFAULT_MAX_ROWS = 50_000
DEFAULT_MAX_COLUMNS = 100
MAX_SELECTED_FEATURES = 20


class MLServiceError(ValueError):
    """Raised when an exploratory ML request is invalid."""


def _environment_int(name, default):
    try:
        value = int(
            os.environ.get(
                name,
                str(default),
            )
        )
    except ValueError:
        return default

    if value <= 0:
        return default

    return value


def _load_dependencies():
    """
    Load optional analytics packages lazily so the core Django project
    can still import without immediately importing the ML stack.
    """

    try:
        import matplotlib

        matplotlib.use("Agg")

        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd

        from sklearn.ensemble import (
            GradientBoostingRegressor,
            RandomForestRegressor,
        )
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import (
            mean_absolute_error,
            mean_squared_error,
            r2_score,
        )
        from sklearn.model_selection import train_test_split
        from sklearn.neighbors import KNeighborsRegressor
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVR

    except ImportError as exc:
        raise MLServiceError(
            "Optional ML dependencies are not installed."
        ) from exc

    return {
        "plt": plt,
        "np": np,
        "pd": pd,
        "GradientBoostingRegressor": GradientBoostingRegressor,
        "RandomForestRegressor": RandomForestRegressor,
        "LinearRegression": LinearRegression,
        "mean_absolute_error": mean_absolute_error,
        "mean_squared_error": mean_squared_error,
        "r2_score": r2_score,
        "train_test_split": train_test_split,
        "KNeighborsRegressor": KNeighborsRegressor,
        "Pipeline": Pipeline,
        "StandardScaler": StandardScaler,
        "SVR": SVR,
    }


def load_uploaded_dataset(upload):
    if upload is None:
        raise MLServiceError(
            "No data file was uploaded."
        )

    file_name = str(
        getattr(
            upload,
            "name",
            "",
        )
    )

    suffix = Path(
        file_name
    ).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise MLServiceError(
            "Only CSV, XLSX, and XLS files are supported."
        )

    max_bytes = _environment_int(
        "PLANTLIFE365_ML_MAX_FILE_BYTES",
        DEFAULT_MAX_FILE_BYTES,
    )

    upload_size = getattr(
        upload,
        "size",
        None,
    )

    if upload_size is not None:
        if upload_size > max_bytes:
            raise MLServiceError(
                f"Dataset exceeds the {max_bytes}-byte upload limit."
            )

    deps = _load_dependencies()
    pd = deps["pd"]

    try:
        upload.seek(0)

        if suffix == ".csv":
            df = pd.read_csv(upload)
        else:
            df = pd.read_excel(upload)

    except Exception as exc:
        raise MLServiceError(
            "The uploaded dataset could not be read."
        ) from exc

    max_rows = _environment_int(
        "PLANTLIFE365_ML_MAX_ROWS",
        DEFAULT_MAX_ROWS,
    )

    max_columns = _environment_int(
        "PLANTLIFE365_ML_MAX_COLUMNS",
        DEFAULT_MAX_COLUMNS,
    )

    if len(df.index) == 0:
        raise MLServiceError(
            "The uploaded dataset contains no rows."
        )

    if len(df.columns) == 0:
        raise MLServiceError(
            "The uploaded dataset contains no columns."
        )

    if len(df.index) > max_rows:
        raise MLServiceError(
            f"Dataset exceeds the {max_rows}-row analysis limit."
        )

    if len(df.columns) > max_columns:
        raise MLServiceError(
            f"Dataset exceeds the {max_columns}-column analysis limit."
        )

    return df


def validate_options(df, options):
    if not isinstance(options, dict):
        raise MLServiceError(
            "Analysis options must be a JSON object."
        )

    response = str(
        options.get(
            "response",
            "",
        )
    ).strip()

    features = options.get(
        "features",
        [],
    )

    models = options.get(
        "models",
        [],
    )

    if not response:
        raise MLServiceError(
            "A response variable is required."
        )

    if response not in df.columns:
        raise MLServiceError(
            "The selected response variable is not in the dataset."
        )

    if not isinstance(features, list):
        raise MLServiceError(
            "Features must be provided as a list."
        )

    clean_features = []

    for feature in features:
        feature_name = str(
            feature
        ).strip()

        if not feature_name:
            continue

        if feature_name == response:
            continue

        if feature_name not in df.columns:
            raise MLServiceError(
                f"Feature '{feature_name}' is not in the dataset."
            )

        if feature_name not in clean_features:
            clean_features.append(
                feature_name
            )

    if not clean_features:
        raise MLServiceError(
            "Select at least one feature different from the response."
        )

    if len(clean_features) > MAX_SELECTED_FEATURES:
        raise MLServiceError(
            f"Select at most {MAX_SELECTED_FEATURES} features."
        )

    if not isinstance(models, list):
        raise MLServiceError(
            "Models must be provided as a list."
        )

    clean_models = []

    for model_key in models:
        model_key = str(
            model_key
        ).strip()

        if model_key not in SUPPORTED_MODELS:
            continue

        if model_key not in clean_models:
            clean_models.append(
                model_key
            )

    if not clean_models:
        raise MLServiceError(
            "Select at least one supported regression model."
        )

    try:
        train_pct = int(
            options.get(
                "train_pct",
                80,
            )
        )
    except (TypeError, ValueError):
        raise MLServiceError(
            "Training percentage must be an integer."
        )

    if train_pct < 60 or train_pct > 90:
        raise MLServiceError(
            "Training percentage must be between 60 and 90."
        )

    try:
        random_seed = int(
            options.get(
                "random_seed",
                42,
            )
        )
    except (TypeError, ValueError):
        raise MLServiceError(
            "Random seed must be an integer."
        )

    if random_seed < 0 or random_seed > 2_147_483_647:
        raise MLServiceError(
            "Random seed is outside the accepted range."
        )

    return {
        "response": response,
        "features": clean_features,
        "models": clean_models,
        "train_pct": train_pct,
        "random_seed": random_seed,
    }


def prepare_numeric_dataset(
    df,
    response,
    features,
):
    deps = _load_dependencies()
    pd = deps["pd"]

    selected_columns = (
        list(features)
        + [response]
    )

    numeric = df[
        selected_columns
    ].copy()

    for column in selected_columns:
        numeric[column] = pd.to_numeric(
            numeric[column],
            errors="coerce",
        )

    original_rows = len(
        numeric.index
    )

    numeric = numeric.dropna()

    clean_rows = len(
        numeric.index
    )

    if clean_rows < 10:
        raise MLServiceError(
            "At least 10 complete numeric rows are required."
        )

    return (
        numeric,
        original_rows,
        clean_rows,
    )


def _build_model(
    model_key,
    seed,
    deps,
):
    if model_key == "linear":
        return deps["Pipeline"](
            [
                (
                    "scaler",
                    deps["StandardScaler"](),
                ),
                (
                    "model",
                    deps["LinearRegression"](),
                ),
            ]
        )

    if model_key == "random_forest":
        return deps["RandomForestRegressor"](
            n_estimators=200,
            random_state=seed,
            n_jobs=-1,
        )

    if model_key == "gbm":
        return deps["GradientBoostingRegressor"](
            n_estimators=150,
            random_state=seed,
        )

    if model_key == "svr":
        return deps["Pipeline"](
            [
                (
                    "scaler",
                    deps["StandardScaler"](),
                ),
                (
                    "model",
                    deps["SVR"](),
                ),
            ]
        )

    if model_key == "knn":
        return deps["Pipeline"](
            [
                (
                    "scaler",
                    deps["StandardScaler"](),
                ),
                (
                    "model",
                    deps["KNeighborsRegressor"](
                        n_neighbors=5
                    ),
                ),
            ]
        )

    raise MLServiceError(
        "Unsupported regression model."
    )


def _extract_feature_scores(
    estimator,
    features,
):
    model = estimator

    if hasattr(
        estimator,
        "named_steps",
    ):
        model = estimator.named_steps.get(
            "model",
            estimator,
        )

    values = None
    label = None

    if hasattr(
        model,
        "feature_importances_",
    ):
        values = model.feature_importances_
        label = "Feature importance"

    elif hasattr(
        model,
        "coef_",
    ):
        values = model.coef_
        label = "Coefficient"

    if values is None:
        return []

    try:
        flattened = list(
            values.ravel()
        )
    except AttributeError:
        flattened = list(
            values
        )

    scores = []

    for feature, value in zip(
        features,
        flattened,
    ):
        scores.append(
            {
                "feature": feature,
                "value": float(value),
                "label": label,
            }
        )

    scores.sort(
        key=lambda item: abs(
            item["value"]
        ),
        reverse=True,
    )

    return scores


def _prediction_plot(
    y_true,
    y_pred,
    model_name,
    deps,
):
    plt = deps["plt"]
    np = deps["np"]

    figure = plt.figure(
        figsize=(
            5.5,
            4.5,
        )
    )

    axis = figure.add_subplot(
        111
    )

    axis.scatter(
        y_true,
        y_pred,
        alpha=0.65,
        s=32,
    )

    low = float(
        min(
            np.min(y_true),
            np.min(y_pred),
        )
    )

    high = float(
        max(
            np.max(y_true),
            np.max(y_pred),
        )
    )

    if math.isclose(
        low,
        high,
    ):
        low = low - 1.0
        high = high + 1.0

    axis.plot(
        [low, high],
        [low, high],
        linestyle="--",
        linewidth=1.2,
    )

    axis.set_xlabel(
        "Actual"
    )

    axis.set_ylabel(
        "Predicted"
    )

    axis.set_title(
        f"{model_name}: Actual vs. Predicted"
    )

    axis.grid(
        True,
        alpha=0.25,
    )

    figure.tight_layout()

    buffer = io.BytesIO()

    figure.savefig(
        buffer,
        format="png",
        dpi=120,
        bbox_inches="tight",
    )

    plt.close(
        figure
    )

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode(
        "ascii"
    )

    return encoded


def run_regression_analysis(
    upload,
    options,
):
    deps = _load_dependencies()

    df = load_uploaded_dataset(
        upload
    )

    clean_options = validate_options(
        df,
        options,
    )

    response = clean_options["response"]
    features = clean_options["features"]
    models = clean_options["models"]
    train_pct = clean_options["train_pct"]
    seed = clean_options["random_seed"]

    numeric, original_rows, clean_rows = prepare_numeric_dataset(
        df,
        response,
        features,
    )

    X = numeric[
        features
    ].to_numpy()

    y = numeric[
        response
    ].to_numpy()

    test_fraction = (
        1.0
        - (
            train_pct
            / 100.0
        )
    )

    train_test_split = deps[
        "train_test_split"
    ]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_fraction,
        random_state=seed,
    )

    if len(y_test) < 2:
        raise MLServiceError(
            "The test partition must contain at least two rows."
        )

    results = []

    for model_key in models:
        display_name = SUPPORTED_MODELS[
            model_key
        ]

        estimator = _build_model(
            model_key,
            seed,
            deps,
        )

        try:
            estimator.fit(
                X_train,
                y_train,
            )

            predictions = estimator.predict(
                X_test
            )

            mae = deps[
                "mean_absolute_error"
            ](
                y_test,
                predictions,
            )

            mse = deps[
                "mean_squared_error"
            ](
                y_test,
                predictions,
            )

            rmse = math.sqrt(
                float(mse)
            )

            r2 = deps[
                "r2_score"
            ](
                y_test,
                predictions,
            )

            plot_b64 = _prediction_plot(
                y_test,
                predictions,
                display_name,
                deps,
            )

            feature_scores = _extract_feature_scores(
                estimator,
                features,
            )

            results.append(
                {
                    "key": model_key,
                    "name": display_name,
                    "mae": float(mae),
                    "rmse": float(rmse),
                    "r2": float(r2),
                    "plot_b64": plot_b64,
                    "feature_scores": feature_scores,
                    "error": None,
                }
            )

        except Exception as exc:
            results.append(
                {
                    "key": model_key,
                    "name": display_name,
                    "mae": None,
                    "rmse": None,
                    "r2": None,
                    "plot_b64": None,
                    "feature_scores": [],
                    "error": (
                        f"{exc.__class__.__name__}: "
                        f"{str(exc)}"
                    ),
                }
            )

    successful = [
        item
        for item in results
        if item["error"] is None
    ]

    failed = [
        item
        for item in results
        if item["error"] is not None
    ]

    successful.sort(
        key=lambda item: item["r2"],
        reverse=True,
    )

    ordered_results = successful + failed

    return {
        "response": response,
        "features": features,
        "train_pct": train_pct,
        "test_pct": 100 - train_pct,
        "random_seed": seed,
        "original_rows": original_rows,
        "clean_rows": clean_rows,
        "train_rows": len(y_train),
        "test_rows": len(y_test),
        "results": ordered_results,
    }
