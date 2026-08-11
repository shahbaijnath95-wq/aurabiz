import sqlite3, uuid, os, datetime

os.makedirs(r'C:\Users\rohit\Desktop\AI\master\data', exist_ok=True)
db = sqlite3.connect(r'C:\Users\rohit\Desktop\AI\master\data\master.db')
c = db.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY, slug TEXT, name TEXT, owner_name TEXT, owner_email TEXT,
    owner_phone TEXT, db_path TEXT, status TEXT, plan TEXT,
    max_products INTEGER DEFAULT 100, max_messages_per_month INTEGER DEFAULT 5000,
    messages_used_this_month INTEGER DEFAULT 0, preferred_language TEXT DEFAULT 'hi',
    created_at TIMESTAMP, updated_at TIMESTAMP)''')

c.execute('''CREATE TABLE IF NOT EXISTS licenses (
    id TEXT PRIMARY KEY, license_key TEXT UNIQUE, tenant_id TEXT, plan TEXT,
    status TEXT, max_activations INTEGER DEFAULT 1, activations_used INTEGER DEFAULT 0,
    owner_name TEXT, owner_email TEXT, owner_phone TEXT, amount_paid REAL,
    ai_tier TEXT DEFAULT 'free', machine_id TEXT, paid_at TIMESTAMP,
    expires_at TIMESTAMP, last_activated_at TIMESTAMP, created_at TIMESTAMP,
    updated_at TIMESTAMP)''')

lic_id = str(uuid.uuid4())
lic_key = 'AURABIZ-TEST-1234-5678-ABCD'
tenant_id = str(uuid.uuid4())
now = datetime.datetime.now(datetime.timezone.utc)

c.execute('INSERT OR IGNORE INTO tenants (id, name, owner_name, owner_email, status, plan, db_path) VALUES (?, ?, ?, ?, ?, ?, ?)',
          (tenant_id, 'Test Business', 'Test User', 'test@example.com', 'active', 'starter', 'test.db'))

c.execute('INSERT OR IGNORE INTO licenses (id, license_key, tenant_id, plan, status, max_activations, owner_name, owner_email, amount_paid, ai_tier, paid_at, expires_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
          (lic_id, lic_key, tenant_id, 'starter', 'issued', 1, 'Test User', 'test@example.com', 999, 'free', now, now + datetime.timedelta(days=30), now))

db.commit()
print(f'License created: {lic_key}')
print(f'Tenant: {tenant_id}')
db.close()
