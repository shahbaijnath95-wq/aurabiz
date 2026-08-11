/**
 * AuraBiz Desktop App — Electron Main Process
 *
 * Features:
 *  - License activation/validation against master backend (:8010)
 *  - Local-first SQLite storage (better-sqlite3) for products
 *  - Free AI (built-in Falcon-style rules) vs Paid AI (platform AI keys)
 */
const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("path");
const fs = require("fs");
const os = require("os");
const crypto = require("crypto");
const { spawn } = require("child_process");

// ─── Service processes ───
let masterProcess = null;
let backendProcess = null;
let botProcess = null;
let frontendProcess = null;

// ─── Resource paths (bundled in EXE via extraResources) ───
function getResourcePath(name) {
  // In dev: ./resources/  |  In packaged: process.resourcesPath
  const basePath = app.isPackaged ? process.resourcesPath : path.join(__dirname);
  return path.join(basePath, "resources", name);
}

// ─── Start Master Backend (port 8010) ───
function startMasterBackend() {
  const masterDir = getResourcePath("master");
  const pythonPath = getResourcePath("python");
  const pythonExe = os.platform() === "win32"
    ? path.join(pythonPath, "python.exe")
    : path.join(pythonPath, "bin", "python3");

  if (!fs.existsSync(masterDir)) {
    log("[MASTER] Master backend dir not found — skipping");
    return;
  }

  if (!fs.existsSync(pythonExe)) {
    log("[MASTER] Python not found — using system python");
    masterProcess = spawn("python", ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8010"], {
      cwd: masterDir,
      stdio: ["ignore", "pipe", "pipe"],
    });
  } else {
    log("[MASTER] Starting with bundled Python: " + pythonExe);
    masterProcess = spawn(pythonExe, ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8010"], {
      cwd: masterDir,
      stdio: ["ignore", "pipe", "pipe"],
    });
  }

  masterProcess.stdout?.on("data", (d) => log("[MASTER] " + d.toString().trim()));
  masterProcess.stderr?.on("data", (d) => log("[MASTER] " + d.toString().trim()));
  masterProcess.on("exit", (code) => {
    log("[MASTER] Process exited with code " + code);
    masterProcess = null;
  });
  log("[MASTER] Starting on port 8010...");
}

// ─── Start Python Backend (port 8000) ───
function startBackend() {
  const backendDir = getResourcePath("backend");
  const pythonPath = getResourcePath("python");
  const pythonExe = os.platform() === "win32"
    ? path.join(pythonPath, "python.exe")
    : path.join(pythonPath, "bin", "python3");

  if (!fs.existsSync(pythonExe)) {
    log("[BACKEND] Python not found at: " + pythonExe + " — using system python");
    // Fallback: try system python
    backendProcess = spawn("python", ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"], {
      cwd: backendDir,
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env, PYTHONPATH: backendDir },
    });
  } else {
    log("[BACKEND] Starting with bundled Python: " + pythonExe);
    backendProcess = spawn(pythonExe, ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"], {
      cwd: backendDir,
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env, PYTHONPATH: backendDir },
    });
  }

  backendProcess.stdout?.on("data", (d) => log("[BACKEND] " + d.toString().trim()));
  backendProcess.stderr?.on("data", (d) => log("[BACKEND] " + d.toString().trim()));
  backendProcess.on("exit", (code) => {
    log("[BACKEND] Process exited with code " + code);
    backendProcess = null;
  });
  log("[BACKEND] Starting on port 8000...");
}

// ─── Start WhatsApp Bot (port 8001) ───
function startBot() {
  const botDir = getResourcePath("whatsapp-bot");
  const nodePath = getResourcePath("node");
  const nodeExe = os.platform() === "win32"
    ? path.join(nodePath, "node.exe")
    : path.join(nodePath, "bin", "node");

  const botScript = path.join(botDir, "bot.js");

  if (!fs.existsSync(botScript)) {
    log("[BOT] bot.js not found at: " + botScript + " — skipping bot");
    return;
  }

  if (!fs.existsSync(nodeExe)) {
    log("[BOT] Node not found at: " + nodeExe + " — using system node");
    botProcess = spawn("node", [botScript], {
      cwd: botDir,
      stdio: ["ignore", "pipe", "pipe"],
    });
  } else {
    log("[BOT] Starting with bundled Node: " + nodeExe);
    botProcess = spawn(nodeExe, [botScript], {
      cwd: botDir,
      stdio: ["ignore", "pipe", "pipe"],
    });
  }

  botProcess.stdout?.on("data", (d) => log("[BOT] " + d.toString().trim()));
  botProcess.stderr?.on("data", (d) => log("[BOT] " + d.toString().trim()));
  botProcess.on("exit", (code) => {
    log("[BOT] Process exited with code " + code);
    botProcess = null;
  });
  log("[BOT] Starting on port 8001...");
}

// ─── Start Frontend (port 3003) ───
function startFrontend() {
  const frontendDir = getResourcePath("frontend");
  const nodePath = getResourcePath("node");
  const nodeExe = os.platform() === "win32"
    ? path.join(nodePath, "node.exe")
    : path.join(nodePath, "bin", "node");

  const serverScript = path.join(frontendDir, "server.js");
  const outDir = path.join(frontendDir, "out");

  // Check if static export exists
  if (!fs.existsSync(outDir)) {
    log("[FRONTEND] Static export (out/) not found — skipping");
    return;
  }

  if (!fs.existsSync(serverScript)) {
    log("[FRONTEND] server.js not found at: " + serverScript + " — skipping");
    return;
  }

  if (!fs.existsSync(nodeExe)) {
    log("[FRONTEND] Node not found — using system node");
    frontendProcess = spawn("node", [serverScript], {
      cwd: frontendDir,
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env, PORT: "3003" },
    });
  } else {
    log("[FRONTEND] Starting with bundled Node: " + nodeExe);
    frontendProcess = spawn(nodeExe, [serverScript], {
      cwd: frontendDir,
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env, PORT: "3003" },
    });
  }

  frontendProcess.stdout?.on("data", (d) => log("[FRONTEND] " + d.toString().trim()));
  frontendProcess.stderr?.on("data", (d) => log("[FRONTEND] " + d.toString().trim()));
  frontendProcess.on("exit", (code) => {
    log("[FRONTEND] Process exited with code " + code);
    frontendProcess = null;
  });
  log("[FRONTEND] Starting on port 3003...");
}

// ─── Create test license on first run ───
async function createTestLicenseIfEmpty() {
  try {
    const res = await fetch("http://127.0.0.1:8010/api/license/plans");
    if (!res.ok) return; // Master backend not ready yet
    
    // Check if any licenses exist
    // If master backend is fresh (no DB), create test license
    const pythonPath = getResourcePath("python");
    const pythonExe = path.join(pythonPath, "python.exe");
    const createScript = path.join(getResourcePath("master"), "create_test_license.py");
    
    if (fs.existsSync(pythonExe) && fs.existsSync(createScript)) {
      log("[STARTUP] Creating test license...");
      spawn(pythonExe, [createScript], { stdio: ["ignore", "pipe", "pipe"] });
    } else if (fs.existsSync(createScript)) {
      spawn("python", [createScript], { stdio: ["ignore", "pipe", "pipe"] });
    }
  } catch (e) {
    log("[STARTUP] Could not create test license: " + e.message);
  }
}

// ─── Start all services ───
function startAllServices() {
  log("=== Starting all services ===");
  startMasterBackend();  // Pehle master (license validation ke liye)
  
  // Test license create karo jab master ready ho jaye
  setTimeout(() => createTestLicenseIfEmpty(), 8000);
  
  setTimeout(() => startBackend(), 3000);   // Backend (business data ke liye)
  setTimeout(() => startBot(), 5000);       // WhatsApp Bot
  setTimeout(() => startFrontend(), 7000);  // Frontend Dashboard
}

// ─── Stop all services ───
function stopAllServices() {
  log("=== Stopping all services ===");
  [masterProcess, backendProcess, botProcess, frontendProcess].forEach((proc) => {
    if (proc && !proc.killed) {
      try { proc.kill("SIGTERM"); } catch (e) { /* ignore */ }
    }
  });
}

// ─── File logger for diagnostics ───
const LOG_PATH = path.join(app.getPath("desktop"), "aurabiz_debug.log");
function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  console.log(line.trim());
  try { fs.appendFileSync(LOG_PATH, line); } catch (e) { /* ignore */ }
}
log("=== AuraBiz Desktop starting ===");

// ─── Master backend URL (env override for production) ───
// Cloud URL for license validation, local for everything else
const CLOUD_MASTER_URL = "https://aurabiz.onrender.com";
const MASTER_URL = process.env.AURABIZ_MASTER_URL || CLOUD_MASTER_URL;
const BOT_URL = process.env.AURABIZ_BOT_URL || "http://127.0.0.1:8001";

// ─── Cloud config file ───
const CLOUD_CONFIG_PATH = path.join(app.getPath("userData"), "cloud-config.json");
function getCloudConfig() {
  try {
    if (fs.existsSync(CLOUD_CONFIG_PATH)) return JSON.parse(fs.readFileSync(CLOUD_CONFIG_PATH, "utf-8"));
  } catch (e) { /* ignore */ }
  return {};
}

// ─── Local data dir ───
const DATA_DIR = path.join(app.getPath("userData"), "data");
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

const DB_PATH = path.join(DATA_DIR, "products.json");
const CONFIG_PATH = path.join(DATA_DIR, "config.json");

// ─── Local storage (JSON file — zero native deps, reliable builds) ───
let products = [];

function loadProducts() {
  try {
    if (fs.existsSync(DB_PATH)) {
      products = JSON.parse(fs.readFileSync(DB_PATH, "utf-8"));
      if (!Array.isArray(products)) products = [];
    }
  } catch (e) {
    console.error("Products load error:", e.message);
    products = [];
  }
  return products;
}

function saveProducts() {
  fs.writeFileSync(DB_PATH, JSON.stringify(products, null, 2));
}

function initDb() {
  loadProducts();
  return true;
}

function readConfig() {
  try {
    if (fs.existsSync(CONFIG_PATH)) return JSON.parse(fs.readFileSync(CONFIG_PATH, "utf-8"));
  } catch (e) { /* ignore */ }
  return {};
}

function writeConfig(cfg) {
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(cfg, null, 2));
}

// ─── Machine ID (PC fingerprint) ───
function getMachineId() {
  const raw = [
    os.hostname(),
    os.platform(),
    os.arch(),
    os.cpus()[0]?.model || "",
    os.totalmem(),
    os.userInfo().username,
  ].join("|");
  return crypto.createHash("sha256").update(raw).digest("hex").slice(0, 32);
}

// ─── HTTP helper (Node 18+ fetch, with timeout) ───
const API_TIMEOUT_MS = 8000; // 8s — fail fast so user gets feedback
async function api(pathname, options = {}) {
  const url = `${MASTER_URL}${pathname}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: options.method || "GET",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  } catch (e) {
    if (e.name === "AbortError") throw new Error("Master backend timeout — localhost:8010 reachable nahi hai");
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

// ─── IPC: License ───
ipcMain.handle("license:activate", async (_e, { licenseKey }) => {
  log("[MAIN] license:activate called, key=" + licenseKey);
  try {
    const machineId = getMachineId();
    log("[MAIN] machineId=" + machineId + " calling backend...");
    const result = await api("/api/license/activate", {
      method: "POST",
      body: { license_key: licenseKey.trim().toUpperCase(), machine_id: machineId },
    });
    log("[MAIN] backend returned: " + JSON.stringify(result));
    if (!result || !result.activated) {
      return { ok: false, error: (result && result.detail) || "Activation failed" };
    }
    const cfg = readConfig();
    cfg.license = { license_key: result.license_key, plan: result.plan, ai_tier: result.ai_tier, machine_id: machineId };
    writeConfig(cfg);
    log("[MAIN] license saved to config, returning ok");
    return { ok: true, license_key: result.license_key, plan: result.plan, ai_tier: result.ai_tier, machine_id: machineId };
  } catch (e) {
    log("[MAIN] license:activate EXCEPTION: " + e.message);
    return { ok: false, error: e.message };
  }
});

ipcMain.handle("license:validate", async () => {
  try {
    const cfg = readConfig();
    if (!cfg.license?.license_key) return { ok: false, error: "No license" };
    const result = await api("/api/license/validate", {
      method: "POST",
      body: { license_key: cfg.license.license_key, machine_id: cfg.license.machine_id },
    });
    return { ok: true, ...result };
  } catch (e) {
    return { ok: false, error: e.message };
  }
});

ipcMain.handle("license:status", () => {
  const cfg = readConfig();
  return { ok: !!cfg.license, license: cfg.license || null };
});

// ─── IPC: Products (local JSON storage) ───
ipcMain.handle("products:list", () => {
  return { ok: true, products: loadProducts() };
});

ipcMain.handle("products:add", (_e, p) => {
  if (!p?.name) return { ok: false, error: "Name required" };
  const id = crypto.randomUUID();
  products.push({
    id,
    name: p.name,
    price: Number(p.price) || 0,
    stock: Number(p.stock) || 0,
    unit: p.unit || "piece",
    category: p.category || "",
    description: p.description || "",
    created_at: new Date().toISOString(),
  });
  saveProducts();
  return { ok: true, id };
});

ipcMain.handle("products:update", (_e, p) => {
  const idx = products.findIndex((x) => x.id === p.id);
  if (idx === -1) return { ok: false, error: "Not found" };
  products[idx] = {
    ...products[idx],
    name: p.name,
    price: Number(p.price) || 0,
    stock: Number(p.stock) || 0,
    unit: p.unit || "piece",
    category: p.category || "",
    description: p.description || "",
  };
  saveProducts();
  return { ok: true };
});

ipcMain.handle("products:delete", (_e, id) => {
  products = products.filter((x) => x.id !== id);
  saveProducts();
  return { ok: true };
});

// ─── IPC: AI settings ───
ipcMain.handle("ai:setTier", (_e, tier) => {
  const cfg = readConfig();
  cfg.ai_tier = tier === "paid" ? "paid" : "free";
  writeConfig(cfg);
  return { ok: true, ai_tier: cfg.ai_tier };
});

ipcMain.handle("ai:getTier", () => {
  const cfg = readConfig();
  return { ai_tier: cfg.ai_tier || "free" };
});

// ─── IPC: AI reply (Free = local rules, Paid = platform AI) ───
ipcMain.handle("ai:reply", async (_e, { message }) => {
  const cfg = readConfig();
  const tier = cfg.ai_tier || "free";
  const text = (message || "").trim();
  if (!text) return { ok: true, reply: "Kuch toh likho ji! 😊" };

  if (tier === "paid") {
    // Paid AI: platform ke AI keys se (master ke through) — abhi simple echo + note
    try {
      const result = await api("/api/license/validate", {
        method: "POST",
        body: { license_key: cfg.license?.license_key, machine_id: cfg.license?.machine_id },
      });
      if (result.ok === false) return { ok: true, reply: "License invalid — paid AI band hai." };
      // Demo paid AI reply (production: master ke AI provider endpoints se)
      return {
        ok: true,
        reply: `🤖 [Paid AI] Aapka message: "${text}" — Premium AI reply yahan aayega (master AI keys ke through).`,
      };
    } catch (e) {
      return { ok: true, reply: "Paid AI reach nahi ho paya. Internet/master check karo." };
    }
  }

  // Free AI: local rule-based (Falcon-style)
  const prod = loadProducts();
  const lower = text.toLowerCase();

  if (/price|kitna|rate|dam|cost/.test(lower)) {
    if (prod.length === 0) return { ok: true, reply: "Abhi koi product add nahi hai. Dashboard se product add karo! 📦" };
    const hit = prod.find((p) => lower.includes(p.name.toLowerCase()));
    const target = hit || prod[0];
    return {
      ok: true,
      reply: `${target.name} ki price ₹${target.price} hai. Stock: ${target.stock} ${target.unit}. Kuch aur chahiye? 😊`,
    };
  }
  if (/stock|kitna bacha|available/.test(lower)) {
    const hit = prod.find((p) => lower.includes(p.name.toLowerCase()));
    if (hit) return { ok: true, reply: `${hit.name} ka stock ${hit.stock} ${hit.unit} hai.` };
    return { ok: true, reply: `Total ${prod.length} products hain. Kaunsa dekhna hai? 📦` };
  }
  if (/order|kharid|buy|lena/.test(lower)) {
    return { ok: true, reply: "Order lene ke liye mujhe product ka naam batao — main stock check karke order confirm karunga! ✅" };
  }
  if (/hi|hello|namaste|hii|hey/.test(lower)) {
    return { ok: true, reply: "Namaste ji! 🙏 Main AuraBiz assistant hoon. Product price, stock, order — kuch bhi puchho!" };
  }

  return {
    ok: true,
    reply: `Main samajh gaya: "${text}". Free AI reply hai yeh. Paid AI ke liye Settings me upgrade karo! 🤖`,
  };
});

// ─── IPC: Business Setup ───
ipcMain.handle("business:saveSetup", async (_e, data) => {
  try {
    const cfg = readConfig();
    cfg.business = {
      name: data.name,
      type: data.type,
      upi_id: data.upi_id,
      whatsapp: data.whatsapp,
      address: data.address,
      completed_at: new Date().toISOString(),
    };
    writeConfig(cfg);
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e.message };
  }
});

ipcMain.handle("business:getSetup", () => {
  const cfg = readConfig();
  return { ok: true, business: cfg.business || null, completed: !!cfg.business };
});

// ─── IPC: WhatsApp Bot API (local bot on port 8001) ───
ipcMain.handle("bot:getQR", async () => {
  try {
    const res = await fetch(`${BOT_URL}/qr`);
    return await res.json();
  } catch (e) {
    return { ok: false, error: "WhatsApp bot start nahi hai. Pehle bot chalao.", qr: null, status: "disconnected" };
  }
});

ipcMain.handle("bot:getStatus", async () => {
  try {
    const res = await fetch(`${BOT_URL}/status`);
    return await res.json();
  } catch (e) {
    return { ok: false, error: "Bot unreachable", status: "disconnected" };
  }
});

ipcMain.handle("bot:register", async (_e, businessId) => {
  try {
    const res = await fetch(`${BOT_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ business_id: businessId }),
    });
    return await res.json();
  } catch (e) {
    return { ok: false, error: e.message };
  }
});

ipcMain.handle("bot:logout", async () => {
  try {
    const res = await fetch(`${BOT_URL}/logout`, { method: "POST" });
    return await res.json();
  } catch (e) {
    return { ok: false, error: e.message };
  }
});

// ─── Window ───
function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "AuraBiz — AI WhatsApp Business Assistant",
    backgroundColor: "#faf9f7",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      devTools: true,
      webSecurity: false,
      allowRunningInsecureContent: false,
    },
  });

  // ─── Cache busting: clear session cache on startup ───
  win.webContents.session.clearCache().then(() => {
    log("Session cache cleared on startup");
  }).catch(() => {});

  // ─── Log renderer crashes ───
  win.webContents.on("render-process-gone", (event, details) => {
    log("[RENDERER CRASH] " + details.reason + " - " + (details.error || ""));
  });

  win.webContents.on("console-message", (event, level, message, line, sourceId) => {
    // Log JS errors from renderer (level 2 = error, 3 = warning)
    if (level >= 2) {
      log("[RENDERER " + (level === 2 ? "ERROR" : "WARN") + "] " + message + " (" + sourceId + ":" + line + ")");
    }
  });

  // ─── IPC bridge logging ───
  ipcMain.on("ipc-log", (_e, msg) => {
    log("[IPC] " + msg);
  });

  // ─── Window controls ───
  ipcMain.handle("window:minimize", () => win.minimize());
  ipcMain.handle("window:maximize", () => {
    if (win.isMaximized()) win.unmaximize();
    else win.maximize();
  });
  ipcMain.handle("window:close", () => win.close());

  // ─── App version ───
  ipcMain.handle("app:version", () => app.getVersion());

  // ─── Load web dashboard (after license login) ───
  ipcMain.handle("app:loadDashboard", (_e, token) => {
    log("[MAIN] Loading web dashboard with token");
    // Store token in session for the web frontend
    const FRONTEND_URL = "http://localhost:3003/dashboard";
    win.loadURL(`${FRONTEND_URL}?token=${token}`);
  });

  // ─── Desktop notifications ───
  ipcMain.handle("notify", (_e, title, body) => {
    const { Notification } = require("electron");
    if (Notification.isSupported()) {
      new Notification({ title, body }).show();
    }
  });

  // ─── Save file dialog ───
  ipcMain.handle("dialog:saveFile", async (_e, defaultName, data) => {
    const { dialog } = require("electron");
    const result = await dialog.showSaveDialog(win, {
      defaultPath: defaultName,
      filters: [{ name: "All Files", extensions: ["*"] }],
    });
    if (!result.canceled && result.filePath) {
      fs.writeFileSync(result.filePath, data);
      return { ok: true, path: result.filePath };
    }
    return { ok: false };
  });

  // Local HTML renderer — license-only flow (no web frontend needed)
  log("Loading local renderer: renderer/index.html");

  // Inject cloud URLs into renderer
  const cloudConfig = getCloudConfig();
  if (cloudConfig.master_url) {
    log("[MAIN] Cloud master URL: " + cloudConfig.master_url);
  }

  win.loadFile(path.join(__dirname, "renderer", "index.html"), {
    query: {
      masterUrl: cloudConfig.master_url || MASTER_URL,
      botUrl: cloudConfig.bot_url || BOT_URL,
      backendUrl: cloudConfig.backend_url || "http://127.0.0.1:8000",
    }
  });

  // Block any navigation away from the local file
  win.webContents.on("will-navigate", (event, url) => {
    if (!url.startsWith("file://")) {
      event.preventDefault();
    }
  });

  // Block popups/external links from opening in app
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("http:")) {
      shell.openExternal(url);
    }
    return { action: "deny" };
  });

  // Title bar
  win.webContents.on("page-title-updated", (event) => {
    event.preventDefault();
    win.setTitle("AuraBiz — AI WhatsApp Business Assistant");
  });
}

app.whenReady().then(() => {
  initDb();
  startAllServices();
  createWindow();
  // Auto-update check (production only)
  if (process.env.NODE_ENV !== "development") {
    try { require("electron-updater").autoUpdater.checkForUpdatesAndNotify(); } catch (e) { /* ignore */ }
  }
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  stopAllServices();
  if (process.platform !== "darwin") app.quit();
});

// Expose helpers for debugging
module.exports = { getMachineId };
