import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect("crag_data.db")
cursor = conn.cursor()

# Insert 20 fake readings
for i in range(20):
    temp = round(random.uniform(10, 35), 1)
    humidity = round(random.uniform(30, 90), 1)
    time = datetime.now() - timedelta(minutes=i*15)
    cursor.execute("INSERT INTO readings (crag, temperature, humidity, timestamp) VALUES (?, ?, ?, ?)",
                   ("Little Babylon", temp, humidity, time))

# Insert 10 random ratings
for i in range(10):
    rating = random.randint(1, 5)
    time = datetime.now() - timedelta(hours=i)
    cursor.execute("INSERT INTO ratings (crag, rating, timestamp) VALUES (?, ?, ?)",
                   ("Little Babylon", rating, time))

conn.commit()
conn.close()
print("🧪 Test data added.")
