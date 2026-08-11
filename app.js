/* AuraBiz Desktop — Renderer Logic */
const api = window.api;
const $ = (sel) => document.querySelector(sel);

let currentTab = "dashboard";
let products = [];
let aiTier = "free";
let license = null;

// ─── Debug tracing (shows in UI for diagnostics) ───
const DEBUG = true;
const dbgLines = [];
function dbg(msg) {
  if (!DEBUG) return;
  console.log("[DBG]", msg);
  dbgLines.push(msg);
  // Also send to main process for file logging
  try { if (window.api && window.api._log) {} } catch(e) {}
  let box = $("#dbg-box");
  if (!box) {
    box = document.createElement("div");
    box.id = "dbg-box";
    box.style.cssText = "position:fixed;bottom:0;left:0;right:0;max-height:120px;overflow:auto;background:#1a1a2e;color:#0f0;font-family:monospace;font-size:11px;padding:6px;z-index:9999;border-top:1px solid #333";
    document.body.appendChild(box);
  }
  const line = document.createElement("div");
  line.textContent = `> ${msg}`;
  box.appendChild(line);
  box.scrollTop = box.scrollHeight;
}

// ─── Tab switching ───
function switchTab(name) {
  currentTab = name;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${name}`));
}
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => switchTab(t.dataset.tab)));

// ─── App boot ───
async function boot() {
  dbg("boot() started");
  try {
    if (!api) { document.body.innerHTML = '<div style="padding:2rem;text-align:center;font-family:sans-serif"><h1>⚠️ API Load Error</h1><p>Preload script nahi chal. App restart karo.</p></div>'; return; }
    dbg("calling licenseStatus...");
    const status = await api.licenseStatus();
    dbg("licenseStatus returned: " + JSON.stringify(status));
    if (status.ok && status.license) {
      dbg("license found, calling validate...");
      const v = await api.licenseValidate();
      dbg("validate returned: " + JSON.stringify(v));
      if (v.ok) {
        license = status.license;
        dbg("license valid, calling checkSetup...");
        await checkSetup();
        dbg("checkSetup returned");
      } else {
        showView("view-license");
        showLicenseError(v.error || "License invalid hai");
      }
    } else {
      dbg("no license, showing view-license");
      showView("view-license");
    }
  } catch (e) {
    dbg("boot EXCEPTION: " + (e.message || e));
    console.error("Boot error:", e);
    showView("view-license");
    showLicenseError("Connection error: " + (e.message || "Master backend reachable nahi hai"));
  }
}

function showView(id) {
  document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
  $(`#${id}`).classList.remove("hidden");
}

function showLicenseError(msg) {
  const el = $("#license-error");
  el.innerHTML = msg + '<br/><span style="font-size:0.8rem;opacity:0.8">💡 Tip: Master backend (:8010) chalu hai? <button onclick="location.reload()" style="background:none;border:1px solid currentColor;border-radius:4px;padding:2px 8px;cursor:pointer;font:inherit">Retry</button></span>';
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 15000);
}

function enterApp() {
  showView("view-app");
  if (license && license.license_key) {
    $("#license-badge").textContent = license.license_key.split("-").pop();
  }
  loadAll();
}

// ─── License activation ───
$("#btn-activate").addEventListener("click", async () => {
  dbg("btn-activate CLICK");
  const key = $("#license-key-input").value.trim();
  dbg("key=" + key);
  if (!key) return showLicenseError("License key daalo");
  const btn = $("#btn-activate");
  $("#license-error").classList.add("hidden");
  $("#license-success").classList.add("hidden");
  btn.disabled = true;
  btn.classList.add("loading");
  btn.innerHTML = '<span class="btn-spinner"></span> Activating...';
  dbg("calling api.licenseActivate...");
  try {
    const res = await api.licenseActivate(key);
    dbg("api.licenseActivate returned: " + JSON.stringify(res));
    if (res.ok) {
      license = res;
      dbg("license set, showing success");
      btn.classList.remove("loading");
      btn.innerHTML = 'Activate License →';
      btn.disabled = false;
      $("#license-success").classList.remove("hidden");
      dbg("waiting 1200ms then checkSetup...");
      setTimeout(async () => {
        try {
          dbg("checkSetup running...");
          await checkSetup();
          dbg("checkSetup done");
        } catch (e) {
          dbg("checkSetup EXCEPTION: " + (e.message || e));
          showLicenseError("Setup check failed: " + (e.message || "Unknown error"));
          const btn2 = $("#btn-activate");
          btn2.classList.remove("loading");
          btn2.innerHTML = 'Activate License →';
          btn2.disabled = false;
        }
      }, 1200);
    } else {
      dbg("activation failed: " + (res.error || "unknown"));
      showLicenseError(res.error || "Activation fail");
      btn.classList.remove("loading");
      btn.innerHTML = 'Activate License →';
      btn.disabled = false;
    }
  } catch (e) {
    dbg("EXCEPTION: " + (e.message || e));
    showLicenseError(e.message || "Connection error — master backend reachable nahi hai");
    btn.classList.remove("loading");
    btn.innerHTML = 'Activate License →';
    btn.disabled = false;
  }
});
$("#license-key-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("#btn-activate").click();
});

// ─── Load all data ───
async function loadAll() {
  await Promise.all([loadProducts(), loadAiTier()]);
}

// ─── Products ───
async function loadProducts() {
  const res = await api.productsList();
  if (!res.ok) return;
  products = res.products;
  renderProducts();
  renderStats();
}

function renderStats() {
  $("#stat-products").textContent = products.length;
  const totalStock = products.reduce((s, p) => s + Number(p.stock || 0), 0);
  const totalValue = products.reduce((s, p) => s + Number(p.price || 0) * Number(p.stock || 0), 0);
  $("#stat-stock").textContent = totalStock;
  $("#stat-value").textContent = "₹" + totalValue.toLocaleString("en-IN");
  $("#stat-plan").textContent = license ? license.plan : "—";
  $("#product-count").textContent = products.length;
}

function renderProducts() {
  const tbody = $("#product-tbody");
  if (products.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty">Abhi koi product nahi — "+ Add Product" dabao</td></tr>';
    return;
  }
  tbody.innerHTML = products.map((p) => `
    <tr>
      <td><b>${esc(p.name)}</b>${p.description ? `<br/><span style="font-size:0.75rem;color:#8b8275">${esc(p.description)}</span>` : ""}</td>
      <td>₹${Number(p.price || 0).toLocaleString("en-IN")}</td>
      <td>${Number(p.stock || 0)}</td>
      <td>${esc(p.unit || "piece")}</td>
      <td>${esc(p.category || "—")}</td>
      <td>
        <button class="action-btn action-edit" onclick="editProduct('${p.id}')">✏️ Edit</button>
        <button class="action-btn action-del" onclick="deleteProduct('${p.id}')">🗑️</button>
      </td>
    </tr>
  `).join("");
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// Product form
$("#btn-new-product").addEventListener("click", () => {
  $("#product-form").classList.remove("hidden");
  $("#product-form").reset();
  $("#pf-id").value = "";
  $("#btn-new-product").classList.add("hidden");
});
$("#btn-cancel-product").addEventListener("click", () => {
  $("#product-form").classList.add("hidden");
  $("#btn-new-product").classList.remove("hidden");
});

$("#product-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = $("#pf-id").value;
  const data = {
    id,
    name: $("#pf-name").value.trim(),
    price: Number($("#pf-price").value) || 0,
    stock: Number($("#pf-stock").value) || 0,
    unit: $("#pf-unit").value,
    category: $("#pf-category").value.trim(),
    description: $("#pf-desc").value.trim(),
  };
  if (!data.name) return;
  const res = id ? await api.productsUpdate(data) : await api.productsAdd(data);
  if (res.ok) {
    $("#product-form").classList.add("hidden");
    $("#btn-new-product").classList.remove("hidden");
    loadProducts();
  }
});

window.editProduct = (id) => {
  const p = products.find((x) => x.id === id);
  if (!p) return;
  $("#pf-id").value = p.id;
  $("#pf-name").value = p.name;
  $("#pf-price").value = p.price;
  $("#pf-stock").value = p.stock;
  $("#pf-unit").value = p.unit || "piece";
  $("#pf-category").value = p.category || "";
  $("#pf-desc").value = p.description || "";
  $("#product-form").classList.remove("hidden");
  $("#btn-new-product").classList.add("hidden");
  window.scrollTo(0, 0);
};

window.deleteProduct = async (id) => {
  if (!confirm("Product delete karna hai?")) return;
  await api.productsDelete(id);
  loadProducts();
};

// ─── AI tier ───
async function loadAiTier() {
  const res = await api.aiGetTier();
  aiTier = res.ai_tier || "free";
  renderAiTier();
}

function renderAiTier() {
  document.querySelectorAll(".ai-option").forEach((o) => {
    o.classList.toggle("active", o.dataset.tier === aiTier);
  });
  const badge = $("#ai-badge");
  badge.textContent = aiTier === "paid" ? "🤖 Paid AI" : "🆓 Free AI";
  badge.className = "badge " + (aiTier === "paid" ? "badge-paid" : "badge-free");
}

document.querySelectorAll(".ai-option").forEach((o) => {
  o.addEventListener("click", async () => {
    aiTier = o.dataset.tier;
    await api.aiSetTier(aiTier);
    renderAiTier();
    addChatMsg("bot", aiTier === "paid" ? "Paid AI enable ho gaya! 🤖" : "Free AI enable ho gaya! 🆓");
  });
});

// ─── AI chat ───
function addChatMsg(who, text) {
  const box = $("#ai-chat");
  const div = document.createElement("div");
  div.className = `chat-msg ${who}`;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

$("#btn-ai-send").addEventListener("click", sendMsg);
$("#ai-input").addEventListener("keydown", (e) => { if (e.key === "Enter") sendMsg(); });

async function sendMsg() {
  const input = $("#ai-input");
  const text = input.value.trim();
  if (!text) return;
  addChatMsg("user", text);
  input.value = "";
  const res = await api.aiReply(text);
  addChatMsg(res.ok ? "bot" : "error", res.ok ? res.reply : (res.error || "AI reply fail"));
}

// ─── Setup Wizard ───
async function checkSetup() {
  try {
    if (!api || !api.businessGetSetup) { enterApp(); return; }
    const res = await api.businessGetSetup();
    if (res.completed) {
      enterApp();
    } else {
      showView("view-setup");
      setupWizard();
    }
  } catch (e) {
    console.error("checkSetup error:", e);
    showLicenseError("Setup check error: " + (e.message || "Unknown"));
    showView("view-setup");
    setupWizard();
  }
}

function setupWizard() {
  const step1 = $("#setup-step-1");
  const step2 = $("#setup-step-2");

  $("#btn-setup-continue").addEventListener("click", async () => {
    try {
      const data = {
        name: $("#setup-business-name").value.trim(),
        type: $("#setup-business-type").value,
        upi_id: $("#setup-upi-id").value.trim(),
        whatsapp: $("#setup-whatsapp").value.trim(),
        address: $("#setup-address").value.trim(),
      };
      if (!data.name || !data.type) return showLicenseError("Business naam aur type required hai");

      const res = await api.businessSaveSetup(data);
      if (!res.ok) return showLicenseError("Save fail — dubara try karo");

      step1.classList.add("hidden");
      step2.classList.remove("hidden");
      startQRPolling();
    } catch (e) {
      showLicenseError("Setup error: " + (e.message || "Unknown"));
    }
  });

  $("#btn-setup-done").addEventListener("click", enterApp);
}

let qrPollInterval = null;

async function startQRPolling() {
  const cfg = await api.licenseStatus();
  await api.botRegister(cfg.license?.license_key || "desktop-user");

  qrPollInterval = setInterval(async () => {
    const qr = await api.botGetQR();
    const status = await api.botGetStatus();
    const qrBox = $("#qr-box");
    const statusEl = $("#bot-status");
    const doneBtn = $("#btn-setup-done");

    if (status.status === "connected") {
      qrBox.innerHTML = '<div class="qr-success">✅ WhatsApp Connected!</div>';
      statusEl.className = "status-badge connected";
      statusEl.innerHTML = `✅ Connected: ${status.user?.phone || "WhatsApp"}`;
      doneBtn.classList.remove("hidden");
      clearInterval(qrPollInterval);
    } else if (qr.qr) {
      qrBox.innerHTML = `<img src="https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(qr.qr)}" alt="QR" />`;
      statusEl.className = "status-badge connecting";
      statusEl.innerHTML = '<span class="spinner"></span> QR Ready — scan karo!';
    } else {
      qrBox.innerHTML = '<p>QR generate ho raha hai...</p>';
      statusEl.className = "status-badge connecting";
      statusEl.innerHTML = '<span class="spinner"></span> Connecting...';
    }
  }, 3000);
}

// ─── Boot ───
boot();
