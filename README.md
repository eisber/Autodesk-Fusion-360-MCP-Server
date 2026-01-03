# Fusion MCP Integration


https://github.com/user-attachments/assets/46c8140e-377d-4618-a304-03861cb3d7d9


## 🎯 About

Fusion MCP Integration bridges AI assistants with Autodesk Fusion 360 through the Model Context Protocol (MCP). This enables:

- ✨ **Conversational CAD** - Create 3D models using natural language
- 🤖 **AI-Driven Automation** - Automate repetitive modeling tasks
- 🔧 **Parametric Control** - Dynamically modify design parameters
- 🎓 **Accessible CAD** - Lower the barrier for non-CAD users

> **Note:** This is designed as an assistive tool and educational project, not a replacement for professional CAD workflows.
> Projects like this can assist people with no experience in CAD workflows.

> **Goal:** Enable conversational CAD and AI-driven automation in Fusion.

---


# Setup

**I highly recommend to do everything inside Visual Studio Code or an other IDE**

---

## Requirements
| Requirement | Link |
|------------|------|
| Python 3.10+ | https://python.org |
| Autodesk Fusion 360 | https://autodesk.com/fusion360 |
| Claude Desktop | https://claude.ai/download |
| VS Code | https://code.visualstudio.com |

---

## Clone Repository
```bash
git clone https://github.com/JustusBraitinger/FusionMCP
```


> **Important:** Do **NOT** start the Add-In yet.



## Install Python Dependencies
```bash
cd Server
python -m venv venv
```

### Activate venv

**Windows PowerShell**
```powershell
.\venv\Scripts\Activate
```

### Install packages
```bash
pip install -r requirements.txt
pip install "mcp[cli]"
```
## Installing the MCP Add-In for Fusion 360

```bash
cd ..
python Install_Addin.py
```
---

## Connect to Claude
The most simple way to add the MCP-Server to Claude Desktop is to run following command:  
```bash
cd Server
uv run mcp install MCP_Server.py
```
The output should be like this:    

```bash
[11/13/25 08:42:37] INFO     Added server 'Fusion' to Claude config
                    INFO     Successfully installed Fusion in Claude app                                                                                                                                                               
```

# Alternative

### Modify Claude Config
In Claude Desktop go to:  
**Settings → Developer → Edit Config**

Add this block (change the path for your system):
```json
{
  "mcpServers": {
    "FusionMCP": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Path\\to\\FusionMCP\\Server",
        "run",
        "MCP_Server.py"
      ]
    }
  }
}
```
> **Note:** Windows paths require double backslashes `\\`


### Using the MCP in Claude
1. Restart Claude if needed (force close if not visible)
2. Click **➕ Add** (bottom left of chat)
3. Select **Add from Fusion**
4. Choose a Fusion MCP prompt

---

## Use MCP in VS Code (Copilot)

The repository includes a `.vscode/mcp.json` file that configures the MCP server automatically when you open the workspace.

### Option 1: Use the included configuration (Recommended)

Just open this repository folder in VS Code. The `.vscode/mcp.json` will be detected automatically.

### Option 2: Add to your global VS Code MCP config

Create or edit the file:
```
%APPDATA%\Code\User\globalStorage\github.copilot-chat\mcp.json
```

Paste (adjust path to your repository location):
```json
{
  "servers": {
    "fusion-mcp": {
      "type": "stdio",
      "command": "powershell",
      "args": ["-Command", "& 'C:/path/to/repo/venv/Scripts/Activate.ps1'; uv run python MCP_Server.py --server_type stdio"],
      "cwd": "C:/path/to/repo/Server"
    }
  }
}
```

### Option 3: HTTP mode (Alternative)

If you prefer HTTP mode, start the server manually:
```bash
cd Server
python MCP_Server.py
```

Then configure:
```json
{
  "servers": {
    "FusionMCP": {
      "url": "http://127.0.0.1:8000/sse",
      "type": "http"
    }
  }
}
```

### Manual HTTP Setup via VS Code Command Palette
1. Press **CTRL + SHIFT + P** → search **MCP: Add Server**
2. Select **HTTP**
3. Enter URL: `http://127.0.0.1:8000/sse`
4. Name it **`FusionMCP`**

---

## Try It Out 😄
Activate the Fusion Addin inside Fusion
### Configured in VS-Code:
Start the server:
```bash
python MCP_Server.py
```
Then type   
```
/mcp.FusionMCP
```
Now you will see a list of predetermined Prompts.   
### Configured in Claude   
Just open Claude, an ask for the FusionMCP

---

## 🛠️ Available Tools

---

### 🔧 Scripting (Primary Method)

| Tool | Description |
| :--- | :--- |
| **execute_fusion_script** | Execute arbitrary Python code directly in Fusion 360. This is the primary method for creating geometry, patterns, and all complex operations. |
| **move_latest_body** | Move the most recently created body by translation. |

---

### 📏 Parameters & Control

| Tool | Description |
| :--- | :--- |
| **count** | Counts the total number of all **model parameters**. |
| **list_parameters** | Lists all defined **model parameters** in detail. |
| **change_parameter** | Changes the value of an existing named parameter. |
| **create_parameter** | Create a new user parameter with expression support. |
| **delete_parameter** | Delete a user parameter from the design. |
| **test_connection** | Tests the communication link to the Fusion 360 server. |
| **undo** | **Undoes** the last operation in Fusion 360. |
| **delete_all** | **Deletes all objects** in the current Fusion 360 session. |
| **get_model_state** | Get current model state (body count, sketch count, etc.). |
| **get_faces_info** | Get information about faces on bodies. |

---

### 📐 Measurement Tools

| Tool | Description |
| :--- | :--- |
| **measure_distance** | Measure minimum distance between two entities. |
| **measure_angle** | Measure angle between two planar faces or linear edges. |
| **measure_area** | Measure the area of a specific face. |
| **measure_volume** | Measure the volume of a body. |
| **measure_edge_length** | Measure the length of an edge. |
| **measure_body_properties** | Get comprehensive body properties. |
| **measure_point_to_point** | Measure distance between two 3D points. |
| **get_edges_info** | Get information about edges on a body. |
| **get_vertices_info** | Get information about vertices on a body. |

---

### 🔬 Parametric & Analysis Tools

| Tool | Description |
| :--- | :--- |
| **get_sketch_info** | Get detailed sketch information (geometry, constraints, profiles). |
| **get_sketch_constraints** | Get geometric constraints on a sketch. |
| **get_sketch_dimensions** | Get dimensions applied to a sketch. |
| **check_interference** | Check for interference between bodies. |
| **get_timeline_info** | Get feature timeline information. |
| **rollback_to_feature** | Roll back to a specific feature in timeline. |
| **rollback_to_end** | Roll forward to end of timeline. |
| **suppress_feature** | Suppress/unsuppress a feature. |
| **get_mass_properties** | Get mass properties (volume, center of mass, etc.). |

---

### 🏗️ Construction Geometry

| Tool | Description |
| :--- | :--- |
| **create_offset_plane** | Create a plane offset from an existing plane. |
| **create_plane_at_angle** | Create a plane at an angle to another plane. |
| **create_midplane** | Create a midplane between two faces. |
| **create_construction_axis** | Create a construction axis. |
| **create_construction_point** | Create a construction point. |
| **list_construction_geometry** | List all construction geometry in the design. |

---

### 🧪 Testing & Snapshots

| Tool | Description |
| :--- | :--- |
| **save_test** | Save a test script for validation. |
| **load_tests** | Load saved tests. |
| **run_tests** | Run all or specific tests. |
| **delete_test** | Delete a saved test. |
| **create_snapshot** | Create a snapshot of current model state. |
| **list_snapshots** | List all available snapshots. |
| **restore_snapshot** | Restore model to a previous snapshot. |
| **delete_snapshot** | Delete a snapshot. |

---

### 💾 Export

| Tool | Description |
| :--- | :--- |
| **export_step** | Exports the model as a **STEP** file. |
| **export_stl** | Exports the model as an **STL** file. |


## Architecture

### MCP_Server.py
- Defines MCP server, tools, and prompts
- Handles HTTP calls to Fusion add-in

### MCP.py
- Fusion Add-in
- Because the Fusion API is not thread-safe, this uses:
  - Custom event handler
  - Task queue

---
### Why This Architecture?

The Fusion 360 API is **not thread-safe** and requires all operations to run on the main UI thread. Our solution:

1. **Event-Driven Design** - Use Fusion's CustomEvent system
2. **Task Queue** - Queue operations for sequential execution
3. **Async Bridge** - HTTP server handles async MCP requests

---

## 📊 Telemetry (Optional)

The MCP Server includes **optional, privacy-focused telemetry** to help understand which tools are most useful and which ones need improvement. This uses [PostHog](https://posthog.com), an open-source analytics platform.

### What We Collect

| Level | Data Collected |
| :--- | :--- |
| **off** | Nothing - telemetry completely disabled |
| **basic** | Tool names, success/failure, error types (no parameters) |
| **detailed** | Above + sanitized parameters (no file paths, scripts, or personal data) |

### What We DON'T Collect
- ❌ File paths or directory names
- ❌ Script contents
- ❌ Personal information
- ❌ Fusion 360 model data
- ❌ API keys or tokens

### Controlling Telemetry

**Via MCP Tools:**
```
# Check current status
get_telemetry_info()

# Disable telemetry
configure_telemetry("off")

# Enable basic telemetry
configure_telemetry("basic")

# Enable detailed telemetry
configure_telemetry("detailed")
```

**Via Environment Variable:**
```bash
# Disable telemetry before starting the server
export FUSION_MCP_TELEMETRY=off
```

**Via Config File:**
Edit `%APPDATA%\fusion360-mcp\telemetry.json`:
```json
{
  "level": "off"
}
```

### Why Telemetry?

Telemetry helps us:
- Understand which tools are actually used
- Identify tools that frequently fail
- Prioritize improvements
- Make data-driven development decisions

Your privacy is important - all data is anonymous and we use a secure, write-only API key.

   
## Security Considerations 🔒
- Local execution → safe by default
- Currently HTTP (OK locally, insecure on networks)
- Validate tool inputs to avoid prompt injection
- Real security depends on tool implementation

---

### This is NOT

- ❌ A production-ready tool
- ❌ A replacement for professional CAD software
- ❌ Suitable for critical engineering work
- ❌ Officially supported by Autodesk

### This IS

- ✅ A proof-of-concept
- ✅ An educational project
- ✅ A demonstration of MCP capabilities
- ✅ A tool for rapid prototyping and learning

---

**This is a proof-of-concept, not production software.**

---

## 🛠️ Developer Setup

For development, you can install the add-in as a **symbolic link** so changes to the source code are immediately reflected in Fusion 360 without re-running the install script.

### Enable Symlink Mode (Recommended)

**Option 1: Enable Windows Developer Mode (one-time setup)**
1. Open **Windows Settings** → **Privacy & Security** → **For developers**
2. Enable **Developer Mode**
3. Run `python Install_Addin.py`

**Option 2: Run as Administrator**
```powershell
# Open PowerShell as Administrator
cd path\to\Autodesk-Fusion-360-MCP-Server
python Install_Addin.py
```

### How it works

- **Symlink mode**: Creates a symbolic link from Fusion's AddIns folder to your source. Changes are instant - just restart Fusion 360.
- **Copy mode** (fallback): Copies files to Fusion's AddIns folder. You must re-run `Install_Addin.py` after each change.

The install script automatically detects if symlinks are available and falls back to copy mode if not.

### Running Tests

```bash
# MCP Add-in tests (mocks Fusion 360 API)
cd MCP
python -m pytest lib/tests -v

# Server tests
cd Server
python -m pytest tests -v
```

---

## Related Projects

Other Fusion 360 MCP implementations (independent projects, not forks):

| Project | Tools | Approach | Notes |
|---------|-------|----------|-------|
| [ArchimedesCrypto/fusion360-mcp-server](https://github.com/ArchimedesCrypto/fusion360-mcp-server) | ~10 | Script generation | Generates Python scripts to copy/paste into Fusion |
| [Misterbra/fusion360-claude-ultimate](https://github.com/Misterbra/fusion360-claude-ultimate) | ~15 | File-based | French adaptation of Japanese tutorial |
| [sockcymbal/autodesk-fusion-mcp-python](https://github.com/sockcymbal/autodesk-fusion-mcp-python) | 1 | HTTP | Hackathon PoC, cube generation only |
| [Joe-Spencer/fusion-mcp-server](https://github.com/Joe-Spencer/fusion-mcp-server) | ~3 | SSE + File | Focus on resources/prompts |
| [KevinZhao-07/Fusion-Mcp-Server](https://github.com/KevinZhao-07/Fusion-Mcp-Server) | ~8 | HTTP | Basic geometry tools |

**This implementation** provides 50+ tools including unique features: arbitrary script execution (`execute_fusion_script`), 9 measurement tools, parametric analysis, construction geometry, testing/snapshot framework, and optional telemetry.

---

## Credits

**Justus Braitinger** ([@JustusBraitinger](https://github.com/JustusBraitinger)) — Original author
- Created the Fusion 360 Add-In architecture and command/palette system
- Designed the HTTP server + task queue pattern for thread-safe Fusion API access
- Implemented core CAD tools (primitives, sketches, extrusion, operations)

**Markus Cozowicz** ([@eisber](https://github.com/eisber)) — Architecture refactoring
- Modular codebase structure (`lib/features/`, `lib/geometry/`, `lib/utils/`, `lib/server/`)
- Server-Sent Events (SSE) for bi-directional communication
- Test infrastructure with mocked Fusion 360 API
- Measurement, parametric, and testing tools

---

## Contact

- [@eisber](https://github.com/eisber)
- justus@braitinger.org
