# AuraBiz / AI WhatsApp Business Assistant — Deep Research Report
**Compiled:** 11 August 2026
**Project Root:** `C:\Users\rohit\Desktop\AI`
**Method:** Full codebase re-verification against `DEEP_RESEARCH_2026-08-05.md` + live DB inspection + port/process checks. Every claim below verified by direct source inspection.

---

## 1. Executive Summary

Project **"AuraBiz"** = multi-tenant SaaS jo small Indian businesses ko AI WhatsApp assistant deta hai (inventory, orders, bookings, payments, loyalty, analytics). 

**6 din me kya hua (5 Aug → 11 Aug):**
- ✅ 12 purane bugs me se ~5 fix hue (payment_status, sentiment methods, X-Tenant-ID bypass, websocket URL, bot healthcheck, bot backend URL env)
- ✅ 8/11 unauthenticated routers pe auth lag gaya
- ✅ **Bada naya feature:** AuraBiz Desktop App (Electron) + License/Purchase system (Razorpay) + landing page (3003) — monetization start ho gayi
- ❌ Multi-tenant abhi bhi **decorative** hai (23/25 tenants ek hi shared `ai_agent.db` pe)
- ❌ **2 naye guaranteed-500 bugs** mile (analytics language/detect NameError + register page broken flow)
- ❌ **Naye security risks:** unauthenticated `POST /chat/cancel-order` aur `POST /chat/broadcast`
- ⚠️ Live spendable API keys working tree me (GOOGLE, CLOUDFLARE, BOT_API_KEY)

**Runtime state (11 Aug):** Master(8010) ✓, Admin-frontend(3002) ✓, Landing(3003) ✓ — **Backend(8000) DOWN, Frontend(3001) DOWN, WhatsApp Bot(8001) DOWN**

**Repo status:** Git repo hai but **zero commits** — kuch bhi history me nahi, saara data untracked. Ye ek hi sabse bada risk hai.

---

## 2. Architecture Map (current)

```
 landing-server:3003  ── marketing page (redirect /login,/register → 3001)
        │
 admin-frontend:3002  ──► master:8010 (85 routes) ──► master/data/master.db (22 tables)
                                    │  reads tenant DBs (raw sqlite3) → sab ZERO data milta hai
 backend:8000  ── 35 routers / ~266 endpoints ──► backend/ai_agent.db (SINGLE SHARED DB, 1.5MB)
        │                    │
        ├── frontend:3001 (34 routes, Next 16, "use client" everywhere)
        └── whatsapp-bot:8001 (Baileys, 1 linked account Rohit Shah)
 desktop-app (Electron "AuraBiz") ──► master:8010 /api/license/* (activation) + bot:8001
```

---

## 3. Component-by-Component Status

### 3.1 Backend (port 8000) — `backend/`
- **Stack:** FastAPI, SQLAlchemy 2.0 async, SQLite/aiosqlite, Python 3.12+ (PROJECT_MEMORY says 3.14). Redis disabled (`database.py:20`).
- **35 routers, ~266 endpoints, 33 DB models, 52 service files.**
- **AI pipeline (best part):** 7-layer fallback — OmniRoute/OpenCode → Cloudflare → Gemini → Groq → OpenRouter → FalconEngine → rule-based. Hallucination guard against real inventory. Real RAG (Qdrant + in-process fallback). Customer memory, self-learning trainer.
- **Tests:** 13 tests in 2 files (`test_basic.py` 8, `test_security.py` 5). 3 tests silently deleted after failing. Tests hit live dev DB aur real user roles mutate karte hain.

### 3.2 Master + Multi-Tenant (port 8010) — `master/`
- `main.py` 1,978 lines, **85 routes inline** (sirf license router alag file me).
- 25 seeded tenants; **23 ka `db_path='ai_agent.db'`** (shared), 2 = `'local-desktop-app'`. **Zero tenants ka apna DB file hai.**
- `master/data/tenants/` **empty**. Repo `tenants/` me sirf 0-byte `test-tenant.db` (0 tables).
- `POST /admin/tenants` registry row banata hai, **DB file nahi banata**.
- **Naya:** `routers/license.py` (429 lines, 9 routes) — create-order, purchase (Razorpay verify), activate, validate, download-exe, admin stats/revoke. Live license activation logged: `AURABIZ-TSB5-7UN4-LY98-LCUM`; 4 licenses, 3 invoices in master.db.
- `master/releases/` me do ~180MB installers: `AuraBiz-Setup.exe` (11 Aug) + `AuraBiz-Test.exe` (10 Aug).

### 3.3 Frontend (port 3001) — `frontend/`
- Next.js 16.2.9, React 19.2.7, Tailwind 3, framer-motion. 34 routes, sab "use client".
- **Root `/` ab marketing landing page hai** (722 lines) with Razorpay checkout + license purchase → master `/api/license/*`.
- **Register page 3-step wizard buggy:** Continue button `setStep(2)` plan step skip karta hai, phir `setStep(3)` out-of-bounds; OTP UI defined but never rendered; `/api/v1/auth/*` calls **relative** hain (Next origin 3001 pe 404 honge — koi rewrite/middleware nahi).

### 3.4 Admin Frontend (port 3002) — `admin-frontend/`
- Next.js 16.2.9, React 19.2.4, Tailwind 4. 22 routes, **naya `/licenses`** page (license management — works, master endpoints exist).
- **Impersonate button broken:** calls `POST /admin/tenants/{id}/impersonate` jo master me **exist nahi karta** → 404.
- 4 aur dead API calls (update/delete tenant, ai-provider test, system health per-service) — unused code.
- No error/not-found/loading boundaries — crash = blank screen.
- **No Dockerfile** — compose build fail karega.

### 3.5 WhatsApp Bot (port 8001) — `whatsapp-bot/`
- `bot.js` 688 lines, Baileys. **Abhi process DOWN hai.**
- `BACKEND_URL` env support **fix ho gaya** (`bot.js:22`).
- Healthcheck ab `/status` ping karta hai (fix).
- `BOT_API_KEY` locally unset → `/send`, `/logout`, `/register` endpoints **open**.
- `auth_state/` = **24,920 files, 8.4 MB** (~86 files/day growing, koi cleanup nahi). `sessions.json` 17 entries, kabhi prune nahi hota.
- Docker issue bacha: `.dockerignore` me `auth_info` hai (nahi `auth_state`) → image me 25k files bake ho jayengi.

### 3.6 Desktop App (port —) — `desktop-app/` (NEW)
- Electron 33.4.11 "AuraBiz", electron-builder NSIS. Built installers exist.
- License activate/validate → master :8010; machine-ID fingerprint (hostname+CPU+RAM+username hash).
- Products **local JSON** me (`userData/data/products.json`) — better-sqlite3 comment hai par switch ho chuka (zero native deps).
- Free AI = local rule-based regex (price/stock/order Hinglish); Paid AI = **placeholder echo** — real AI reply nahi, sirf canned string.
- `electron-updater` referenced but **not installed**.

### 3.7 `.freebuff/` — `desktop-v2.db` (1.7 MB)
Test DB: `projects`(1), `threads`(2), `messages`(6), `queue_items`(3), `thread_deliveries`(0) — desktop app ke experiments/test data, main flow me nahi.

### 3.8 Landing server — `landing-server.js` (port 3003)
Simple Node HTTP server, Hinglish marketing page, `/login|/register|/dashboard|/setup` → 302 redirect to `localhost:3001`. **Abhi running hai.**

---

## 4. Bug Verification (5 Aug report vs 11 Aug reality)

### ✅ FIXED (5 bugs + 8 auth gaps)
| # | Issue | Evidence |
|---|---|---|
| 1 | Order `payment_status` column missing | `models.py:655` ab exists + `database.py:88-108` auto-migration |
| 2 | analytics calls non-existent sentiment methods | ab `get_sentiment_summary()` / `get_customer_engagement()` real calls |
| 3 | X-Tenant-ID header bypasses JWT | `middleware/tenant.py` — JWT claim pehle; header sirf unauthenticated requests ke liye |
| 4 | bot hardcoded `127.0.0.1:8000` | `bot.js:22` → `process.env.BACKEND_URL \|\| ...` |
| 5 | bot healthcheck pings nonexistent `/health` | Dockerfile ab `/status` ping karta hai |
| 6 | bot_proxy never forwards BOT_API_KEY | `bot_proxy.py:18-22` `_bot_headers()` ab forward karta hai |
| 7-14 | 8 unauthenticated routers | followups, scheduled_messages, inventory_alerts, orders_bookings, exports, cart, bot_stats, uploads — sab auth + `verify_business_access` |

### ❌ STILL BROKEN (11 bugs)
| # | Issue | Location |
|---|---|---|
| 1 | Multi-tenancy decorative — 23/25 tenants shared DB, no per-tenant files, POST /admin/tenants doesn't create DB | `master/main.py:237-264`, `seed_tenants.py:36` |
| 2 | Master↔backend: no auth link, 2 independent JWTs | `master/main.py` vs `backend/routers/auth.py` |
| 3 | 5 missing master endpoints (PUT/DELETE tenant, impersonate, ai-provider test, health/{service}) | admin-frontend calls → 404 |
| 4 | Broken tenant data proxy — opens `master/ai_agent.db` (0-byte), analytics aggregator reads it → **sab analytics ZERO**, `platform_stats` 0 rows | `main.py:743-780`, `services/analytics_aggregator.py:29-33` |
| 5 | Suspension cosmetic — backend ko pata hi nahi | `main.py:283-293` |
| 6 | whatsapp-monitor placeholder — sab "connected" fabricated | `main.py:1152-1204` |
| 7 | Chat-parsed orders still bypass OrderManager (no atomic stock/payment) | `chat.py:739-870` |
| 8 | Voice messages broken — `GROQ_API_KEY` commented out + `os.getenv` never sees `.env` (no load_dotenv, pydantic-settings doesn't export) | `.env`, `voice_service.py:8` |
| 9 | IDOR: customers (10/11 endpoints incl. bulk export), orders (list/stats/update), inventory, templates, trainer import-chat — **no ownership check** | `customers.py`, `orders.py`, `inventory.py` |
| 10 | `skills/` 12 files orphaned | `backend/skills/` |
| 11 | Alembic drift — `main.py:29` still `create_all`; 4 migrations unused | `main.py`, `alembic/` |
| 12 | In-memory services: FeedbackManager, EscalationManager, OTP store, knowledge chunks — restart pe data gayab | `services/feedback_manager.py`, etc. |
| 13 | 3 open routers: monitoring `/metrics` (public system info), feedback POST, orders POST/invoice/payment-link | `monitoring.py`, `orders.py` |
| 14 | `__import__('datetime')` hack (webhooks + payments) | `webhooks.py:123`, `payments.py:76` |
| 15 | start scripts: `start-all.ps1` ab sahi path use karta hai ✓, lekin `TENANT_SETUP.md` abhi bhi `E:\AI` reference karta hai; `start.bat`/`start-servers.ps1` **exist hi nahi karte** | `TENANT_SETUP.md` |
| 16 | auth_state 24,920 files growing, sessions.json never pruned | `bot.js` |
| 17 | Docker: admin-frontend no Dockerfile; `chat.py:31` still hardcoded `127.0.0.1:8001`; `bot_config.py:13` path resolves outside container; `.dockerignore` wrong dir; NEXT_PUBLIC envs baked at build; `.env.docker` BOT_API_KEY mismatch | compose + Dockerfiles |

### 🆕 NEW BUGS (11 Aug discovery)
| # | Issue | Location | Severity |
|---|---|---|---|
| 1 | `POST /api/v1/analytics/language/detect` — **guaranteed NameError → 500** (`business_id`/`db` undefined) | `analytics.py:262-279` | HIGH (crash) |
| 2 | `POST /chat/cancel-order` — **no auth**, koi bhi kisi bhi order ko payment_id se cancel kar sakta hai | `chat.py:1231-1235` | CRITICAL |
| 3 | `POST /chat/broadcast` — **no auth** broadcast | `chat.py:1422` | HIGH |
| 4 | `GET /chat/loyalty/{customer_id}` — no auth loyalty data read | `chat.py:1337` | MEDIUM |
| 5 | Register page broken: wizard skips steps, relative `/api/v1` fetches → 404 (no Next rewrite) | `frontend/src/app/register/page.tsx` | HIGH (signup broken) |
| 6 | `os.getenv` vs `.env` plumbing — OPENCODE_URL/MODEL, BOT_API_KEY, trainer/knowledge GOOGLE key kabhi read nahi hote | `free_ai.py:51-53`, `bot_proxy.py:15`, `trainer.py:207` | MEDIUM |
| 7 | `GET /knowledge/documents` empty business_id → **sab tenants' chunks dump** | `knowledge.py:105` | HIGH |
| 8 | OTP API response me return hota hai ("development me" comment) + in-memory store | `auth.py:63-89` | MEDIUM |
| 9 | Public `X-Tenant-ID` on unauth endpoints → arbitrary tenant DB files ban sakte hain (disk-fill DoS) | `middleware/tenant.py:33-38` | MEDIUM |
| 10 | Desktop Paid AI = placeholder echo, real AI nahi | `desktop-app/main.js:224-228` | PRODUCT |
| 11 | `master/ai_agent.db` 0-byte file (broken proxy side-effect) | master dir | LOW |

---

## 5. Security Audit (current)

| # | Finding | Severity |
|---|---|---|
| 1 | **Live spendable keys in working tree:** `.env` (GOOGLE_AI_API_KEY, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, BOT_API_KEY, 2× 64-char secrets). `.env` is gitignored ✓ — lekin **repo me zero commits** hai, koi backup/sharing karo toh keys rotate karna zaroori | CRITICAL |
| 2 | Unauthenticated `POST /chat/cancel-order` (order cancel by payment_id) | CRITICAL |
| 3 | Unauthenticated `POST /chat/broadcast` | HIGH |
| 4 | IDOR: customers bulk export, orders read/modify by any logged-in user | HIGH |
| 5 | TeamMember.permissions never enforced — koi bhi team member full access | HIGH |
| 6 | Bot endpoints open locally (BOT_API_KEY unset) | HIGH |
| 7 | Public `/metrics` (psutil system info) | MEDIUM |
| 8 | `merchant@upi` hardcoded — saare UPI links fake/undeliverable | MEDIUM |
| 9 | Weak default admin creds (`admin@platform.com / ChangeMe!SecureAdmin2026`) printed in scripts | MEDIUM |
| 10 | Forgot-password stub — token without email flow | MEDIUM |
| 11 | `creds.json` WhatsApp signing keys plaintext | MEDIUM |
| 12 | QR → third-party `api.qrserver.com` | LOW |
| 13 | No secret scanning in CI; master/bot/admin-frontend images kabhi build nahi hote CI me | MEDIUM |

---

## 6. Strengths (kya achha hai)

1. **7-layer AI fallback + hallucination guard** — zero API keys pe bhi WhatsApp replies chalti hain
2. **Order integrity** (OrderManager): SELECT FOR UPDATE, idempotency keys, atomic stock, cancel-pe-stock-restore
3. **Real RAG** knowledge base + customer long-term memory
4. **Secure webhooks** (HMAC SHA-256, backoff, replay)
5. **~50 well-structured service modules**, middleware hygiene (rate-limit, security headers, request IDs)
6. **Monetization start ho gayi:** desktop app + license/Razorpay purchase + marketing landing page
7. **Hinglish UX** for target users, 34 pages ka polished feature surface

---

## 7. Recommended Action Plan (priority order)

### P0 — Abhi fix karo (security/data)
1. `.env` me keys **rotate karo** + repo ko pehla commit karo (backup banao)
2. `POST /chat/cancel-order` aur `/chat/broadcast` pe auth + business check
3. `analytics.py` `/language/detect` NameError fix (params me `business_id: str`, `db: AsyncSession = Depends(get_db)` add karo)
4. Register page fix (step wizard + `/api/v1` absolute URLs ya Next rewrites)
5. customers/orders/inventory/templates me `verify_business_access` add karo

### P1 — Multi-tenant ya single-tenant, decide karo
6. Ya toh per-tenant DB provisioning + master↔backend linkage implement karo, ya explicitly "single-tenant" declare karo
7. Master analytics aggregator ka `db_path` resolution fix (sab zeros aana band hoga)
8. Impersonate + missing master endpoints implement karo

### P2 — Product
9. Desktop app ka Paid AI real karo (master AI providers se)
10. Voice messages enable karo (GROQ key uncomment + load_dotenv fix)
11. Chat-parsed orders ko OrderManager se unify karo

### P3 — Polish/DevOps
12. `admin-frontend/Dockerfile` banao; `chat.py`/`bot_config.py` env-driven karo; `.dockerignore` fix
13. auth_state cleanup job + sessions.json pruning
14. Scheduler ko real follow-ups bhejne do; in-memory services DB-backed karo
15. CI me: secret scanning, master+admin-frontend+bot builds, `push: false` → real deploy
16. `TENANT_SETUP.md` me `E:\AI` → correct path; deleted `start.bat` references hatao

---

## 8. Metrics Snapshot

| Metric | Value |
|---|---|
| Backend routers / endpoints | 35 / ~266 |
| Services | 52 |
| DB models | 33 (backend) + 22 (master) |
| Frontend routes | 34 (3001) + 22 (3002) |
| Master routes | 85 (76 inline + 9 license) |
| Tests | 13 (2 files) |
| Tenants (master registry) | 25 (23 → shared ai_agent.db) |
| Backend DB | ai_agent.db 1.5 MB — 61 businesses, 61 users, 111 customers, 20 orders, 69 products |
| WhatsApp auth_state files | 24,920 (8.4 MB, growing ~86/day) |
| Desktop installers | AuraBiz-Setup.exe + AuraBiz-Test.exe (~180 MB each) |
| Git | 0 commits |
| Running services (11 Aug) | master 8010, admin-frontend 3002, landing 3003 |

---

*Report compiled from full codebase re-verification on 11 Aug 2026. All bug claims verified by direct source inspection; line numbers refer to current working tree.*
