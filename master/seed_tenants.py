import sqlite3
import uuid
import re
from datetime import datetime, timezone

master = sqlite3.connect('master/data/master.db')
backend = sqlite3.connect('backend/ai_agent.db')

biz_rows = backend.execute("SELECT id, name, phone_number, preferred_language, user_id FROM businesses").fetchall()
user_rows = backend.execute("SELECT id, email, full_name FROM users").fetchall()
user_map = {r[0]: (r[1], r[2]) for r in user_rows}

count = 0
for biz in biz_rows:
    biz_id, name, phone, lang, user_id = biz
    email, full_name = user_map.get(user_id, (None, None))
    if not email:
        continue

    # Skip if already exists
    existing = master.execute("SELECT id FROM tenants WHERE owner_email = ?", (email,)).fetchone()
    if existing:
        continue

    # Unique slug
    base_slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    slug = base_slug
    suffix = 1
    while master.execute("SELECT id FROM tenants WHERE slug = ?", (slug,)).fetchone():
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    master.execute(
        """INSERT INTO tenants (id, slug, name, owner_name, owner_email, owner_phone, db_path, status, plan, preferred_language, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (biz_id, slug, name, full_name, email, phone, "ai_agent.db", "active", "starter", lang or "hi", datetime.now(timezone.utc).isoformat())
    )
    count += 1

master.commit()
print(f"Seeded {count} new tenants")

tenants = master.execute("SELECT id, name, owner_email, status FROM tenants").fetchall()
print(f"Total tenants: {len(tenants)}")
for t in tenants:
    print(f"  {t[1]} | {t[2]} | {t[3]}")

master.close()
backend.close()
