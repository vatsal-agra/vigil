# Fresh demo data, then the pre-flight check. Run about 5 minutes before presenting.
#
#   powershell -ExecutionPolicy Bypass -File scripts\demo-reset.ps1
#
# WARNING: wipes the database volume. The demo account is re-seeded with four
# monitors and 24 hours of backfilled history, so every chart is full and
# every timestamp is recent. Anything else in the database is deleted.

Set-Location (Split-Path $PSScriptRoot -Parent)
docker info *> $null
if ($LASTEXITCODE -ne 0) { Write-Host "Start Docker Desktop first, wait for 'Engine running', then re-run." -ForegroundColor Red; exit 1 }

Write-Host "Stopping the stack and wiping demo data..." -ForegroundColor Cyan
docker compose down -v

Write-Host "Building and starting all five containers..." -ForegroundColor Cyan
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { Write-Host "docker compose up failed - see the output above." -ForegroundColor Red; exit 1 }

Write-Host "Waiting for the API to report healthy..." -ForegroundColor Cyan
$deadline = (Get-Date).AddMinutes(4)
do {
    Start-Sleep -Seconds 3
    $health = docker inspect -f "{{.State.Health.Status}}" vigil-api-1 2>$null
} until ($health -eq "healthy" -or (Get-Date) -gt $deadline)

Write-Host "Warming up the web app (first page compile)..." -ForegroundColor Cyan
foreach ($p in "/login", "/", "/status/demo", "/monitors/1") {
    try { Invoke-WebRequest "http://localhost:3000$p" -UseBasicParsing -TimeoutSec 120 | Out-Null } catch {}
}
Write-Host "Waiting for the worker's first probe cycle (up to 3 minutes)..." -ForegroundColor Cyan
$deadline = (Get-Date).AddMinutes(3)
do {
    Start-Sleep -Seconds 5
    $cycled = docker compose logs --since 5m worker 2>$null | Select-String "cycle complete"
} until ($cycled -or (Get-Date) -gt $deadline)

& "$PSScriptRoot\demo-check.ps1"
