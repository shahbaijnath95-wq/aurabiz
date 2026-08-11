"""Add advanced fields to products table."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "ai_agent.db")

NEW_COLUMNS = [
    ("brand", "VARCHAR(150)"),
    ("model", "VARCHAR(150)"),
    ("warranty", "VARCHAR(100)"),
    ("hsn_code", "VARCHAR(20)"),
    ("gst_rate", "REAL DEFAULT 0.0"),
    ("tags", "TEXT DEFAULT '[]'"),
    ("specs", "TEXT DEFAULT '{}'"),
    ("gallery", "TEXT DEFAULT '[]'"),
]

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(products)")
    existing = {row[1] for row in cursor.fetchall()}
    
    for col_name, col_type in NEW_COLUMNS:
        if col_name not in existing:
            try:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")
                print(f"  + Added: {col_name}")
            except Exception as e:
                print(f"  ! {col_name}: {e}")
        else:
            print(f"  - {col_name}: already exists")
    
    conn.commit()
    conn.close()
    print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
