# Fusion MCP Integration

https://github.com/user-attachments/assets/46c8140e-377d-4618-a304-03861cb3d7d9

## 🎯 About

Fusion MCP Integration bridges AI assistants with Autodesk Fusion 360 through the Model Context Protocol (MCP). This enables:

- ✨ **Conversational CAD** - Create 3D models using natural language
- 🤖 **AI-Driven Automation** - Automate repetitive modeling tasks
- 🔧 **Parametric Control** - Dynamically modify design parameters
- 🎓 **Accessible CAD** - Lower the barrier for non-CAD users

> **Note:** This is designed as an assistive tool and educational project, not a replacement for professional CAD workflows.

---

## ⚡ Quick Start (5 Minutes)

**Prerequisites:** [Python 3.10+](https://python.org), [Autodesk Fusion 360](https://autodesk.com/fusion360), [uv](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# 1. Clone the repository
git clone https://github.com/JustusBraitinger/FusionMCP
cd FusionMCP

# 2. Install Python dependencies
cd Server
uv sync
cd ..

# 3. Install Fusion 360 Add-In
python Install_Addin.py

# 4. Enable Add-In in Fusion 360:
#    Fusion 360 → Utilities → Scripts and Add-Ins → Add-Ins tab
#    Select "MCP" → Click "Run" → ✅ Check "Run on Startup"

# 5. Connect your AI assistant (see below)
```

---

## 🔌 Connect to AI Assistants

### Claude Code (Recommended)

```bash
# One-liner installation (replace path)
claude mcp add fusion-mcp --transport stdio -- uv run --directory /path/to/FusionMCP/Server python MCP_Server.py --server_type stdio

# Or just open the repo in Claude Code - .mcp.json auto-configures it
```

### VS Code with GitHub Copilot

**Option 1:** Open this repository in VS Code — the `.vscode/mcp.json` auto-configures everything.

**Option 2:** Add to global config at `%APPDATA%\Code\User\globalStorage\github.copilot-chat\mcp.json`:

```json
{
  "servers": {
    "fusion-mcp": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "C:/path/to/FusionMCP/Server", "python", "MCP_Server.py", "--server_type", "stdio"]
    }
  }
}
```

### Claude Desktop

```bash
cd FusionMCP/Server
uv run mcp install MCP_Server.py
```

Or edit Claude's config (`Settings → Developer → Edit Config`):

```json
{
  "mcpServers": {
    "FusionMCP": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\Path\\to\\FusionMCP\\Server", "python", "MCP_Server.py"]
    }
  }
}
```

> **Note:** Windows paths in JSON require double backslashes `\\`

---

## 🔧 Fusion 360 Add-In Installation (Detailed)

### Step 1: Run the Install Script

```bash
python Install_Addin.py
```

This automatically:
- Finds your Fusion 360 AddIns folder
- Creates a **symbolic link** (best) or copies files (fallback)

### Step 2: Enable the Add-In in Fusion 360

1. Open **Fusion 360**
2. Press **`Shift+S`** (or go to `Utilities → Scripts and Add-Ins`)
3. Click the **`Add-Ins`** tab
4. Select **`MCP`** from the list
5. Click **`Run`**
6. ✅ Check **"Run on Startup"** for auto-enable

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "MCP" not in list | Re-run `python Install_Addin.py`, restart Fusion 360 |
| Symlink error | Enable **Developer Mode** (Windows Settings → For Developers) OR run as Admin |
| Add-In won't start | Check `View → Text Commands` in Fusion for errors |
| Connection refused | Ensure the Add-In is running (check Add-Ins panel) |

### Manual Installation

1. Navigate to: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns`
2. Copy the entire `MCP` folder there
3. Restart Fusion 360 and enable via Add-Ins panel

---

## 🛠️ Available Tools

### 🔧 Core Scripting

| Tool | Description |
| :--- | :--- |
| **execute_fusion_script** | Execute Python code directly in Fusion 360. Primary method for geometry creation. |
| **cancel_fusion_task** | Cancel a long-running task. |

### 📏 Measurement Tools (9 tools)

| Tool | Description |
| :--- | :--- |
| **measure_distance** | Measure minimum distance between entities. |
| **measure_angle** | Measure angle between faces or edges. |
| **measure_area** | Measure face area. |
| **measure_volume** | Measure body volume. |
| **measure_edge_length** | Measure edge length. |
| **measure_body_properties** | Get volume, surface area, bounding box, centroid. |
| **measure_point_to_point** | Measure distance between two 3D points. |
| **get_edges_info** | Get edge details (length, type, endpoints). |
| **get_vertices_info** | Get vertex positions. |

### 🔍 Inspection Tools

| Tool | Description |
| :--- | :--- |
| **get_model_state** | Get body count, sketch count, etc. |
| **get_faces_info** | Get face details (area, type, geometry). |
| **inspect_adsk_api** | Explore the Fusion 360 API. |
| **get_adsk_class_info** | Get documentation for adsk classes. |

### ⚙️ Parameters

| Tool | Description |
| :--- | :--- |
| **list_parameters** | List all model parameters. |
| **set_parameter** | Change a parameter value. |
| **create_user_parameter** | Create a new user parameter. |

### 🏗️ Parametric & Construction

| Tool | Description |
| :--- | :--- |
| **check_all_interferences** | Check for body interference. |
| **list_construction_geometry** | List construction planes, axes, points. |
| **suppress_feature** | Suppress/unsuppress timeline features. |

### 🧪 Testing & Snapshots

| Tool | Description |
| :--- | :--- |
| **save_test** / **load_tests** / **run_tests** / **delete_test** | Save and run validation tests. |
| **create_snapshot** / **list_snapshots** / **restore_snapshot** / **delete_snapshot** | Snapshot and rollback model state. |

### 🔧 Infrastructure

| Tool | Description |
| :--- | :--- |
| **test_connection** | Test connection to Fusion 360. |
| **undo** | Undo the last action. |
| **delete_all** | Delete all bodies. |
| **get_telemetry_info** / **configure_telemetry** | Manage telemetry. |

---

## 🏗️ Architecture

```
┌─────────────────┐     MCP Protocol      ┌──────────────────┐
│   AI Assistant  │◄────────────────────►│   MCP_Server.py  │
│ (Claude/Copilot)│    (stdio/SSE)        │   (Python)       │
└─────────────────┘                       └────────┬─────────┘
                                                   │ HTTP
                                                   ▼
                                          ┌──────────────────┐
                                          │   Fusion Add-In  │
                                          │   (MCP.py)       │
                                          └────────┬─────────┘
                                                   │ Fusion API
                                                   ▼
                                          ┌──────────────────┐
                                          │   Fusion 360     │
                                          └──────────────────┘
```

**Why this architecture?** The Fusion 360 API is **not thread-safe** and requires operations on the main UI thread. The Add-In uses a custom event handler + task queue to safely bridge HTTP requests.

### MCP.py
- Fusion Add-In with custom event handler + task queue
- Safe bridging of HTTP requests to Fusion's main UI thread

---

## 📊 Telemetry (Optional)

The MCP Server includes **optional, privacy-focused telemetry** using [PostHog](https://posthog.com).

| Level | Data Collected |
| :--- | :--- |
| **off** | Nothing |
| **basic** | Tool names, success/failure, error types |
| **detailed** | Above + sanitized parameters (no file paths or scripts) |

**We DON'T collect:** File paths, script contents, personal info, model data, API keys.

```bash
# Disable via environment variable
export FUSION_MCP_TELEMETRY=off

# Or via tool
configure_telemetry("off")
```

---

## 🔒 Security

- ✅ Local execution only → safe by default
- ⚠️ HTTP communication (OK locally, insecure over networks)
- ⚠️ Scripts execute with full Fusion API access

---

## ⚠️ Disclaimer

| This is NOT | This IS |
|-------------|---------|
| ❌ Production-ready | ✅ A proof-of-concept |
| ❌ Professional CAD replacement | ✅ An educational project |
| ❌ For critical engineering | ✅ MCP capabilities demo |
| ❌ Officially Autodesk-supported | ✅ Rapid prototyping tool |

---

## 🛠️ Developer Setup

### Symlink Mode (Instant Updates)

```powershell
# Option 1: Enable Windows Developer Mode
#   Settings → Privacy & Security → For Developers → Enable

# Option 2: Run as Administrator
python Install_Addin.py
```

### Running Tests

```bash
cd Server && python -m pytest tests -v      # Server tests
cd MCP && python -m pytest lib/tests -v     # Add-in tests
```

---

## 🔗 Related Projects

| Project | Tools | Notes |
|---------|-------|-------|
| [ArchimedesCrypto/fusion360-mcp-server](https://github.com/ArchimedesCrypto/fusion360-mcp-server) | ~10 | Script generation |
| [Misterbra/fusion360-claude-ultimate](https://github.com/Misterbra/fusion360-claude-ultimate) | ~15 | French adaptation |
| [Joe-Spencer/fusion-mcp-server](https://github.com/Joe-Spencer/fusion-mcp-server) | ~3 | SSE + File |

**This implementation** provides 25+ tools with unique features: arbitrary script execution, 9 measurement tools, API inspection, parametric analysis, and testing/snapshot framework.

---

## 👥 Credits

**Justus Braitinger** ([@JustusBraitinger](https://github.com/JustusBraitinger)) — Original author

**Markus Cozowicz** ([@eisber](https://github.com/eisber)) — Architecture refactoring

---

## 📬 Contact

- [@eisber](https://github.com/eisber)
- justus@braitinger.org
