# Shared file transfer helpers for deploy.ps1 scripts.
# Prefers robocopy over SMB (restartable /Z). Falls back to scp over SSH.
# scp shows live progress by polling remote file size over a parallel SSH session.

$script:DeploySshOptions = @(
    '-o', 'ConnectTimeout=30',
    '-o', 'ServerAliveInterval=30',
    '-o', 'ServerAliveCountMax=20',
    '-o', 'TCPKeepAlive=yes'
)

function Write-DeployLog {
    param(
        [string]$Message,
        [ValidateSet('Info', 'Ok', 'Warn', 'Error', 'Step')]
        [string]$Level = 'Info'
    )
    $ts = Get-Date -Format 'HH:mm:ss'
    $prefix = switch ($Level) {
        'Ok'    { '[OK]   ' }
        'Warn'  { '[WARN] ' }
        'Error' { '[ERR]  ' }
        'Step'  { '[STEP] ' }
        default { '[....] ' }
    }
    $color = switch ($Level) {
        'Ok'    { 'Green' }
        'Warn'  { 'Yellow' }
        'Error' { 'Red' }
        'Step'  { 'Cyan' }
        default { 'Gray' }
    }
    Write-Host "$ts $prefix$Message" -ForegroundColor $color
}

function Format-DeployBytes {
    param([long]$Bytes)
    if ($Bytes -ge 1GB) { return ('{0:N2} GB' -f ($Bytes / 1GB)) }
    if ($Bytes -ge 1MB) { return ('{0:N1} MB' -f ($Bytes / 1MB)) }
    if ($Bytes -ge 1KB) { return ('{0:N0} KB' -f ($Bytes / 1KB)) }
    return "$Bytes B"
}

function Invoke-DeploySsh {
    param(
        [string]$Server,
        [string]$RemoteCommand
    )
    & ssh @DeploySshOptions $Server $RemoteCommand
}

function Test-DeploySshKeyAuth {
    param([string]$Server)
    & ssh @($DeploySshOptions + '-o', 'BatchMode=yes') $Server 'true' 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Get-SshHostFromServer {
    param([string]$Server)
    if ($Server -match '@(.+)$') { return $Matches[1] }
    return $Server
}

function Convert-RemoteDirToUnc {
    param(
        [string]$SmbRoot,
        [string]$RemoteDir
    )
    $relative = $RemoteDir -replace '^/home/evdillen/?', '' -replace '/', '\'
    if ($relative) {
        return Join-Path $SmbRoot $relative
    }
    return $SmbRoot
}

function Test-SmbRoot {
    param([string]$SmbRoot)
    if (-not $SmbRoot) { return $false }
    try {
        return Test-Path -LiteralPath $SmbRoot -ErrorAction Stop
    } catch {
        return $false
    }
}

function Get-RemoteFileBytes {
    param(
        [string]$Server,
        [string]$RemotePath
    )
    $remotePathEsc = $RemotePath -replace "'", "'\''"
    $result = Invoke-DeploySsh -Server $Server -RemoteCommand "stat -c %s '$remotePathEsc' 2>/dev/null || echo 0"
    if ($LASTEXITCODE -ne 0) { return 0 }
    $line = ($result | Select-Object -First 1).ToString().Trim()
    if ($line -match '^\d+$') { return [long]$line }
    return 0
}

function Remove-RemoteDeployFile {
    param(
        [string]$Server,
        [string]$RemotePath
    )
    $remotePathEsc = $RemotePath -replace "'", "'\''"
    Invoke-DeploySsh -Server $Server -RemoteCommand "rm -f '$remotePathEsc'" | Out-Null
}

function Get-DeployTransferSource {
    param([string]$LocalPath)

    $ext = [System.IO.Path]::GetExtension($LocalPath).ToLowerInvariant()
    if ($ext -notin @('.sh', '.yaml', '.yml')) {
        return @{
            Path = $LocalPath
            Cleanup = $false
        }
    }

    $content = [System.IO.File]::ReadAllText($LocalPath)
    $normalized = $content -replace "`r`n", "`n" -replace "`r", "`n"
    if ($normalized -ceq $content) {
        return @{
            Path = $LocalPath
            Cleanup = $false
        }
    }

    $tempFile = [System.IO.Path]::Combine(
        [System.IO.Path]::GetTempPath(),
        "deploy-$([System.IO.Path]::GetFileName($LocalPath))"
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($tempFile, $normalized, $utf8NoBom)
    return @{
        Path = $tempFile
        Cleanup = $true
    }
}

function Test-RobocopyExitCode {
    param([int]$ExitCode)
    return ($ExitCode -lt 8)
}

function Write-DeployScpProgressLine {
    param(
        [long]$RemoteBytes,
        [long]$LocalBytes,
        [datetime]$StartedAt,
        [datetime]$LastProgressAt,
        [int]$StallWarnSeconds
    )

    $elapsed = (Get-Date) - $StartedAt
    $pct = if ($LocalBytes -gt 0) {
        [math]::Min(100, [math]::Round(100.0 * $RemoteBytes / $LocalBytes, 1))
    } else { 0 }
    $avgSpeed = if ($elapsed.TotalSeconds -gt 0) { $RemoteBytes / $elapsed.TotalSeconds } else { 0 }
    $elapsedStr = '{0}m {1}s' -f [int][math]::Floor($elapsed.TotalMinutes), ($elapsed.Seconds)
    $stallSecs = [int]((Get-Date) - $LastProgressAt).TotalSeconds
    $speedStr = "$(Format-DeployBytes ([long]$avgSpeed))/s"
    $line = "scp $(Format-DeployBytes $RemoteBytes) / $(Format-DeployBytes $LocalBytes) ($pct%) | $speedStr | $elapsedStr"

    if ($stallSecs -ge $StallWarnSeconds) {
        Write-DeployLog "$line | STALLED ${stallSecs}s" -Level Warn
    } else {
        Write-DeployLog $line -Level Info
    }
    [Console]::Out.Flush()
}

function Invoke-DeployScpForegroundVerbose {
    param(
        [string]$Server,
        [string]$Source,
        [string]$RemoteDir,
        [string]$RemotePath,
        [string]$FileName,
        [long]$LocalBytes
    )

    $dest = "${Server}:$RemoteDir/"
    Write-DeployLog "Starting scp (foreground): $FileName ($(Format-DeployBytes $LocalBytes))" -Level Step
    Write-DeployLog "Enter SSH password when prompted (only one prompt with password auth)" -Level Warn
    Write-DeployLog "Verbose scp output follows..." -Level Info

    $startedAt = Get-Date
    & scp -v @DeploySshOptions $Source $dest 2>&1 | ForEach-Object {
        $line = $_.ToString().Trim()
        if ($line) { Write-DeployLog "scp: $line" -Level Info }
    }
    $exitCode = $LASTEXITCODE
    $totalSecs = [int]((Get-Date) - $startedAt).TotalSeconds

    if ($exitCode -ne 0) {
        $exitLabel = if ($null -ne $exitCode) { "$exitCode" } else { 'unknown' }
        Write-DeployLog "scp failed with exit code $exitLabel after ${totalSecs}s" -Level Error
        return $(if ($null -ne $exitCode) { $exitCode } else { 1 })
    }

    Write-DeployLog "scp done: $FileName in ${totalSecs}s (trust scp exit code; no post-check without key auth)" -Level Ok
    return 0
}

function Invoke-DeployScpWithProgress {
    param(
        [string]$Server,
        [string]$Source,
        [string]$RemoteDir,
        [string]$RemotePath,
        [string]$FileName,
        [long]$LocalBytes,
        [int]$PollSeconds = 3,
        [int]$StallWarnSeconds = 45,
        [int]$StallKillSeconds = 600
    )

    if (-not (Test-DeploySshKeyAuth -Server $Server)) {
        Write-DeployLog "No SSH key auth - using foreground scp (parallel progress needs keys)" -Level Warn
        return (Invoke-DeployScpForegroundVerbose `
            -Server $Server -Source $Source -RemoteDir $RemoteDir `
            -RemotePath $RemotePath -FileName $FileName -LocalBytes $LocalBytes)
    }

    $dest = "${Server}:$RemoteDir/"
    Write-DeployLog "Starting scp: $FileName ($(Format-DeployBytes $LocalBytes)) -> $dest" -Level Step
    Write-DeployLog "Source path: $Source" -Level Info
    Write-DeployLog "Polling remote file size every ${PollSeconds}s (SSH key auth active)" -Level Info

    # scp runs in a background job so this thread can print live progress.
    # Foreground scp blocks the runspace; timer events only flush after scp returns.
    $sshOpts = @($DeploySshOptions + '-o', 'BatchMode=yes', '-C')
    $startedAt = Get-Date
    $lastRemoteBytes = 0L
    $lastProgressAt = $startedAt
    $lastLoggedAt = $startedAt.AddSeconds(-$PollSeconds)
    $exitCode = $null

    # Pass source via env var so paths with spaces survive the job boundary reliably.
    $env:DEPLOY_SCP_SOURCE = $Source
    $scpJob = Start-Job -ScriptBlock {
        param([string]$DestPath, [object]$Options)
        $sourcePath = $env:DEPLOY_SCP_SOURCE
        if (-not $sourcePath) { return 1 }
        & scp @Options $sourcePath $DestPath
        return $LASTEXITCODE
    } -ArgumentList $dest, $sshOpts

    Write-DeployLog "scp job started (id $($scpJob.Id))" -Level Info

    while ($scpJob.State -eq 'Running') {
        Start-Sleep -Milliseconds 500

        if (((Get-Date) - $lastLoggedAt).TotalSeconds -ge $PollSeconds) {
            $remoteBytes = Get-RemoteFileBytes -Server $Server -RemotePath $RemotePath
            if ($remoteBytes -gt $lastRemoteBytes) {
                $lastProgressAt = Get-Date
                $lastRemoteBytes = $remoteBytes
            }

            Write-DeployScpProgressLine `
                -RemoteBytes $remoteBytes `
                -LocalBytes $LocalBytes `
                -StartedAt $startedAt `
                -LastProgressAt $lastProgressAt `
                -StallWarnSeconds $StallWarnSeconds

            $lastLoggedAt = Get-Date
            $stallSecs = [int]((Get-Date) - $lastProgressAt).TotalSeconds
            if ($stallSecs -ge $StallKillSeconds) {
                Write-DeployLog "No progress for $([int]($StallKillSeconds / 60)) minutes - stopping scp" -Level Error
                Stop-Job $scpJob -ErrorAction SilentlyContinue
                $exitCode = 1
                break
            }
        }
    }

    if (-not $exitCode) {
        $exitCode = Receive-Job -Job $scpJob -Wait -ErrorAction SilentlyContinue
        if ($scpJob.Error.Count -gt 0) {
            foreach ($errRecord in $scpJob.Error) {
                $text = $errRecord.Exception.Message.Trim()
                if ($text) { Write-DeployLog "scp: $text" -Level Warn }
            }
        }
    }

    Remove-Job $scpJob -Force -ErrorAction SilentlyContinue
    Remove-Item Env:DEPLOY_SCP_SOURCE -ErrorAction SilentlyContinue

    $totalSecs = [int]((Get-Date) - $startedAt).TotalSeconds
    $finalBytes = Get-RemoteFileBytes -Server $Server -RemotePath $RemotePath

    if ($finalBytes -gt 0 -and $finalBytes -lt $LocalBytes) {
        $pctDone = [math]::Round(100.0 * $finalBytes / $LocalBytes, 1)
        Write-DeployLog "Partial transfer on server: $(Format-DeployBytes $finalBytes) ($pctDone%). Re-run deploy to retry from scratch." -Level Warn
    }

    if ($exitCode -ne 0) {
        $exitLabel = if ($null -ne $exitCode) { "$exitCode" } else { 'unknown' }
        Write-DeployLog "scp failed with exit code $exitLabel after ${totalSecs}s (connection reset? re-run deploy)" -Level Error
        return $(if ($null -ne $exitCode) { $exitCode } else { 1 })
    }

    if ($finalBytes -ne $LocalBytes) {
        Write-DeployLog "Size mismatch after scp: remote $(Format-DeployBytes $finalBytes) vs local $(Format-DeployBytes $LocalBytes)" -Level Error
        return 1
    }

    Write-DeployLog "scp done: $FileName ($(Format-DeployBytes $finalBytes)) in ${totalSecs}s" -Level Ok
    return 0
}

function Copy-FileToDeployServer {
    param(
        [string]$Server,
        [string]$LocalPath,
        [string]$RemoteDir,
        [string]$SmbRoot = "",
        [switch]$Resumable
    )

    if (-not (Test-Path -LiteralPath $LocalPath)) {
        Write-Error "Local file not found: $LocalPath"
        return 1
    }

    $transferSource = Get-DeployTransferSource -LocalPath $LocalPath
    try {
        $localItem = Get-Item -LiteralPath $transferSource.Path
        $fileName = (Get-Item -LiteralPath $LocalPath).Name
        $remotePath = "$RemoteDir/$fileName"
        $localBytes = $localItem.Length

        Write-DeployLog "Checking remote state for $fileName..." -Level Step
        $remoteBytes = Get-RemoteFileBytes -Server $Server -RemotePath $remotePath
        if ($remoteBytes -eq $localBytes -and $localBytes -gt 0) {
            Write-DeployLog "Skip $fileName - already complete on server ($(Format-DeployBytes $localBytes))" -Level Ok
            return 0
        }
        if ($remoteBytes -gt 0 -and $remoteBytes -ne $localBytes) {
            Write-DeployLog "Removing stale/partial remote $fileName ($(Format-DeployBytes $remoteBytes) / $(Format-DeployBytes $localBytes))" -Level Warn
            Remove-RemoteDeployFile -Server $Server -RemotePath $remotePath
        }

        if ($SmbRoot -and (Test-SmbRoot $SmbRoot)) {
            $uncDest = Convert-RemoteDirToUnc -SmbRoot $SmbRoot -RemoteDir $RemoteDir
            if (-not (Test-Path -LiteralPath $uncDest)) {
                New-Item -ItemType Directory -Path $uncDest -Force | Out-Null
            }

            $robocopyArgs = @(
                $localItem.DirectoryName,
                $uncDest,
                $fileName,
                '/FFT',
                '/R:3',
                '/W:5',
                '/NP'
            )
            if ($Resumable) { $robocopyArgs += '/Z' }

            Write-DeployLog "Starting robocopy -> $uncDest" -Level Step
            & robocopy @robocopyArgs | Out-Host
            if (Test-RobocopyExitCode $LASTEXITCODE) {
                Write-DeployLog "robocopy done: $fileName" -Level Ok
                return 0
            }
            Write-DeployLog "robocopy failed (exit $LASTEXITCODE); falling back to scp" -Level Warn
        }

        if ($Resumable -and $remoteBytes -gt 0 -and $remoteBytes -lt $localBytes) {
            Write-DeployLog "scp cannot resume partial files - restarting from byte 0" -Level Warn
        }

        $showProgress = $localBytes -ge 1MB
        if ($showProgress) {
            return (Invoke-DeployScpWithProgress `
                -Server $Server `
                -Source $localItem.FullName `
                -RemoteDir $RemoteDir `
                -RemotePath $remotePath `
                -FileName $fileName `
                -LocalBytes $localBytes)
        }

        Write-DeployLog "Starting scp (small file): $fileName ($(Format-DeployBytes $localBytes))" -Level Step
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        & scp @DeploySshOptions $localItem.FullName "${Server}:$RemoteDir/"
        $sw.Stop()
        if ($LASTEXITCODE -ne 0) {
            Write-DeployLog "scp failed (exit $LASTEXITCODE) after $($sw.ElapsedMilliseconds)ms" -Level Error
            return $LASTEXITCODE
        }
        Write-DeployLog "scp done: $fileName in $($sw.ElapsedMilliseconds)ms" -Level Ok
        return 0
    } finally {
        if ($transferSource.Cleanup -and (Test-Path -LiteralPath $transferSource.Path)) {
            Remove-Item -LiteralPath $transferSource.Path -Force -ErrorAction SilentlyContinue
        }
    }
}

function Resolve-DeploySmbRoot {
    param(
        [string]$Server,
        [string]$SmbRoot
    )
    if ($SmbRoot) { return $SmbRoot }
    $hostPart = Get-SshHostFromServer -Server $Server
    return "\\$hostPart\evdillen"
}