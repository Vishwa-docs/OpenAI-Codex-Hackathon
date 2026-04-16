const { app, BrowserWindow, dialog } = require("electron");
const path = require("path");

function createWindow() {
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

  const targetUrl = process.env.COCKPIT_DESKTOP_URL || "http://127.0.0.1:3000/projects/new";
  window.loadURL(targetUrl);

  window.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("second-instance", async () => {
  const result = await dialog.showMessageBox({
    type: "info",
    title: "Cloud Migration Cockpit",
    message: "The desktop shell is already running.",
  });
  return result.response;
});
