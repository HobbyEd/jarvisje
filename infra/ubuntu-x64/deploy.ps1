# Deploy the latest locally built Sogyo Chatbot image to the server
# Uses the .tar.gz from build-local-image.ps1
#
# Resilient copy strategy:
# - Before copying we SSH to the server and list what is already present
#   in deploy-artifacts/. This allows the process to continue after
#   an interrupted session.
# - Large tarball: robocopy over SMB (/Z = restartable) when -SmbRoot is reachable.
#   Falls back to scp with live progress polling (remote file size every 3s).
# - Small files: same robocopy-over-SMB path, else scp.
#
# SMB root defaults to \\<host>\evdillen (maps to /home/evdillen on the server).
# Override when your share name differs: .\deploy.ps1 -SmbRoot '\\192.168.165.15\home'
#
# One-time service setup: infra/ubuntu-x64/setup-sogyo-service.sh
# Production host: 192.168.165.15 (enterprise). Prefer SSH keys over password.

param(
    [string]$Server = "evdillen@192.168.165.15",
    [string]$SmbRoot = ""
)

. (Join-Path $PSScriptRoot "Copy-ToDeployServer.ps1")

$RemoteBase = "/home/evdillen/sogyo-chatbot"
$RemoteArtifacts = "$RemoteBase/deploy-artifacts"
$ResolvedSmbRoot = Resolve-DeploySmbRoot -Server $Server -SmbRoot $SmbRoot
$deployStarted = Get-Date

Write-DeployLog "=== Sogyo Chatbot Deploy ===" -Level Step
Write-DeployLog "Server: $Server" -Level Info
Write-DeployLog "Tip: SSH key auth avoids silent password waits during scp" -Level Info

# NOTE: This file must stay ASCII-only. Non-ASCII chars + Google Drive sync
# frequently cause "string missing terminator" parser errors on Windows.

$artifactsDir = "deploy-artifacts"
$artifact = Get-ChildItem $artifactsDir -Filter "sogyo-chatbot-*.tar.gz" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $artifact) {
    Write-Error "No artifact found in $artifactsDir. Run build-local-image.ps1 first."
    exit 1
}

Write-DeployLog "Local artifact: $($artifact.Name) ($(Format-DeployBytes $artifact.Length))" -Level Info

if (Test-SmbRoot $ResolvedSmbRoot) {
    Write-DeployLog "SMB share reachable: $ResolvedSmbRoot (robocopy /Z)" -Level Ok
} else {
    Write-DeployLog "SMB not reachable: $ResolvedSmbRoot - using scp with progress polling" -Level Warn
}

Write-DeployLog "Preparing remote directories..." -Level Step
Invoke-DeploySsh -Server $Server -RemoteCommand "mkdir -p $RemoteArtifacts"
if ($LASTEXITCODE -ne 0) {
    Write-DeployLog "mkdir on server failed (exit $LASTEXITCODE)" -Level Error
    exit 1
}
Invoke-DeploySsh -Server $Server -RemoteCommand "sudo chown -R evdillen:evdillen $RemoteBase 2>/dev/null || true"

Invoke-DeploySsh -Server $Server -RemoteCommand "test -d $RemoteArtifacts"
if ($LASTEXITCODE -ne 0) {
    Write-DeployLog "Remote directory $RemoteArtifacts missing after prep" -Level Error
    exit 1
}
Write-DeployLog "Remote directories ready" -Level Ok

Write-DeployLog "Listing remote deploy-artifacts/ ..." -Level Step
$remoteArtifactsListing = Invoke-DeploySsh -Server $Server -RemoteCommand "ls -lh $RemoteArtifacts/ 2>/dev/null || echo no-artifacts-dir-or-empty"
foreach ($line in ($remoteArtifactsListing | Out-String).Trim().Split("`n")) {
    if ($line.Trim()) { Write-DeployLog "  remote: $line" -Level Info }
}

$tarName = $artifact.Name
if ($remoteArtifactsListing -match [regex]::Escape($tarName)) {
    Write-DeployLog "Tarball $tarName already present on server (may skip if complete)" -Level Ok
} else {
    Write-DeployLog "Tarball $tarName not yet on server" -Level Warn
}

Write-DeployLog "Phase 1/3: transfer config files" -Level Step
# Repo name: docker-compose.prod-local.yaml → on server: docker-compose.yaml
$composeFile = Join-Path $PSScriptRoot "docker-compose.prod-local.yaml"
if (Test-Path $composeFile) {
    $transferExit = Copy-FileToDeployServer -Server $Server -LocalPath $composeFile -RemoteDir $RemoteBase -SmbRoot $ResolvedSmbRoot
    if ($transferExit -ne 0) {
        Write-DeployLog "docker-compose.prod-local.yaml transfer failed" -Level Error
        exit 1
    }
    Invoke-DeploySsh -Server $Server -RemoteCommand "mv -f $RemoteBase/docker-compose.prod-local.yaml $RemoteBase/docker-compose.yaml 2>/dev/null || true"
}

$serverScript = Join-Path $PSScriptRoot "server-deploy.sh"
$transferExit = Copy-FileToDeployServer -Server $Server -LocalPath $serverScript -RemoteDir $RemoteBase -SmbRoot $ResolvedSmbRoot
if ($transferExit -ne 0) {
    Write-DeployLog "server-deploy.sh transfer failed" -Level Error
    exit 1
}

Write-DeployLog "chmod +x server-deploy.sh on server" -Level Step
Invoke-DeploySsh -Server $Server -RemoteCommand "chmod +x $RemoteBase/server-deploy.sh"

Write-DeployLog "Phase 2/3: transfer Docker image tarball (largest step)" -Level Step
$transferExit = Copy-FileToDeployServer -Server $Server -LocalPath $artifact.FullName -RemoteDir $RemoteArtifacts -SmbRoot $ResolvedSmbRoot -Resumable
if ($transferExit -ne 0) {
    Write-DeployLog "Artifact transfer failed (exit $transferExit)" -Level Error
    exit 1
}

Write-DeployLog "Phase 3/3: run server-deploy.sh on server" -Level Step
Invoke-DeploySsh -Server $Server -RemoteCommand "cd $RemoteBase; ./server-deploy.sh $tarName"
if ($LASTEXITCODE -ne 0) {
    Write-DeployLog "server-deploy.sh failed (exit $LASTEXITCODE)" -Level Error
    exit 1
}

$totalMins = [int][math]::Round(((Get-Date) - $deployStarted).TotalMinutes)
Write-DeployLog "Deployment complete (total ~${totalMins} min)" -Level Ok

Write-DeployLog "Cleaning up old local artifacts (keep last 2)..." -Level Step
$localTars = Get-ChildItem $artifactsDir -Filter "sogyo-chatbot-*.tar.gz" | Sort-Object LastWriteTime -Descending
if ($localTars.Count -gt 2) {
    $localTars | Select-Object -Skip 2 | Remove-Item -Force -ErrorAction SilentlyContinue
}
Write-DeployLog "Done." -Level Ok