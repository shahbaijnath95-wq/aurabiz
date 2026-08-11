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

// ─── File logger for diagnostics ───
const LOG_PATH = path.join(app.getPath("desktop"), "aurabiz_debug.log");
function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  console.log(line.trim());
  try { fs.appendFileSync(LOG_PATH, line); } catch (e) { /* ignore */ }
}
log("=== AuraBiz Desktop starting ===");

// ─── Master backend URL (env override for production) ───
const MASTER_URL = process.env.AURABIZ_MASTER_URL || "http://localhost:8010";
const BOT_URL = process.env.AURABIZ_BOT_URL || "http://127.0.0.1:8001";

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
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "AuraBiz",
    backgroundColor: "#faf9f7",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadFile(path.join(__dirname, "renderer", "index.html"));

  // Open external links in browser
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

app.whenReady().then(() => {
  initDb();
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
  if (process.platform !== "darwin") app.quit();
});

// Expose helpers for debugging
module.exports = { getMachineId };
