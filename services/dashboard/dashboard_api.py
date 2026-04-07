"""
Chennai Flood Alert Dashboard API
Serves live alert data from alerts_log.csv + Redis registered count
Deploy alongside your existing docker stack
"""
import os
import csv
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

CSV_PATH = os.getenv("ALERTS_CSV", "/data/alerts_log.csv")
PORT = int(os.getenv("DASHBOARD_PORT", "8081"))

SHELTER_MAP = {
    "velachery": "Velachery Govt School, Vijayanagar",
    "adyar": "Anna University Campus",
    "tambaram": "Railway Welfare Hall, Tambaram",
    "saidapet": "Community Center North",
    "porur": "Porur Lions Club Shelter",
    "neelankari": "Neelankari Govt School",
    "t nagar": "T Nagar Community Hall",
    "anna nagar": "Anna Nagar Tower Park Shelter",
    "perambur": "Perambur Railway Quarters",
    "chrompet": "Chrompet Govt Higher Sec School",
}

NDRF_MAP = {
    "velachery": "Chennai Zone 4", "adyar": "Chennai Zone 3",
    "tambaram": "Chennai South", "saidapet": "Chennai Zone 2",
    "t nagar": "Chennai Zone 1", "anna nagar": "Chennai Zone 1",
    "porur": "Chennai West", "perambur": "Chennai North",
    "chrompet": "Chennai South", "neelankari": "Chennai South",
}

def read_alerts():
    alerts = []
    if not os.path.exists(CSV_PATH):
        return alerts
    try:
        with open(CSV_PATH, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 4:
                    zone = row[1].strip()
                    zone_lower = zone.lower()
                    alerts.append({
                        "timestamp": row[0],
                        "zone": zone,
                        "severity": row[2].strip(),
                        "depth_cm": int(float(row[3])) if row[3].strip() else 0,
                        "report_count": int(row[4]) if len(row) > 4 and row[4].strip() else 1,
                        "shelter": SHELTER_MAP.get(zone_lower, "Nearest government school"),
                        "ndrf": NDRF_MAP.get(zone_lower, "Chennai NDRF"),
                    })
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return list(reversed(alerts))  # newest first

def get_registered_count():
    try:
        import redis
        r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
        return r.scard("registered_numbers")
    except:
        return 0

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress access logs

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/alerts":
            alerts = read_alerts()
            reg = get_registered_count()
            payload = json.dumps({
                "alerts": alerts,
                "registered_count": reg,
                "last_updated": datetime.now().isoformat(),
                "total": len(alerts),
            })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload.encode())

        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')

        elif self.path == "/" or self.path == "/dashboard":
            # Serve the dashboard HTML
            html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
            if os.path.exists(html_path):
                with open(html_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    print(f"Dashboard API running on port {PORT}")
    print(f"Reading alerts from: {CSV_PATH}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()