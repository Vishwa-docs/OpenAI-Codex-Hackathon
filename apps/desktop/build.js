const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const APP_NAME = "Cloud Migration Cockpit";
const ROOT = path.resolve(__dirname, "../..");
const SOURCE_APP = path.join(ROOT, "node_modules", "electron", "dist", "Electron.app");
const DIST_DIR = path.join(__dirname, "dist");
const DEST_APP = path.join(DIST_DIR, `${APP_NAME}.app`);
const PUBLIC_DOWNLOADS_DIR = path.join(ROOT, "apps", "web", "public", "downloads");
const ZIP_PATH = path.join(PUBLIC_DOWNLOADS_DIR, "cloud-migration-cockpit-judge-macos.zip");
const RUNTIME_PATH = path.join(DEST_APP, "Contents", "Resources", "app", "desktop-runtime.json");

function replacePlistValue(contents, key, value) {
  return contents.replace(new RegExp(`(<key>${key}</key>\\s*<string>)([^<]*)(</string>)`), `$1${value}$3`);
}

function ensureClean(pathname) {
  fs.rmSync(pathname, { recursive: true, force: true });
}

function copyDesktopResources() {
  const appResources = path.join(DEST_APP, "Contents", "Resources", "app");
  fs.mkdirSync(appResources, { recursive: true });
  for (const file of ["main.js", "preload.js", "package.json"]) {
    fs.copyFileSync(path.join(__dirname, file), path.join(appResources, file));
  }

  fs.writeFileSync(
    path.join(appResources, "desktop-runtime.json"),
    JSON.stringify(
      {
        workspaceRoot: ROOT,
        appMode: "judge",
        apiPort: 8000,
        workerPort: 8001,
        webPort: 3000,
        apiHealthUrl: "http://127.0.0.1:8000/api/v1/health",
        workerHealthUrl: "http://127.0.0.1:8001/health",
        intakeUrl: "http://127.0.0.1:3000/projects/new",
      },
      null,
      2
    )
  );
}

function renameBundle() {
  const macOsDir = path.join(DEST_APP, "Contents", "MacOS");
  fs.renameSync(path.join(macOsDir, "Electron"), path.join(macOsDir, APP_NAME));

  const infoPlistPath = path.join(DEST_APP, "Contents", "Info.plist");
  let infoPlist = fs.readFileSync(infoPlistPath, "utf8");
  infoPlist = replacePlistValue(infoPlist, "CFBundleDisplayName", APP_NAME);
  infoPlist = replacePlistValue(infoPlist, "CFBundleExecutable", APP_NAME);
  infoPlist = replacePlistValue(infoPlist, "CFBundleName", APP_NAME);
  infoPlist = replacePlistValue(infoPlist, "CFBundleIdentifier", "com.openai.cloudmigrationcockpit");
  fs.writeFileSync(infoPlistPath, infoPlist);
}

function buildZip() {
  fs.mkdirSync(PUBLIC_DOWNLOADS_DIR, { recursive: true });
  ensureClean(ZIP_PATH);
  execFileSync("ditto", ["-c", "-k", "--sequesterRsrc", "--keepParent", DEST_APP, ZIP_PATH], {
    stdio: "inherit",
  });
}

function main() {
  if (!fs.existsSync(SOURCE_APP)) {
    throw new Error(`Electron.app was not found at ${SOURCE_APP}. Run npm install first.`);
  }

  fs.mkdirSync(DIST_DIR, { recursive: true });
  ensureClean(DEST_APP);
  fs.cpSync(SOURCE_APP, DEST_APP, { recursive: true });
  renameBundle();
  copyDesktopResources();
  buildZip();

  console.log(`Built ${DEST_APP}`);
  console.log(`Packaged download ${ZIP_PATH}`);
  console.log(`Runtime manifest ${RUNTIME_PATH}`);
}

main();
