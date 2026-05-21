import sqlite3

conn = sqlite3.connect("mulex.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS fraud_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account TEXT,
    amount REAL,
    risk TEXT,
    prediction TEXT
)
""")

conn.commit()
