# 🪟 Tenant Setup Guide — Windows pe Install Karne ka Complete Flow

> Is guide ko follow karke aap naya tenant (business) 5 minute me ready kar sakte ho.

---

## 📋 Prerequisites (Ek Baar Install Karo)

### 1. Python 3.12+ (3.14 recommended)

```powers
# Download: https://www.python.org/downloads/
# Install ke time "Add Python to PATH" zaroor check karo
python --version
```

### 2. Node.js 22+

```powers
# Download: https://nodejs.org/
node --version
npm --version
```

### 3. Git (Optional)

```powers
# Download: https://git-scm.com/
git --version
```

---

## 🚀 Step 1: Project Setup (Ek Baar)

```powers
# E:\AI folder me jao
cd E:\AI

# Backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Master backend dependencies
cd master
pip install -r requirements.txt
cd ..

# Frontend dependencies
cd frontend
npm install
cd ..

# Admin frontend dependencies
cd admin-frontend
npm install
cd ..

# WhatsApp bot dependencies
cd whatsapp-bot
npm install
cd ..
```

---

## 🚀 Step 2: Environment File Check Karo

`.env` file `E:\AI\.env` me honi chahiye (already exists). Isme yeh fields zaroor hon:

```env
JWT_SECRET_KEY=<any-random-string>
GOOGLE_AI_API_KEY=<free-key-from-aistudio.google.com>
OPENROUTER_API_KEY=<free-key-from-openrouter.ai>
GROQ_API_KEY=<free-key-from-console.groq.com>
```

**Free API keys lena ho to:**
- OpenRouter: https://openrouter.ai → Sign up → Create Key (FREE)
- Google AI: https://aistudio.google.com → Get API key (FREE, 1500 req/day)
- Groq: https://console.groq.com → Create key (FREE, 14400 req/day)

---

## 🚀 Step 3: Saare Servers Start Karo

### Tarika 1: One-Click (Recommended)

```powers
cd E:\AI
start.bat
```

Yeh 5 servers start karega:

| Server | Port | URL |
|--------|------|-----|
| Master Backend | 8010 | http://127.0.0.1:8010 |
| Backend (API) | 8000 | http://127.0.0.1:8000 |
| Frontend (Tenant) | 3001 | http://127.0.0.1:3001 |
| Admin Frontend | 3002 | http://127.0.0.1:3002 |
| WhatsApp Bot | 8001 | http://127.0.0.1:8001 |

### Tarika 2: Manual (Alag-alag terminals me)

```powers
# Terminal 1 — Master Backend
cd E:\AI\master
python -m uvicorn main:app --host 0.0.0.0 --port 8010 --reload

# Terminal 2 — Backend
cd E:\AI\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3 — Frontend
cd E:\AI\frontend
npx next dev -p 3001

# Terminal 4 — Admin Frontend
cd E:\AI\admin-frontend
npx next dev -p 3002

# Terminal 5 — WhatsApp Bot
cd E:\AI\whatsapp-bot
node bot.js
```

---

## 🎯 Step 4: Naya Tenant Create Karo

### Tarika A: Admin Panel se (Recommended)

1. Browser me kholo: **http://127.0.0.1:3002**
2. Login karo:
   - **Email:** `admin@platform.com`
   - **Password:** `ChangeMe!SecureAdmin2026`
3. **Tenants** page me jao
4. **Create Tenant** button click karo
5. Yeh fields bharo:
   - Business Name (e.g., "Priya Beauty Salon")
   - Owner Name
   - Owner Email
   - Owner Phone
   - Plan: starter / growth / enterprise
6. **Create** button dabao
7. Tenant ko `http://127.0.0.1:3001/register` ka URL bhejo

### Tarika B: Self-Register (End-User Flow)

1. Tenant browser me khole: **http://127.0.0.1:3001/register**
2. Yeh details bharo:
   - Full Name
   - Email
   - Password
   - Business Name
   - Business Phone
3. **Register** button dabao
4. Backend `businesses` table me entry create karega
5. Login → Dashboard access

---

## 🎯 Step 5: Tenant Onboarding (5 Min Flow)

Tenant register karne ke baad:

### 5.1 WhatsApp Connect Karo

1. Tenant login kare: **http://127.0.0.1:3001/login**
2. Sidebar me **WhatsApp Connect** page kholo
3. **QR Code** scan kare apne WhatsApp se (WhatsApp Web ki tarah)
4. Status: **Connected** dikh jayega

### 5.2 Inventory Add Karo

1. **Inventory** page me jao
2. **Add Product** button
3. Yeh fields bharo:
   - Product Name (e.g., "Hair Cut")
   - Type: Product / Service
   - Price
   - Stock (products ke liye)
   - Brand, Model, HSN, GST (optional)
4. **Save** dabao

### 5.3 Business Profile Update Karo

1. **Settings → Business Profile**
2. Business name, address, phone, logo update karo
3. **Save** dabao

### 5.4 AI Training (Optional)

1. **AI Training** page me jao
2. Apni business ki PDF/DOC/TXT file upload karo (menu, price list, policies)
3. AI isko RAG knowledge base me use karega

### 5.5 Test Message Bhejo

1. Apne WhatsApp se tenant ke business number pe message bhejo
2. AI automatic Hinglish reply karega
3. **Inbox** page me conversation dikh jayegi

---

## 🐳 Docker Deployment (Production)

### Production ke liye (multi-tenant, scale):

```powers
cd E:\AI
docker compose up -d
```

Yeh 7 services start karega:
- PostgreSQL (5432)
- Redis (6379)
- Qdrant (6333)
- Master Backend (8010)
- Backend (8000)
- Frontend (3001)
- Admin Frontend (3002)
- WhatsApp Bot (8001)

### Production overrides:

```powers
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## ⚠️ Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `Port 8000 already in use` | `netstat -ano \| findstr :8000` → PID kill: `taskkill /F /PID <pid>` |
| `Port 3001 already in use` | `netstat -ano \| findstr :3001` → PID kill |
| `ModuleNotFoundError: fastapi` | `cd backend && pip install -r requirements.txt` |
| `Cannot find module 'baileys'` | `cd whatsapp-bot && npm install` |
| `Cannot find module 'next'` | `cd frontend && npm install` |
| `Next.js: port 3000 occupied` | `npx next dev -p 3001` (start.bat already handles) |
| `SQLite: database is locked` | Backend ko single worker me rakho: `--workers 1` |
| `JWT decode error` | `.env` me `JWT_SECRET_KEY` same hona chahiye master+backend me |
| `Admin login fails (401)` | `master/data/master.db` delete karke master restart karo |
| `Tenant DB not created` | `master/data/tenants/` folder exist karna chahiye (config.py auto-creates) |
| `WhatsApp QR nahi aa raha` | Port 8001 check karo, `whatsapp-bot/sessions.json` delete karke retry |
| `localhost slow on Windows` | `127.0.0.1` use karo (IPv6 issue) |
| `Python 3.14 em-dash SyntaxError` | `—` ko `--` se replace karo |
| `OAuth2PasswordRequestForm uses username` | Login me email ko `username` field me bhejo |
| `Frontend toast API confusion` | Hamesha `toast("message", "type")` use karo |
| `Qdrant connection refused` | Docker me `QDRANT_URL=qdrant` hona chahiye, `localhost` nahi |

---

## 🔑 Default Credentials

| Service | URL | Email | Password |
|---------|-----|-------|----------|
| Admin Panel | http://127.0.0.1:3002 | admin@platform.com | ChangeMe!SecureAdmin2026 |
| Backend Docs | http://127.0.0.1:8000/docs | - | - |
| Test Tenant | http://127.0.0.1:3001 | priya@demo.com | 123456 |

---

## 📞 Quick Tenant Onboarding Checklist

Naya tenant aaya — yeh 5 minute me ready:

- [ ] Admin panel (`:3002`) login karo
- [ ] **Create Tenant** → name, email, phone bharo
- [ ] Tenant ko `:3001/register` ka URL bhejo
- [ ] Tenant register karke login kare
- [ ] **WhatsApp Connect** page → QR scan kare
- [ ] **Inventory** me products add kare
- [ ] **Settings → Business Profile** update kare
- [ ] **AI Training** me business info upload kare (optional)
- [ ] Test message bhejo WhatsApp pe → AI reply verify karo

---

## 💰 Tenant Pricing (Charge Karne Ke Liye)

| Plan | Setup Fee | Monthly | Features |
|------|-----------|---------|----------|
| **Starter** | ₹0 | ₹0 | 50 products, 500 msgs/mo |
| **Growth** | ₹999 one-time | ₹999/mo | Unlimited products, 5000 msgs, broadcasts |
| **Enterprise** | ₹2,999 one-time | ₹2,999/mo | White-label, multi-staff, Cloud API |

**Setup fee (ek baar):** Installation + training + 1 week support = ₹999-2,999 charge karo.

---

## 🌐 Public Access (Cloud pe deploy karne ke liye)

### Option A: Ngrok (Quick Testing)

```powers
# Install: https://ngrok.com/
ngrok http 3001  # Frontend public URL
ngrok http 3002  # Admin panel public URL
ngrok http 8000  # Backend API public URL
```

### Option B: Cloudflare Tunnel (Production, FREE)

```powers
# Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
cloudflared tunnel --url http://localhost:3001
```

### Option C: Windows VPS (Hostinger, AWS, DigitalOcean)

1. VPS pe RDP se connect karo
2. Python + Node install karo
3. Project folder copy karo (`scp` ya GitHub se clone)
4. `start.bat` chalao
5. Cloudflare Tunnel se public URL banao

---

## ✅ Verification (Sab Kuch Chal Raha Hai Ya Nahi)

Sab servers start hone ke baad yeh URLs check karo:

| URL | Expected |
|-----|----------|
| http://127.0.0.1:8000/health | `{"status":"healthy"}` |
| http://127.0.0.1:8000/docs | Swagger UI khule |
| http://127.0.0.1:8010/docs | Master Swagger UI khule |
| http://127.0.0.1:3001 | Frontend login page |
| http://127.0.0.1:3002 | Admin login page |
| http://127.0.0.1:8001/status | WhatsApp bot status |

Agar koi URL nahi khul raha, to corresponding server ka terminal check karo — error hoga wahan.

---

## 🆘 Troubleshooting

### Server start nahi ho raha?

```powers
# 1. Port check karo
netstat -ano | findstr :8000
netstat -ano | findstr :8010
netstat -ano | findstr :3001
netstat -ano | findstr :3002
netstat -ano | findstr :8001

# 2. Process kill karo
taskkill /F /PID <pid>

# 3. Server restart karo
cd E:\AI\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Database reset karna ho?

```powers
# Tenant DB delete
del E:\AI\backend\ai_agent.db

# Master DB delete (admin reset)
del E:\AI\master\data\master.db

# Backend restart karo — tables auto-create honge
```

### WhatsApp bot reconnect nahi ho raha?

```powers
# Session delete karke fresh QR scan
del E:\AI\whatsapp-bot\sessions.json
del E:\AI\whatsapp-bot\auth_info /Q
cd E:\AI\whatsapp-bot
node bot.js
```

---

**Last updated:** 25 July 2026
