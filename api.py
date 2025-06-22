from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from static.score_cal import calculate_score
import sqlite3

app = Flask(__name__)
CORS(app)

# ------------------------
# DATABASE CONNECTION
# ------------------------
def get_db_connection():
    conn = sqlite3.connect('crag_data.db')
    conn.row_factory = sqlite3.Row
    return conn

# ------------------------
# 1. GET LATEST READING
# ------------------------
@app.route('/latest', methods=['GET'])
def get_latest():
    conn = get_db_connection()
    reading = conn.execute("""
        SELECT * FROM readings
        WHERE crag = 'The Cave'
        ORDER BY timestamp DESC
        LIMIT 1
    """).fetchone()
    conn.close()

    if reading:
        return jsonify({
            "temp": reading["temperature"],
            "humidity": reading["humidity"],
            "timestamp": reading["timestamp"]
        })
    else:
        return jsonify({"error": "No data"}), 404

# ------------------------
# 2. POST A NEW RATING
# ------------------------
@app.route('/ratings', methods=['POST'])
def post_rating():
    data = request.get_json()
    rating = int(data.get("rating", 0))

    if 1 <= rating <= 5:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO ratings (crag, rating) VALUES (?, ?)",
            ("The Cave", rating)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Rating saved"}), 200
    else:
        return jsonify({"error": "Invalid rating"}), 400
    
# ------------------------
# 2. POST SCORE
# ------------------------
@app.route("/score", methods=["GET"])
def score():
    conn = get_db_connection()
    reading = conn.execute("""
        SELECT temperature, humidity
        FROM readings
        WHERE crag = 'The Cave'
        ORDER BY timestamp DESC
        LIMIT 1
    """).fetchone()
    conn.close()

    if reading:
        temp = reading["temperature"]
        humidity = reading["humidity"]
        score = calculate_score(temp, humidity)
        return jsonify({
            "temp": temp,
            "humidity": humidity,
            "score": score
        })
    else:
        return jsonify({"error": "No readings found"}), 404



# ------------------------
# 3. GET ALL RATINGS
# ------------------------
@app.route('/ratings', methods=['GET'])
def get_ratings():
    conn = get_db_connection()
    ratings = conn.execute("""
        SELECT rating, timestamp FROM ratings
        WHERE crag = 'The Cave'
        ORDER BY timestamp DESC
    """).fetchall()
    conn.close()

    return jsonify([dict(r) for r in ratings])

# ------------------------
# 4. FUTURE: POST SENSOR DATA (Arduino)
# ------------------------
@app.route('/update', methods=['POST'])
def update_data():
    data = request.get_json()
    try:
        temp = float(data.get("temperature"))
        humidity = float(data.get("humidity"))
        crag = data.get("crag", "The Cave")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # ← add this line

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO readings (crag, temperature, humidity, timestamp)
            VALUES (?, ?, ?, ?)
        """, (crag, temp, humidity, timestamp))
        conn.commit()
        conn.close()

        return jsonify({"message": "Data received"}), 200
    except Exception as e:
        return jsonify({"error": f"Invalid data format: {str(e)}"}), 400

# ------------------------
# MAIN
# ------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5001)
