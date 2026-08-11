# Multi-Tenant Architecture + Super Admin Panel

## Overview
Separate database per tenant + standalone React admin dashboard for full platform control.

---

## 1. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SUPER ADMIN REACT APP                     │
│                  (localhost:3002 or admin.domain.com)        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │Dashboard │ │Tenants   │ │Analytics │ │Billing/Plans │   │
│  │          │ │Management│ │          │ │              │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ API calls
┌───────────────────────────▼─────────────────────────────────┐
│              MASTER BACKEND (port 8010)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Master Database (PostgreSQL/SQLite)                  │   │
│  │  - tenants registry                                   │   │
│  │  - admin users                                        │   │
│  │  - platform analytics                                 │   │
│  │  - billing/subscriptions                              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Tenant Router → routes to correct tenant DB          │   │
│  │  DB Pool: {                                           │   │
│  │    "tenant_abc": sqlite:///./tenants/abc.db,          │   │
│  │    "tenant_def": sqlite:///./tenants/def.db,          │   │
│  │  }                                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────┬──────────────────────────────┬────────────────────┘
           │                              │
    ┌──────▼──────┐              ┌────────▼────────┐
    │ Tenant A DB │              │  Tenant B DB    │
    │ (abc.db)    │              │  (def.db)       │
    │ Priya Salon │              │  Kirana Shop    │
    └─────────────┘              └─────────────────┘
```

---

## 2. Master Database Schema

```sql
-- MASTER DB (platform-level data)

-- Tenant Registry
CREATE TABLE tenants (
    id TEXT PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,           -- URL-friendly: "priya-beauty-salon"
    name TEXT NOT NULL,                   -- Business name
    owner_name TEXT,
    owner_email TEXT UNIQUE NOT NULL,
    owner_phone TEXT,
    db_path TEXT NOT NULL,               -- "./tenants/{id}.db"
    status TEXT DEFAULT 'active',        -- active | suspended | deleted | trial
    plan TEXT DEFAULT 'starter',         -- starter | growth | enterprise
    trial_ends_at TIMESTAMP,
    subscription_id TEXT,                -- Stripe/Razorpay subscription ID
    max_products INTEGER DEFAULT 100,
    max_messages_per_month INTEGER DEFAULT 1000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    suspended_at TIMESTAMP,
    suspend_reason TEXT
);

-- Admin Users (super admin panel login)
CREATE TABLE admin_users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'admin',           -- super_admin | admin | viewer
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Platform Analytics (daily aggregates)
CREATE TABLE platform_stats (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,                  -- "2026-07-01"
    total_tenants INTEGER DEFAULT 0,
    active_tenants INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    total_revenue REAL DEFAULT 0.0,
    new_signups INTEGER DEFAULT 0,
    churned INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Billing & Invoices
CREATE TABLE platform_invoices (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'INR',
    status TEXT DEFAULT 'pending',       -- pending | paid | failed | overdue
    plan TEXT NOT NULL,
    billing_period TEXT,                 -- "2026-07" 
    payment_method TEXT,
    payment_id TEXT,                     -- Stripe/Razorpay payment ID
    invoice_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP
);

-- Audit Log (super admin actions)
CREATE TABLE admin_audit_log (
    id TEXT PRIMARY KEY,
    admin_user_id TEXT,
    action TEXT NOT NULL,                -- tenant.create, tenant.suspend, etc.
    target_tenant_id TEXT,
    details TEXT,                        -- JSON blob
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feature Flags
CREATE TABLE feature_flags (
    id TEXT PRIMARY KEY,
    flag_name TEXT UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    description TEXT,
    target_tenant_ids TEXT,              -- JSON array, null = all tenants
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Tenant DB Schema (per-tenant)

Same as current schema, but:
- Each tenant gets own `.db` file
- No `business_id` column needed (each DB is already isolated)
- Add `tenant_id` column for cross-reference

```
tenants/
  ├── priya-beauty-salon/
  │   └── database.db
  ├── kirana-shop/
  │   └── database.db
  └── tech-repair/
      └── database.db
```

---

## 4. Master Backend API (port 8010)

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/login` | Super admin login |
| POST | `/admin/logout` | Logout |
| GET | `/admin/me` | Current admin profile |

### Tenant Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/tenants` | List all tenants (with filters) |
| POST | `/admin/tenants` | Create new tenant |
| GET | `/admin/tenants/:id` | Get tenant details |
| PUT | `/admin/tenants/:id` | Update tenant |
| DELETE | `/admin/tenants/:id` | Soft delete tenant |
| POST | `/admin/tenants/:id/suspend` | Suspend tenant |
| POST | `/admin/tenants/:id/reactivate` | Reactivate tenant |
| POST | `/admin/tenants/:id/impersonate` | Login as tenant (view their dashboard) |

### Platform Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/analytics/overview` | Total tenants, messages, revenue |
| GET | `/admin/analytics/daily` | Daily stats (last 30 days) |
| GET | `/admin/analytics/top-tenants` | Top tenants by usage/revenue |
| GET | `/admin/analytics/growth` | Signups, churn, MRR |

### Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/billing/invoices` | All invoices |
| POST | `/admin/billing/invoices` | Create invoice |
| PUT | `/admin/billing/invoices/:id` | Update invoice status |
| GET | `/admin/billing/revenue` | Revenue reports |

### Tenant Data Access (proxy)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/tenants/:id/data/:table` | Read any table from tenant DB |
| GET | `/admin/tenants/:id/customers` | View tenant's customers |
| GET | `/admin/tenants/:id/orders` | View tenant's orders |
| GET | `/admin/tenants/:id/messages` | View tenant's messages |

---

## 5. Super Admin React App Structure

```
admin-app/
├── package.json
├── next.config.js              # port 3002
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout with sidebar
│   │   ├── page.tsx            # Dashboard (overview)
│   │   ├── login/
│   │   │   └── page.tsx        # Admin login
│   │   ├── tenants/
│   │   │   ├── page.tsx        # Tenant list (table)
│   │   │   ├── new/
│   │   │   │   └── page.tsx    # Create tenant form
│   │   │   └── [id]/
│   │   │       ├── page.tsx    # Tenant detail
│   │   │       ├── customers/
│   │   │       ├── orders/
│   │   │       ├── messages/
│   │   │       └── settings/
│   │   ├── analytics/
│   │   │   └── page.tsx        # Platform analytics
│   │   ├── billing/
│   │   │   └── page.tsx        # Billing & invoices
│   │   └── settings/
│   │       └── page.tsx        # Platform settings
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   ├── TenantCard.tsx
│   │   ├── StatsCard.tsx
│   │   ├── RevenueChart.tsx
│   │   ├── TenantTable.tsx
│   │   └── AdminGuard.tsx     # Auth guard
│   ├── lib/
│   │   ├── api.ts             # Master API client
│   │   └── auth.ts            # Admin auth
│   └── types/
│       └── index.ts
```

---

## 6. Implementation Plan (5 Phases)

### Phase 1: Master Database + API (2-3 days)
- [ ] Create master DB schema
- [ ] Create master backend (FastAPI on port 8010)
- [ ] Admin auth (JWT + login)
- [ ] Tenant CRUD API
- [ ] Tenant DB creation/migration

### Phase 2: Tenant Isolation (2-3 days)
- [ ] Refactor current backend to support tenant DB switching
- [ ] TenantMiddleware: extract tenant_id from JWT/header → route to correct DB
- [ ] DB connection pool (lazy load tenant DBs)
- [ ] Migrate current data to tenant-specific DB

### Phase 3: Super Admin React App (3-4 days)
- [ ] Setup Next.js app on port 3002
- [ ] Admin login page
- [ ] Dashboard with platform stats
- [ ] Tenant list + detail pages
- [ ] Tenant impersonation (login as tenant)

### Phase 4: Analytics + Billing (2-3 days)
- [ ] Platform analytics dashboard
- [ ] Revenue charts
- [ ] Invoice management
- [ ] Subscription/plan management

### Phase 5: Production Hardening (2 days)
- [ ] Rate limiting per tenant
- [ ] Usage metering (messages, API calls)
- [ ] Auto-suspend on quota exceeded
- [ ] Backup system for tenant DBs
- [ ] Admin audit logging

---

## 7. Key Files to Create/Modify

### New Files
```
master/
├── main.py                    # FastAPI master app
├── config.py                  # Master config
├── database.py                # Master DB connection
├── models.py                  # Master DB models
├── routers/
│   ├── admin_auth.py          # Admin login/logout
│   ├── admin_tenants.py       # Tenant CRUD
│   ├── admin_analytics.py     # Platform stats
│   └── admin_billing.py       # Billing
├── services/
│   ├── tenant_manager.py      # Create/delete/suspend tenants
│   ├── db_router.py           # Route to correct tenant DB
│   └── analytics.py           # Aggregate platform stats
└── middleware/
    └── admin_auth.py          # Admin JWT middleware

admin-app/                     # Next.js admin dashboard
├── src/app/...
├── src/components/...
└── src/lib/...

Modified Files
├── backend/main.py            # Add tenant middleware
├── backend/database.py        # Support multi-DB
├── backend/config.py          # Add master DB config
└── backend/auth.py            # Add tenant_id to JWT
```

---

## 8. Migration Strategy (Current → Multi-Tenant)

```
Step 1: Create master DB
Step 2: For each business_id in current DB:
        a. Create new tenant DB file
        b. Copy all rows WHERE business_id = X
        c. Register in tenants table
Step 3: Update backend to use tenant routing
Step 4: Test with existing data
Step 5: Deploy
```

---

## 9. Estimated Cost

| Item | Cost |
|------|------|
| PostgreSQL (Supabase free tier) | $0 |
| React admin app (Vercel free) | $0 |
| Master backend (same VPS) | $0 extra |
| Total | $0 (all free tier) |
