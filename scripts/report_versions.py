#!/usr/bin/env python3

"""
Report PlantLife365 reproducibility-critical package versions.
"""

import importlib.metadata
import platform
import sys


DISTRIBUTIONS = [
    "Django",
    "django-cors-headers",
    "djangorestframework",
    "python-dotenv",
    "Pillow",
    "numpy",
    "pandas",
    "matplotlib",
    "seaborn",
    "scikit-learn",
    "openpyxl",
    "xlrd",
    "requests",
    "pyserial",
    "pytest",
    "pytest-django",
    "coverage",
]


def main():
    print(
        "Python:",
        sys.version.split()[0],
    )

    print(
        "Platform:",
        platform.platform(),
    )

    for distribution in DISTRIBUTIONS:
        try:
            version = importlib.metadata.version(
                distribution
            )

        except importlib.metadata.PackageNotFoundError:
            version = "NOT INSTALLED"

        print(
            f"{distribution}: {version}"
        )


if __name__ == "__main__":
    main()
