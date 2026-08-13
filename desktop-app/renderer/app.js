/* ─────────────────────────────────────────────────────
   AuraBiz Desktop App v2 — License-Only Flow
   ───────────────────────────────────────────────────── */

// Master backend URL — cloud (sab local hai except license validation)
const params = new URLSearchParams(window.location.search);
const API = params.get("masterUrl") || "https://aurabiz.onrender.com";
const BOT = params.get("botUrl") || "http://127.0.0.1:8001";
const BACKEND = params.get("backendUrl") || "http://127.0.0.1:8000";

console.log("[AuraBiz] Master:", API, "| Bot:", BOT, "| Backend:", BACKEND);

let licenseKey = "";
let currentView = "license";
let currentPage = "dashboard";
let products = [];
let aiTier = "free";

/* ─── BOOT ────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  // Check if already activated
  const saved = localStorage.getItem("aurabiz_license");
  if (saved) {
    licenseKey = saved;
    showView("setup");
    setTimeout(() => renderQr(), 2000);
  }
  bindEvents();
});

/* ─── EVENTS ──────────────────────────────────────── */
function bindEvents() {
  document.getElementById("btn-activate").onclick = activateLicense;
  document.getElementById("btn-setup-continue").onclick = saveSetupAndShowQR;
  document.getElementById("btn-setup-done").onclick = () => launchWebDashboard();
  document.getElementById("btn-new-product").onclick = showAddProduct;
  document.getElementById("product-form").onsubmit = saveProduct;
  document.getElementById("btn-cancel-product").onclick = hideProductForm;
  document.getElementById("btn-ai-send").onclick = sendAiMessage;
  document.getElementById("ai-input").onkeydown = (e) => {
    if (e.key === "Enter") sendAiMessage();
  };
  // Bot logs toggle
  if (document.getElementById("btn-show-logs")) {
    document.getElementById("btn-show-logs").onclick = showBotLogs;
  }
}

/* ─── VIEWS ───────────────────────────────────────── */
function showView(view) {
  document.querySelectorAll(".view, #view-app").forEach(v => v.classList.add("hidden"));
  if (view === "license") {
    document.getElementById("view-license").classList.remove("hidden");
  } else if (view === "setup") {
    document.getElementById("view-setup").classList.remove("hidden");
  } else if (view === "app") {
    document.getElementById("view-app").classList.remove("hidden");
    loadDashboard();
  }
  currentView = view;
}

/* ─── LICENSE ACTIVATION ──────────────────────────── */
async function activateLicense() {
  const key = document.getElementById("license-key-input").value.trim();
  if (!key) return;

  const err = document.getElementById("license-error");
  const suc = document.getElementById("license-success");
  err.classList.add("hidden");
  suc.classList.add("hidden");

  try {
    // Step 1: Try ACTIVATE first (first time on this machine)
    let res = await fetch(`${API}/api/license/activate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ license_key: key, machine_id: "desktop-" + navigator.userAgent.slice(0, 30) }),
    });
    let data = await res.json().catch(() => ({}));

    // If already activated on this machine, activate returns ok
    // If already activated on DIFFERENT machine, we get 403
    if (res.ok && data.activated) {
      licenseKey = key;
      localStorage.setItem("aurabiz_license", key);
      localStorage.setItem("aurabiz_plan", data.plan || "free");
      localStorage.setItem("aurabiz_ai_tier", data.ai_tier || "free");
      suc.classList.remove("hidden");
      setTimeout(() => showView("setup"), 1500);
      return;
    }

    // Step 2: If activate failed, try VALIDATE (maybe already activated earlier)
    res = await fetch(`${API}/api/license/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ license_key: key, machine_id: "desktop-" + navigator.userAgent.slice(0, 30) }),
    });
    data = await res.json().catch(() => ({}));

    if (res.ok && data.valid) {
      licenseKey = key;
      localStorage.setItem("aurabiz_license", key);
      localStorage.setItem("aurabiz_plan", data.plan || "free");
      localStorage.setItem("aurabiz_ai_tier", data.ai_tier || "free");
      suc.classList.remove("hidden");
      setTimeout(() => showView("setup"), 1500);
    } else {
      err.textContent = data.detail || data.error || "License invalid hai!";
      err.classList.remove("hidden");
    }
  } catch (e) {
    err.textContent = "Server se connect nahi ho paaya. Master backend (port 8010) chal raha hai?";
    err.classList.remove("hidden");
  }
}

/* ─── SETUP WIZARD ────────────────────────────────── */
function saveSetupAndShowQR() {
  const name = document.getElementById("setup-business-name").value.trim();
  const type = document.getElementById("setup-business-type").value;
  if (!name || !type) return alert("Business name aur type zaroori hai!");

  localStorage.setItem("aurabiz_business_name", name);
  localStorage.setItem("aurabiz_business_type", type);
  localStorage.setItem("aurabiz_upi", document.getElementById("setup-upi-id").value.trim());
  localStorage.setItem("aurabiz_whatsapp", document.getElementById("setup-whatsapp").value.trim());
  localStorage.setItem("aurabiz_address", document.getElementById("setup-address").value.trim());

  document.getElementById("setup-step-1").classList.add("hidden");
  document.getElementById("setup-step-2").classList.remove("hidden");
  renderQr();
  startBotStatusPoll();
}

async function renderQr() {
  const box = document.getElementById("qr-box");
  let retries = 0;
  const maxRetries = 5;

  async function tryFetchQR() {
    try {
      const res = await fetch(`${BOT}/qr`);
      const data = await res.json();
      if (data.status === "connected" || data.connected) {
        box.innerHTML = '<p style="color:var(--accent);font-weight:700">WhatsApp Already Connected! ✅</p>';
        document.getElementById("bot-status").className = "status-badge online";
        document.getElementById("bot-status").innerHTML = '<span class="dot green"></span> WhatsApp Connected!';
        document.getElementById("btn-setup-done").classList.remove("hidden");
      } else if (data.qr) {
        box.innerHTML = '<img src="' + data.qr + '" width="220" height="220" />';
      } else {
        // QR not ready yet — retry
        retries++;
        if (retries < maxRetries) {
          box.innerHTML = `<p class="muted">QR load ho raha hai... (${retries}/${maxRetries})</p>`;
          setTimeout(tryFetchQR, 3000);
        } else {
          box.innerHTML = '<p class="muted">QR generate nahi ho paya. Bot restart karo ya check karo port 8001.</p>';
        }
      }
    } catch (e) {
      retries++;
      console.log(`[AuraBiz] Bot fetch failed (${retries}/${maxRetries}):`, e.message);
      if (retries < maxRetries) {
        box.innerHTML = `<p class="muted">Bot start ho raha hai... (${retries}/${maxRetries})</p>`;
        setTimeout(tryFetchQR, 3000);
      } else {
        box.innerHTML = '<p class="muted">Bot server se connect nahi ho paaya (port 8001).<br/>Debug log check karo Desktop pe: <b>aurabiz_debug.log</b></p>';
      }
    }
  }

  tryFetchQR();
}

function startBotStatusPoll() {
  const poll = setInterval(async () => {
    try {
      const res = await fetch(`${BOT}/status`);
      const data = await res.json();
      const badge = document.getElementById("bot-status");
      const btnDone = document.getElementById("btn-setup-done");
      if (data.connected) {
        badge.className = "status-badge online";
        badge.innerHTML = '<span class="dot green"></span> WhatsApp Connected!';
        document.getElementById("qr-box").innerHTML = '<p style="color:var(--accent);font-weight:700">WhatsApp Connected! ✅</p>';
        btnDone.classList.remove("hidden");
        clearInterval(poll);
      } else {
        badge.className = "status-badge connecting";
        badge.innerHTML = '<span class="spinner"></span> Waiting for QR scan...';
      }
    } catch { /* bot down */ }
  }, 3000);
}

/* ─── DASHBOARD ───────────────────────────────────── */
function loadDashboard() {
  loadStats();
  loadProducts();
  updateLicenseBadge();
  startBotStatusCheck();
}

function loadStats() {
  const totalProducts = products.length;
  const totalStock = products.reduce((s, p) => s + (p.stock || 0), 0);
  const totalValue = products.reduce((s, p) => s + (p.price || 0) * (p.stock || 0), 0);
  document.getElementById("stat-products").textContent = totalProducts;
  document.getElementById("stat-stock").textContent = totalStock;
  document.getElementById("stat-value").textContent = "Rs." + totalValue.toLocaleString("en-IN");

  const plan = localStorage.getItem("aurabiz_plan") || "free";
  document.getElementById("stat-plan").textContent = plan.charAt(0).toUpperCase() + plan.slice(1);
  document.getElementById("sidebar-plan").textContent = plan.charAt(0).toUpperCase() + plan.slice(1) + " Plan";
  document.getElementById("license-badge").textContent = plan.toUpperCase();
}

function updateLicenseBadge() {
  const plan = localStorage.getItem("aurabiz_plan") || "free";
  document.getElementById("license-badge").textContent = plan.toUpperCase();
  document.getElementById("settings-license-info").textContent = "License: " + licenseKey + " | Plan: " + plan;
}

/* ─── PRODUCTS ────────────────────────────────────── */
async function loadProducts() {
  try {
    const res = await fetch(`${BOT}/products`);
    if (res.ok) {
      products = await res.json();
      renderProducts();
    }
  } catch {
    // Use localStorage fallback
    const saved = localStorage.getItem("aurabiz_products");
    products = saved ? JSON.parse(saved) : [];
    renderProducts();
  }
}

function renderProducts() {
  const tbody = document.getElementById("product-tbody");
  const count = document.getElementById("product-count");
  count.textContent = products.length;
  if (!products.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty">Koi product nahi. Add karo!</td></tr>';
    return;
  }
  tbody.innerHTML = products.map(p => `<tr>
    <td><strong>${esc(p.name)}</strong></td>
    <td>Rs.${esc(String(p.price || 0))}</td>
    <td>${esc(String(p.stock || 0))}</td>
    <td>${esc(p.unit || "piece")}</td>
    <td>${esc(p.category || "-")}</td>
    <td><button class="btn-sm edit" onclick="editProduct('${esc(p.id)}')">Edit</button><button class="btn-sm delete" onclick="deleteProduct('${esc(p.id)}')">Delete</button></td>
  </tr>`).join("");
}

function showAddProduct() {
  document.getElementById("product-form").classList.remove("hidden");
  document.getElementById("pf-id").value = "";
  document.getElementById("pf-name").focus();
}

function hideProductForm() {
  document.getElementById("product-form").classList.add("hidden");
  document.getElementById("product-form").reset();
}

async function saveProduct(e) {
  e.preventDefault();
  const name = document.getElementById("pf-name").value.trim();
  const price = parseFloat(document.getElementById("pf-price").value) || 0;
  const stock = parseInt(document.getElementById("pf-stock").value) || 0;
  const unit = document.getElementById("pf-unit").value;
  const category = document.getElementById("pf-category").value.trim();
  const desc = document.getElementById("pf-desc").value.trim();
  if (!name) return;

  const editId = document.getElementById("pf-id").value;
  if (editId) {
    const idx = products.findIndex(p => p.id === editId);
    if (idx >= 0) {
      products[idx] = { ...products[idx], name, price, stock, unit, category, description: desc };
    }
  } else {
    products.push({ id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), name, price, stock, unit, category, description: desc });
  }

  localStorage.setItem("aurabiz_products", JSON.stringify(products));
  renderProducts();
  loadStats();
  hideProductForm();
}

function editProduct(id) {
  const p = products.find(x => x.id === id);
  if (!p) return;
  document.getElementById("pf-id").value = p.id;
  document.getElementById("pf-name").value = p.name;
  document.getElementById("pf-price").value = p.price;
  document.getElementById("pf-stock").value = p.stock;
  document.getElementById("pf-unit").value = p.unit;
  document.getElementById("pf-category").value = p.category;
  document.getElementById("pf-desc").value = p.description || "";
  showAddProduct();
}

async function deleteProduct(id) {
  if (!confirm("Delete karna hai?")) return;
  products = products.filter(p => p.id !== id);
  localStorage.setItem("aurabiz_products", JSON.stringify(products));
  renderProducts();
  loadStats();
}

/* ─── AI CHAT ─────────────────────────────────────── */
async function sendAiMessage() {
  const input = document.getElementById("ai-input");
  const text = input.value.trim();
  if (!text) return;

  addChat("user", text);
  input.value = "";
  input.disabled = true;

  try {
    const res = await fetch(`${BOT}/api/ai/${aiTier}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, products: products }),
    });
    const data = await res.json();
    addChat("bot", data.reply || data.error || "Koi response nahi mila.");
  } catch {
    addChat("bot", "AI server se connect nahi ho paaya (port 8001).");
  } finally {
    input.disabled = false;
    input.focus();
  }
}

function addChat(role, text) {
  const box = document.getElementById("ai-chat");
  const div = document.createElement("div");
  div.className = "chat-msg " + role;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

/* ─── BOT STATUS ──────────────────────────────────── */
function startBotStatusCheck() {
  setInterval(async () => {
    try {
      const res = await fetch(`${BOT}/status`);
      const data = await res.json();
      const badge = document.getElementById("wa-connection-badge");
      const avatar = document.getElementById("wa-avatar");
      const name = document.getElementById("wa-name");
      const phone = document.getElementById("wa-phone");

      if (data.connected) {
        badge.className = "status-badge online";
        badge.innerHTML = '<span class="dot green"></span> Connected';
        avatar.textContent = "?";
        name.textContent = data.name || "WhatsApp User";
        phone.textContent = data.phone || "";
      } else {
        badge.className = "status-badge offline";
        badge.innerHTML = '<span class="dot red"></span> Not Connected';
        name.textContent = "Not Connected";
        phone.textContent = "QR scan karo Settings me";
      }
    } catch {
      const badge = document.getElementById("wa-connection-badge");
      badge.className = "status-badge offline";
      badge.innerHTML = '<span class="dot red"></span> Bot Offline';
    }
  }, 5000);
}

/* ─── WEB DASHBOARD LAUNCH ──────────────────────────── */
function launchWebDashboard() {
  const btn = document.getElementById("btn-setup-done");
  btn.textContent = "Dashboard khol rahe hain...";
  btn.disabled = true;

  // Local renderer mein hi dashboard hai (backend/frontend servers ki zaroorat nahi)
  // Web dashboard try karo, fail ho toh local app view dikhao
  try {
    // Local app view show karo (Products, AI, WhatsApp sab yahan hai)
    showView("app");
    btn.textContent = "Done - Dashboard Kholo";
    btn.disabled = false;
  } catch (e) {
    btn.textContent = "Done - Dashboard Kholo";
    btn.disabled = false;
    console.error("Dashboard launch error:", e);
  }
}
function switchPage(page) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.getElementById("page-" + page).classList.add("active");
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.querySelector(`[data-page="${page}"]`).classList.add("active");
  document.getElementById("page-title").textContent =
    page === "dashboard" ? "Dashboard" :
    page === "products" ? "Products" :
    page === "ai" ? "AI Assistant" :
    page === "whatsapp" ? "WhatsApp" :
    page === "settings" ? "Settings" : "";
  currentPage = page;
}

function toggleSidebar() {
   document.getElementById("app-sidebar").classList.toggle("open");
}

/* ─── BOT LOGS (Debug) ──────────────────────────────── */
async function showBotLogs() {
  const logsEl = document.getElementById("bot-logs");
  const btn = document.getElementById("btn-show-logs");
  if (logsEl.classList.contains("hidden")) {
    logsEl.classList.remove("hidden");
    btn.textContent = "Hide Bot Logs";
    try {
      if (window.desktopAPI && window.desktopAPI.getBotDiagnostics) {
        const diag = await window.desktopAPI.getBotDiagnostics();
        let html = "=== Bot Diagnostics ===\n";
        html += `Process running: ${diag.processRunning}\n`;
        html += `Bot started: ${diag.started}\n`;
        html += `Port: ${diag.port}\n`;
        html += `\n--- Resource Paths ---\n`;
        html += `Bot dir: ${diag.resourcePath?.bot || 'N/A'}\n`;
        html += `Node exists: ${diag.resourcePath?.nodeExists}\n`;
        html += `Bot.js exists: ${diag.resourcePath?.botJsExists}\n`;
        html += `\n--- Bot Logs ---\n`;
        diag.logs.forEach(l => html += l + "\n");
        logsEl.textContent = html;
      } else {
        logsEl.textContent = "desktopAPI not available - check aurabiz_debug.log on Desktop";
      }
    } catch (e) {
      logsEl.textContent = "Error fetching diagnostics: " + e.message;
    }
  } else {
    logsEl.classList.add("hidden");
    btn.textContent = "Show Bot Logs";
  }
}

/* ─── AI TIER TOGGLE ──────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".ai-option").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll(".ai-option").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      aiTier = btn.dataset.tier;
    };
  });
});

/* ─── HELPERS ─────────────────────────────────────── */
function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
