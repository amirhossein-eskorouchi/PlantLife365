# Quick Start

This guide creates a clean local PlantLife365 development environment.

The maintained repository uses Python 3.11.

---

## 1. Create an isolated environment

Using Conda:

    conda create --prefix .venv python=3.11 pip -y

If the workstation has an incompatible third-party Conda solver plugin:

    $env:CONDA_SOLVER = "classic"
    conda --no-plugins create --solver classic --prefix .venv python=3.11 pip -y
    Remove-Item Env:CONDA_SOLVER -ErrorAction SilentlyContinue

The `.venv` directory is excluded from Git.

---

## 2. Install dependencies

Windows:

    .\.venv\python.exe -m pip install --upgrade pip
    .\.venv\python.exe -m pip install -r requirements.txt
    .\.venv\python.exe -m pip install -r requirements-dev.txt

---

## 3. Create local configuration

Copy the safe configuration template:

    Copy-Item .env.example .env

Edit `.env` for the local workstation.

Do not commit `.env`.

---

## 4. Create the local database

Run:

    .\.venv\python.exe manage.py migrate

The resulting `db.sqlite3` file is excluded from Git.

---

## 5. Create an administrator if needed

Run:

    .\.venv\python.exe manage.py createsuperuser

---

## 6. Start PlantLife365

Run:

    .\.venv\python.exe manage.py runserver

The standard development address is normally:

`http://127.0.0.1:8000/`

---

## 7. Configure an ESP32 device

Copy `firmware/esp32/config.example.py` to `firmware/esp32/config.py`.

Configure the local device/network values.

Do not commit `config.py`.

See [DEVICE_API.md](DEVICE_API.md).

---

## 8. Optional local Ollama assistant

The maintained application defaults to an Ollama-compatible loopback endpoint:

`http://127.0.0.1:11434/api/generate`

The assistant is optional.

The core monitoring application does not require a running Ollama server.

---

## 9. Test exploratory analytics

A synthetic software-test dataset is available at:

`examples/sample_sensor_regression.csv`

It is not field-collected agricultural data.

---

## 10. Validate the repository

Run:

    powershell -ExecutionPolicy Bypass -File scripts/validate.ps1

Successful validation checks:

1. Python syntax
2. package consistency
3. Django configuration
4. migration consistency
5. automated tests
6. Git whitespace

---

## Historical source

A normal clone does not require the original private development archive.

Selected reviewed historical source is already preserved under `research/historical_reference/`.
