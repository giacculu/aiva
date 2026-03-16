# Script per aggiungere colonne mancanti a sofia.db
import sqlite3

conn = sqlite3.connect("data/semantic.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE facts ADD COLUMN priority INTEGER DEFAULT 0")
    print("✅ priority aggiunta")
except:
    print("ℹ️ priority già presente")

try:
    cursor.execute("ALTER TABLE facts ADD COLUMN retention_days INTEGER DEFAULT 365")
    print("✅ retention_days aggiunta")
except:
    print("ℹ️ retention_days già presente")

conn.commit()
conn.close()