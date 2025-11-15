from flask import Flask, current_app, request, jsonify, render_template
import requests
from flask_cors import CORS
from datetime import datetime, timedelta
from collections import defaultdict
from static.score_cal import calculate_score, IDEAL_TEMP, IDEAL_HUMIDITY, MARGIN
import sqlite3
import base64
import struct

CRAG_LOCATIONS = {
    "The Cave": {"lat": -43.5, "lon": 172.6},
    "Little Babylon": {"lat": -43.4, "lon": 172.7},
}

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return render_template("index.html")

@app.route('/crag/<name>')
def crag_page(name):
    crag_name = name.replace("-", " ").title()

    if crag_name not in CRAG_LOCATIONS:
        return render_template("404.html", crag_name=crag_name), 404

    lat = CRAG_LOCATIONS[crag_name]["lat"]
    lon = CRAG_LOCATIONS[crag_name]["lon"]

    return render_template("crag.html", crag_name=crag_name, lat=lat, lon=lon)

# ------------------------
# DATABASE CONNECTION
# ------------------------
def get_db_connection():
    conn = sqlite3.connect('crag_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/db-tables')
def db_tables():
    conn = get_db_connection()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(tables)


# ------------------------
# LORAWAN ENDPOINT (The Things Network Integration)
# ------------------------
@app.route('/lorawan/uplink', methods=['POST'])
def lorawan_uplink():
    """
    Receives uplink messages from The Things Network webhook
    Expected payload format: 4 bytes
    - Bytes 0-1: Temperature (int16, scaled by 100)
    - Bytes 2-3: Humidity (int16, scaled by 100)
    """
    try:
        data = request.get_json()
        
        # Extract device info
        device_id = data.get('end_device_ids', {}).get('device_id', 'unknown')
        
        # Get the base64 encoded payload
        frm_payload = data.get('uplink_message', {}).get('frm_payload', '')
        
        if not frm_payload:
            return jsonify({"error": "No payload received"}), 400
        
        # Decode base64 payload
        raw_bytes = base64.b64decode(frm_payload)
        
        # Unpack the data (assuming 2 bytes temp, 2 bytes humidity)
        if len(raw_bytes) >= 4:
            # Big-endian signed 16-bit integers
            temp_raw = struct.unpack('>h', raw_bytes[0:2])[0]
            humidity_raw = struct.unpack('>h', raw_bytes[2:4])[0]
            
            # Scale back to actual values
            temperature = temp_raw / 100.0
            humidity = humidity_raw / 100.0
            
            # Determine which crag based on device_id (you can customize this)
            # For now, default to "The Cave"
            crag = "The Cave"
            if "babylon" in device_id.lower():
                crag = "Little Babylon"
            
            # Store in database
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO readings (crag, temperature, humidity, timestamp)
                VALUES (?, ?, ?, ?)
            """, (crag, temperature, humidity, timestamp))
            conn.commit()
            conn.close()
            
            print(f"✓ LoRaWAN data received: {crag} - Temp: {temperature}°C, Humidity: {humidity}%")
            
            return jsonify({
                "status": "success",
                "message": "Data stored successfully",
                "device_id": device_id,
                "crag": crag,
                "temperature": temperature,
                "humidity": humidity
            }), 200
        else:
            return jsonify({"error": "Invalid payload length"}), 400
            
    except Exception as e:
        print(f"Error processing LoRaWAN uplink: {str(e)}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500


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
# 2. POST A NEW RATING (Enhanced with wind_surfers and visited_at)
# ------------------------
@app.route('/ratings', methods=['POST'])
def post_rating():
    data = request.get_json()
    crag = data.get("crag", "The Cave")
    rating = int(data.get("rating", 0))
    wind_surfers = int(data.get("wind_surfers", 0))  # 1 if checked, 0 if not
    visited_at = data.get("visited_at")  # ISO format datetime from frontend
    
    # If no visited_at provided, use current time
    if not visited_at:
        visited_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if 1 <= rating <= 5:
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO ratings (crag, rating, wind_surfers, visited_at, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (crag, rating, wind_surfers, visited_at, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return jsonify({"message": "Rating saved successfully"}), 200
    else:
        return jsonify({"error": "Invalid rating (must be 1-5)"}), 400
    
# ------------------------
# 3. GET SCORE
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
# 4. GET ALL RATINGS
# ------------------------
@app.route('/ratings', methods=['GET'])
def get_ratings():
    crag = request.args.get("crag", "The Cave")
    conn = get_db_connection()
    ratings = conn.execute("""
        SELECT rating, wind_surfers, visited_at, timestamp 
        FROM ratings
        WHERE crag = ?
        ORDER BY timestamp DESC
        LIMIT 50
    """, (crag,)).fetchall()
    conn.close()

    return jsonify([dict(r) for r in ratings])

# ------------------------
# 5. MANUAL SENSOR DATA UPDATE (for testing)
# ------------------------
@app.route('/update', methods=['POST'])
def update_data():
    data = request.get_json()
    try:
        temp = float(data.get("temperature"))
        humidity = float(data.get("humidity"))
        crag = data.get("crag", "The Cave")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
# 6. RAINFALL API
# ------------------------
@app.route('/api/rainfall')
def get_daily_rainfall():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({'error': 'Missing coordinates (lat/lon)'}), 400

    url = (
        f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}'
        '&daily=precipitation_sum&timezone=auto'
        '&past_days=7'
        '&forecast_days=0'
    )

    try:
        resp = requests.get(url, timeout=10)
    except requests.RequestException as e:
        # network error / DNS / firewall — surface it
        current_app.logger.exception("Error contacting Open-Meteo")
        return jsonify({'error': f'Failed to fetch from weather API: {str(e)}'}), 502

    try:
        data = resp.json()
    except ValueError:
        current_app.logger.error("Open-Meteo returned non-JSON", extra={'text': resp.text})
        return jsonify({'error': 'Weather API returned non-JSON'}), 502

    # Defensive: ensure keys exist
    if 'daily' not in data or 'time' not in data['daily'] or 'precipitation_sum' not in data['daily']:
        current_app.logger.error("Unexpected weather API response", extra={'resp': data})
        # return the API's response for debugging
        return jsonify({'error': 'Weather API response missing daily precipitation', 'api_response': data}), 502

    dates = data['daily']['time']
    rainfall = data['daily']['precipitation_sum']

    # Ensure same lengths
    if len(dates) != len(rainfall):
        current_app.logger.warning("Dates and rainfall arrays length mismatch", extra={'dates_len': len(dates), 'rain_len': len(rainfall)})
        # zip will handle safely, but we log it
    result = [[date, float(rain)] for date, rain in zip(dates, rainfall)]

    return jsonify(result)

    
# ------------------------
# 7. CONDITIONS CHART DATA
# ------------------------
@app.route('/api/conditions')
def api_conditions():
    crag = request.args.get('crag')
    range_param = request.args.get('range', '12h')

    if not crag:
        return jsonify({"error": "Missing crag parameter"}), 400

    now = datetime.now()
    conn = get_db_connection()

    def parse_timestamp(ts):
        try:
            return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            return datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')

    if range_param == '12h':
        since = now - timedelta(hours=12)

        rows = conn.execute("""
            SELECT timestamp, temperature, humidity
            FROM readings
            WHERE crag = ?
              AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (crag, since.strftime('%Y-%m-%d %H:%M:%S'))).fetchall()

        labels = []
        temperatures = []
        humidities = []
        
        for row in rows:
            dt = parse_timestamp(row['timestamp'])
            labels.append(dt.strftime('%H:%M'))
            temperatures.append(row['temperature'])
            humidities.append(row['humidity'])

        conn.close()

        return jsonify({
            "labels": labels,
            "temperature": temperatures,
            "humidity": humidities
        })

    elif range_param == '7d':
        since = now - timedelta(days=7)

        rows = conn.execute("""
            SELECT timestamp, temperature, humidity
            FROM readings
            WHERE crag = ?
              AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (crag, since.strftime('%Y-%m-%d %H:%M:%S'))).fetchall()

        conn.close()

        daily_data = {}
        for row in rows:
            dt = parse_timestamp(row['timestamp'])
            day = dt.strftime('%Y-%m-%d')
            if day not in daily_data:
                daily_data[day] = {
                    "temp_sum": 0,
                    "humidity_sum": 0,
                    "count": 0
                }
            daily_data[day]["temp_sum"] += row['temperature']
            daily_data[day]["humidity_sum"] += row['humidity']
            daily_data[day]["count"] += 1

        labels = []
        temperatures = []
        humidities = []

        for day in sorted(daily_data.keys()):
            labels.append(day)
            data = daily_data[day]
            temperatures.append(round(data["temp_sum"] / data["count"], 1))
            humidities.append(round(data["humidity_sum"] / data["count"], 1))

        return jsonify({
            "labels": labels,
            "temperature": temperatures,
            "humidity": humidities
        })

    else:
        conn.close()
        return jsonify({"error": "Invalid range parameter, use '12h' or '7d'"}), 400
  
# ------------------------
# MAIN
# ------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)