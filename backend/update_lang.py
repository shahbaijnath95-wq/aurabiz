import sqlite3

conn = sqlite3.connect("ai_agent.db")
cur = conn.cursor()

# Add preferred_language column
try:
    cur.execute("ALTER TABLE businesses ADD COLUMN preferred_language VARCHAR(10) DEFAULT 'mr'")
    conn.commit()
    print("Added preferred_language column")
except Exception as e:
    print(f"Column may already exist: {e}")

# Set Priya's business to Marathi
cur.execute("UPDATE businesses SET preferred_language = 'mr'")
conn.commit()
print(f"Updated {cur.rowcount} business(es) to mr")

# Verify
cur.execute("SELECT id, name, preferred_language FROM businesses")
for row in cur.fetchall():
    print(f"  {row[1]} -> {row[2]}")

conn.close()
