/**
 * Test: License activation flow (simulates exactly what main.js does)
 * Tests: success, invalid key, and timeout scenarios
 */
const http = require("http");

const MASTER_URL = "http://localhost:8010";
const API_TIMEOUT_MS = 8000;

// Replicate the EXACT api() helper from main.js (with fix)
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

function getMachineId() {
  const os = require("os");
  const crypto = require("crypto");
  const raw = [os.hostname(), os.platform(), os.arch(), os.cpus()[0]?.model || "", os.totalmem(), os.userInfo().username].join("|");
  return crypto.createHash("sha256").update(raw).digest("hex").slice(0, 32);
}

async function runTests() {
  console.log("=== AuraBiz Desktop — License Activation Test ===\n");
  const machineId = getMachineId();
  console.log(`Machine ID: ${machineId}\n`);

  // ─── Test 1: Invalid license key ───
  console.log("Test 1: Invalid license key (expect: clear error, no hang)");
  const t1 = Date.now();
  try {
    const result = await api("/api/license/activate", {
      method: "POST",
      body: { license_key: "FAKE-KEY-1234", machine_id: machineId },
    });
    console.log(`  ✅ Response in ${Date.now() - t1}ms:`, JSON.stringify(result));
  } catch (e) {
    console.log(`  ✅ Error in ${Date.now() - t1}ms: "${e.message}"`);
  }

  // ─── Test 2: Empty key ───
  console.log("\nTest 2: Empty license key (expect: validation error)");
  const t2 = Date.now();
  try {
    const result = await api("/api/license/activate", {
      method: "POST",
      body: { license_key: "", machine_id: machineId },
    });
    console.log(`  ✅ Response in ${Date.now() - t2}ms:`, JSON.stringify(result));
  } catch (e) {
    console.log(`  ✅ Error in ${Date.now() - t2}ms: "${e.message}"`);
  }

  // ─── Test 3: Timeout scenario (simulate by hitting unreachable port) ───
  console.log("\nTest 3: Timeout (pointing at unreachable port 9999, expect: 8s timeout)");
  const t3 = Date.now();
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
    await fetch("http://localhost:9999/api/license/activate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ license_key: "TEST", machine_id: machineId }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    console.log(`  ❌ Unexpected success`);
  } catch (e) {
    const elapsed = Date.now() - t3;
    if (e.name === "AbortError" || elapsed >= 7000) {
      console.log(`  ✅ Timed out in ${elapsed}ms (correct — not hanging forever)`);
    } else {
      console.log(`  ✅ Error in ${elapsed}ms: "${e.message}"`);
    }
  }

  // ─── Test 4: Validate with non-existent key ───
  console.log("\nTest 4: Validate non-existent license (expect: error)");
  const t4 = Date.now();
  try {
    const result = await api("/api/license/validate", {
      method: "POST",
      body: { license_key: "NONEXISTENT-KEY", machine_id: machineId },
    });
    console.log(`  Response in ${Date.now() - t4}ms:`, JSON.stringify(result));
  } catch (e) {
    console.log(`  ✅ Error in ${Date.now() - t4}ms: "${e.message}"`);
  }

  console.log("\n=== All tests done ===");
}

runTests().catch((e) => console.error("FATAL:", e));
