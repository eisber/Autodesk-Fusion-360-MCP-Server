/**
 * Build script for Claude Desktop Extension (.mcpb)
 *
 * Creates a .mcpb file which is a ZIP archive containing:
 * - manifest.json
 * - dist/ (compiled JavaScript)
 * - icon.png (optional)
 */

import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
import archiver from "archiver";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, "..");

const OUTPUT_FILE = path.join(ROOT_DIR, "fusion360-mcp.mcpb");
const DIST_DIR = path.join(ROOT_DIR, "dist");

async function build(): Promise<void> {
  console.log("Building Claude Desktop Extension (.mcpb)...\n");

  // Ensure dist exists
  if (!fs.existsSync(DIST_DIR)) {
    console.error("Error: dist/ directory not found.");
    console.error("Run 'npm run build' first to compile TypeScript.");
    process.exit(1);
  }

  // Check manifest exists
  const manifestPath = path.join(ROOT_DIR, "manifest.json");
  if (!fs.existsSync(manifestPath)) {
    console.error("Error: manifest.json not found.");
    process.exit(1);
  }

  // Create output stream
  const output = fs.createWriteStream(OUTPUT_FILE);
  const archive = archiver("zip", { zlib: { level: 9 } });

  output.on("close", () => {
    const sizeKB = (archive.pointer() / 1024).toFixed(2);
    console.log(`\n✓ Created ${path.basename(OUTPUT_FILE)} (${sizeKB} KB)`);
    console.log(`  Location: ${OUTPUT_FILE}`);
    console.log("\nTo install:");
    console.log("  1. Open Claude Desktop");
    console.log("  2. Go to Settings > Extensions");
    console.log("  3. Click 'Install from file'");
    console.log(`  4. Select ${path.basename(OUTPUT_FILE)}`);
  });

  archive.on("error", (err) => {
    throw err;
  });

  archive.on("warning", (err) => {
    if (err.code === "ENOENT") {
      console.warn("Warning:", err.message);
    } else {
      throw err;
    }
  });

  archive.pipe(output);

  // Add manifest.json
  console.log("Adding manifest.json");
  archive.file(manifestPath, { name: "manifest.json" });

  // Add compiled JS files
  console.log("Adding dist/ directory");
  archive.directory(DIST_DIR, "dist");

  // Add package.json (needed for dependencies resolution)
  const packageJsonPath = path.join(ROOT_DIR, "package.json");
  if (fs.existsSync(packageJsonPath)) {
    console.log("Adding package.json");
    archive.file(packageJsonPath, { name: "package.json" });
  }

  // Add node_modules (only production dependencies)
  const nodeModulesPath = path.join(ROOT_DIR, "node_modules");
  if (fs.existsSync(nodeModulesPath)) {
    console.log("Adding node_modules (production dependencies)");
    // Add only the necessary modules
    const prodDeps = [
      "@modelcontextprotocol",
      "posthog-node",
      "zod",
      // Add transitive dependencies as needed
    ];

    for (const dep of prodDeps) {
      const depPath = path.join(nodeModulesPath, dep);
      if (fs.existsSync(depPath)) {
        archive.directory(depPath, `node_modules/${dep}`);
      }
    }
  }

  // Add icon if exists
  const iconPath = path.join(ROOT_DIR, "icon.png");
  if (fs.existsSync(iconPath)) {
    console.log("Adding icon.png");
    archive.file(iconPath, { name: "icon.png" });
  } else {
    console.log("Note: icon.png not found (optional)");
  }

  // Add README if exists
  const readmePath = path.join(ROOT_DIR, "README.md");
  if (fs.existsSync(readmePath)) {
    console.log("Adding README.md");
    archive.file(readmePath, { name: "README.md" });
  }

  await archive.finalize();
}

build().catch((error) => {
  console.error("Build failed:", error);
  process.exit(1);
});
