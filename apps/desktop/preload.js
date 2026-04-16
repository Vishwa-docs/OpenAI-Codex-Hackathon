const { contextBridge } = require("electron");
const fs = require("fs");
const path = require("path");

function readRuntime() {
  const runtimePath = path.join(__dirname, "desktop-runtime.json");
  if (!fs.existsSync(runtimePath)) {
    return null;
  }

  return JSON.parse(fs.readFileSync(runtimePath, "utf8"));
}

contextBridge.exposeInMainWorld("cockpitDesktop", {
  platform: process.platform,
  packaged: process.env.NODE_ENV === "production",
  runtime: readRuntime(),
});
