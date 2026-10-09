from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math


class ParkingService(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self.send_json({"status": "ok"})
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path != "/calculate":
            self.send_json({"error": "Not found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))

            minutes = data["minutes"]
            rate = data.get("hourly_rate", 100)

            if (type(minutes) not in (int, float)
                    or type(rate) not in (int, float)
                    or not math.isfinite(minutes)
                    or not math.isfinite(rate)
                    or minutes < 0 or rate < 0):
                raise ValueError("Invalid parking values")

            hours = math.ceil(minutes / 60)
            total = round(hours * rate, 2)

            self.send_json({
                "minutes": minutes,
                "billed_hours": hours,
                "hourly_rate": rate,
                "total": total,
                "currency": "RUB"
            })

        except (ValueError, KeyError, TypeError, OverflowError):
            self.send_json({"error": "Invalid request"}, 400)


server = HTTPServer(("0.0.0.0", 5001), ParkingService)
print("Parking calculation service started", flush=True)
server.serve_forever()
