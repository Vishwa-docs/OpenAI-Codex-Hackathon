const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("cockpitDesktop", {
  platform: process.platform,
  packaged: process.env.NODE_ENV === "production",
});
