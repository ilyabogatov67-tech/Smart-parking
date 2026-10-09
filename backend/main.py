import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "dbname": os.getenv("DB_NAME", "parking"),
    "user": os.getenv("DB_USER", "parking_user"),
    "password": os.getenv("DB_PASSWORD", "parking_pass")
}

CALC_URL = os.getenv(
    "CALC_URL",
    "http://web-service:5001/calculate"
)


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/sessions", methods=["GET"])
def get_sessions():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, plate, minutes, billed_hours,
                           hourly_rate::float AS hourly_rate,
                           total::float AS total,
                           created_at
                    FROM parking_sessions
                    ORDER BY id DESC
                """)
                rows = cur.fetchall()

        sessions = []
        for row in rows:
            item = dict(row)
            item["created_at"] = item["created_at"].isoformat()
            sessions.append(item)

        return jsonify({"sessions": sessions})

    except psycopg2.Error:
        app.logger.exception("Database error")
        return jsonify({"error": "Database unavailable"}), 503


@app.route("/api/sessions", methods=["POST"])
def create_session():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    plate = data.get("plate")
    minutes = data.get("minutes")

    if not isinstance(plate, str) or not plate.strip():
        return jsonify({"error": "Enter car plate"}), 400

    plate = plate.strip().upper()

    if len(plate) > 20:
        return jsonify({"error": "Plate is too long"}), 400

    if type(minutes) is not int or not 1 <= minutes <= 43200:
        return jsonify({"error": "Invalid parking duration"}), 400

    try:
        response = requests.post(
            CALC_URL,
            json={
                "minutes": minutes,
                "hourly_rate": 100
            },
            timeout=5
        )
        response.raise_for_status()
        result = response.json()

    except (requests.RequestException, ValueError):
        app.logger.exception("Calculation service error")
        return jsonify({"error": "Calculation unavailable"}), 502

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO parking_sessions
                    (plate, minutes, billed_hours, hourly_rate, total)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, plate, minutes, billed_hours,
                              hourly_rate::float AS hourly_rate,
                              total::float AS total, created_at
                """, (
                    plate,
                    minutes,
                    result["billed_hours"],
                    result["hourly_rate"],
                    result["total"]
                ))

                row = dict(cur.fetchone())
                row["created_at"] = row["created_at"].isoformat()

        return jsonify(row), 201

    except psycopg2.Error:
        app.logger.exception("Database error")
        return jsonify({"error": "Database unavailable"}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
