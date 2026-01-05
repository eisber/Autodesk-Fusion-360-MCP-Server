# =============================================================================
# Generate ICO file from SVG for Windows installer
# Requires: Inkscape or ImageMagick (magick convert)
# =============================================================================

param(
    [string]$SvgPath = "$PSScriptRoot\..\assets\icon.svg",
    [string]$OutputPath = "$PSScriptRoot\..\assets\icon.ico"
)

$ErrorActionPreference = "Stop"

Write-Host "Generating ICO file from SVG..." -ForegroundColor Cyan

# Check for ImageMagick
$magick = Get-Command magick -ErrorAction SilentlyContinue

if ($magick) {
    Write-Host "Using ImageMagick..." -ForegroundColor Green
    
    # Generate multiple sizes for ICO
    $sizes = @(16, 32, 48, 64, 128, 256)
    $tempFiles = @()
    
    foreach ($size in $sizes) {
        $tempFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', ".png"
        $tempFiles += $tempFile
        & magick convert -background none -resize "${size}x${size}" $SvgPath $tempFile
    }
    
    # Combine into ICO
    & magick convert $tempFiles $OutputPath
    
    # Cleanup temp files
    $tempFiles | ForEach-Object { Remove-Item $_ -ErrorAction SilentlyContinue }
    
    Write-Host "✅ Generated: $OutputPath" -ForegroundColor Green
}
else {
    # Fallback: Check for Inkscape
    $inkscape = Get-Command inkscape -ErrorAction SilentlyContinue
    
    if ($inkscape) {
        Write-Host "Using Inkscape..." -ForegroundColor Green
        
        $tempPng = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', ".png"
        & inkscape --export-filename=$tempPng --export-width=256 --export-height=256 $SvgPath
        
        # Note: Inkscape can't create ICO directly, need ImageMagick for final conversion
        Write-Host "⚠️ Inkscape exported PNG. Install ImageMagick to create ICO." -ForegroundColor Yellow
        Write-Host "   PNG saved to: $tempPng" -ForegroundColor Gray
    }
    else {
        Write-Host @"
❌ Neither ImageMagick nor Inkscape found.

To generate the ICO file, install one of:
  - ImageMagick: https://imagemagick.org/script/download.php
  - Inkscape: https://inkscape.org/release/

Or use an online converter:
  - https://convertio.co/svg-ico/
  - https://cloudconvert.com/svg-to-ico

Upload: $SvgPath
Save as: $OutputPath
"@ -ForegroundColor Red
        exit 1
    }
}
