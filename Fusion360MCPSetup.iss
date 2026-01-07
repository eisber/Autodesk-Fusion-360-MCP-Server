; =============================================================================
; Fusion 360 MCP Add-In - Inno Setup Installer Script
; =============================================================================
; 
; This installer:
; 1. Copies the MCP Add-In to Fusion 360's AddIns folder
; 2. Creates Start Menu shortcuts
;
; The MCP Server (.mcpb file) is distributed separately for Claude Desktop.
;
; Build: iscc Fusion360MCPSetup.iss
; =============================================================================

; Version is set by CI/CD pipeline, fallback for local builds
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

#define AppName "Fusion 360 MCP Add-In"
#define AppPublisher "eisber"
#define AppURL "https://github.com/eisber/Autodesk-Fusion-360-MCP-Server"

[Setup]
; Unique app identifier (DO NOT CHANGE after first release)
AppId={{3c486893-8b8f-4f5c-b218-b1cd6e94ca6e}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases

; Installation directories
DefaultDirName={autopf}\FusionMCPAddIn
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; Output settings
OutputDir=dist
OutputBaseFilename=FusionMCPAddInSetup-{#AppVersion}

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
LZMANumBlockThreads=4

; Installer appearance
WizardStyle=modern
WizardSizePercent=110,110

; Privileges - allow per-user install (no admin needed)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Uninstall
UninstallDisplayIcon={app}\assets\icon.ico
UninstallDisplayName={#AppName}
Uninstallable=yes

; Architecture
ArchitecturesInstallIn64BitMode=x64compatible

; Misc
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=AI-powered CAD assistant for Autodesk Fusion 360
VersionInfoCopyright=Copyright (C) 2024-2026 {#AppPublisher}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; MCP Add-In - stored in app folder, copied to Fusion in [Code]
Source: "MCP\*"; DestDir: "{app}\MCP"; Flags: ignoreversion recursesubdirs createallsubdirs; \
  Excludes: "*.pyc,__pycache__,.pytest_cache,mcp_debug.log,.env,venv,.venv"

; Assets (optional - may not have generated icons yet)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; \
  Excludes: "*.svg"

; Documentation
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
; Start Menu
Name: "{group}\{#AppName} Documentation"; Filename: "{#AppURL}"
Name: "{group}\Add-In Folder"; Filename: "{app}\MCP"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

[Run]
; Open documentation in browser
Filename: "{#AppURL}"; Description: "View documentation"; Flags: postinstall shellexec skipifsilent unchecked

[UninstallDelete]
; Clean up generated files
Type: filesandordirs; Name: "{app}\MCP\__pycache__"
Type: files; Name: "{app}\MCP\mcp_debug.log"

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nThe installer will copy the Fusion 360 MCP Add-In to enable AI-powered CAD assistance.%n%nNote: The MCP Server extension (.mcpb file) for Claude Desktop is distributed separately.%n%nClick Next to continue.

[Code]
// =============================================================================
// Utility Functions
// =============================================================================

function GetFusionAddInsPath: String;
begin
  Result := ExpandConstant('{userappdata}') + '\Autodesk\Autodesk Fusion 360\API\AddIns';
end;

// =============================================================================
// Fusion 360 Add-In Installation
// =============================================================================

procedure InstallFusionAddIn;
var
  SourceDir, DestDir: String;
  ResultCode: Integer;
begin
  SourceDir := ExpandConstant('{app}\MCP');
  DestDir := GetFusionAddInsPath + '\MCP';
  
  Log('Installing Fusion 360 Add-In...');
  Log('  Source: ' + SourceDir);
  Log('  Destination: ' + DestDir);
  
  // Create AddIns directory if needed
  if not DirExists(GetFusionAddInsPath) then
  begin
    Log('Creating Fusion AddIns directory...');
    ForceDirectories(GetFusionAddInsPath);
  end;
  
  // Remove existing installation
  if DirExists(DestDir) then
  begin
    Log('Removing existing Add-In...');
    DelTree(DestDir, True, True, True);
  end;
  
  // Try to create symlink first (preserves dev workflow)
  if Exec('cmd.exe', '/c mklink /D "' + DestDir + '" "' + SourceDir + '"', 
          '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
    begin
      Log('Add-In installed via symlink');
      Exit;
    end;
  end;
  
  // Fallback to copy
  Log('Symlink failed, copying files...');
  if Exec('cmd.exe', '/c xcopy "' + SourceDir + '" "' + DestDir + '" /E /I /Y /Q',
          '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
      Log('Add-In installed via copy')
    else
      Log('xcopy failed with code: ' + IntToStr(ResultCode));
  end
  else
    Log('Failed to execute xcopy');
end;

// =============================================================================
// Uninstall
// =============================================================================

procedure UninstallFusionAddIn;
var
  AddInPath: String;
begin
  AddInPath := GetFusionAddInsPath + '\MCP';
  
  if DirExists(AddInPath) then
  begin
    Log('Removing Fusion 360 Add-In from: ' + AddInPath);
    DelTree(AddInPath, True, True, True);
  end;
end;

// =============================================================================
// Event Handlers
// =============================================================================

function InitializeSetup: Boolean;
begin
  Result := True;
  Log('Fusion 360 MCP Add-In Installer v{#AppVersion}');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Install Fusion 360 Add-In
    InstallFusionAddIn;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Remove Fusion 360 Add-In
    UninstallFusionAddIn;
  end;
end;

function InitializeUninstall: Boolean;
begin
  Result := True;
  Log('Fusion 360 MCP Add-In Uninstaller');
end;

