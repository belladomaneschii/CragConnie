from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from static.score_cal import calculate_score, IDEAL_TEMP, IDEAL_HUMIDITY, MARGIN
import sqlite3

app = Flask(__name__)
# add decorateds
CORS(app)


@app.route("/")
def home():
    return render_template("index.html")

@app.route('/crag/<name>')
def crag_page(name):
    # Replace hyphens with spaces if you use slugs (optional)
    crag_name = name.replace("-", " ").title()

    if crag_name not in ["The Cave", "Little Babylon"]:
        return render_template("404.html", crag_name=crag_name), 404

    return render_template("crag.html", crag_name=crag_name)

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
    crag = request.args.get("crag")
    if not crag:
        return jsonify({"error": "Missing required query parameter: crag"}), 400
    conn = get_db_connection()
    reading = conn.execute("""
        SELECT * FROM readings
        WHERE crag = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (crag,)).fetchone()
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
    crag = request.args.get("crag")
    if not crag:
        return jsonify({"error": "Missing required query parameter: crag"}), 400

    conn = get_db_connection()

    latest = conn.execute("""
        SELECT temperature, humidity
        FROM readings
        WHERE crag = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (crag,)).fetchone()

    if not latest:
        conn.close()
        return jsonify({"error": "No readings found"}), 404

    temp = latest["temperature"]
    humidity = latest["humidity"]

 
    margin_temp = IDEAL_TEMP * MARGIN
    margin_humidity = IDEAL_HUMIDITY * MARGIN

    nearby_ratings = conn.execute("""
        SELECT rating
        FROM ratings
        JOIN readings ON ratings.timestamp = readings.timestamp
        WHERE readings.crag = ?
          AND ratings.crag = ?
          AND ABS(readings.temperature - ?) <= ?
          AND ABS(readings.humidity - ?) <= ?
    """, (crag, crag, temp, margin_temp, humidity, margin_humidity)).fetchall()

    conn.close()

    if nearby_ratings:
        avg_rating = sum([r["rating"] for r in nearby_ratings]) / len(nearby_ratings)
    else:
        avg_rating = 2.5  

    score = calculate_score(temp, humidity, avg_rating)

    return jsonify({
        "temp": temp,
        "humidity": humidity,
        "avg_rating_used": avg_rating if nearby_ratings else None,
        "matching_ratings": len(nearby_ratings),
        "score": round(score, 1)
    })



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
