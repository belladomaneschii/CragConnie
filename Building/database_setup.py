import sqlite3

# Connects to (or creates) a file called 'crag_data.db'
conn = sqlite3.connect('crag_data.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crag TEXT,
    temperature REAL,
    humidity REAL,
    timestamp TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crag TEXT,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    comment TEXT,
    timestamp TEXT
)
""")

conn.commit()
