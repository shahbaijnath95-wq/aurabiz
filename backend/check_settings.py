import sqlite3, json
c = sqlite3.connect(r'E:\AI\backend\ai_agent.db')
c.row_factory = sqlite3.Row
r = c.execute("SELECT * FROM settings WHERE business_id='c5ac0190-cf9e-46e6-a7a9-7d86d15fcba9'").fetchall()
print(f"Settings rows: {len(r)}")
for row in r:
    for k in row.keys():
        print(f"  {k}: {str(row[k])[:100]}")
c.close()
