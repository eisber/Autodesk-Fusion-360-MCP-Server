# Uninstall MCP Add-In from Fusion 360
# This script removes the MCP entry from Fusion 360's JSLoadedScriptsinfo file
#
# Usage: .\uninstall-addin.ps1
#        .\uninstall-addin.ps1 -AddinName "SomeOtherAddin"

param(
    [string]$AddinName = "MCP"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Fusion 360 Add-In Uninstaller ===" -ForegroundColor Cyan
Write-Host ""

# Find the Fusion 360 user profile folder
$fusionBasePath = "$env:APPDATA\Autodesk\Autodesk Fusion 360"

if (-not (Test-Path $fusionBasePath)) {
    Write-Host "ERROR: Fusion 360 AppData folder not found at: $fusionBasePath" -ForegroundColor Red
    exit 1
}

# Find the user profile folder (alphanumeric folder like BYZ2NYY8PDKFFP53)
$profileFolders = Get-ChildItem -Path $fusionBasePath -Directory | Where-Object { 
    $_.Name -match '^[A-Z0-9]+$' -and (Test-Path "$($_.FullName)\JSLoadedScriptsinfo")
}

if ($profileFolders.Count -eq 0) {
    Write-Host "ERROR: No Fusion 360 profile folder with JSLoadedScriptsinfo found" -ForegroundColor Red
    exit 1
}

foreach ($profileFolder in $profileFolders) {
    $configFile = Join-Path $profileFolder.FullName "JSLoadedScriptsinfo"
    
    Write-Host "Processing profile: $($profileFolder.Name)" -ForegroundColor Yellow
    Write-Host "Config file: $configFile" -ForegroundColor Gray
    
    # Read and parse the JSON
    $content = Get-Content $configFile -Raw
    $json = $content | ConvertFrom-Json
    
    # Find the add-in entry
    $addinEntry = $json.loadedScripts | Where-Object { $_.name -eq $AddinName }
    
    if ($addinEntry) {
        Write-Host ""
        Write-Host "Found '$AddinName' add-in:" -ForegroundColor Green
        Write-Host "  Path: $($addinEntry.path)" -ForegroundColor Gray
        Write-Host "  Run on startup: $($addinEntry.runOnStartup)" -ForegroundColor Gray
        Write-Host ""
        
        # Create backup
        $backupFile = "$configFile.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $configFile $backupFile
        Write-Host "Backup created: $backupFile" -ForegroundColor Gray
        
        # Remove the add-in entry
        $json.loadedScripts = @($json.loadedScripts | Where-Object { $_.name -ne $AddinName })
        
        # Save the updated JSON
        $json | ConvertTo-Json -Depth 10 | Set-Content $configFile -Encoding UTF8
        
        Write-Host "'$AddinName' has been removed from Fusion 360!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Please restart Fusion 360 for changes to take effect." -ForegroundColor Yellow
    }
    else {
        Write-Host "'$AddinName' not found in this profile" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Cyan
