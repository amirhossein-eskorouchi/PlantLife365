#!/usr/bin/env python3

"""
Compile maintained PlantLife365 Python files in memory.

No .pyc files are intentionally written.
"""

from pathlib import Path


ROOTS = [
    Path("PlantLife365"),
    Path("dashboard"),
    Path("scripts"),
    Path("tests"),
]


def main():
    python_files = []

    for root in ROOTS:
        if not root.exists():
            continue

        python_files.extend(
            path
            for path in root.rglob("*.py")
            if "__pycache__" not in path.parts
        )

    failures = []

    for path in sorted(
        python_files
    ):
        try:
            source = path.read_text(
                encoding="utf-8"
            )

            compile(
                source,
                str(path),
                "exec",
            )

        except Exception as exc:
            failures.append(
                (
                    path,
                    exc,
                )
            )

    if failures:
        for path, exc in failures:
            print(
                f"[FAIL] {path}: {exc}"
            )

        raise SystemExit(
            1
        )

    print(
        f"[OK] Syntax checked {len(python_files)} Python files."
    )


if __name__ == "__main__":
    main()
