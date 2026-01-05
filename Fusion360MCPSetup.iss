; =============================================================================
; Fusion 360 MCP Server - Inno Setup Installer Script
; =============================================================================
; 
; This installer:
; 1. Downloads and installs uv (Python package manager) if not present
; 2. Copies the MCP Add-In to Fusion 360's AddIns folder
; 3. Copies the Server folder to the installation directory
; 4. Runs "uv sync" to install Python dependencies
; 5. Optionally configures Claude Desktop
; 6. Creates Start Menu shortcuts
;
; Build: iscc Fusion360MCPSetup.iss
; =============================================================================

; Version is set by CI/CD pipeline, fallback for local builds
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

#define AppName "Fusion 360 MCP Server"
#define AppPublisher "eisber"
#define AppURL "https://github.com/eisber/Autodesk-Fusion-360-MCP-Server"
#define AppExeName "MCP_Server.py"

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
DefaultDirName={autopf}\FusionMCPServer
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; License and readme
LicenseFile=LICENSE
InfoAfterFile=README.md

; Output settings
OutputDir=dist
OutputBaseFilename=FusionMCPServerSetup-{#AppVersion}

; Icon (generated from assets/icon.svg)
; SetupIconFile=assets\icon.ico

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

; Signing (populated by CI/CD if available)
; SignTool=signtool sign /f "$CERT_FILE" /p "$CERT_PASSWORD" /tr http://timestamp.digicert.com /td sha256 /fd sha256 $f

; Misc
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=AI-powered CAD assistant for Autodesk Fusion 360
VersionInfoCopyright=Copyright (C) 2024-2026 {#AppPublisher}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "full"; Description: "Full installation (recommended)"
Name: "server"; Description: "Server only (Add-In installed separately)"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "server"; Description: "MCP Server (required)"; Types: full server custom; Flags: fixed
Name: "addin"; Description: "Fusion 360 Add-In"; Types: full custom
Name: "shared"; Description: "Shared Python modules"; Types: full server custom; Flags: fixed

[Tasks]
Name: "configureclaude"; Description: "Configure Claude Desktop automatically"; GroupDescription: "AI Assistant Integration:"; Components: server
Name: "desktopicon"; Description: "Create desktop shortcut to Server folder"; GroupDescription: "Additional shortcuts:"

[Files]
; Server files (always installed)
Source: "Server\*"; DestDir: "{app}\Server"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: server; \
  Excludes: "*.pyc,__pycache__,*.egg-info,.pytest_cache,.coverage,venv,.venv,.env,*.log"

; Shared modules
Source: "shared\*"; DestDir: "{app}\shared"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: shared; \
  Excludes: "*.pyc,__pycache__"

; MCP Add-In - stored in app folder, copied to Fusion in [Code]
Source: "MCP\*"; DestDir: "{app}\MCP"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: addin; \
  Excludes: "*.pyc,__pycache__,.pytest_cache,mcp_debug.log,.env,venv,.venv"

; Assets (optional - may not have generated icons yet)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist; \
  Excludes: "*.svg"

; Documentation
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#AppName} Documentation"; Filename: "{app}\README.md"
Name: "{group}\Server Folder"; Filename: "{app}\Server"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\Fusion MCP Server"; Filename: "{app}\Server"; Tasks: desktopicon

[Run]
; Run uv sync after installation (if uv is available)
Filename: "{code:GetUvPath}"; Parameters: "sync"; WorkingDir: "{app}\Server"; \
  StatusMsg: "Installing Python dependencies (this may take a minute)..."; \
  Flags: runhidden waituntilterminated; Check: UvExists

; Open README after install
Filename: "{app}\README.md"; Description: "View documentation"; Flags: postinstall shellexec skipifsilent unchecked

[UninstallDelete]
; Clean up generated files and virtual environment
Type: filesandordirs; Name: "{app}\Server\.venv"
Type: filesandordirs; Name: "{app}\Server\__pycache__"
Type: filesandordirs; Name: "{app}\shared\__pycache__"
Type: filesandordirs; Name: "{app}\MCP\__pycache__"

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nThe installer will:%n- Download uv (Python package manager) if needed%n- Install the MCP Server%n- Optionally install the Fusion 360 Add-In%n- Optionally configure Claude Desktop%n%nClick Next to continue.

[Code]
var
  DownloadPage: TDownloadWizardPage;
  UvInstalled: Boolean;

// =============================================================================
// Utility Functions
// =============================================================================

function GetUvPath(Param: String): String;
var
  UvPath: String;
begin
  // Check common uv installation locations
  
  // User's .local/bin (Unix-style, also works on Windows with newer uv)
  UvPath := ExpandConstant('{userappdata}') + '\..\Local\uv\uv.exe';
  if FileExists(UvPath) then
  begin
    Result := UvPath;
    Exit;
  end;
  
  // Newer uv location
  UvPath := ExpandConstant('{localappdata}') + '\uv\uv.exe';
  if FileExists(UvPath) then
  begin
    Result := UvPath;
    Exit;
  end;
  
  // Legacy location
  UvPath := ExpandConstant('{userappdata}') + '\.local\bin\uv.exe';
  if FileExists(UvPath) then
  begin
    Result := UvPath;
    Exit;
  end;
  
  // Try PATH (will work if uv is globally installed)
  Result := 'uv';
end;

function UvExists: Boolean;
var
  UvPath: String;
  ResultCode: Integer;
begin
  Result := UvInstalled;
  if Result then Exit;
  
  UvPath := GetUvPath('');
  
  // Test if uv can be executed
  if Exec('cmd.exe', '/c "' + UvPath + '" --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := (ResultCode = 0)
  else
    Result := False;
    
  UvInstalled := Result;
end;

function GetFusionAddInsPath: String;
begin
  Result := ExpandConstant('{userappdata}') + '\Autodesk\Autodesk Fusion 360\API\AddIns';
end;

function GetClaudeConfigPath: String;
begin
  Result := ExpandConstant('{userappdata}') + '\Claude\claude_desktop_config.json';
end;

// =============================================================================
// UV Installation
// =============================================================================

function DownloadUv: Boolean;
var
  ResultCode: Integer;
begin
  Result := False;
  
  Log('Downloading and installing uv...');
  
  // Use PowerShell to run the official uv installer
  if Exec('powershell.exe',
    '-ExecutionPolicy Bypass -NoProfile -NonInteractive -Command "& { irm https://astral.sh/uv/install.ps1 | iex }"',
    '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
    begin
      Log('uv installer completed successfully');
      // Give it a moment to finish writing files
      Sleep(2000);
      
      // Verify installation
      UvInstalled := False; // Reset cache
      Result := UvExists;
      
      if Result then
        Log('uv verified at: ' + GetUvPath(''))
      else
        Log('uv installation could not be verified');
    end
    else
      Log('uv installer exited with code: ' + IntToStr(ResultCode));
  end
  else
    Log('Failed to launch PowerShell for uv installation');
end;

// =============================================================================
// JSON Manipulation for Claude Config
// =============================================================================

function EscapeBackslashes(const S: String): String;
var
  i: Integer;
begin
  Result := '';
  for i := 1 to Length(S) do
  begin
    if S[i] = '\' then
      Result := Result + '\\'
    else
      Result := Result + S[i];
  end;
end;

procedure ConfigureClaudeDesktop;
var
  ConfigPath, ConfigDir: String;
  ServerDir, UvPath: String;
  ConfigContent, McpEntry, NewContent: String;
  ConfigLines: TArrayOfString;
  i, InsertPos: Integer;
  HasMcpServers, HasFusionMcp: Boolean;
begin
  ConfigPath := GetClaudeConfigPath;
  ConfigDir := ExtractFilePath(ConfigPath);
  
  Log('Configuring Claude Desktop at: ' + ConfigPath);
  
  // Create config directory if needed
  if not DirExists(ConfigDir) then
  begin
    if not ForceDirectories(ConfigDir) then
    begin
      Log('Failed to create Claude config directory');
      Exit;
    end;
  end;
  
  // Prepare paths (escaped for JSON)
  ServerDir := EscapeBackslashes(ExpandConstant('{app}\Server'));
  UvPath := EscapeBackslashes(GetUvPath(''));
  
  // MCP server entry
  McpEntry := '    "fusion-mcp": {' + #13#10 +
              '      "command": "' + UvPath + '",' + #13#10 +
              '      "args": ["run", "--directory", "' + ServerDir + '", "python", "MCP_Server.py", "--server_type", "stdio"]' + #13#10 +
              '    }';
  
  if FileExists(ConfigPath) then
  begin
    // Read existing config
    if not LoadStringsFromFile(ConfigPath, ConfigLines) then
    begin
      Log('Failed to read existing Claude config');
      Exit;
    end;
    
    // Build content string and check for existing entries
    ConfigContent := '';
    HasMcpServers := False;
    HasFusionMcp := False;
    
    for i := 0 to GetArrayLength(ConfigLines) - 1 do
    begin
      ConfigContent := ConfigContent + ConfigLines[i] + #13#10;
      if Pos('"mcpServers"', ConfigLines[i]) > 0 then
        HasMcpServers := True;
      if Pos('"fusion-mcp"', ConfigLines[i]) > 0 then
        HasFusionMcp := True;
    end;
    
    if HasFusionMcp then
    begin
      Log('fusion-mcp already configured in Claude Desktop');
      // Could update it, but let's leave existing config alone
      Exit;
    end;
    
    if HasMcpServers then
    begin
      // Find mcpServers opening brace and insert after it
      NewContent := '';
      for i := 0 to GetArrayLength(ConfigLines) - 1 do
      begin
        NewContent := NewContent + ConfigLines[i] + #13#10;
        if (Pos('"mcpServers"', ConfigLines[i]) > 0) or 
           ((Pos('"mcpServers"', ConfigContent) > 0) and (Pos('{', ConfigLines[i]) > 0) and (i > 0) and (Pos('"mcpServers"', ConfigLines[i-1]) > 0)) then
        begin
          // Check if next line has opening brace
          if (i + 1 < GetArrayLength(ConfigLines)) and (Trim(ConfigLines[i+1]) = '{') then
            Continue;
          if Pos('{', ConfigLines[i]) > 0 then
          begin
            NewContent := NewContent + McpEntry + ',' + #13#10;
          end;
        end;
      end;
      ConfigContent := NewContent;
    end
    else
    begin
      // No mcpServers section, need to add one
      // Find first { and insert after it
      InsertPos := Pos('{', ConfigContent);
      if InsertPos > 0 then
      begin
        NewContent := Copy(ConfigContent, 1, InsertPos) + #13#10 +
                      '  "mcpServers": {' + #13#10 +
                      McpEntry + #13#10 +
                      '  },' +
                      Copy(ConfigContent, InsertPos + 1, Length(ConfigContent));
        ConfigContent := NewContent;
      end;
    end;
  end
  else
  begin
    // Create new config file
    ConfigContent := '{' + #13#10 +
                     '  "mcpServers": {' + #13#10 +
                     McpEntry + #13#10 +
                     '  }' + #13#10 +
                     '}' + #13#10;
  end;
  
  // Write config
  if SaveStringToFile(ConfigPath, ConfigContent, False) then
    Log('Claude Desktop configuration saved')
  else
    Log('Failed to save Claude Desktop configuration');
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
  UvInstalled := False;
  Log('Fusion 360 MCP Server Installer v{#AppVersion}');
end;

procedure InitializeWizard;
begin
  // Create download page for uv
  DownloadPage := CreateDownloadPage(
    'Installing Prerequisites',
    'Please wait while uv (Python package manager) is being installed...',
    nil
  );
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  NeedsRestart := False;
  
  // Check if uv is installed
  if not UvExists then
  begin
    Log('uv not found, attempting installation...');
    
    DownloadPage.Show;
    try
      DownloadPage.SetText('Installing uv...', 'Downloading from astral.sh');
      DownloadPage.SetProgress(0, 100);
      
      if not DownloadUv then
      begin
        Result := 'Failed to install uv (Python package manager).' + #13#10 + #13#10 +
                  'Please install uv manually from:' + #13#10 +
                  'https://docs.astral.sh/uv/getting-started/installation/' + #13#10 + #13#10 +
                  'Then run this installer again.';
      end
      else
        DownloadPage.SetProgress(100, 100);
    finally
      DownloadPage.Hide;
    end;
  end
  else
    Log('uv found at: ' + GetUvPath(''));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Install Fusion 360 Add-In
    if WizardIsComponentSelected('addin') then
      InstallFusionAddIn;
    
    // Configure Claude Desktop
    if WizardIsTaskSelected('configureclaude') then
      ConfigureClaudeDesktop;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Remove Fusion 360 Add-In
    UninstallFusionAddIn;
    
    // Note: We intentionally do NOT remove Claude Desktop config
    // to preserve user's other MCP server configurations
    Log('Note: Claude Desktop configuration preserved (remove fusion-mcp entry manually if desired)');
  end;
end;

function InitializeUninstall: Boolean;
begin
  Result := True;
  Log('Fusion 360 MCP Server Uninstaller');
end;
