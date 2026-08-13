/**
 * AuraBiz Desktop — Preload for Web Dashboard Mode
 * Exposes minimal IPC bridge for desktop-specific features.
 */
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("desktopAPI", {
  // Platform info
  platform: process.platform,
  isElectron: true,

  // Load web dashboard after license login
  loadDashboard: (token) => ipcRenderer.invoke("app:loadDashboard", token),

  // File dialog (for exports, etc.)
  saveFile: (defaultName, data) => ipcRenderer.invoke("dialog:saveFile", defaultName, data),

  // App info
  getVersion: () => ipcRenderer.invoke("app:version"),

  // Notifications
  notify: (title, body) => ipcRenderer.invoke("notify", title, body),

  // Window controls
  minimize: () => ipcRenderer.invoke("window:minimize"),
  maximize: () => ipcRenderer.invoke("window:maximize"),
  close: () => ipcRenderer.invoke("window:close"),

  // Logging
  log: (msg) => ipcRenderer.send("ipc-log", msg),

  // Bot diagnostics
  getBotDiagnostics: () => ipcRenderer.invoke("bot:diagnostics"),
});
