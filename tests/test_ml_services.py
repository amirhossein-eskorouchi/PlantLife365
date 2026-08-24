import math

from django.core.files.uploadedfile import SimpleUploadedFile

from dashboard.ml_services import run_regression_analysis


def sample_csv():
    lines = [
        "temperature,humidity,light,target"
    ]

    for index in range(
        1,
        31,
    ):
        temperature = (
            18
            + index * 0.4
        )

        humidity = (
            40
            + index * 0.7
        )

        light = (
            30
            + index * 1.2
        )

        target = (
            0.6 * temperature
            + 0.2 * humidity
            + 0.1 * light
        )

        lines.append(
            (
                f"{temperature:.3f},"
                f"{humidity:.3f},"
                f"{light:.3f},"
                f"{target:.3f}"
            )
        )

    return (
        "\n".join(
            lines
        )
        + "\n"
    ).encode(
        "utf-8"
    )


def test_linear_regression_analysis_runs():
    upload = SimpleUploadedFile(
        "synthetic_sensor_data.csv",
        sample_csv(),
        content_type="text/csv",
    )

    result = run_regression_analysis(
        upload,
        {
            "response": "target",
            "features": [
                "temperature",
                "humidity",
                "light",
            ],
            "models": [
                "linear",
            ],
            "train_pct": 80,
            "random_seed": 42,
        },
    )

    assert result["response"] == "target"

    assert result["clean_rows"] == 30

    assert result["train_rows"] > 0

    assert result["test_rows"] > 0

    assert len(
        result["results"]
    ) == 1

    model_result = result[
        "results"
    ][0]

    assert model_result[
        "error"
    ] is None

    assert model_result[
        "mae"
    ] >= 0

    assert model_result[
        "rmse"
    ] >= 0

    assert model_result[
        "plot_b64"
    ]


def test_random_forest_is_reproducible_for_fixed_seed():
    first_upload = SimpleUploadedFile(
        "sample1.csv",
        sample_csv(),
        content_type="text/csv",
    )

    second_upload = SimpleUploadedFile(
        "sample2.csv",
        sample_csv(),
        content_type="text/csv",
    )

    options = {
        "response": "target",
        "features": [
            "temperature",
            "humidity",
            "light",
        ],
        "models": [
            "random_forest",
        ],
        "train_pct": 80,
        "random_seed": 42,
    }

    first = run_regression_analysis(
        first_upload,
        options,
    )

    second = run_regression_analysis(
        second_upload,
        options,
    )

    first_result = first[
        "results"
    ][0]

    second_result = second[
        "results"
    ][0]

    assert first_result[
        "error"
    ] is None

    assert second_result[
        "error"
    ] is None

    assert math.isclose(
        first_result["mae"],
        second_result["mae"],
        rel_tol=1e-12,
        abs_tol=1e-12,
    )

    assert math.isclose(
        first_result["rmse"],
        second_result["rmse"],
        rel_tol=1e-12,
        abs_tol=1e-12,
    )

    assert math.isclose(
        first_result["r2"],
        second_result["r2"],
        rel_tol=1e-12,
        abs_tol=1e-12,
    )
