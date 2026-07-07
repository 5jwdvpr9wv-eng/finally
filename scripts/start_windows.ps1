# Idempotent start script for FinAlly (Windows PowerShell).
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$ImageName = "finally"
$ContainerName = "finally"

Set-Location $ProjectRoot

if (-not (Test-Path ".env")) {
    Write-Host "No .env file found -- copying .env.example to .env."
    Write-Host "Edit .env and add your OPENROUTER_API_KEY before using AI chat."
    Copy-Item ".env.example" ".env"
}

$Port = 8000
$envLine = Select-String -Path ".env" -Pattern '^HOST_PORT=' -ErrorAction SilentlyContinue | Select-Object -Last 1
if ($envLine) {
    $value = ($envLine.Line -split '=', 2)[1].Trim()
    if ($value) { $Port = $value }
}

New-Item -ItemType Directory -Force -Path "db" | Out-Null

$Build = $false
if ($args -contains "--build") {
    $Build = $true
}

docker image inspect $ImageName *> $null
if ($LASTEXITCODE -ne 0) {
    $Build = $true
}

if ($Build) {
    Write-Host "Building $ImageName image..."
    docker build -t $ImageName $ProjectRoot
}

$existing = docker ps -a -q -f "name=^$ContainerName`$"
if ($existing) {
    $running = docker ps -q -f "name=^$ContainerName`$"
    if ($running) {
        Write-Host "FinAlly is already running at http://localhost:$Port"
        exit 0
    }
    Write-Host "Removing stopped container $ContainerName..."
    docker rm $ContainerName | Out-Null
}

$conflictingContainer = docker ps --filter "publish=$Port" --format '{{.Names}}' | Where-Object { $_ -ne $ContainerName }
if ($conflictingContainer) {
    Write-Error "Port $Port is already in use by Docker container '$conflictingContainer'. Stop that container, or set HOST_PORT in .env to a free port and rerun this script."
    exit 1
}

$portInUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($portInUse) {
    $procId = $portInUse[0].OwningProcess
    $procName = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
    Write-Error "Port $Port is already in use by process '$procName' (PID $procId). Stop that process, or set HOST_PORT in .env to a free port and rerun this script."
    exit 1
}

Write-Host "Starting FinAlly..."
docker run -d `
    --name $ContainerName `
    -v "${ProjectRoot}\db:/app/db" `
    -p "${Port}:8000" `
    --env-file "$ProjectRoot\.env" `
    $ImageName

Write-Host "FinAlly is running at http://localhost:$Port"
