/**
 * AuraBiz Desktop App — Preload Script
 * Exposes a safe, minimal API to the renderer via contextBridge.
 */
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  // License
  licenseActivate: (licenseKey) => ipcRenderer.invoke("license:activate", { licenseKey }),
  licenseValidate: () => ipcRenderer.invoke("license:validate"),
  licenseStatus: () => ipcRenderer.invoke("license:status"),

  // Products (local storage)
  productsList: () => ipcRenderer.invoke("products:list"),
  productsAdd: (p) => ipcRenderer.invoke("products:add", p),
  productsUpdate: (p) => ipcRenderer.invoke("products:update", p),
  productsDelete: (id) => ipcRenderer.invoke("products:delete", id),

  // AI
  aiSetTier: (tier) => ipcRenderer.invoke("ai:setTier", tier),
  aiGetTier: () => ipcRenderer.invoke("ai:getTier"),
  aiReply: (message) => ipcRenderer.invoke("ai:reply", { message }),

  // Business Setup
  businessSaveSetup: (data) => ipcRenderer.invoke("business:saveSetup", data),
  businessGetSetup: () => ipcRenderer.invoke("business:getSetup"),

  // WhatsApp Bot (local bot on port 8001)
  botGetQR: () => ipcRenderer.invoke("bot:getQR"),
  botGetStatus: () => ipcRenderer.invoke("bot:getStatus"),
  botRegister: (businessId) => ipcRenderer.invoke("bot:register", businessId),
  botLogout: () => ipcRenderer.invoke("bot:logout"),
});
