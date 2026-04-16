const { app, BrowserWindow, dialog, shell } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const SINGLE_INSTANCE = app.requestSingleInstanceLock();
if (!SINGLE_INSTANCE) {
  app.quit();
}

let mainWindow = null;
let stackProcess = null;
let stackWasStartedByDesktop = false;

function readRuntimeConfig() {
  const runtimePath = path.join(__dirname, "desktop-runtime.json");
  if (fs.existsSync(runtimePath)) {
    return JSON.parse(fs.readFileSync(runtimePath, "utf8"));
  }

  return {
    workspaceRoot: path.resolve(__dirname, "../.."),
    appMode: "judge",
    apiPort: 8000,
    workerPort: 8001,
    webPort: 3000,
    apiHealthUrl: "http://127.0.0.1:8000/api/v1/health",
    workerHealthUrl: "http://127.0.0.1:8001/health",
    intakeUrl: "http://127.0.0.1:3000/projects/new",
  };
}

function resolvePythonBinary(workspaceRoot) {
  const venvPython = path.join(workspaceRoot, ".venv", "bin", "python");
  if (fs.existsSync(venvPython)) {
    return venvPython;
  }
  return "python3";
}

async function waitForUrl(url, timeoutMs = 90000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return true;
      }
    } catch (_error) {
      // Keep waiting while services start.
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  return false;
}

async function ensureLocalStack(runtime) {
  const checks = await Promise.all([
    waitForUrl(runtime.apiHealthUrl, 2500),
    waitForUrl(runtime.workerHealthUrl, 2500),
    waitForUrl(runtime.intakeUrl, 2500),
  ]);
  if (checks.every(Boolean)) {
    return;
  }

  if (!fs.existsSync(runtime.workspaceRoot)) {
    throw new Error(`Workspace root not found: ${runtime.workspaceRoot}`);
  }

  if (!stackProcess || stackProcess.exitCode !== null) {
    const logDir = path.join(runtime.workspaceRoot, "artifacts");
    const logPath = path.join(logDir, "desktop-stack.log");
    fs.mkdirSync(logDir, { recursive: true });
    const logFd = fs.openSync(logPath, "a");
    const pythonBinary = resolvePythonBinary(runtime.workspaceRoot);
    const scriptPath = path.join(runtime.workspaceRoot, "scripts", "dev_stack.py");
    stackProcess = spawn(
      pythonBinary,
      [
        scriptPath,
        "--skip-infra",
        "--app-mode",
        runtime.appMode,
        "--no-reload",
        "--api-port",
        String(runtime.apiPort),
        "--worker-port",
        String(runtime.workerPort),
        "--web-port",
        String(runtime.webPort),
      ],
      {
        cwd: runtime.workspaceRoot,
        env: {
          ...process.env,
          APP_MODE: runtime.appMode,
          NEXT_PUBLIC_APP_MODE: runtime.appMode,
          NEXT_PUBLIC_DEFAULT_WORKSPACE_ID: "workspace-judge",
          NEXT_PUBLIC_API_BASE_URL: `http://127.0.0.1:${runtime.apiPort}/api/v1`,
          NEXT_PUBLIC_WORKER_BASE_URL: `http://127.0.0.1:${runtime.workerPort}`,
          NEXT_PUBLIC_DESKTOP_DOWNLOAD_URL: "/downloads/cloud-migration-cockpit-judge-macos.zip",
        },
        stdio: ["ignore", logFd, logFd],
      }
    );
    stackWasStartedByDesktop = true;
  }

  const started = await Promise.all([
    waitForUrl(runtime.apiHealthUrl, 90000),
    waitForUrl(runtime.workerHealthUrl, 90000),
    waitForUrl(runtime.intakeUrl, 90000),
  ]);
  if (!started.every(Boolean)) {
    throw new Error("The local web, API, and worker services did not all become healthy in time.");
  }
}

function stopLocalStack() {
  if (!stackWasStartedByDesktop || !stackProcess || stackProcess.exitCode !== null) {
    return;
  }

  stackProcess.kill("SIGTERM");
  stackProcess = null;
}

function createWindow(targetUrl) {
  const window = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1200,
    minHeight: 800,
    backgroundColor: "#020617",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });

  window.loadURL(targetUrl);

  window.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  return window;
}

app.whenReady().then(async () => {
  try {
    const runtime = readRuntimeConfig();
    await ensureLocalStack(runtime);
    mainWindow = createWindow(process.env.COCKPIT_DESKTOP_URL || runtime.intakeUrl);
  } catch (error) {
    dialog.showErrorBox(
      "Cloud Migration Cockpit",
      error instanceof Error ? error.message : "The local runtime failed to start."
    );
    mainWindow = createWindow("data:text/html,<html><body style='background:#020617;color:white;font-family:sans-serif;padding:32px'><h1>Cloud Migration Cockpit</h1><p>The local runtime failed to start. Check artifacts/desktop-stack.log and relaunch the app.</p></body></html>");
  }

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      const runtime = readRuntimeConfig();
      mainWindow = createWindow(process.env.COCKPIT_DESKTOP_URL || runtime.intakeUrl);
    }
  });
});

app.on("window-all-closed", () => {
  stopLocalStack();
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  stopLocalStack();
});

app.on("second-instance", () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) {
      mainWindow.restore();
    }
    mainWindow.focus();
  }
});
