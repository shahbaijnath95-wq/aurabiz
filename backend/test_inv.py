import sqlite3
c = sqlite3.connect('E:\\AI\\backend\\ai_agent.db')
c.row_factory = sqlite3.Row
rows = c.execute("SELECT id,name,price,stock_quantity,item_type,description,category FROM products WHERE business_id='c5ac0190-cf9e-46e6-a7a9-7d86d15fcba9' AND is_active=1").fetchall()
print('=== ALL INVENTORY ===')
for r in rows:
    print(f'{r["name"]:35s} | Rs {r["price"]:>6} | stock={r["stock_quantity"]:>3} | type={r["item_type"]:8s} | cat={r["category"] or "-"}')
c.close()
