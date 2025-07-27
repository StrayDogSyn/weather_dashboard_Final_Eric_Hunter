<#
.SYNOPSIS
    Automatic README Screenshot Update Automation Setup

.DESCRIPTION
    This PowerShell script provides multiple automation options for updating
    the README.md file with the most recent screenshot:
    
    1. File Watcher - Monitors assets/images folder for new files
    2. Scheduled Task - Runs update at specified intervals
    3. Manual Update - One-time update execution

.PARAMETER Mode
    Automation mode: 'watch', 'schedule', or 'update'

.PARAMETER Interval
    For schedule mode: interval in minutes (default: 60)

.EXAMPLE
    .\Setup-AutoScreenshotUpdate.ps1 -Mode update
    .\Setup-AutoScreenshotUpdate.ps1 -Mode watch
    .\Setup-AutoScreenshotUpdate.ps1 -Mode schedule -Interval 30
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('watch', 'schedule', 'update', 'help')]
    [string]$Mode,
    
    [Parameter(Mandatory=$false)]
    [int]$Interval = 60
)

# Configuration
$ScriptPath = Split-Path $PSScriptRoot -Parent
$ImagesPath = Join-Path $ScriptPath "assets\images"
$UpdateScript = Join-Path $PSScriptRoot "update_readme_screenshot.py"
$TaskName = "WeatherDashboard-ScreenshotUpdate"

function Show-Help {
    Write-Host "README Screenshot Auto-Updater" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available modes:" -ForegroundColor Yellow
    Write-Host "  update   - Update README once with latest screenshot" -ForegroundColor White
    Write-Host "  watch    - Monitor images folder and auto-update on changes" -ForegroundColor White
    Write-Host "  schedule - Create scheduled task for periodic updates" -ForegroundColor White
    Write-Host "  help     - Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\Setup-AutoScreenshotUpdate.ps1 -Mode update" -ForegroundColor Gray
    Write-Host "  .\Setup-AutoScreenshotUpdate.ps1 -Mode watch" -ForegroundColor Gray
    Write-Host "  .\Setup-AutoScreenshotUpdate.ps1 -Mode schedule -Interval 30" -ForegroundColor Gray
}

function Update-Screenshot {
    Write-Host "Updating README with latest screenshot..." -ForegroundColor Green
    
    try {
        Set-Location $PSScriptRoot
        $result = & python $UpdateScript 2>&1
        Write-Host $result -ForegroundColor White
        Write-Host "Update completed successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "Error updating screenshot: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Start-FileWatcher {
    Write-Host "Starting file watcher for $ImagesPath" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop watching..." -ForegroundColor Yellow
    Write-Host ""
    
    # Create file system watcher
    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = $ImagesPath
    $watcher.Filter = "*.png"
    $watcher.IncludeSubdirectories = $false
    $watcher.EnableRaisingEvents = $true
    
    # Define the action to take when a file is created or modified
    $action = {
        $path = $Event.SourceEventArgs.FullPath
        $name = $Event.SourceEventArgs.Name
        $changeType = $Event.SourceEventArgs.ChangeType
        
        Write-Host "Detected $($changeType): $($name)" -ForegroundColor Yellow
        
        # Wait a moment for file to be fully written
        Start-Sleep -Seconds 2
        
        # Update README
        Update-Screenshot
        Write-Host ""
    }
    
    # Register event handlers
    Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $action
    Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action
    
    try {
        # Keep the script running
        while ($true) {
            Start-Sleep -Seconds 1
        }
    }
    finally {
        # Clean up
        $watcher.EnableRaisingEvents = $false
        $watcher.Dispose()
        Get-EventSubscriber | Unregister-Event
        Write-Host "File watcher stopped." -ForegroundColor Red
    }
}

function Setup-ScheduledTask {
    Write-Host "Setting up scheduled task for every $Interval minutes..." -ForegroundColor Cyan
    
    try {
        # Remove existing task if it exists
        if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "Removed existing scheduled task" -ForegroundColor Yellow
        }
        
        # Create new scheduled task
        $action = New-ScheduledTaskAction -Execute "python" -Argument $UpdateScript -WorkingDirectory $PSScriptRoot
        $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes $Interval) -RepetitionDuration (New-TimeSpan -Days 365) -At (Get-Date)
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Automatically update README.md with latest screenshot"
        
        Write-Host "Scheduled task created successfully!" -ForegroundColor Green
        Write-Host "Will run every $Interval minutes" -ForegroundColor White
        Write-Host "Manage via Task Scheduler or: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    }
    catch {
        Write-Host "Error creating scheduled task: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Try running PowerShell as Administrator" -ForegroundColor Yellow
    }
}

# Main execution
switch ($Mode) {
    'help' {
        Show-Help
    }
    'update' {
        Update-Screenshot
    }
    'watch' {
        if (-not (Test-Path $ImagesPath)) {
            Write-Host "Images directory not found: $ImagesPath" -ForegroundColor Red
            exit 1
        }
        Start-FileWatcher
    }
    'schedule' {
        Setup-ScheduledTask
    }
}