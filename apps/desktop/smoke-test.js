const path = require("path");
const fs = require("fs");

const requiredFiles = ["main.js", "preload.js", "package.json"];
const missing = requiredFiles.filter((file) => !fs.existsSync(path.join(__dirname, file)));

if (missing.length > 0) {
  console.error(`Missing desktop files: ${missing.join(", ")}`);
  process.exit(1);
}

console.log("Desktop shell smoke test passed.");
