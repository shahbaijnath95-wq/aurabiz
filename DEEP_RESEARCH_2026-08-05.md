# AI WhatsApp Business Assistant — Complete Deep Research Report

> **Compiled:** 5 August 2026
> **Project Root:** `C:\Users\rohit\Desktop\AI`
> **Method:** Full codebase read + cross-module verification (33 routers, ~50 services, 2 Next.js apps, WhatsApp bot, Docker, CI/CD)

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Architecture Map](#2-architecture-map)
3. [Backend Deep Dive (port 8000)](#3-backend-deep-dive-port-8000)
4. [AI System Analysis](#4-ai-system-analysis)
5. [Master + Multi-Tenant Architecture (port 8010)](#5-master--multi-tenant-architecture-port-8010)
6. [Frontend Deep Dive (port 3001)](#6-frontend-deep-dive-port-3001)
7. [Admin Frontend Deep Dive (port 3002)](#7-admin-frontend-deep-dive-port-3002)
8. [WhatsApp Bot Deep Dive (port 8001)](#8-whatsapp-bot-deep-dive-port-8001)
9. [Docker & Deployment](#9-docker--deployment)
10. [Security Audit](#10-security-audit)
11. [Verified Bugs & Critical Issues](#11-verified-bugs--critical-issues)
12. [Stub / Placeholder Code Inventory](#12-stub--placeholder-code-inventory)
13. [Strengths](#13-strengths)
14. [Recommended Action Plan](#14-recommended-action-plan)

---

## 1. Project Overview

**What it is:** A multi-tenant SaaS platform that lets small Indian businesses (SMBs) run an AI-powered WhatsApp assistant. Customers chat with the business over WhatsApp; the AI handles inquiries, product lookup, orders, bookings, payments, loyalty, and follow-ups. Businesses manage everything from a web dashboard.

**Scale (code):**

| Component | Files | Approx. Lines | Tech |
|---|---|---|---|
| `backend/` | 136 | ~20,500 | FastAPI, SQLAlchemy 2.0 async, SQLite, Qdrant |
| `master/` | 8 | ~2,300 | FastAPI (75 routes inline), SQLite |
| `frontend/` | 539 | ~124,000 | Next.js 16.2.9, React 19, Tailwind 3, framer-motion |
| `admin-frontend/` | 516 | ~55,400 | Next.js 16.2.9, React 19, Tailwind 4 |
| `whatsapp-bot/` | 24,409 | ~26,500 | Node.js, Baileys 7 |

**The 5 services:**
| Service | Port | Role |
|---|---|---|
| Master Backend | 8010 | Super-admin API — tenants, billing, AI config, analytics |
| Backend API | 8000 | Tenant business API — all business logic + AI |
| Frontend | 3001 | Business-owner dashboard (Hinglish UI) |
| Admin Frontend | 3002 | Platform-operator super-admin panel |
| WhatsApp Bot | 8001 | Baileys WhatsApp Web connection + QR pairing + HTTP bridge |

---

## 2. Architecture Map

```
                          ┌─────────────────────┐
                          │  admin-frontend:3002 │  Platform operator panel
                          └──────────┬──────────┘
                                     │  http://localhost:8010 (master API)
                          ┌──────────▼──────────┐
                          │   master:8010       │  Tenant registry, billing, AI keys,
                          │   (75 routes)       │  analytics aggregation, backups
                          └──────────┬──────────┘
                                     │  reads tenant DBs (sqlite) for analytics
                          ┌──────────▼──────────┐
                          │   backend:8000      │  Business logic + AI pipeline
                          │   (37 routers)      │  Per-tenant SQLite (default shared)
                          └──┬───────────┬──────┘
                    ┌────────┘           └────────┐
          ┌─────────▼─────────┐          ┌────────▼────────┐
          │  frontend:3001    │          │ whatsapp-bot:8001│
          │  owner dashboard  │          │ Baileys socket    │
          └─────────┬─────────┘          │ + HTTP bridge     │
                    │                    └────────┬─────────┘
                    │  ws://127.0.0.1:8000/ws     │ POST /api/v1/chat
                    └──────────────┬──────────────┘
                                   ▼
                        WhatsApp (Web protocol)
```

---

## 3. Backend Deep Dive (port 8000)

### 3.1 Stack & Setup
- FastAPI + SQLAlchemy 2.0 async + `aiosqlite`, Python 3.12
- JWT auth via python-jose; passlib bcrypt (fixed to 4.0.1 — see issues)
- Redis **explicitly disabled** (`database.py:19`, `redis_client = None`)
- 37 routers registered in `main.py`; loguru logging
- Middleware chain (correct order): RequestLogging → RateLimit (1.0/s token bucket) → Tenant → CORS → SecurityHeaders → RequestID

### 3.2 Router Inventory (37 routers)

| Router | Purpose | Auth |
|---|---|---|
| `auth.py` | Login, register, business create/update, forgot/reset password | Public (login/register) |
| `chat.py` | Core AI chat endpoint (voice/image/text), conversations, admin reply | Public + JWT |
| `customers.py` | Customer CRUD, segments, search, CSV import/export | JWT |
| `inventory.py` | Products/services CRUD, stock, low-stock, analytics | JWT |
| `orders.py` | Orders list/stats/update, invoice | JWT (POST open) |
| `orders_bookings.py` | Bookings/appointments | **NO AUTH** |
| `payments.py` | Payment links, UPI QR, status | JWT |
| `analytics.py` | Dashboard, revenue, customers, insights, activity | JWT |
| `loyalty.py` | Points, tiers, referrals, history | JWT |
| `admin.py` | Billing overview, API keys, QR gen, notifications | require_admin |
| `integrations.py` | Google Business, Instagram, Razorpay, PhonePe, Tally | JWT |
| `webhooks.py` | Register/test/retry webhooks + delivery logs | JWT |
| `templates.py` | WhatsApp templates | JWT |
| `broadcast.py` | Broadcast messages | JWT |
| `coupons.py` | Coupon CRUD | JWT |
| `segments.py` | Dynamic customer segments | JWT |
| `teams.py` | Team + RBAC permissions | JWT |
| `feedback.py` | NPS, reviews, surveys | JWT (POST open) |
| `revenue.py` | Forecast, patterns, alerts, what-if | JWT |
| `followups.py` | Follow-up scheduling | **NO AUTH** |
| `scheduled_messages.py` | Scheduled messages | **NO AUTH** |
| `inventory_alerts.py` | Stock alerts | **NO AUTH** |
| `exports.py` | CSV/JSON export jobs | **NO AUTH** |
| `cart.py` | Cart operations | **NO AUTH** |
| `bot_proxy.py` | Proxy to bot (QR, status, send, logout) | JWT |
| `bot_config.py` | Read/write bot_config.json | JWT |
| `bot_stats.py` | WhatsApp message stats from DB | **NO AUTH** |
| `monitoring.py` | Metrics, health | Public |
| `knowledge.py` | RAG knowledge base upload/index | JWT |
| `trainer.py` | Falcon AI trainer | JWT |
| `uploads.py` | File uploads (images) | **NO AUTH** |
| `transactions.py` | Transaction records | JWT |
| `audit.py` | Audit logs, compliance | JWT |
| `catalog.py` | Catalog, search, recommendations | JWT |
| `settings.py` | Business settings | JWT |

### 3.3 Database Schema (SQLite)
Core models in `models.py`: `User`, `Business`, `Customer`, `Product`, `Order`, `OrderItem`, `Transaction`, `Payment`, `Coupon`, `LoyaltyProgram`, `LoyaltyTier`, `LoyaltyTransaction`, `Referral`, `Review`, `Survey`, `Segment`, `Team`, `TeamMember`, `InventoryAlert`, `FollowUp`, `ScheduledMessage`, `Webhook`, `WebhookLog`, `Template`, `ChatMessage`, `Conversation`, `ExportJob`, `AuditLog`, `Setting`, `Booking`, `Wholesaler`.

---

## 4. AI System Analysis

### 4.1 Provider Fallback Chain (`free_ai.py`)
```
OpenCode/OmniRoute (localhost:3000, keyless)
  → Cloudflare Workers AI
    → Google Gemini (gemini-2.5-flash)
      → Groq (llama-3.1-8b-instant)
        → OpenRouter
          → FalconEngine (local LLM-ish engine)
            → falcon_reply rule-based legacy
              → Knowledge-base fallback
```
**Verdict:** 7-layer graceful degradation — WhatsApp replies keep working even with zero API keys. Best-engineered part of the system.

### 4.2 Supporting AI Services
- **`falcon_engine.py` (59KB)** — main local AI engine with intent detection, tools, memory
- **`free_ai.py` (69KB)** — multi-provider orchestration + hallucination guard
- **`openai_brain.py`** — OpenAI adapter
- **`embedding_service.py`** — Gemini `text-embedding-004` (768-dim) embeddings
- **`vector_store.py`** — Qdrant with in-process fallback (Qdrant not running locally)
- **`knowledge_base.py`** — RAG over business documents (PDF/DOCX/XLSX/CSV/TXT/MD via `document_parser.py`)
- **`memory_manager.py`** — per-customer facts + recent interactions in `ai_memory` vector collection
- **`language_service.py`** — Hinglish/Hindi detection + localization
- **`falcon_trainer.py`** — self-learning from corrections (JSON-file, atomic writes, file lock)
- **`falcon_smart.py`** — SmartResponder (greetings, suggestions, offers, seasonal)
- **`conversation_analytics.py`** — sentiment, engagement, intents
- **13 `skills/`** modules (analytics, appointments, billing, catalog, feedback, followup, greeting, orders, payments, pricing, support) — **ORPHANED, never imported**

### 4.3 Chat Flow (`routers/chat.py`, ~900 lines)
1. Voice → transcription → AI; Image → caption extraction
2. Build context: customer memory, last 10 messages, inventory search, orders, coupons, knowledge base, language
3. `get_ai_reply_free()` → hallucination check against real inventory
4. Save inbound/outbound `WhatsAppMessage`, update `Conversation`
5. Auto-create Booking/Order+Transaction when AI text confirms
6. Admin reply via `BOT_URL/send`

---

## 5. Master + Multi-Tenant Architecture (port 8010)

### 5.1 What It Does
- Complete super-admin API (75 routes inline in `master/main.py`, 1,889 lines)
- Tenant registry, AI provider CRUD, analytics aggregation, billing/invoices, audit, feature flags, team, API keys, support tickets, notifications, webhooks, backups, resellers, white-label, integrations
- `master/services/analytics_aggregator.py` reads tenant DBs directly via sqlite3
- `master/services/platform_ai.py` — platform-level AI key store

### 5.2 **CRITICAL FINDING: Multi-tenancy is decorative, not functional**

Verified evidence:
1. **All 10 seeded tenants have `db_path = 'ai_agent.db'`** — every tenant points at the shared `backend/ai_agent.db`
2. `master/data/tenants/` is **empty**; repo `tenants/` has only an empty `test-tenant.db` (0 tables)
3. **`POST /admin/tenants` never creates a tenant DB file** — comment says "Create tenant DB" but only writes a registry row
4. `db_path` **mismatch**: master records `master/data/tenants/{id}.db`; backend lazily creates `<repo>/tenants/{id}.db`
5. **No component ever sends `X-Tenant-ID` header** — every request resolves to `tenant_id="default"` → shared DB
6. Per-tenant DB code path (`database.py:33-53`) is **dead code in practice**
7. **Security caveat:** the *unauthenticated* `X-Tenant-ID` header is honored BEFORE JWT verification → anyone can steer requests into another tenant's DB

### 5.3 Master ↔ Backend Auth
**None exists.** Two fully independent JWT systems:
- Master: `MASTER_JWT_SECRET`, claims `{sub, exp}` — no tenant_id
- Backend: `SECRET_KEY`/`JWT_SECRET_KEY`, claims `{sub, tenant_id, exp}`

No token exchange, no shared secret. Master tokens meaningless to backend and vice-versa.

### 5.4 Missing Master Endpoints (admin-frontend calls → 404)
- `PUT /admin/tenants/{id}`, `DELETE /admin/tenants/{id}`
- `POST /admin/tenants/{id}/impersonate` — **impersonation entirely unimplemented**
- `POST /admin/ai-providers/{id}/test`
- `GET /admin/system/health/{service}`

### 5.5 Broken Tenant Data Proxy
`GET /admin/tenants/{id}/data/{table}` — with `db_path='ai_agent.db'` relative, sqlite3 creates a 0-byte `master/ai_agent.db` then 500s (whitelist even omits `businesses`/`users`).

### 5.6 Suspension is Cosmetic
`suspend` flips a flag in master DB only — backend has no knowledge; suspended tenant keeps working.

### 5.7 Effective Reality
**Single-tenant app with a decorative super-admin registry.** The full multi-tenant promise (per-tenant DB → isolation → admin inspection/impersonation) is NOT realized.

---

## 6. Frontend Deep Dive (port 3001)

### 6.1 Stack
Next.js 16.2.9, React 19.2.7, Tailwind 3.4.15, framer-motion, lucide-react, TypeScript, App Router, **100% client-rendered** ("use client" everywhere, no SSR/SEO/metadata).

### 6.2 Route Map (34 routes)
- **Auth:** `/`, `/login`, `/register`, `/setup` (6-step wizard), `/forgot-password`
- **Dashboard:** `/dashboard` (stats, revenue chart, activity, websocket), `/dashboard/inventory`, `/dashboard/loyalty`
- **Business ops (`/admin/*` — business management, not super-admin):** `/admin`, `/admin/appointments`, `/admin/broadcast`, `/admin/coupons`, `/admin/feedback`, `/admin/inbox`, `/admin/orders`, `/admin/settings` (5 tabs), `/admin/whatsapp` (QR polling)
- **Tools:** `/ai-training`, `/analytics`, `/audit`, `/catalog`, `/chat`, `/customer-portal`, `/exports`, `/followups`, `/integrations`, `/pay`, `/revenue`, `/scheduled-messages`, `/segments`, `/templates`, `/teams`, `/webhooks`, `/wholesalers`

### 6.3 API Layer (`src/lib/api.ts`, 589 lines)
- `API_BASE = NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000" + "/api/v1"`
- Generic `request<T>()`: token + business_id from localStorage, 401 → wipe + hard redirect
- **Auto-unwrap quirk (l.65-71):** any object with exactly one array key collapses to that array — type-unsafe
- 26 typed domain modules; auth.login bypasses wrapper (form-encoded)

### 6.4 Real-time
`use-websocket.ts` → hardcoded `ws://127.0.0.1:8000/ws?business_id=...&token=...` — 3s auto-reconnect. **Does not honor NEXT_PUBLIC_API_URL.**

### 6.5 Design
Distinctive warm off-white/amber-gold theme, rounded-2xl, custom classes (`btn-gold`, `input-angel`, `shadow-card`), framer-motion animations, skeletons, emoji sidebar icons, **Hinglish UI copy**, global `FloatingChat` widget (auto-sends "Hello!" when opened — even on login page).

---

## 7. Admin Frontend Deep Dive (port 3002)

### 7.1 Stack
Next.js 16.2.9, React 19.2.4, Tailwind 4 (CSS-first), lucide-react 1.22, react-hot-toast, English UI, no framer-motion, no error boundaries.

### 7.2 Route Map (21 routes)
`/login`, dashboard group: `dashboard`, `tenants`, `tenants/[id]` (5 tabs + impersonate), `ai-config`, `analytics`, `billing` (plans: starter 0 / growth 999 / enterprise 2999), `audit`, `team`, `api-keys`, `feature-flags`, `whatsapp-monitor`, `support`, `notifications`, `webhooks`, `backups`, `system-health`, `resellers`, `white-label`, `integrations`

### 7.3 API Layer (`lib/api.ts`, 402 lines)
- `MASTER_API = NEXT_PUBLIC_MASTER_API_URL || "http://localhost:8010"`
- Singleton `MasterAPI` class, token in `localStorage["admin_token"]`
- No 401 auto-handling (layout guard handles it); no websocket

### 7.4 Notable Gaps
- No `error.tsx`/`not-found.tsx`/`loading.tsx` — crash = blank screen
- Heavy `any[]` typing
- Calls 4+ master endpoints that don't exist (see §5.4)

---

## 8. WhatsApp Bot Deep Dive (port 8001)

### 8.1 Architecture
Single file `bot.js` (685 lines): Baileys multi-file auth (`auth_state/`), exponential-backoff reconnect, `loggedOut` → wipe auth + fresh QR, `creds.update` persistence. **Uses reverse-engineered WhatsApp Web protocol, NOT official Cloud API** (`whatsapp_client.py` is dead code).

### 8.2 Message Flow
```
WhatsApp message → bot.js messages.upsert
  → business-hours gate → POST http://127.0.0.1:8000/api/v1/chat
    → backend: customer lookup, history, inventory, AI pipeline
    → reply text (optionally IMAGE_URL: marker for media)
  → outbox queue (200ms rate limit, 3 retries) → sendMessage
```

### 8.3 HTTP Bridge (same process, port 8001)
| Route | Purpose |
|---|---|
| `/`, `/scan` | QR pairing HTML page (polls every 3s, uses external `api.qrserver.com`) |
| `/qr` | `{qr, status, user}` |
| `/status` | connection status, uptime, queue stats |
| `/logout` | wipe auth_state (requires BOT_API_KEY) |
| `/send` | admin outbound send (requires key) |
| `/register` | change business_id (requires key) |

**If `BOT_API_KEY` env unset → all endpoints open/unauthenticated.** Locally it runs unset.

### 8.4 Current State
One linked account: `Rohit Shah` (917567857818). 24,404 auth-state files on disk (Baileys device cache, unbounded growth).

---

## 9. Docker & Deployment

### 9.1 docker-compose.yml (7 services)
`db` (postgres:16), `redis` (redis:7), `qdrant` (v1.12.4), `master`, `backend`, `frontend` (3001:3000), `admin-frontend` (3002:3000), `whatsapp-bot` (8001).

### 9.2 Docker Findings (all verified)
| # | Issue | Severity |
|---|---|---|
| 1 | **`admin-frontend` has NO Dockerfile** → compose build fails | Critical |
| 2 | **Bot can't reach backend in Docker:** `bot.js:21` hardcodes `127.0.0.1:8000`, ignores `BACKEND_URL` env | Critical |
| 3 | **Backend can't reach bot in Docker:** `chat.py:31` & `bot_proxy.py:12` hardcode `127.0.0.1:8001` | Critical |
| 4 | **Bot auth not persisted:** Dockerfile creates `/app/auth_info`, compose mounts it — but bot uses `auth_state` | High |
| 5 | **Bot healthcheck broken:** pings `/health` which doesn't exist → always unhealthy | High |
| 6 | **`bot_config.py` path broken in Docker:** resolves outside container | High |
| 7 | **NEXT_PUBLIC envs set at runtime but Next.js inlines at build time** — baked-in defaults win | High |
| 8 | **Backend Dockerfile imports `master.services.platform_ai`** (cross-package) — backend image only copies `./backend` → ImportError silently swallowed → platform AI keys never work in containers | Medium |
| 9 | `.env.docker` sets `BOT_API_KEY=change-me-in-production` → backend's unauthenticated bot calls get 401 | High |
| 10 | `docker-compose.prod.yml` uses `${POSTGRES_PASSWORD}`/`${REDIS_PASSWORD}` not defined in `.env.docker` | Medium |

### 9.3 CI/CD (`.github/workflows/ci.yml`)
- Backend: pip install + pytest + ruff (E,F)
- Frontend: npm ci + lint + build
- Docker: builds backend/frontend/bot images — **`push: false`, no deploy step**
- **Gaps:** no bot/master tests, admin-frontend/master images never built, **no secret scanning despite live keys in tree**

---

## 10. Security Audit

### 10.1 CRITICAL — Live API Keys in Plaintext
Real, spendable credentials sitting in working-tree files:
- `.env`: `JWT_SECRET_KEY`, `GOOGLE_AI_API_KEY`, `OPENROUTER_API_KEY` (`sk-or-v1-...`), `GROQ_API_KEY` (`gsk_...`)
- `backend/.env`: `SECRET_KEY`, `JWT_SECRET_KEY`, `GOOGLE_AI_API_KEY`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `BOT_API_KEY`

Also referenced in `FULL_PROJECT_RESEARCH.md`. Repo has **zero commits** (nothing in git history yet) — but keys must be **rotated** if this tree is ever shared/backed up.

### 10.2 Other Security Issues
| # | Issue | Severity |
|---|---|---|
| 1 | **11 routers with NO auth** (followups, scheduled_messages, inventory_alerts, orders_bookings, exports, cart, feedback POST, bot_stats, uploads, monitoring, orders POST) | High |
| 2 | **IDOR risk:** most business routers only check "logged in" not business ownership — any authed user can query any `business_id` | High |
| 3 | **`X-Tenant-ID` header bypasses JWT verification** (honored first) — tenant isolation bypass | High |
| 4 | **Bot admin endpoints unauthenticated locally** (`/send`, `/logout`, `/register` with BOT_API_KEY unset) | High |
| 5 | Weak default admin `admin@platform.com / ChangeMe!SecureAdmin2026`, printed in start scripts | Medium |
| 6 | Forgot-password flow is an insecure stub — token without real email flow | Medium |
| 7 | UPI payment link defaults to hardcoded `merchant@upi`; client-supplied business_id trusted | Medium |
| 8 | `creds.json` = WhatsApp signing keys in plaintext on disk (gitignored, but sensitive) | Medium |
| 9 | QR sent to third-party `api.qrserver.com` | Low |
| 10 | `.env.docker.example` listed in `.gitignore` — example should be committed | Low |

---

## 11. Verified Bugs & Critical Issues

All verified by direct code inspection:

### Data Integrity
| # | Bug | Location |
|---|---|---|
| 1 | **`Order` model has NO `payment_status` column, but `order_manager.py:109` writes `payment_status="pending"`** → runtime AttributeError / silent column loss | `models.py:635` vs `order_manager.py:109` |
| 2 | **Duplicate order systems:** chat-parsed orders (from AI reply text) bypass OrderManager's atomic stock/payment logic | `chat.py:713-826` vs `chat.py:1073-1147` |
| 3 | **`analytics.py` calls non-existent methods** `get_sentiment_analysis()`/`get_engagement_metrics()` → AttributeError (confirmed in logs) | `routers/analytics.py:192,208` vs `conversation_analytics.py` (real: `get_sentiment_summary`, `get_customer_engagement`) |
| 4 | **Scheduler marks follow-ups "sent" without sending** | `scheduler.py:26-29` |
| 5 | **In-memory state loses data on restart:** FeedbackManager, EscalationManager, PromptManager, MessageQueue, falcon_features LoyaltyManager/Calendar/Broadcasts, ConnectionManager | several `services/*` |
| 6 | **Loyalty split-brain:** DB-backed `loyalty_manager.py` vs in-memory `falcon_features.LoyaltyManager`; chat orders use in-memory → points vanish on restart | `chat.py:809-821` |

### Operational
| # | Bug | Location |
|---|---|---|
| 7 | **All start scripts hardcode `E:\AI`** (doesn't exist; project at `C:\Users\rohit\Desktop\AI`) → nothing launches as-is | `start-all.ps1`, `start.bat`, `start-servers.ps1`, etc. |
| 8 | **`start-all.ps1` misnamed:** only starts backend+master, never frontend/admin/bot | `start-all.ps1` |
| 9 | **`start.bat` runs `taskkill /F /IM python.exe` + `node.exe`** — kills EVERY Python/Node process on the machine | `start.bat:9-10` |
| 10 | **`bot_proxy.py` never forwards BOT_API_KEY** → 401 once key configured | `bot_proxy.py` |
| 11 | **Voice messages broken:** `GROQ_API_KEY` commented out in `backend/.env` + pydantic-settings don't export to os.environ → every voice note gets fallback text | `voice_service.py:8` |
| 12 | **`auth_state/` file explosion:** 24,404 files, no cleanup → unbounded growth | `bot.js` |
| 13 | **`sessions.json` unbounded** — never pruned | `bot.js` |
| 14 | **Timezone-naive `datetime.utcnow()`** mixed with `replace(tzinfo=None)` workarounds throughout | backend services |
| 15 | **Alembic drift:** 4 versions exist but `main.py:30` uses `create_all` | `alembic/` |
| 16 | **`skills/` package orphaned** — never imported anywhere | `backend/skills/` |
| 17 | **Only 1 real test** (`tests/test_basic.py`) + 8 scratch `test_*.py` files at root | `tests/` |
| 18 | **`webhooks.py:108` uses `__import__('datetime')` inline hack** | `webhooks.py` |

---

## 12. Stub / Placeholder Code Inventory

Code that returns zeros/empty/hardcoded values instead of real logic:

| Service | Stubbed Feature |
|---|---|
| `admin_service.py:37-44` | Billing overview = zeros, subscription stubs |
| `audit_service.py:43-48` | `export_audit_logs` returns path WITHOUT writing file; compliance all-zeros |
| `tally_client.py` / `google_business.py` / `instagram_service.py` | All methods return `[]`/`{}` |
| `feedback_manager.py` | `send_nps_survey` returns True (never sends); NPS zeros |
| `revenue_forecaster.py:46-94` | Flat 1000 forecast; patterns/demand/what-if hardcoded |
| `analytics_engine.py:191-216` | MRR/churn/CLV/segmentation all zeros |
| `customer_service.py` | CSV import returns `{imported: 0}`; merge just counts |
| `inventory_manager.py` | Turnover/dead-stock zeros |
| `template_manager.py` | `send_test` returns "sent"; analytics zeros |
| `tool_executor.py` | All tools hardcoded (inventory always available, qty 50) |
| `voice_service.py:19` | Static fallback when no Groq key |
| `sentiment_analyzer.get_sentiment_trend` | Zeros |
| Master `whatsapp-monitor` | Placeholder statuses |

---

## 13. Strengths

1. **Resilient 7-provider AI fallback chain** with hallucination guard against real inventory — best part of the system
2. **Order integrity where used:** SELECT...FOR UPDATE, idempotency keys, retry-with-backoff, atomic stock, payment↔order state machine with stock restoration on cancel
3. **Self-learning trainer** with atomic file writes + file lock
4. **Real RAG knowledge base** (Qdrant + in-process fallback, Gemini embeddings, multi-format document parser, per-business docs)
5. **Customer long-term memory** in vector store
6. **Secure webhooks** — HMAC SHA-256, exponential backoff, delivery logs, replay
7. **Good middleware hygiene** — rate limiting, security headers, request IDs
8. **Massive feature surface** — loyalty, coupons, segments, RBAC teams, templates, broadcasts, inventory alerts, exports, bookings, UPI/Razorpay/PhonePe payments, revenue forecasting, audit — all with Hinglish UX
9. **Well-structured backend services layer** (~50 focused service modules)
10. **Polished UX** — onboarding wizard, skeletons, error boundaries, distinctive branding

---

## 14. Recommended Action Plan

### Priority 1 (Fix now — data/security)
1. Fix Order `payment_status` column mismatch
2. Unify chat-parsed orders with OrderManager (atomic stock/payment)
3. Fix `analytics.py` to call real methods (`get_sentiment_summary`, `get_customer_engagement`)
4. Add auth + business-ownership checks to the 11 unauthenticated routers
5. Rotate ALL live API keys (Google, Groq, OpenRouter, Cloudflare, JWT secrets)
6. Fix `X-Tenant-ID` header bypass (validate after JWT, or remove header path)

### Priority 2 (Make multi-tenancy real OR simplify)
7. Decide: implement real per-tenant DB provisioning + master↔backend linkage, or explicitly declare single-tenant
8. Fix master tenant data proxy + `db_path` consistency
9. Implement missing master endpoints (PUT/DELETE tenant, impersonate, AI test, health detail)

### Priority 3 (Make Docker actually work)
10. Create `admin-frontend/Dockerfile`
11. Fix bot↔backend↔bot networking (use env-driven URLs: `BACKEND_URL`, `BOT_URL`)
12. Fix bot auth volume (`auth_state`), add `/health` route, fix healthcheck
13. Pass NEXT_PUBLIC_* as build ARGs

### Priority 4 (Polish)
14. Fix start scripts → use `$PSScriptRoot` (no more E:\AI)
15. Replace in-memory services with DB persistence (feedback, escalations, prompts, queue, loyalty)
16. Wire scheduler to actually send follow-ups / add cleanup for auth_state
17. Remove orphaned `skills/` or wire them up
18. Add error boundaries to admin-frontend
19. Add secret scanning to CI + more tests

---

*Report compiled from full codebase analysis on 5 Aug 2026. All bug claims verified by direct source inspection; line numbers refer to current working tree.*
