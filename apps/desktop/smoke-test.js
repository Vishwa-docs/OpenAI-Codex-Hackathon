const fs = require("fs");
const path = require("path");

const appBundle = path.join(__dirname, "dist", "Cloud Migration Cockpit.app");
const runtimeManifest = path.join(appBundle, "Contents", "Resources", "app", "desktop-runtime.json");
const downloadZip = path.join(__dirname, "..", "web", "public", "downloads", "cloud-migration-cockpit-judge-macos.zip");
const requiredFiles = [appBundle, runtimeManifest, downloadZip];
const missing = requiredFiles.filter((file) => !fs.existsSync(file));

if (missing.length > 0) {
  console.error(`Missing desktop files: ${missing.join(", ")}`);
  process.exit(1);
}

console.log("Desktop package smoke test passed.");
