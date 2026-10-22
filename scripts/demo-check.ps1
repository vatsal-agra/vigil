# Pre-flight check before a live demo. Read-only: changes nothing.
#
#   powershell -ExecutionPolicy Bypass -File scripts\demo-check.ps1
#
# Prints one line per check, green or red, and exits non-zero if anything failed.

$ErrorActionPreference = "Continue"
$failed = 0
function Pass($msg) { Write-Host "  [ OK ] $msg" -ForegroundColor Green }
function Fail($msg, $hint) {
    Write-Host "  [FAIL] $msg" -ForegroundColor Red
    if ($hint) { Write-Host "         -> $hint" -ForegroundColor Yellow }
    $script:failed++
}

Set-Location (Split-Path $PSScriptRoot -Parent)
Write-Host "`nVigil pre-flight check`n" -ForegroundColor Cyan

# 1. Docker engine
docker info *> $null
if ($LASTEXITCODE -eq 0) { Pass "Docker engine is running" }
else { Fail "Docker engine is not running" "Start Docker Desktop and wait for 'Engine running', then re-run."; exit 1 }

# 2. Containers
$expected = "vigil-api-1", "vigil-cache-1", "vigil-db-1", "vigil-web-1", "vigil-worker-1"
$running = docker compose ps --format "{{.Name}}|{{.State}}|{{.Health}}" 2>$null
foreach ($name in $expected) {
    $row = $running | Where-Object { $_ -like "$name|*" }
    if (-not $row) { Fail "$name is not running" "Run: docker compose up -d"; continue }
    $state, $health = ($row -split "\|")[1], ($row -split "\|")[2]
    if ($state -ne "running") { Fail "$name is $state" "Run: docker compose up -d" }
    elseif ($health -and $health -ne "healthy") { Fail "$name is $health" "Wait 30 s and re-run; if it persists: docker compose logs $($name -replace 'vigil-|-1','')" }
    else { Pass ("$name running" + $(if ($health) { " ($health)" } else { "" })) }
}

# 3. Health endpoint
try {
    $h = Invoke-RestMethod http://localhost:8000/health -TimeoutSec 10
    if ($h.status -eq "ok") { Pass "GET /health: api, database and cache all ok" }
    else { Fail "GET /health says $($h.status): database=$($h.database) cache=$($h.cache)" "docker compose up -d" }
} catch { Fail "API not answering on http://localhost:8000" "docker compose up -d; then docker compose logs api" }

# 4. Demo account and dashboard data
try {
    $body = @{ email = "demo@vigil.dev"; password = "vigil-demo-2026" } | ConvertTo-Json
    $tok = (Invoke-RestMethod http://localhost:8000/api/auth/login -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10).access_token
    Pass "Demo login works (demo@vigil.dev)"
    $mons = Invoke-RestMethod http://localhost:8000/api/monitors -Headers @{ Authorization = "Bearer $tok" } -TimeoutSec 10
    if ($mons.Count -ge 4) { Pass "Dashboard API returns $($mons.Count) monitors" }
    else { Fail "Dashboard API returns $($mons.Count) monitors (expected 4)" "Reset demo data: scripts\demo-reset.ps1" }
    $withHistory = @($mons | Where-Object { $_.uptime_24h -ne $null }).Count
    if ($withHistory -ge 4) { Pass "All monitors have 24 h history (charts will be full)" }
    else { Fail "Only $withHistory monitors have 24 h history - charts will look empty" "Reset demo data: scripts\demo-reset.ps1" }
} catch { Fail "Demo login failed" "Reset demo data: scripts\demo-reset.ps1" }

# 5. Web pages
foreach ($p in "/login", "/status/demo") {
    try {
        $r = Invoke-WebRequest "http://localhost:3000$p" -UseBasicParsing -TimeoutSec 60
        if ($r.StatusCode -eq 200) { Pass "Web page http://localhost:3000$p loads" }
    } catch { Fail "Web page http://localhost:3000$p does not load" "Port 3000 taken? Check: Get-NetTCPConnection -LocalPort 3000" }
}

# 6. Worker activity
$recent = docker compose logs --since 3m worker 2>$null | Select-String "cycle complete"
if ($recent) { Pass "Probe worker completed $($recent.Count) cycle(s) in the last 3 minutes" }
else { Fail "No probe cycles in the last 3 minutes" "docker compose restart worker   (needs internet to reach example.com / httpbin.org)" }

# 7. Outbound internet (the monitors probe real sites)
try { Invoke-WebRequest https://example.com -UseBasicParsing -TimeoutSec 8 | Out-Null; Pass "Internet reachable (monitored sites can be probed)" }
catch { Fail "No internet: every monitor will turn DOWN during the demo" "Use a phone hotspot, or present the outage as intended behaviour" }

Write-Host ""
if ($failed -eq 0) { Write-Host "All checks passed. Ready to present." -ForegroundColor Green; exit 0 }
else { Write-Host "$failed check(s) failed - see the hints above." -ForegroundColor Red; exit 1 }
