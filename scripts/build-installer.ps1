<#
.SYNOPSIS
    Build the Fusion 360 MCP Server Windows installer locally

.DESCRIPTION
    Compiles the Inno Setup script to create a distributable installer.
    Requires Inno Setup 6 to be installed.

.PARAMETER Version
    Version number to embed in the installer. If not specified, extracts from pyproject.toml

.PARAMETER Open
    Open the output folder after building

.EXAMPLE
    .\build-installer.ps1
    
.EXAMPLE
    .\build-installer.ps1 -Version "1.2.0" -Open
#>

param(
    [string]$Version,
    [switch]$Open
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host @"

╔═══════════════════════════════════════════════════════════════════════════════╗
║              FUSION 360 MCP SERVER - BUILD INSTALLER                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Find Inno Setup
$InnoSetup = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $InnoSetup)) {
    Write-Host "❌ Inno Setup 6 not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Inno Setup 6 from:" -ForegroundColor Yellow
    Write-Host "  https://jrsoftware.org/isdl.php" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
Write-Host "✅ Found Inno Setup" -ForegroundColor Green

# Get version from pyproject.toml if not specified
if (-not $Version) {
    $pyproject = Join-Path $RootDir "pyproject.toml"
    if (Test-Path $pyproject) {
        $content = Get-Content $pyproject -Raw
        if ($content -match 'version\s*=\s*"([^"]+)"') {
            $Version = $Matches[1]
            Write-Host "📋 Version from pyproject.toml: $Version" -ForegroundColor Cyan
        }
    }
    if (-not $Version) {
        $Version = "0.0.0"
        Write-Host "⚠️ Could not detect version, using: $Version" -ForegroundColor Yellow
    }
}
else {
    Write-Host "📋 Using specified version: $Version" -ForegroundColor Cyan
}

# Check for icon
$iconPath = Join-Path $RootDir "assets\icon.ico"
$svgPath = Join-Path $RootDir "assets\icon.svg"
$issPath = Join-Path $RootDir "Fusion360MCPSetup.iss"

if (-not (Test-Path $iconPath) -and (Test-Path $svgPath)) {
    Write-Host "📎 Generating icon from SVG..." -ForegroundColor Cyan
    & "$ScriptDir\generate-icon.ps1" -SvgPath $svgPath -OutputPath $iconPath
}

# Create output directory
$outputDir = Join-Path $RootDir "dist"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Compile installer
Write-Host ""
Write-Host "🔨 Compiling installer..." -ForegroundColor Cyan
Push-Location $RootDir
try {
    & $InnoSetup "/DAppVersion=$Version" $issPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Compilation failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}

# Show result
Write-Host ""
$outputFile = Get-ChildItem "$outputDir\*.exe" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($outputFile) {
    $size = [math]::Round($outputFile.Length / 1MB, 2)
    Write-Host "✅ Build successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 Output: $($outputFile.FullName)" -ForegroundColor Cyan
    Write-Host "   Size:   $size MB" -ForegroundColor Gray
    Write-Host ""
    
    if ($Open) {
        Start-Process explorer.exe -ArgumentList "/select,`"$($outputFile.FullName)`""
    }
    
    Write-Host "To test:" -ForegroundColor Yellow
    Write-Host "  $($outputFile.Name)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To test silently:" -ForegroundColor Yellow
    Write-Host "  $($outputFile.Name) /VERYSILENT /LOG=install.log" -ForegroundColor Gray
}
else {
    Write-Host "❌ No output file found" -ForegroundColor Red
    exit 1
}
