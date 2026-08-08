# build-local-image.ps1
#
# Builds the Sogyo Chatbot Docker image locally from the current git state
# (recommended to be on main) and prepares a transfer-ready artifact.
#
# This script only builds and exports the image locally.
# It does NOT deploy, rsync, or interact with the remote server.
#
# Prerequisites:
#   - Docker Desktop must be running (Windows)
#   - A .dockerignore file exists in the project root (recommended)
#
# Usage:
#   .\infra\build-local-image.ps1
#   .\infra\build-local-image.ps1 -Tag "v0.2-myfeature"
#
# Output:
#   - Local Docker image tagged sogyo-chatbot:<tag>
#   - deploy-artifacts/sogyo-chatbot-<tag>.tar.gz  (ready for later rsync + docker load)

param(
    [string]$Tag
)

$ErrorActionPreference = "Stop"

Write-Host "=== Sogyo Chatbot - Local Image Builder ===" -ForegroundColor Green
Write-Host "This prepares a Docker image from the current git checkout." -ForegroundColor Yellow
Write-Host "Run this from the project root." -ForegroundColor Yellow
Write-Host ""

# Ensure we are in a git repo
try {
    $gitRoot = git rev-parse --show-toplevel 2>$null
    if (-not $gitRoot) { throw "Not a git repository" }
    Set-Location $gitRoot
} catch {
    Write-Error "This script must be run from inside the git repository."
    exit 1
}

# Determine tag from git if not provided
if (-not $Tag) {
    try {
        $shortSha = git rev-parse --short HEAD
        $branch = git rev-parse --abbrev-ref HEAD
        $Tag = "$branch-$shortSha"
    } catch {
        $Tag = "latest"
    }
}

$ImageName = "sogyo-chatbot"
$FullImage = "${ImageName}:${Tag}"

# Use absolute paths based on current git root to avoid relative path resolution issues
# (especially important on Windows with complex paths like Google Drive folders)
$projectRoot = (Get-Location).Path
$ArtifactsDir = Join-Path $projectRoot "deploy-artifacts"
$TarFile = Join-Path $ArtifactsDir "sogyo-chatbot-$Tag.tar.gz"

Write-Host "Git state:"
git log -1 --oneline
Write-Host ""

# === Pre-flight checks for Docker ===
Write-Host "Checking Docker environment..." -ForegroundColor Cyan

try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker CLI not found"
    }
    Write-Host "  Docker CLI: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Error @"
Docker CLI is not available in your PATH.

On Windows:
1. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Start Docker Desktop and wait until the whale icon in the system tray shows it's running.
3. Open a new PowerShell window after Docker Desktop is ready.
"@
    exit 1
}

# Verify the Docker daemon is actually running
try {
    $serverVersion = docker info --format '{{.ServerVersion}}' 2>&1
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($serverVersion)) {
        throw "Docker daemon not reachable"
    }
    Write-Host "  Docker daemon is running (Server version: $serverVersion)" -ForegroundColor Green
} catch {
    Write-Error @"
Failed to connect to the Docker daemon.

Error details:
$($_.Exception.Message)

Common causes on Windows:
- Docker Desktop is not started.
- Docker Desktop is still starting up (wait 30-60 seconds after launch).
- You may need to run PowerShell "as Administrator" the first time.
- WSL2 backend issues (check Docker Desktop Settings > General).

Please start / restart Docker Desktop and try again.
"@
    exit 1
}

Write-Host ""

# Build the image (context = project root)
Write-Host "Building Docker image: $FullImage" -ForegroundColor Cyan
Write-Host "Using Dockerfile: infra/ubuntu-x64/Dockerfile"
Write-Host "Note: .dockerignore is used to keep the build context small and clean." -ForegroundColor DarkGray
Write-Host ""

docker build `
    --progress=plain `
    -t $FullImage `
    -f infra/ubuntu-x64/Dockerfile `
    .

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed with exit code $LASTEXITCODE"
    Write-Host ""
    Write-Host "Tips:" -ForegroundColor Yellow
    Write-Host "  - Check the build output above for missing dependencies or COPY errors."
    Write-Host "  - Make sure you have a .dockerignore in the project root."
    Write-Host "  - Try cleaning: docker builder prune"
    exit 1
}

Write-Host ""
Write-Host "Build successful: $FullImage" -ForegroundColor Green

# Prepare artifacts directory for transfer
if (-not (Test-Path $ArtifactsDir)) {
    New-Item -ItemType Directory -Path $ArtifactsDir -Force | Out-Null
}

Write-Host "Exporting image to compressed tarball (ready for rsync to server)..."
Write-Host "Target: $TarFile"

# Google Drive / OneDrive / antivirus often keep locks on large files in synced folders.
# We use a temp file + retries to work around "file is being used by another process".

# Cross-platform export (Windows-friendly, no external gzip required)
$tarPath = [System.IO.Path]::ChangeExtension($TarFile, '.tar')

Write-Host "Saving Docker image to temporary .tar..."
docker save $FullImage -o $tarPath

if ($LASTEXITCODE -ne 0 -or -not (Test-Path $tarPath)) {
    Write-Error "Failed to save Docker image to .tar"
    if (Test-Path $tarPath) { Remove-Item $tarPath -Force }
    exit 1
}

Write-Host "Compressing to .tar.gz using built-in .NET GZipStream..."

$tempGz = "$TarFile.tmp"
$maxRetries = 5
$retryDelayMs = 2000

# Try to remove any existing target or temp file first (Google Drive / AV often holds locks)
for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        if (Test-Path $TarFile) { Remove-Item $TarFile -Force -ErrorAction Stop }
        if (Test-Path $tempGz)  { Remove-Item $tempGz  -Force -ErrorAction Stop }
        break
    } catch {
        if ($i -eq $maxRetries) { throw "Could not remove existing $TarFile or temp after $maxRetries attempts: $_" }
        Write-Host "  Lock detected on artifact file, retrying in $($retryDelayMs/1000)s... ($i/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Milliseconds $retryDelayMs
    }
}

try {
    $inStream  = [System.IO.File]::OpenRead($tarPath)
    $outStream = [System.IO.File]::Create($tempGz)
    $gzip      = New-Object System.IO.Compression.GZipStream(
                     $outStream,
                     [System.IO.Compression.CompressionMode]::Compress
                 )
    $inStream.CopyTo($gzip)
    $gzip.Dispose()
    $outStream.Dispose()
    $inStream.Dispose()

    # Atomic-ish move to final name (helps with locks)
    Move-Item -Path $tempGz -Destination $TarFile -Force

    Remove-Item $tarPath -Force
} catch {
    Write-Error "Failed to compress to .tar.gz: $_"
    if (Test-Path $tarPath) { Remove-Item $tarPath -Force -ErrorAction SilentlyContinue }
    if (Test-Path $tempGz)  { Remove-Item $tempGz  -Force -ErrorAction SilentlyContinue }
    if (Test-Path $TarFile) { Remove-Item $TarFile -Force -ErrorAction SilentlyContinue }
    exit 1
}

$size = (Get-Item $TarFile).Length / 1MB
Write-Host ""
Write-Host "=== Preparation complete ===" -ForegroundColor Green
Write-Host "Local Docker image : $FullImage"
Write-Host "Transfer artifact  : $TarFile  ($([math]::Round($size, 2)) MB)"
Write-Host ""
Write-Host "The image is now ready to be copied to the server (via future rsync script)"
Write-Host "and loaded with:"
Write-Host "  docker load -i $TarFile"
Write-Host ""
Write-Host "Optional: tag as latest locally"
Write-Host "  docker tag $FullImage ${ImageName}:latest"
Write-Host ""