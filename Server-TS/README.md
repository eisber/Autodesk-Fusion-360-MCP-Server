# Fusion 360 MCP Server (TypeScript)

A TypeScript implementation of the MCP (Model Context Protocol) server for Autodesk Fusion 360.

## Features

- **33+ Tools** for interacting with Fusion 360:
  - Infrastructure: test_connection, get_model_state, undo, delete_all
  - Scripting: execute_fusion_script (execute arbitrary Python in Fusion 360)
  - Inspection: inspect_adsk_api, get_faces_info, get_edges_info, get_vertices_info
  - Measurement: measure_distance, measure_angle, measure_area, measure_volume, etc.
  - Parameters: list_parameters, set_parameter, create_user_parameter
  - Parametric: check_all_interferences, list_construction_geometry, suppress_feature
  - Testing: create_snapshot, restore_snapshot, save_test, run_tests
  - Telemetry: configure_telemetry

- **Real-time SSE Communication** with Fusion 360 Add-In
- **Progress Reporting** for long-running scripts
- **Anonymous Telemetry** (opt-out available) for improving the server

## Prerequisites

1. **Node.js 18+** installed
2. **Fusion 360** with the MCP Add-In installed and running
3. **Claude Desktop** (for using as a Desktop Extension)

## Installation

### As a Claude Desktop Extension

1. Build the extension:
   ```bash
   cd Server-TS
   npm install
   npm run build
   npm run package
   ```

2. Install in Claude Desktop:
   - Open Claude Desktop
   - Go to Settings > Extensions
   - Click "Install from file"
   - Select `fusion360-mcp.mcpb`

### Manual Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fusion360": {
      "command": "node",
      "args": ["/path/to/Server-TS/dist/index.js", "--server_type=stdio"]
    }
  }
}
```

## Development

### Install Dependencies

```bash
npm install
```

### Build

```bash
npm run build
```

### Run Tests

```bash
npm test
```

### Run in Development Mode

```bash
npm run dev
```

## Configuration

### Environment Variables

- `FUSION_MCP_BASE_URL` - Base URL for the Fusion 360 Add-In server (default: `http://localhost:5000`)
- `FUSION_MCP_TELEMETRY` - Telemetry level: `off`, `basic`, or `detailed`

### Telemetry

This server collects anonymous usage data to help improve the project:
- Tool names and success/failure rates
- Error types (no personal data)
- Platform information

To opt out:
```bash
export FUSION_MCP_TELEMETRY=off
```

Or use the `configure_telemetry` tool:
```
configure_telemetry("off")
```

## Project Structure

```
Server-TS/
├── src/
│   ├── index.ts           # Entry point, MCP server setup
│   ├── config.ts          # Configuration
│   ├── instructions.ts    # System instructions
│   ├── prompts.ts         # Prompt templates
│   ├── sse-client.ts      # SSE client for Fusion Add-In
│   ├── telemetry.ts       # PostHog telemetry
│   └── tools/
│       ├── index.ts       # Tool exports
│       ├── base.ts        # Base utilities
│       ├── validation.ts  # Infrastructure tools
│       ├── scripting.ts   # Script execution
│       ├── measurement.ts # Measurement tools
│       ├── inspection.ts  # API inspection
│       ├── parameters.ts  # Parameter tools
│       ├── parametric.ts  # Parametric tools
│       ├── testing.ts     # Test tools
│       └── telemetry-tools.ts
├── tests/
│   └── *.test.ts          # Vitest tests
├── scripts/
│   └── build-mcpb.ts      # Desktop Extension builder
├── manifest.json          # Desktop Extension manifest
├── package.json
└── tsconfig.json
```

## License

MIT
