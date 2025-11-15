import sqlite3
import random
from datetime import datetime, timedelta
import random
import math

DB_PATH = "CragConnie\crag_data.db"
CRAG = "The Cave"
CRAG_NAME = "The Cave" 

base_date = datetime(2025, 7, 23, 7, 0)  # July 23, 7:00 AM
times = [base_date + timedelta(hours=i) for i in range(15)]  # Until 9 PM

# Generate varied readings
def generate_readings():
    readings = []
    temp = random.uniform(10, 18)
    humid = random.uniform(70, 90)
    for t in times:
        temp += random.uniform(-0.5, 0.5)
        humid += random.uniform(-1.0, 1.0)
        readings.append((CRAG_NAME, round(temp, 1), round(humid, 1), t.isoformat()))
    return readings

readings = generate_readings()

# Insert into DB
with sqlite3.connect(DB_PATH) as conn:
    c = conn.cursor()
    for r in readings:
        c.execute(
            "INSERT INTO readings (crag, temperature, humidity, timestamp) VALUES (?, ?, ?, ?)",
            r
        )
    conn.commit()
conn.close()
print("🧪 Test data added.")
