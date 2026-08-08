# Combined build + deploy + configure script for Sogyo Chatbot
#
# Smart behavior:
# - If a tarball for the *current* git commit already exists in deploy-artifacts/
#   AND the working tree is clean, the build step is skipped (faster re-deploy).
# - If you have uncommitted changes, it will always rebuild.
# - Explicit -Tag always forces a build.
#
# Usage:
#   pwsh -ExecutionPolicy Bypass -File infra/full-deploy.ps1
#   pwsh -ExecutionPolicy Bypass -File infra/full-deploy.ps1 -Tag "master-abc1234"
#
# Prerequisites on server (one time):
#   - Run infra/setup-sogyo-service.sh once to create the systemctl service
#
# After running this, the latest image will be loaded and running on the .10 server.

param(
    [string]$Tag
)

$ErrorActionPreference = "Stop"

Write-Host "=== Sogyo Chatbot - Full Build + Deploy ===" -ForegroundColor Cyan
Write-Host ""

# Determine current git-based tag (same logic as build-local-image.ps1)
$computedTag = $null
$expectedArtifact = $null
if (-not $Tag) {
    try {
        $shortSha = git rev-parse --short HEAD
        $branch = git rev-parse --abbrev-ref HEAD
        $computedTag = "$branch-$shortSha"
        $expectedArtifact = "deploy-artifacts\sogyo-chatbot-$computedTag.tar.gz"
    } catch {
        $computedTag = $null
    }
}

$skipBuild = $false
if ($expectedArtifact -and (Test-Path $expectedArtifact)) {
    # Check if working tree is clean (no uncommitted changes)
    $porcelain = git status --porcelain 2>$null
    if (-not $porcelain) {
        Write-Host ">>> Artifact for current commit ($computedTag) already exists and working tree is clean." -ForegroundColor Yellow
        Write-Host ">>> Skipping build step (image was already built for this commit)." -ForegroundColor Yellow
        $skipBuild = $true
    } else {
        Write-Host ">>> Artifact for current commit exists, but there are uncommitted local changes." -ForegroundColor Yellow
        Write-Host ">>> Forcing full rebuild to include dirty tree." -ForegroundColor Yellow
    }
}

# Step 1: Build (unless we can safely skip)
if ($skipBuild) {
    Write-Host ">>> Step 1/2: Build skipped (reusing existing artifact for HEAD)." -ForegroundColor Yellow
} else {
    Write-Host ">>> Step 1/2: Building Docker image..." -ForegroundColor Yellow
    if ($Tag) {
        & "$PSScriptRoot\build-local-image.ps1" -Tag $Tag
    } else {
        & "$PSScriptRoot\build-local-image.ps1"
    }
}

Write-Host ""
Write-Host ">>> Step 2/2: Deploying to server..." -ForegroundColor Yellow
Write-Host "    (deploy.ps1 will inspect the server and use robocopy /Z or scp for the big tarball)" -ForegroundColor DarkGray
& "$PSScriptRoot\deploy.ps1"

Write-Host ""
Write-Host "=== Full deploy finished ===" -ForegroundColor Green
Write-Host "The server should now be running the latest image."
Write-Host "Check with: ssh evdillen@192.168.165.15 'systemctl status sogyo-ollama sogyo-chatbot --no-pager'"
Write-Host "Or:          ssh evdillen@192.168.165.15 'docker compose -f ~/sogyo-chatbot/docker-compose.yaml ps'"
Write-Host "Public:      https://jarvisje.com/health"
Write-Host ""
Write-Host "Tip: If SSH drops during transfer of the large image tarball, just run this command again."
Write-Host "     robocopy /Z (via SMB) will resume the transfer instead of starting over." -ForegroundColor Yellow