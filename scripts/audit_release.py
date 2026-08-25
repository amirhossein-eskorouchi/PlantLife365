"""Audit the PlantLife365 public-release boundary.

This script uses only Python's standard library. It audits Git release
candidates: tracked files plus non-ignored untracked files. In CI, all
release files are tracked.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

REQUIRED_FILES = {
    ".env.example",
    ".github/workflows/ci.yml",
    ".gitignore",
    "CHANGELOG.md",
    "CITATION.cff",
    "LICENSE",
    "NOTICE",
    "README.md",
    "SECURITY.md",
    "docs/FINAL_AUDIT.md",
    "docs/HISTORICAL_REFERENCE_POLICY.md",
    "docs/PROVENANCE.md",
    "docs/SECURITY.md",
    "manage.py",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-lock.txt",
    "research/inventory/historical_sanitization_manifest.csv",
    "scripts/audit_release.py",
}

FORBIDDEN_EXACT_PATHS = {
    ".env",
    "db.sqlite3",
    "firmware/esp32/config.py",
}

FORBIDDEN_EXTENSIONS = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".pt",
    ".pth",
    ".ckpt",
    ".onnx",
    ".h5",
    ".keras",
    ".tflite",
    ".zip",
    ".7z",
    ".rar",
    ".pyc",
    ".sqlite",
    ".sqlite3",
    ".bin",
    ".uf2",
}

FORBIDDEN_PATH_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "staticfiles",
}

FORBIDDEN_DIRECTORY_PREFIXES = (
    "media/",
    "outputs/",
    "runs/",
    "data/",
    "results/generated/",
)

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".yml",
    ".yaml",
    ".json",
    ".csv",
    ".ini",
    ".cfg",
    ".ino",
    ".html",
    ".cff",
    ".example",
}

EXTENSIONLESS_TEXT_FILES = {
    "LICENSE",
    "NOTICE",
}

MAX_FILE_BYTES = 25 * 1024 * 1024


def fail(message: str) -> None:
    raise RuntimeError(f"[FAIL] {message}")


def git_paths(*arguments: str) -> set[str]:
    completed = subprocess.run(
        ["git", *arguments, "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    decoded = completed.stdout.decode("utf-8", errors="surrogateescape")
    return {path for path in decoded.split("\0") if path}


def release_candidates() -> set[str]:
    tracked = git_paths("ls-files")
    untracked = git_paths("ls-files", "--others", "--exclude-standard")
    return tracked | untracked


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_required_files(candidates: set[str]) -> None:
    missing = sorted(REQUIRED_FILES - candidates)
    if missing:
        fail("Missing required release files: " + ", ".join(missing))

    for relative in sorted(REQUIRED_FILES):
        if not (ROOT / relative).is_file():
            fail(f"Required release file is absent: {relative}")

    print(f"[OK] Required release files: {len(REQUIRED_FILES)}")


def check_forbidden_files(candidates: set[str]) -> None:
    findings: list[str] = []

    for relative in sorted(candidates):
        normalized = relative.replace("\\", "/")
        path = Path(normalized)
        lower = normalized.lower()

        if normalized in FORBIDDEN_EXACT_PATHS:
            findings.append(normalized)
            continue

        if path.suffix.lower() in FORBIDDEN_EXTENSIONS:
            findings.append(normalized)
            continue

        if any(part in FORBIDDEN_PATH_PARTS for part in path.parts):
            findings.append(normalized)
            continue

        if any(lower.startswith(prefix) for prefix in FORBIDDEN_DIRECTORY_PREFIXES):
            findings.append(normalized)

    if findings:
        fail("Forbidden release files: " + ", ".join(findings))

    print("[OK] No forbidden secret, cache, runtime, model, archive, or firmware binary files.")


def check_file_sizes(candidates: set[str]) -> None:
    findings: list[str] = []

    for relative in sorted(candidates):
        path = ROOT / relative
        if path.is_file() and path.stat().st_size > MAX_FILE_BYTES:
            findings.append(
                f"{relative} ({path.stat().st_size / (1024 * 1024):.2f} MB)"
            )

    if findings:
        fail("Files exceed 25 MB: " + ", ".join(findings))

    print("[OK] No release file exceeds 25 MB.")


def is_text_candidate(relative: str) -> bool:
    path = Path(relative)
    return (
        path.suffix.lower() in TEXT_EXTENSIONS
        or path.name in EXTENSIONLESS_TEXT_FILES
    )


def check_private_patterns(candidates: set[str]) -> None:
    findings: list[str] = []

    private_linux_root = "/home/" + "siol1/"
    private_windows_root = "C:" + "\\Users\\" + "ae1028\\"
    private_onedrive = "OneDrive - " + "Mississippi State University"

    for relative in sorted(candidates):
        path = ROOT / relative

        if not path.is_file() or not is_text_candidate(relative):
            continue

        if path.resolve() == SELF:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")

        if (
            private_linux_root in text
            or private_windows_root in text
            or private_onedrive in text
        ):
            findings.append(relative)

    if findings:
        fail("Private workstation patterns found in: " + ", ".join(findings))

    print("[OK] No targeted private workstation pattern remains.")


def check_license() -> None:
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")

    required = (
        "MIT License",
        "Copyright (c) 2026 PlantLife365 contributors",
        "Permission is hereby granted, free of charge",
        'THE SOFTWARE IS PROVIDED "AS IS"',
    )

    for value in required:
        if value not in text:
            fail(f"Required MIT License text is missing: {value}")

    forbidden = (
        "historical reference material",
        "third-party material",
        "See the repository NOTICE file",
    )

    for value in forbidden:
        if value in text:
            fail(f"Nonstandard boundary language is inside LICENSE: {value}")

    print("[OK] Standard MIT License validated.")


def check_notice() -> None:
    text = (ROOT / "NOTICE").read_text(encoding="utf-8")

    required = (
        "Amirhossein Eskorouchi",
        "Abhro Shome Pias",
        "Dongmin Ethan Kang",
        "Niraj Ghimire",
        "research/historical_reference/",
        "historical_sanitization_manifest.csv",
        "Third-Party Dependencies",
    )

    for value in required:
        if value not in text:
            fail(f"Required NOTICE content is missing: {value}")

    print("[OK] Team, historical, and third-party NOTICE boundaries validated.")


def check_citation() -> None:
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")

    required = (
        "cff-version: 1.2.0",
        'title: "PlantLife365"',
        "type: software",
        "version: 0.1.0",
        "date-released: 2026-08-25",
        'family-names: "Eskorouchi"',
        'given-names: "Amirhossein"',
        'family-names: "Pias"',
        'given-names: "Abhro Shome"',
        'family-names: "Kang"',
        'given-names: "Dongmin Ethan"',
        'family-names: "Ghimire"',
        'given-names: "Niraj"',
        'license: "MIT"',
        "https://github.com/amirhossein-eskorouchi/PlantLife365",
    )

    for value in required:
        if value not in text:
            fail(f"Required citation metadata is missing: {value}")

    print("[OK] Version 0.1.0 citation metadata and four authors validated.")


def check_readme() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    if "No license file is currently included" in text:
        fail("Obsolete unresolved-license statement remains in README.md.")

    required = (
        "## Team",
        "## Citation",
        "[CITATION.cff](CITATION.cff)",
        "[MIT License](LICENSE)",
        "[NOTICE](NOTICE)",
        "docs/HISTORICAL_REFERENCE_POLICY.md",
    )

    for value in required:
        if value not in text:
            fail(f"Required README release content is missing: {value}")

    print("[OK] README release, citation, and licensing content validated.")


def check_sanitization_manifest() -> None:
    manifest_path = (
        ROOT
        / "research"
        / "inventory"
        / "historical_sanitization_manifest.csv"
    )
    inventory_path = (
        ROOT
        / "research"
        / "inventory"
        / "research_extensions_inventory.csv"
    )

    inventory_text = inventory_path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).lower()

    with manifest_path.open(
        newline="",
        encoding="utf-8-sig",
    ) as stream:
        rows = list(csv.DictReader(stream))

    if len(rows) != 5:
        fail(f"Expected five sanitization rows; found {len(rows)}.")

    replacement_total = 0

    for row in rows:
        relative = row["public_path"]
        path = ROOT / relative

        if not path.is_file():
            fail(f"Sanitized public path is missing: {relative}")

        current_hash = sha256(path)
        if current_hash != row["sanitized_sha256"].lower():
            fail(f"Sanitized SHA-256 mismatch: {relative}")

        original_hash = row["original_sha256"].lower()
        if original_hash not in inventory_text:
            fail(f"Original SHA-256 is absent from inventory: {relative}")

        replacement_total += int(row["replacement_count"])

    if replacement_total != 7:
        fail(
            "Expected seven historical path replacements; "
            f"found {replacement_total}."
        )

    print("[OK] Five sanitization records and seven replacements validated.")


def main() -> int:
    print("=" * 68)
    print("PLANTLIFE365 PUBLIC-RELEASE AUDIT")
    print("=" * 68)

    candidates = release_candidates()
    print(f"[OK] Release candidate files: {len(candidates)}")

    check_required_files(candidates)
    check_forbidden_files(candidates)
    check_file_sizes(candidates)
    check_private_patterns(candidates)
    check_license()
    check_notice()
    check_citation()
    check_readme()
    check_sanitization_manifest()

    print("=" * 68)
    print("PUBLIC-RELEASE AUDIT RESULT")
    print("=" * 68)
    print("[OK] PlantLife365 release boundary passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
