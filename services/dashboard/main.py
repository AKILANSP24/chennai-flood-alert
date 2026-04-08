import os
import csv
import json
import urllib.request
import urllib.parse
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse

app = FastAPI()

CSV_PATH = os.getenv("ALERTS_CSV", "/data/alerts_log.csv")

SHELTER_MAP = {
    "velachery": "Velachery Govt School, Vijayanagar",
    "adyar": "Anna University Campus",
    "tambaram": "Railway Welfare Hall, Tambaram",
    "tambaram la": "Railway Welfare Hall, Tambaram",
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
    "tambaram": "Chennai South", "tambaram la": "Chennai South",
    "saidapet": "Chennai Zone 2", "t nagar": "Chennai Zone 1",
    "anna nagar": "Chennai Zone 1", "porur": "Chennai West",
    "perambur": "Chennai North", "chrompet": "Chennai South",
    "neelankari": "Chennai South",
}

def read_alerts():
    alerts = []
    if not os.path.exists(CSV_PATH):
        return alerts
    try:
        with open(CSV_PATH, "r") as f:
            for row in csv.reader(f):
                if len(row) >= 4:
                    zone = row[1].strip()
                    alerts.append({
                        "timestamp": row[0],
                        "zone": zone,
                        "severity": row[2].strip(),
                        "depth_cm": int(float(row[3])) if row[3].strip() else 0,
                        "report_count": int(row[4]) if len(row) > 4 and row[4].strip() else 1,
                        "shelter": SHELTER_MAP.get(zone.lower(), "Nearest government school"),
                        "ndrf": NDRF_MAP.get(zone.lower(), "Chennai NDRF"),
                    })
    except Exception as e:
        print(f"CSV read error: {e}")
    return list(reversed(alerts))

def get_registered_count():
    try:
        import redis
        r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
        return r.scard("registered_numbers")
    except:
        return 0

@app.get("/", response_class=HTMLResponse)
def root():
    html_path = "/app/dashboard.html"
    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            return f.read()
    return "<h1>dashboard.html not found in /app/</h1>"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/alerts")
def get_alerts():
    alerts = read_alerts()
    return {
        "alerts": alerts,
        "registered_count": get_registered_count(),
        "last_updated": datetime.now().isoformat(),
        "total": len(alerts),
    }

@app.post("/api/emergency")
def send_emergency(request: dict):
    zone = request.get("zone", "All Zones")
    severity = request.get("severity", "critical")
    message = request.get("message", "Flood alert issued.")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not channel:
        return {"status": "error", "message": "Telegram not configured in .env"}
    alert_text = (
        f"🚨 DASHBOARD ALERT: {severity.upper()} 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 Zone: {zone}\n"
        f"⚠️ {message}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 Issued from Command Dashboard"
    )
    try:
        params = urllib.parse.urlencode({"chat_id": channel, "text": alert_text})
        url = f"https://api.telegram.org/bot{token}/sendMessage?{params}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            result = json.loads(resp.read())
            return {"status": "sent", "ok": result.get("ok")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/report/download")
def download_report():
    import subprocess
    pdf_path = "/data/reports/chennai_flood_report.pdf"
    # Regenerate fresh report
    try:
        subprocess.run(
            ["Rscript", "/r-analysis/flood_report.R"],
            timeout=120, capture_output=True
        )
    except Exception:
        pass
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="Chennai_Flood_Report.pdf"
        )
    return {"error": "Report not generated yet"}