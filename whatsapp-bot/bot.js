/**
 * WhatsApp Bot — Baileys se FREE mein connect hota hai
 * Koi API approval nahi, koi monthly cost nahi!
 * 
 * Flow:
 * 1. QR code generate hota hai
 * 2. Business owner scan karta hai phone se
 * 3. Customer message karta hai → AI reply karta hai
 */

const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, downloadMediaMessage } = require("@whiskeysockets/baileys");
const pino = require("pino");
const QRCode = require("qrcode");
const fs = require("fs");
const path = require("path");
const os = require("os");
const http = require("http");
const https = require("https");

// ============ CONFIG ============
// Use APPDATA for writable files (auth_state, sessions) — C:\Program Files is read-only!
const APPDATA_DIR = process.env.APPDATA || path.join(os.homedir(), "AppData", "Roaming");
const WRITABLE_DIR = path.join(APPDATA_DIR, "AuraBiz");
if (!fs.existsSync(WRITABLE_DIR)) fs.mkdirSync(WRITABLE_DIR, { recursive: true });

const AUTH_DIR = path.join(WRITABLE_DIR, "auth_state");
if (!fs.existsSync(AUTH_DIR)) fs.mkdirSync(AUTH_DIR, { recursive: true });

const PORT = 8001;
// Backend URL (env-driven so Docker networking works)
const PYTHON_BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000";
const SESSION_FILE = path.join(WRITABLE_DIR, "sessions.json");
// CONFIG_FILE AppData mein — install dir (C:\Program Files) read-only hai!
const CONFIG_FILE = path.join(WRITABLE_DIR, "bot_config.json");

// API Key for securing bot endpoints
// Set via environment variable BOT_API_KEY or in bot_config.json
const BOT_API_KEY = process.env.BOT_API_KEY || null;

// Check API key from request
function checkAuth(req, res) {
  // If no API key configured, allow all (backward compatible)
  if (!BOT_API_KEY) return true;
  
  const authHeader = req.headers["authorization"] || req.headers["x-api-key"] || "";
  const key = authHeader.replace("Bearer ", "").trim();
  
  if (key !== BOT_API_KEY) {
    res.writeHead(401, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Unauthorized. Provide valid API key in Authorization header." }));
    return false;
  }
  return true;
}

// Load or fetch business_id
function getBusinessId() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const cfg = JSON.parse(fs.readFileSync(CONFIG_FILE, "utf-8"));
      if (cfg.business_id) return cfg.business_id;
    }
  } catch {}
  return "business-1"; // fallback
}
let BUSINESS_ID = getBusinessId();

// ============ BUSINESS HOURS CONFIG ============
function getBusinessHours() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const cfg = JSON.parse(fs.readFileSync(CONFIG_FILE, "utf-8"));
      if (cfg.business_hours) {
        const bh = cfg.business_hours;
        // If explicitly disabled, return null (no hours check)
        if (bh.enabled === false) return null;
        // Support both old format (start_hour/end_hour) and new format (open/close)
        // Also auto-set defaults if missing
        return {
          open: bh.open ?? bh.start_hour ?? 10,
          close: bh.close ?? bh.end_hour ?? 20,
          days: bh.days ?? [1, 2, 3, 4, 5, 6],
          timezone: bh.timezone || "Asia/Kolkata",
          closed_message: bh.closed_message || "",
        };
      }
    }
  } catch (e) { console.error("getBusinessHours error:", e.message); }
  // Default: 10 AM - 8 PM, Mon-Sat
  return { open: 10, close: 20, days: [1, 2, 3, 4, 5, 6], timezone: "Asia/Kolkata", closed_message: "" };
}

function isWithinBusinessHours() {
  try {
    const hours = getBusinessHours();
    if (!hours) return true; // Business hours disabled
    const now = new Date();
    const formatter = new Intl.DateTimeFormat("en-US", {
      timeZone: hours.timezone || "Asia/Kolkata",
      hour: "numeric", hour12: false,
      weekday: "short",
    });
    const parts = formatter.formatToParts(now);
    const hourMap = {};
    for (const p of parts) hourMap[p.type] = parseInt(p.value, 10);
    const currentHour = hourMap.hour;
    const dayMap = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
    const currentDay = dayMap[parts.find(p => p.type === "weekday")?.value] ?? now.getDay();
    
    if (!hours.days.includes(currentDay)) return false;
    if (currentHour < hours.open || currentHour >= hours.close) return false;
    return true;
  } catch (e) { console.error("isWithinBusinessHours error:", e.message); return true; }
}

function getBusinessHoursMessage() {
  const hours = getBusinessHours();
  if (hours && hours.closed_message) return hours.closed_message;
  if (!hours) return "Hum abhi open hain! Aapki kya madad kar sakta hoon?";
  const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const openDays = hours.days.map(d => dayNames[d]).join(", ");
  const fmtHour = (h) => h > 12 ? h - 12 : (h === 0 ? 12 : h);
  const fmtAMPM = (h) => h >= 12 ? 'PM' : 'AM';
  return `Hum abhi closed hain. 😴\n\n🕐 Hamare working hours:\n📅 ${openDays}\n⏰ ${fmtHour(hours.open)}:00 ${fmtAMPM(hours.open)} - ${fmtHour(hours.close)}:00 ${fmtAMPM(hours.close)}\n\nKal subah ${fmtHour(hours.open)} baje milte hain! 🙏`;
}

// ============ IMAGE DOWNLOAD HELPER ============
function downloadImage(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith("https") ? https : http;
    client.get(url, { timeout: 10000 }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        // Follow redirect
        return downloadImage(res.headers.location).then(resolve).catch(reject);
      }
      if (res.statusCode !== 200) {
        return reject(new Error(`HTTP ${res.statusCode}`));
      }
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => resolve(Buffer.concat(chunks)));
      res.on("error", reject);
    }).on("error", reject);
  });
}

// Parse IMAGE_URL: marker from reply text
function parseImageReply(text) {
  if (!text) return { imageUrl: null, cleanText: text };
  const match = text.match(/^IMAGE_URL:(https?:\/\/\S+)\n([\s\S]*)$/);
  if (match) return { imageUrl: match[1], cleanText: match[2] };
  return { imageUrl: null, cleanText: text };
}

// ============ STATE ============
let sock = null;
let currentQR = null;
let connectionStatus = "disconnected"; // disconnected | connecting | connected
let connectedUser = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 60000; // max 60s

// Persistent sessions — file-backed
let customerSessions = {};
function loadSessions() {
  try {
    if (fs.existsSync(SESSION_FILE)) {
      customerSessions = JSON.parse(fs.readFileSync(SESSION_FILE, "utf-8"));
    }
  } catch { customerSessions = {}; }
}
function saveSessions() {
  try { fs.writeFileSync(SESSION_FILE, JSON.stringify(customerSessions, null, 2)); } catch {}
}
loadSessions();

// ============ MESSAGE QUEUE — 1000+ customers handle ============
const outbox = []; // { phone, message, imageUrl, attempts, status }
const RATE_LIMIT_MS = 200; // 200ms between messages = 5 msg/sec
const MAX_RETRIES = 3;
let processingQueue = false;

function enqueueMessage(phone, message, imageUrl = null) {
  outbox.push({ phone, message, imageUrl, attempts: 0, status: "queued", created: Date.now() });
}

async function processOutbox() {
  if (processingQueue || !sock || connectionStatus !== "connected") return;
  processingQueue = true;

  while (outbox.length > 0) {
    const item = outbox.find(m => m.status === "queued");
    if (!item) break;

    item.status = "sending";
    item.attempts++;

    try {
      if (item.imageUrl) {
        // Download image and send as image message with caption
        try {
          const imgBuffer = await downloadImage(item.imageUrl);
          await sock.sendMessage(item.phone, { image: imgBuffer, caption: item.message });
          console.log(`📤 Sent image + text to ${item.phone}`);
        } catch (imgErr) {
          console.error(`❌ Image download failed, sending text only: ${imgErr.message}`);
          await sock.sendMessage(item.phone, { text: item.message });
        }
      } else {
        await sock.sendMessage(item.phone, { text: item.message });
      }
      item.status = "sent";
      console.log(`📤 Sent to ${item.phone}: ${item.message.substring(0, 30)}...`);
    } catch (err) {
      console.error(`❌ Send failed to ${item.phone}:`, err.message);
      if (item.attempts < MAX_RETRIES) {
        item.status = "queued"; // retry
      } else {
        item.status = "failed";
      }
    }

    // Rate limit — wait between messages
    await new Promise(r => setTimeout(r, RATE_LIMIT_MS));
  }

  // Clean old sent/failed messages (keep last 100)
  while (outbox.length > 100) {
    const idx = outbox.findIndex(m => m.status === "sent" || m.status === "failed");
    if (idx >= 0) outbox.splice(idx, 1);
    else break;
  }

  processingQueue = false;
}

// Process queue every 500ms
setInterval(processOutbox, 500);

// ============ AI REPLY (Python backend se) ============
async function getAIReply(message, customerName, phone) {
  try {
    if (!customerSessions[phone]) {
      customerSessions[phone] = `wa-${phone}-${BUSINESS_ID.substring(0, 8)}`;
      saveSessions();
    }

    const res = await fetch(`${PYTHON_BACKEND}/api/v1/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        business_id: BUSINESS_ID,
        session_id: customerSessions[phone],
        customer_name: customerName || undefined,
        customer_phone: phone || undefined,
      }),
    });
    const data = await res.json();
    return data.reply || data.response || "Maaf kijiye, abhi kuch gadbad ho raha hai.";
  } catch (err) {
    console.error("AI reply error:", err.message);
    return "Maaf kijiye, system abhi busy hai. Thodi der mein try karo.";
  }
}

async function getAIAudioReply(audioBase64, customerName, phone) {
  try {
    if (!customerSessions[phone]) {
      customerSessions[phone] = `wa-${phone}-${BUSINESS_ID.substring(0, 8)}`;
      saveSessions();
    }

    const res = await fetch(`${PYTHON_BACKEND}/api/v1/chat/audio`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        audio_base64: audioBase64,
        business_id: BUSINESS_ID,
        session_id: customerSessions[phone],
        customer_name: customerName || undefined,
        customer_phone: phone || undefined,
      }),
    });
    const data = await res.json();
    return data.reply || data.response || "Maaf kijiye, voice process nahi ho paya.";
  } catch (err) {
    console.error("AI audio reply error:", err.message);
    return "Maaf kijiye, system abhi busy hai. Thodi der mein try karo.";
  }
}

// ============ START BOT ============
async function startBot() {
  console.log("🤖 WhatsApp Bot start ho raha hai...");

  // Auth state folder
  if (!fs.existsSync(AUTH_DIR)) {
    fs.mkdirSync(AUTH_DIR, { recursive: true });
  }

  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    printQRInTerminal: true,
    logger: pino({ level: "silent" }),
    browser: ["AI Business Assistant", "Chrome", "1.0.0"],
  });

  // ---- Connection Updates ----
  sock.ev.on("connection.update", (update) => {
    try {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        currentQR = qr;
        connectionStatus = "connecting";
        console.log("📱 QR Code ready hai — scan karo!");
        console.log(`🌐 QR Page: http://localhost:${PORT}`);
      }

      if (connection === "close") {
        const reason = lastDisconnect?.error?.output?.statusCode;
        console.log(`❌ Connection closed. Reason: ${reason}`);

        if (reason === DisconnectReason.loggedOut) {
          console.log("🔓 Logged out — naya QR chahiye");
          connectionStatus = "disconnected";
          currentQR = null;
          reconnectAttempts = 0;
          // Clear auth state
          try { fs.rmSync(AUTH_DIR, { recursive: true, force: true }); } catch (e) { console.error("Clear auth error:", e.message); }
        } else {
          reconnectAttempts++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
          console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttempts})...`);
          connectionStatus = "connecting";
          setTimeout(() => startBot(), delay);
        }
      }

      if (connection === "open") {
        connectionStatus = "connected";
        currentQR = null;
        reconnectAttempts = 0;
        if (sock) connectedUser = sock.user;
        console.log(`✅ Connected as: ${sock?.user?.name || "Unknown"}`);
        console.log(`📱 Phone: ${sock?.user?.id?.split(":")[0] || "Unknown"}`);
      }
    } catch (e) { console.error("connection.update error:", e.message); }
  });

  // ---- Save Credentials ----
  sock.ev.on("creds.update", saveCreds);

  // ---- Incoming Messages ----
  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    try {
      if (type !== "notify") return;

      for (const msg of messages) {
        // Skip own messages
        if (msg.key.fromMe) continue;

        // Skip status updates
        if (msg.key.remoteJid === "status@broadcast") continue;

        const from = msg.key.remoteJid;
        
        // Handle voice messages first
        const isAudio = msg.message?.audioMessage || msg.message?.documentMessage?.mimetype?.startsWith("audio/");
        if (isAudio) {
          const senderName = msg.pushName || "Customer";
          const phone = from.split("@")[0];
          console.log(`📨 ${senderName} (${phone}): [Voice Message]`);
          
          if (!isWithinBusinessHours()) {
            enqueueMessage(from, getBusinessHoursMessage());
            continue;
          }
          
          if (sock) await sock.sendPresenceUpdate("recording", from).catch(() => {});
          
          try {
            // Download the audio buffer
            const buffer = await downloadMediaMessage(msg, 'buffer', {}, { 
              logger: pino({ level: 'silent' }),
              reuploadRequest: sock.updateMediaMessage
            });
            const base64Audio = buffer.toString('base64');
            const reply = await getAIAudioReply(base64Audio, senderName, phone);
            
            enqueueMessage(from, reply);
          } catch (audioErr) {
            console.error("Error processing audio message:", audioErr.message);
            enqueueMessage(from, "Maaf kijiye, main aapka voice note download nahi kar paya.");
          }
          
          if (sock) await sock.sendPresenceUpdate("paused", from).catch(() => {});
          continue; // Skip the rest of text processing
        }

        const text = msg.message?.conversation || 
                     msg.message?.extendedTextMessage?.text || 
                     msg.message?.buttonsResponseMessage?.selectedButtonId ||
                     msg.message?.listResponseMessage?.singleSelectReply?.selectedRowId ||
                     "";

        // Handle image messages (photo captions)
        const imageMessage = msg.message?.imageMessage;
        const imageCaption = imageMessage?.caption || "";
        const hasImage = !!imageMessage;

        // If no text but has image, use caption; if neither, skip
        if (!text.trim() && !hasImage) continue;
        const effectiveText = text.trim() || imageCaption || "image received";

        // Get sender name
        const senderName = msg.pushName || "Customer";
        const phone = from.split("@")[0];

        console.log(`📨 ${senderName} (${phone}): ${effectiveText}${hasImage ? ' [image]' : ''}`);

        // Business hours auto-reply
        if (!isWithinBusinessHours()) {
          console.log(`🕐 Outside business hours — sending auto-reply`);
          enqueueMessage(from, getBusinessHoursMessage());
          if (sock) await sock.sendPresenceUpdate("paused", from).catch(() => {});
          continue;
        }

        // Show typing indicator — only if sock exists
        if (sock) await sock.sendPresenceUpdate("composing", from).catch(() => {});

        // Get AI reply — send effectiveText (handles both text and image captions)
        const reply = await getAIReply(effectiveText, senderName, phone);

        // Parse IMAGE_URL: marker from reply
        const { imageUrl, cleanText } = parseImageReply(reply);

        // Queue message — rate limited (with optional image)
        enqueueMessage(from, cleanText, imageUrl);

        // Stop typing
        if (sock) await sock.sendPresenceUpdate("paused", from).catch(() => {});

        console.log(`🤖 Queued reply for ${phone}: ${reply.substring(0, 50)}...`);
      }
    } catch (e) { console.error("messages.upsert error:", e.message); }
  });

  console.log("🤖 Bot ready hai! QR scan ka wait karo...");
}

// ============ HTTP SERVER (QR Page + Status) ============
const server = http.createServer((req, res) => {
  // CORS — Electron renderer file:// origin bhi allow karo (desktop app)
  const origin = req.headers.origin;
  const allowedOrigins = ["http://127.0.0.1:3001", "http://localhost:3001", "http://localhost:3000", "file://", "null"];
  if (origin && (allowedOrigins.includes(origin) || origin.startsWith("file://") || origin === "null")) {
    res.setHeader("Access-Control-Allow-Origin", origin);
  } else if (!origin) {
    res.setHeader("Access-Control-Allow-Origin", "*");
  } else {
    res.setHeader("Access-Control-Allow-Origin", "http://127.0.0.1:3001");
  }
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.writeHead(200);
    return res.end();
  }

  // Register business (set business_id)
  if (req.url === "/register" && req.method === "POST") {
    if (!checkAuth(req, res)) return;
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 4096) { req.destroy(); return; }
    });
    req.on("end", () => {
      try {
        const data = JSON.parse(body);
        if (data.business_id) {
          // Merge: existing config rakho, sirf business_id update karo
          let config = {};
          try { config = JSON.parse(fs.readFileSync(CONFIG_FILE, "utf-8")); } catch {}
          config.business_id = data.business_id;
          fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
          BUSINESS_ID = data.business_id; // in-memory bhi update
          res.writeHead(200, { "Content-Type": "application/json" });
          return res.end(JSON.stringify({ status: "ok", business_id: data.business_id }));
        }
      } catch (e) { console.error("Register error:", e.message); }
      res.writeHead(400, { "Content-Type": "application/json" });
      return res.end(JSON.stringify({ error: "business_id required" }));
    });
    return;
  }

  // QR Code endpoint (PROTECTED)
  if (req.url === "/qr" && req.method === "GET") {
    if (!checkAuth(req, res)) return;

    const sendResponse = (qrData) => {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        qr: qrData,
        status: connectionStatus,
        user: connectedUser ? { name: connectedUser.name, phone: connectedUser.id?.split(":")[0] } : null,
      }));
    };

    if (currentQR) {
      QRCode.toDataURL(currentQR, { width: 256, margin: 1 })
        .then(qrData => sendResponse(qrData))
        .catch(e => {
          console.error("QR generation error:", e.message);
          sendResponse(null);
        });
    } else {
      sendResponse(null);
    }
    return;
  }

  // Status endpoint (PROTECTED)
  if (req.url === "/status" && req.method === "GET") {
    if (!checkAuth(req, res)) return;
    res.writeHead(200, { "Content-Type": "application/json" });
    return res.end(JSON.stringify({
      status: connectionStatus,
      user: connectedUser ? { name: connectedUser.name, phone: connectedUser.id?.split(":")[0] } : null,
      uptime: process.uptime(),
      queue: {
        pending: outbox.filter(m => m.status === "queued").length,
        sent: outbox.filter(m => m.status === "sent").length,
        failed: outbox.filter(m => m.status === "failed").length,
        total: outbox.length,
      },
    }));
  }

  // Logout endpoint
  if (req.url === "/logout" && req.method === "POST") {
    if (!checkAuth(req, res)) return;
    if (sock) {
      sock.logout().catch(e => console.error("Logout error:", e.message));
      sock = null;
      currentQR = null;
      connectionStatus = "disconnected";
      connectedUser = null;
      // Clear auth
      if (fs.existsSync(AUTH_DIR)) {
        fs.rmSync(AUTH_DIR, { recursive: true, force: true });
      }
    }
    res.writeHead(200, { "Content-Type": "application/json" });
    return res.end(JSON.stringify({ status: "logged_out" }));
  }

  // Send message endpoint — admin dashboard se WhatsApp pe message bhejne ke liye
  if (req.url === "/send" && req.method === "POST") {
    if (!checkAuth(req, res)) return;
    let body = "";
    req.on("data", (chunk) => body += chunk);
    req.on("end", async () => {
      try {
        const data = JSON.parse(body);
        const { phone, message, image_url } = data;
        if (!phone || !message) {
          res.writeHead(400, { "Content-Type": "application/json" });
          return res.end(JSON.stringify({ error: "phone and message required" }));
        }
        if (!sock || connectionStatus !== "connected") {
          res.writeHead(503, { "Content-Type": "application/json" });
          return res.end(JSON.stringify({ error: "Bot connected nahi hai" }));
        }
        // Format phone: strip non-digits, add @s.whatsapp.net
        const jid = phone.replace(/\D/g, "") + "@s.whatsapp.net";
        if (image_url) {
          try {
            const imgBuffer = await downloadImage(image_url);
            await sock.sendMessage(jid, { image: imgBuffer, caption: message });
          } catch (imgErr) {
            console.error(`Image send failed, sending text only: ${imgErr.message}`);
            await sock.sendMessage(jid, { text: message });
          }
        } else {
          await sock.sendMessage(jid, { text: message });
        }
        console.log(`📤 Admin se bheja ${phone}: ${message.substring(0, 50)}...`);
        res.writeHead(200, { "Content-Type": "application/json" });
        return res.end(JSON.stringify({ status: "sent", to: phone }));
      } catch (err) {
        console.error("Send error:", err.message);
        res.writeHead(500, { "Content-Type": "application/json" });
        return res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // QR HTML Page
  if (req.url === "/" || req.url === "/scan") {
    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WhatsApp Bot - QR Scan</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #111b21; min-height: 100vh; display: flex; align-items: center; justify-content: center; color: white; }
    .container { text-align: center; padding: 40px; max-width: 400px; }
    .logo { font-size: 64px; margin-bottom: 16px; }
    h1 { font-size: 24px; margin-bottom: 8px; }
    .subtitle { color: #8696a0; margin-bottom: 32px; }
    #qr-box { background: white; border-radius: 16px; padding: 20px; display: inline-block; margin: 20px 0; min-height: 200px; min-width: 200px; display: flex; align-items: center; justify-content: center; }
    #qr-box img { width: 200px; height: 200px; border-radius: 8px; }
    #status { margin-top: 20px; padding: 12px 24px; border-radius: 12px; font-size: 14px; }
    .connecting { background: #25d366; }
    .connected { background: #00a884; }
    .disconnected { background: #667781; }
    .spinner { width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.3); border-top: 3px solid white; border-radius: 50%; animation: spin 1s linear infinite; display: inline-block; margin-right: 8px; }
    @keyframes spin { 100% { transform: rotate(360deg); } }
    .steps { margin-top: 32px; text-align: left; }
    .steps li { color: #8696a0; margin: 8px 0; font-size: 14px; }
    .steps li strong { color: #e9edef; }
  </style>
</head>
<body>
  <div class="container">
    <div class="logo">🤖</div>
    <h1>WhatsApp Bot</h1>
    <p class="subtitle">QR code scan karo aur bot start ho jayega!</p>
    
    <div id="qr-box">
      <p style="color: #667781;">Loading...</p>
    </div>
    
    <div id="status" class="connecting">
      <span class="spinner"></span> Connecting...
    </div>
    
    <ol class="steps">
      <li><strong>Step 1:</strong> Apne phone pe WhatsApp kholo</li>
      <li><strong>Step 2:</strong> Settings → Linked Devices → Link a Device</li>
      <li><strong>Step 3:</strong> Upar ka QR code scan karo</li>
      <li><strong>Step 4:</strong> Bot start ho jayega! 🎉</li>
    </ol>
  </div>

  <script>
    async function checkStatus() {
      try {
        const res = await fetch('/qr');
        const data = await res.json();
        
        const qrBox = document.getElementById('qr-box');
        const status = document.getElementById('status');
        
        if (data.status === 'connected') {
          qrBox.innerHTML = '<p style="color: #00a884; font-size: 48px;">✅</p>';
          status.className = 'connected';
          status.innerHTML = '✅ Connected! Bot chal raha hai.';
        } else if (data.qr) {
          // Generate QR code using API
          qrBox.innerHTML = '<img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + encodeURIComponent(data.qr) + '" alt="QR Code">';
          status.className = 'connecting';
          status.innerHTML = '<span class="spinner"></span> QR Ready — scan karo!';
        } else {
          qrBox.innerHTML = '<p style="color: #667781;">QR generate ho raha hai...</p>';
          status.className = 'connecting';
          status.innerHTML = '<span class="spinner"></span> Connecting...';
        }
      } catch (e) {
        console.error(e);
      }
    }
    
    checkStatus();
    setInterval(checkStatus, 3000); // Poll every 3 seconds
  </script>
</body>
</html>`;

    res.writeHead(200, { "Content-Type": "text/html" });
    return res.end(html);
  }

  res.writeHead(404);
  res.end("Not found");
});

// ============ START EVERYTHING ============
server.listen(PORT, () => {
  console.log(`🌐 QR Page: http://localhost:${PORT}`);
  console.log(`📊 Status API: http://localhost:${PORT}/status`);
  console.log(`🔑 Logout API: http://localhost:${PORT}/logout`);
});

startBot().catch((err) => {
  console.error("Bot start error:", err);
  // process.exit nahi karte — auto-retry ke liye
  setTimeout(() => {
    console.log("🔄 Bot restart ho raha hai...");
    startBot().catch(e => console.error("Bot restart bhi fail:", e.message));
  }, 5000);
});
