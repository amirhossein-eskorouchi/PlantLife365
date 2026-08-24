$ErrorActionPreference = "Stop"

$repoResult = @(
    git rev-parse --show-toplevel 2>$null
)

if ($LASTEXITCODE -ne 0) {
    throw "Not inside a Git repository."
}

$repo = $repoResult[0].Trim()

Set-Location $repo

$windowsPython = Join-Path $repo ".venv\python.exe"

$unixPython = Join-Path $repo ".venv/bin/python"

$pythonExe = $null

if (Test-Path $windowsPython) {
    $pythonExe = $windowsPython
}
elseif (Test-Path $unixPython) {
    $pythonExe = $unixPython
}

if (-not $pythonExe) {
    throw "PlantLife365 .venv was not found."
}

$env:DJANGO_SECRET_KEY = "local-validation-only-secret"
$env:DEBUG = "False"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1,testserver"
$env:MPLBACKEND = "Agg"
$env:PYTHONDONTWRITEBYTECODE = "1"

Write-Host ""
Write-Host "PlantLife365 Validation"
Write-Host "======================="
Write-Host ""

Write-Host "[1/6] Python syntax"

& $pythonExe scripts/check_syntax.py

if ($LASTEXITCODE -ne 0) {
    throw "Python syntax validation failed."
}

Write-Host ""
Write-Host "[2/6] Dependency consistency"

& $pythonExe -m pip check

if ($LASTEXITCODE -ne 0) {
    throw "pip check failed."
}

Write-Host ""
Write-Host "[3/6] Django system check"

& $pythonExe manage.py check

if ($LASTEXITCODE -ne 0) {
    throw "Django system check failed."
}

Write-Host ""
Write-Host "[4/6] Migration consistency"

& $pythonExe manage.py makemigrations --check --dry-run

if ($LASTEXITCODE -ne 0) {
    throw "Migration consistency check failed."
}

Write-Host ""
Write-Host "[5/6] Automated tests"

& $pythonExe -m pytest -q

if ($LASTEXITCODE -ne 0) {
    throw "Automated test suite failed."
}

Write-Host ""
Write-Host "[6/6] Git whitespace"

git diff --check

if ($LASTEXITCODE -ne 0) {
    throw "Git whitespace check failed."
}

Write-Host ""
Write-Host "[OK] VALIDATION PASSED"
