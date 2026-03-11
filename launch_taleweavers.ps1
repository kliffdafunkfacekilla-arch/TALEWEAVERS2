# launch_taleweavers.ps1
# Master Orchestration Script for T.A.L.E.W.E.A.V.E.R.
# SMART VERSION: Dynamic Port Discovery & Service Peering

$ErrorActionPreference = "Stop"

$logo = @"
====================================================================
                        T.A.L.E.W.E.A.V.E.R.
                  SAGA DIRECTOR ORCHESTRATION HUB
====================================================================
"@

Write-Host $logo -ForegroundColor Cyan

# --- 1. SMART PORT DISCOVERY ---
Write-Host "[+] Initializing Smart Port Discovery..." -ForegroundColor Yellow

$Services = @(
    "director", "world_architect", "rules_engine", "asset_foundry", "vtt"
)

$registryPath = Join-Path $PSScriptRoot "saga_registry.json"
$Registry = @{}
$ExistingRegistry = @{}

if (Test-Path $registryPath) {
    Write-Host "[+] Found existing saga_registry.json. Respecting manual overrides..." -ForegroundColor Green
    $ExistingRegistry = Get-Content $registryPath | ConvertFrom-Json
}

$CurrentPort = 8000
$UsedPorts = @()

foreach ($service in $Services) {
    # 1. Check if port is already defined in existing registry (works for PSCustomObject)
    if ($null -ne $ExistingRegistry.$service) {
        $SearchPort = $ExistingRegistry.$service
        Write-Host "    -> ${service}: Using manual port $SearchPort" -ForegroundColor Gray
        $Registry[$service] = $SearchPort
        $UsedPorts += $SearchPort
        continue
    }

    # 2. Otherwise, discover a new port
    if ($service -eq "chronos") { $SearchPort = 9000 }
    elseif ($service -eq "vtt") { $SearchPort = 5173 }
    else { $SearchPort = $CurrentPort }

    $found = $false
    while (-not $found) {
        if (-not (Get-NetTCPConnection -LocalPort $SearchPort -ErrorAction SilentlyContinue) -and ($UsedPorts -notcontains $SearchPort)) {
            $Registry[$service] = $SearchPort
            $UsedPorts += $SearchPort
            $found = $true
            if ($SearchPort -lt 9000 -and $SearchPort -ne 5173) { $CurrentPort = $SearchPort + 1 }
        }
        else {
            $SearchPort++
        }
    }
}

# Write the Registry for backends
$registryPath = Join-Path $PSScriptRoot "saga_registry.json"
$Registry | ConvertTo-Json | Set-Content -Path $registryPath
Write-Host "[+] Dynamic Service Registry generated: $registryPath" -ForegroundColor DarkGray

# Write the .env.local for React VTT
$vttEnvPath = Join-Path $PSScriptRoot "saga_vtt_client\.env.local"
$envContent = @(
    "VITE_SAGA_DIRECTOR_URL=http://localhost:$($Registry['director'])",
    "VITE_SAGA_ARCHITECT_URL=http://localhost:$($Registry['world_architect'])",
    "VITE_SAGA_RULES_ENGINE_URL=http://localhost:$($Registry['rules_engine'])",
    "VITE_SAGA_ASSET_FOUNDRY_URL=http://localhost:$($Registry['asset_foundry'])"
)
$envContent | Set-Content -Path $vttEnvPath
Write-Host "[+] React Environment Config generated: $vttEnvPath" -ForegroundColor DarkGray

# --- 2. LAUNCH PERSISTENT SPLASH SCREEN ---
$splashImagePath = Join-Path $PSScriptRoot "Gemini_Generated_Image_mo9pfymo9pfymo9p.png"
$splashProcess = $null

if (Test-Path $splashImagePath) {
    Write-Host "[+] Launching persistent splash screen..." -ForegroundColor Cyan
    $splashScript = @"
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        `$form = New-Object Windows.Forms.Form
        `$form.Text = 'TALEWEAVERS_BOOT'
        `$form.FormBorderStyle = 'None'
        `$form.StartPosition = 'CenterScreen'
        `$form.Topmost = `$true
        `$form.ShowInTaskbar = `$false
        try {
            `$img = [System.Drawing.Image]::FromFile('$($splashImagePath.Replace('\','\\'))')
            `$form.BackgroundImage = `$img
            `$form.BackgroundImageLayout = 'Zoom'
            `$form.Width = `$img.Width
            `$form.Height = `$img.Height
            `$form.ShowDialog()
        } finally {
            if (`$img) { `$img.Dispose() }
        }
"@
    $splashProcess = Start-Process powershell -ArgumentList "-WindowStyle Hidden", "-Command", $splashScript -PassThru
}

# --- 3. LAUNCH BACKEND & FRONTEND ---
$serversScript = Join-Path $PSScriptRoot "start_servers.py"
Write-Host "[+] Igniting the SAGA Ecosystem..." -ForegroundColor Cyan

if (Test-Path $serversScript) {
    $pythonProcess = Start-Process -FilePath "python" -ArgumentList $serversScript -PassThru -NoNewWindow -WorkingDirectory $PSScriptRoot
}
else {
    Write-Host "[!] CRITICAL FAILURE: start_servers.py missing!" -ForegroundColor Red
    if ($splashProcess) { Stop-Process -Id $splashProcess.Id -Force }
    Pause ; exit 1
}

# --- 4. STABILIZATION & HEALTH AUDIT ---
Write-Host "[+] Synchronizing streams. This may take up to 45 seconds for AI models to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10 # Increase initial grace period for slow-loading models

$StartupFailures = @()
foreach ($key in $Registry.Keys) {
    $port = $Registry[$key]
    $online = $false
    $attempts = 45 # Total wait time approx 45-55s
    
    Write-Host "[?] Auditing $key on Port $port..." -ForegroundColor Gray -NoNewline
    
    while (-not $online -and $attempts -gt 0) {
        if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
            $online = $true
            Write-Host " [OK]" -ForegroundColor Green
        }
        else {
            Start-Sleep -Seconds 1
            $attempts--
        }
    }
    
    if (-not $online) { 
        $StartupFailures += "$key (Port $port)" 
        Write-Host " [FAILED]" -ForegroundColor Red
    }
}

if ($StartupFailures.Count -gt 0) {
    Write-Host ""
    Write-Host "[!] AUDIT FAILURE: The following services did not respond in time:" -ForegroundColor Red
    foreach ($svc in $StartupFailures) { Write-Host "    - $svc" -ForegroundColor Red }
    Write-Host "[!] Tip: Some models take a long time to load. Try running again if this was a first-time setup." -ForegroundColor Yellow
    if ($splashProcess) { Stop-Process -Id $splashProcess.Id -Force }
    Pause ; exit 1
}

Write-Host "[+] All services synchronized and healthy." -ForegroundColor Green

# --- 5. OPEN UI & CLEANUP ---
Write-Host "[+] Systems ready. Opening VTT Interface..." -ForegroundColor Green
if ($splashProcess) { Stop-Process -Id $splashProcess.Id -Force -ErrorAction SilentlyContinue }

Start-Process "http://localhost:$($Registry['vtt'])"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  THE ENGINE IS LIVE. PRESS CTRL+C TO SHUT DOWN ALL SERVICES.       " -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Cyan

Wait-Process -Id $pythonProcess.Id
