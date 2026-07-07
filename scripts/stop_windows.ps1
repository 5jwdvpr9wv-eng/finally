# Idempotent stop script for FinAlly (Windows PowerShell).
# Stops and removes the container; the db/ volume mount is left untouched.
$ErrorActionPreference = "Stop"

$ContainerName = "finally"

$existing = docker ps -a -q -f "name=^$ContainerName`$"
if ($existing) {
    Write-Host "Stopping FinAlly..."
    docker stop $ContainerName *> $null
    docker rm $ContainerName *> $null
    Write-Host "FinAlly stopped."
} else {
    Write-Host "FinAlly is not running."
}
