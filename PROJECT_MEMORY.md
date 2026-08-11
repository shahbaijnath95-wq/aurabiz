# AI WhatsApp Business Assistant — Project Memory

> Complete project documentation — kya bana hai, kaise kaam karta hai, kya baaki hai.

---

## 🎯 Project Overview

**Kya hai?** — AI-powered WhatsApp Business Assistant jo small Indian businesses (kirana, salons, restaurants, repair shops) ko automatic WhatsApp replies, inventory management, orders, bookings, payments, aur analytics provide karta hai.

**Target Users** — Small Indian businesses with near-zero technical skill. 100% Hinglish responses (Hindi words in English script).

**Cost** — 100% FREE. WhatsApp via Baileys (no Meta API cost), AI via OpenRouter free models.

---

## 🏗️ Architecture

```
C:\Users\rohit\Desktop\AI\
├── .env                          # Environment variables
├── start-all.ps1                 # One-click server startup (all 5 servers)
├── backend/                      # FastAPI Python backend (port 8000)
│   ├── main.py                   # App entry, CORS, router registration
│   ├── config.py                 # Pydantic BaseSettings
│   ├── database.py               # SQLAlchemy async (SQLite), Redis disabled
│   ├── models.py                 # 22+ DB tables
│   ├── schemas.py                # Pydantic request/response models
│   ├── auth.py                   # JWT authentication
│   ├── routers/                  # 20+ API routers
│   ├── services/                 # Business logic services
│   ├── uploads/                  # Uploaded images storage
│   ├── data/                     # Settings JSON storage
│   └── ai_agent.db               # SQLite database
├── frontend/                     # Next.js 16 frontend (port 3001)
│   ├── src/app/                  # Pages (20+)
│   ├── src/components/           # Reusable components
│   └── src/lib/                  # API client, auth, toast, websocket
└── whatsapp-bot/                 # Node.js Baileys bot (port 8001)
    ├── bot.js                    # WhatsApp bot logic
    ├── bot_config.json           # Bot settings (business hours, welcome msg)
    └── sessions.json             # Persistent WhatsApp sessions
```

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, FastAPI, SQLAlchemy async, SQLite (aiosqlite) |
| Frontend | Next.js 16 (Turbopack), React, Tailwind CSS |
| WhatsApp | Baileys (WhatsApp Web protocol) — FREE |
| AI | OpenRouter (MiMo V2.5 Free, Nemotron 3 Ultra Free) — FREE |
| PDF | fpdf2 for invoice generation |
| Cache | Redis disabled (optional) |
| Auth | JWT tokens, OAuth2PasswordRequestForm |

---

## 📊 Database Tables (22+)

| Table | Purpose |
|-------|---------|
| `businesses` | Business profiles (name, type, phone, address, logo) |
| `users` | Admin users (email, password, full_name) |
| `customers` | WhatsApp customers (phone_number, name, total_orders, total_spent) |
| `conversations` | Chat conversations (status: open/waiting/closed/escalated) |
| `whatsapp_messages` | All messages (content, direction: inbound/outbound, sender) |
| `products` | Products + Services (item_type, brand, model, warranty, hsn_code, gst_rate, tags, specs, gallery, duration_minutes) |
| `bookings` | Service appointments (service_name, booking_date, booking_time, status) |
| `orders` | Customer orders (product_name, quantity, delivery_type, delivery_address, status tracking) |
| `payments` | Payment records (amount, method, status) |
| `coupons` | Discount coupons (code, discount_type, discount_value, min_order) |
| `cart_items` | Shopping cart (product_id, quantity) |
| `feedback` | Customer reviews (rating 1-5, comment) |
| `broadcasts` | Broadcast messages (message, target_count, sent_count) |
| `loyalty_points` | Loyalty program |
| `invoices` | Invoice records |
| `integrations` | Third-party integrations |
| `api_keys` | API key management |
| `webhooks` | Webhook subscriptions |
| `templates` | Message templates |
| `scheduled_messages` | Scheduled messages |
| `conversation_contexts` | AI conversation context |
| `audit_logs` | Audit trail |

---

## 🔌 Backend API Endpoints (50+)

### Auth
- `POST /api/v1/auth/register` — New user register
- `POST /api/v1/auth/login` — Login (OAuth2 form)
- `GET /api/v1/auth/me` — Current user

### Chat (WhatsApp AI)
- `POST /chat` — Send message to AI bot
- `GET /chat/conversations/{business_id}` — List conversations
- `GET /chat/messages/{conversation_id}` — Chat messages
- `POST /chat/reply` — Manual admin reply
- `POST /chat/buy` — Buy product
- `POST /chat/book` — Book service
- `GET /chat/order/{order_id}` — Order status
- `GET /chat/qr/{business_id}` — Bot QR code

### Inventory
- `GET /api/v1/inventory/{business_id}` — List products
- `POST /api/v1/inventory` — Add product
- `PUT /api/v1/inventory/{id}` — Update product
- `DELETE /api/v1/inventory/{id}` — Delete product
- `GET /api/v1/inventory/reorder-alerts` — Low stock alerts

### Orders
- `GET /orders/{business_id}` — List orders
- `POST /orders` — Create order
- `PUT /orders/{order_id}` — Update order status
- `GET /orders/{order_id}/invoice` — Download PDF invoice
- `GET /orders/{order_id}/payment-link` — Payment page data

### Bookings
- `GET /api/v1/bookings/{business_id}` — List bookings
- `PUT /api/v1/bookings/{booking_id}/status` — Update status

### Coupons
- `GET /coupons/{business_id}` — List coupons
- `POST /coupons` — Create coupon
- `POST /coupons/validate` — Validate coupon code

### Cart
- `GET /cart/{business_id}/{customer_id}` — Get cart
- `POST /cart` — Add to cart
- `DELETE /cart/{item_id}` — Remove from cart

### Feedback
- `GET /feedback/{business_id}` — List feedback
- `POST /feedback` — Submit feedback
- `GET /feedback/{business_id}/stats` — Feedback stats

### Broadcast
- `POST /broadcast` — Send broadcast message
- `GET /broadcast/{business_id}` — List broadcasts

### Customers
- `GET /api/v1/customers/{business_id}` — List customers

### Analytics
- `GET /api/v1/analytics/{business_id}` — Dashboard analytics
- `GET /api/v1/analytics/{business_id}/trends` — Trends data

### Payments
- `GET /api/v1/payments/{business_id}` — List payments
- `POST /api/v1/payments/generate-qr` — Generate UPI QR

### Admin
- `GET /admin/payments` — Admin payments list
- `POST /admin/payments/{id}/status` — Update payment
- `POST /admin/qr/generate` — Generate QR

### Bot Config
- `GET /bot/config` — Get bot settings
- `PUT /bot/config` — Update bot settings

### Bot Stats
- `GET /bot/stats/{business_id}` — Message stats + recent messages

### Settings
- `GET /settings` — All settings
- `PUT /settings/invoice` — Invoice settings
- `PUT /settings/ai` — AI API settings
- `PUT /settings/payments` — Payment gateway settings
- `PUT /settings/profile` — Business profile

### Uploads
- `POST /upload` — Single image upload (5MB max)
- `POST /upload/multiple` — Multiple images
- `GET /uploads/{filename}` — Serve uploaded image

### Other
- `GET /health` — Health check
- `GET /docs` — Swagger UI
- `WS /ws` — WebSocket for real-time updates

---

## 🖥️ Frontend Pages (22+)

### Public
- `/login` — Login page
- `/register` — Register page
- `/pay` — Customer payment page (UPI QR, pay button)

### Dashboard
- `/dashboard` — Main dashboard with analytics cards, recent activity
- `/dashboard/inventory` — Advanced inventory (Product/Service toggle, brand, model, warranty, HSN, GST, tags, specs, photo upload)

### Analytics
- `/analytics` — Detailed analytics
- `/revenue` — Revenue tracking

### Customers
- `/customer-portal` — Customer management

### Business
- `/admin/orders` — Orders (status filter, update, invoice download)
- `/admin/appointments` — Bookings with stats
- `/admin/coupons` — Coupon CRUD
- `/admin/feedback` — Customer reviews with stats
- `/admin/broadcast` — Send broadcast messages

### WhatsApp
- `/admin/whatsapp` — Bot connect (QR scan, settings, test chat, message logs)
- `/admin/inbox` — Conversation inbox (chat view, manual reply)
- `/templates` — Message templates

### Tools
- `/webhooks` — Webhook management
- `/integrations` — Third-party integrations
- `/audit` — Audit log

### Settings
- `/admin` — Admin panel
- `/admin/settings` — Settings (Invoice, AI API, Payments, Business Profile)

---

## 🤖 AI Bot Flow (WhatsApp)

```
Customer Message → Baileys Bot → FastAPI /chat endpoint
    ↓
Product Search (rapidfuzz fuzzy matching, threshold 70%)
    ↓
AI Intent Detection:
  - Product inquiry → Product info + "Buy karna hai?"
  - Service inquiry → Service info + available slots
  - Booking → Date/time ask → Create booking
  - Order → Quantity → Delivery/Pickup → Address → Confirm order
  - Payment → UPI ID / QR code
  - Order status → Show latest order
  - Coupon → Validate + apply
  - Feedback → Ask rating 1-5
  - Cart → Show/add/remove items
  - Repeat order → "Wahi order karo"
    ↓
Hinglish Response (100% Hindi in English script)
```

### Smart Features:
- **Fuzzy product matching** — "mouse" finds "Logitech Mouse", "laptop repair" finds "Laptop Repair Service"
- **Word-by-word history matching** — "Mujha computer repair karna hai" matches "Laptop Repair"
- **Quantity-only message flow** — "2 piece" after "Mouse buy karna hai" → finds Mouse from history, creates order
- **Brand handling** — "Dell ka mouse" → finds Mouse, "Logitech" (unknown brand) → generic reply
- **Business hours** — Outside hours auto-reply with working hours
- **Typing delay** — Simulates realistic human behavior
- **Session persistence** — `sessions.json` file-backed
- **Conversation history** — Last 10 messages sent to AI for context

---

## 📸 Image Upload

- **Endpoint:** `POST /upload` (single), `POST /upload/multiple` (batch)
- **Storage:** `C:\Users\rohit\Desktop\AI\backend\uploads\` directory
- **Serving:** `GET /uploads/{filename}` (static files)
- **Frontend:** `ImageUpload` component (drag & drop, preview, delete)
- **Limits:** JPG, PNG, WebP, GIF — max 5MB per file

---

## 📄 Invoice PDF

- **Library:** fpdf2
- **Endpoint:** `GET /orders/{order_id}/invoice`
- **Features:**
  - Business name, address, phone, GST number
  - Item table with qty, unit price, amount
  - Subtotal, discount, delivery fee, total
  - Payment status (pending/confirmed/delivered/cancelled)
  - Delivery type (pickup/delivery)
  - Thank you message
- **Download:** Button on orders page per order

---

## ⚙️ Settings System

- **Storage:** `C:\Users\rohit\Desktop\AI\backend\data\business_settings.json`
- **Sections:**
  - **Invoice:** Business name, GST, address, bank details, UPI, terms
  - **AI API:** Provider (OpenRouter/OpenAI/Gemini), API key, model, temperature, system prompt
  - **Payments:** Razorpay, PhonePe, UPI gateway keys
  - **Profile:** Business name, type, phone, email, address, website, logo

---

## 🔑 Important Conventions

### Backend
- **Port:** 8000 (uvicorn)
- **DB:** SQLite at `C:\Users\rohit\Desktop\AI\backend\ai_agent.db`
- **Auth:** JWT in `Authorization: Bearer <token>`
- **Response format:** camelCase JSON (`accessToken`, `fullName`)
- **Business ID:** UUID format, stored in `businesses` table
- **WhatsApp messages:** `direction` = "inbound" / "outbound"
- **Conversations:** `status` = open / waiting / closed / escalated

### Frontend
- **Port:** 3001 (port 3000 occupied)
- **URLs:** All use `127.0.0.1` (not `localhost` — IPv6 issue)
- **Toast API:** `toast("message", "type")` — NOT `toast({ type, message })`
- **Auth context:** `useAuth()` returns `{ businessId, isAuthenticated, user, business }`
- **API client:** `import { inventory, orders, chat } from "@/lib/api"`

### WhatsApp Bot
- **Port:** 8001
- **Config:** `bot_config.json` (business_id, welcome_message, business_hours, auto_reply)
- **Sessions:** `sessions.json` (persistent, per phone number)
- **IST timezone:** All time checks use `Asia/Kolkata`

---

## 🧪 Test Data

### Test User
- **Email:** priya@demo.com
- **Password:** 123456
- **Business:** Priya Beauty Salon
- **Business ID:** `c5ac0190-cf9e-46e6-a7a9-7d86d15fcba9`

### Demo Products (20+ salon services, 5 repair services, 9 products)
- Hair Cut, Hair Color, Facial, Manicure, Pedicure, etc.
- Laptop Repair, Computer Repair, AC Repair, etc.
- Mouse, Keyboard, USB Drive, Pen Drive, etc.

### WhatsApp Bot
- **Phone:** 917567857818
- **Status:** Connected as Rohit Shah

---

## 📝 What's Been Built (Complete List)

### Core Features
- [x] FastAPI backend with async SQLAlchemy
- [x] Next.js frontend with Tailwind CSS
- [x] WhatsApp bot (Baileys) — FREE
- [x] AI integration (OpenRouter free models)
- [x] JWT authentication
- [x] Business hours auto-reply
- [x] Typing delay simulation

### Inventory
- [x] Products + Services (separate types)
- [x] Advanced fields: brand, model, warranty, HSN, GST, tags, specs
- [x] Photo upload (drag & drop)
- [x] Fuzzy search (rapidfuzz)
- [x] Low stock alerts
- [x] Stock management

### Orders & Bookings
- [x] Order creation from chat
- [x] Order status tracking (pending → confirmed → shipped → delivered)
- [x] Invoice PDF generation
- [x] Service bookings with date/time
- [x] Delivery vs pickup
- [x] Address collection

### Payments
- [x] UPI QR code generation
- [x] Payment link generation
- [x] Razorpay integration (optional)
- [x] PhonePe integration (optional)
- [x] Payment confirmation

### Customer Engagement
- [x] Coupon system (percent/flat discount)
- [x] Cart system
- [x] Customer feedback (1-5 rating)
- [x] Broadcast messages
- [x] Repeat orders ("Wahi order karo")
- [x] Order tracking queries

### Admin
- [x] Dashboard analytics
- [x] Conversation inbox
- [x] Manual reply
- [x] Bot settings (business hours, welcome message)
- [x] Test chat
- [x] Message logs
- [x] Settings (Invoice, AI, Payments, Profile)

### Technical
- [x] Image upload + serving
- [x] WebSocket real-time updates
- [x] Rate limiting
- [x] Request logging
- [x] Audit trail
- [x] Webhook management

---

## 🔜 What's Left (Next Steps)

### High Priority
- [ ] Mobile responsive testing (all pages)
- [ ] End-to-end testing (full flow)
- [ ] Production deployment guide

### Medium Priority
- [ ] Email notifications (order confirmation)
- [ ] SMS integration
- [ ] Customer segmentation
- [ ] Advanced analytics (charts, graphs)

### Low Priority
- [ ] Mobile app (React Native)
- [ ] Multi-business support
- [ ] API rate limiting per business
- [ ] White-label solution

---

## 🐛 Known Issues & Fixes

| Issue | Fix |
|-------|-----|
| `localhost` slow on Windows | Use `127.0.0.1` everywhere |
| Groq model defaults to English for English input | Few-shot Hinglish examples in system prompt |
| Business name hallucination by Groq | Fetch from DB in chat.py before AI call |
| Python 3.14 em-dash SyntaxError | Replace `—` with `--` |
| Port 3000 occupied | Frontend on port 3001 |
| `OAuth2PasswordRequestForm` uses `username` | Login sends email as `username` field |
| `Business.business_name` doesn't exist | Use `Business.name` |
| `WhatsAppMessage.timestamp` doesn't exist | Use `created_at` |
| `WhatsAppMessage.conversation_id` doesn't exist | Link by `customer_id` + `business_id` |
| Frontend toast API confusion | Always `toast("message", "type")` |
| Backend camelCase vs frontend snake_case | API handles both cases |
| 3 routers missing `/api/v1` prefix | `chat.py`, `bot_config.py`, `uploads.py` now have `prefix="/api/v1"` |
| Frontend hardcoded URLs missing `/api/v1` | coupons, broadcast, feedback, settings, whatsapp, ImageUpload fixed |
| `bot.js` calling `/chat` after prefix change | Fixed to `/api/v1/chat`, `PYTHON_BACKEND` changed to `127.0.0.1` |
| Chat frontend using raw fetch bypassing auth | Rewritten to use `request()` wrapper |
| E2E test passes 59/59 | All API flows verified working |
| Quantity-only message ("2 piece") not finding product from history | Fixed: `past_msgs[1:]` instead of `past_msgs[:-1]` (past_msgs is in ASC order after reversed()) |
| Pickup/delivery response not saving Order to DB | Fixed: `free_ai.py` STEP 0j now includes Product/Quantity/Total when inventory_context exists |
| Pickup qty always shows 1 | Fixed: `chat.py` extracts last_qty from outbound messages and passes to `get_fallback_reply` |
| Groq invents products not in inventory (Speaker, TV, Tablet) | Hallucination check in `chat.py` — loads ALL product names from DB, checks reply against known hallucination words, falls back to rule-based reply |
| `inventory_context` empty when no products matched | Hallucination check uses separate DB query for ALL product names, not just matched products |
| "Kya naam hai" matches Nail Polish (enamel contains name) | Added "name"/"naam" to inventory stop words |

---

*Last updated: 27 June 2026*
