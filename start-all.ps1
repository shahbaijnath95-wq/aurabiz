# start-all.ps1 — Start all 5 AuraBiz servers
# Usage:  powershell -ExecutionPolicy Bypass -File start-all.ps1
$ROOT = "C:\Users\rohit\Desktop\AI"

Write-Host "============================================"
Write-Host "  AuraBiz - Start All 5 Servers"
Write-Host "============================================"
Write-Host ""

# Check which are already running
$running = @{}
try { Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop | Out-Null; $running["backend"] = $true; Write-Host "  Backend 8000:  Already running" } catch { $running["backend"] = $false }
try { Invoke-WebRequest -Uri "http://127.0.0.1:8010/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop | Out-Null; $running["master"] = $true; Write-Host "  Master 8010:   Already running" } catch { $running["master"] = $false }
try { Invoke-WebRequest -Uri "http://127.0.0.1:3001" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop | Out-Null; $running["frontend"] = $true; Write-Host "  Frontend 3001: Already running" } catch { $running["frontend"] = $false }
try { Invoke-WebRequest -Uri "http://127.0.0.1:3002" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop | Out-Null; $running["admin"] = $true; Write-Host "  Admin 3002:    Already running" } catch { $running["admin"] = $false }
try { Invoke-WebRequest -Uri "http://127.0.0.1:8001" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop | Out-Null; $running["bot"] = $true; Write-Host "  Bot 8001:      Already running" } catch { $running["bot"] = $false }
Write-Host ""

# ─── Helper to start a hidden background process ───────────────
function Start-Hidden {
    param($WorkDir, $Exe, $Args)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = $Args
    $psi.WorkingDirectory = $WorkDir
    $psi.UseShellExecute = $true
    $psi.CreateNoWindow = $true
    $psi.WindowStyle = "Hidden"
    return [System.Diagnostics.Process]::Start($psi)
}

if (-not $running["master"]) {
    Write-Host "[1/5] Starting Master Backend (8010)..."
    Start-Hidden "$ROOT\master" "python" "-m uvicorn main:app --host 0.0.0.0 --port 8010" | Out-Null
    Start-Sleep -Seconds 5
}

if (-not $running["backend"]) {
    Write-Host "[2/5] Starting Backend (8000)..."
    Start-Hidden "$ROOT\backend" "python" "-m uvicorn main:app --host 0.0.0.0 --port 8000" | Out-Null
    Start-Sleep -Seconds 7
}

if (-not $running["frontend"]) {
    Write-Host "[3/5] Starting Frontend (3001)..."
    Start-Hidden "$ROOT\frontend" "cmd" "/c npx next dev -p 3001" | Out-Null
    Start-Sleep -Seconds 12
}

if (-not $running["admin"]) {
    Write-Host "[4/5] Starting Admin Frontend (3002)..."
    Start-Hidden "$ROOT\admin-frontend" "cmd" "/c npx next dev -p 3002" | Out-Null
    Start-Sleep -Seconds 12
}

if (-not $running["bot"]) {
    Write-Host "[5/5] Starting WhatsApp Bot (8001)..."
    Start-Hidden "$ROOT\whatsapp-bot" "node" "bot.js" | Out-Null
    Start-Sleep -Seconds 6
}

Write-Host ""
Write-Host "============================================"
Write-Host "  Final Health Check"
Write-Host "============================================"
try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5; Write-Host "  Backend  8000: $($r.StatusCode) OK" } catch { Write-Host "  Backend  8000: FAILED" }
try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:8010/health" -UseBasicParsing -TimeoutSec 5; Write-Host "  Master   8010: $($r.StatusCode) OK" } catch { Write-Host "  Master   8010: FAILED" }
try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:3001" -UseBasicParsing -TimeoutSec 5; Write-Host "  Frontend 3001: $($r.StatusCode) OK" } catch { Write-Host "  Frontend 3001: FAILED" }
try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:3002" -UseBasicParsing -TimeoutSec 5; Write-Host "  Admin    3002: $($r.StatusCode) OK" } catch { Write-Host "  Admin    3002: FAILED" }
try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:8001" -UseBasicParsing -TimeoutSec 5; Write-Host "  Bot      8001: $($r.StatusCode) OK" } catch { Write-Host "  Bot      8001: FAILED" }
Write-Host "============================================"
Write-Host ""
Write-Host "Frontend: http://localhost:3001  (priya@demo.com / 123456)"
Write-Host "Admin:    http://localhost:3002  (admin@platform.com / ChangeMe!SecureAdmin2026)"
Write-Host "Docs:     http://localhost:8000/docs"
