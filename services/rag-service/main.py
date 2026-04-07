from fastapi import FastAPI
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag-service")

app = FastAPI()

# Chennai flood knowledge base — pure dictionary lookup
# No torch, no sentence-transformers, no heavy ML
# Simple keyword matching works perfectly for known Chennai zones
KNOWLEDGE_BASE = {
    "velachery": {
        "shelter": "Velachery Government School, Vijayanagar",
        "ndrf_unit": "Chennai Zone 4",
        "historical_depth_cm": 120,
        "risk_level": "critical",
        "evacuation_route": "100 Feet Road towards Taramani"
    },
    "tambaram": {
        "shelter": "Tambaram Municipality Office",
        "ndrf_unit": "Chengalpattu Zone",
        "historical_depth_cm": 80,
        "risk_level": "high",
        "evacuation_route": "GST Road north towards Chrompet"
    },
    "adyar": {
        "shelter": "Adyar Cancer Institute Grounds",
        "ndrf_unit": "Chennai Zone 3",
        "historical_depth_cm": 100,
        "risk_level": "critical",
        "evacuation_route": "LB Road towards Thiruvanmiyur"
    },
    "saidapet": {
        "shelter": "Saidapet Bus Terminus",
        "ndrf_unit": "Chennai Zone 3",
        "historical_depth_cm": 150,
        "risk_level": "critical",
        "evacuation_route": "Mount Road north towards Chennai Central"
    },
    "mudichur": {
        "shelter": "Mudichur Panchayat Office",
        "ndrf_unit": "Chengalpattu Zone",
        "historical_depth_cm": 90,
        "risk_level": "high",
        "evacuation_route": "Old Mahabalipuram Road north"
    },
    "porur": {
        "shelter": "Porur Government Hospital",
        "ndrf_unit": "Chennai Zone 2",
        "historical_depth_cm": 60,
        "risk_level": "high",
        "evacuation_route": "Mount Poonamallee Road towards Koyambedu"
    },
    "perambur": {
        "shelter": "Perambur Railway Quarters Community Hall",
        "ndrf_unit": "Chennai Zone 1",
        "historical_depth_cm": 55,
        "risk_level": "medium",
        "evacuation_route": "Perambur Barracks Road towards Basin Bridge"
    },
    "t nagar": {
        "shelter": "T Nagar Bus Terminus",
        "ndrf_unit": "Chennai Zone 3",
        "historical_depth_cm": 45,
        "risk_level": "medium",
        "evacuation_route": "Panagal Park area elevated zone"
    },
    "anna nagar": {
        "shelter": "Anna Nagar Tower Park",
        "ndrf_unit": "Chennai Zone 2",
        "historical_depth_cm": 20,
        "risk_level": "low",
        "evacuation_route": "Generally safe — can receive evacuees"
    },
    "chrompet": {
        "shelter": "Chrompet Government School",
        "ndrf_unit": "Chengalpattu Zone",
        "historical_depth_cm": 70,
        "risk_level": "high",
        "evacuation_route": "GST Road towards St Thomas Mount"
    },
    "chembarambakkam": {
        "shelter": "Chembarambakkam Reservoir Alert Zone",
        "ndrf_unit": "Chennai Zone 2",
        "historical_depth_cm": 0,
        "risk_level": "critical",
        "evacuation_route": "Downstream zones: Adyar, Saidapet, Valasaravakkam — evacuate immediately"
    }
}

DEFAULT_RESPONSE = {
    "shelter": "Nearest government school or elevated building",
    "ndrf_unit": "Chennai NDRF Control Room: 044-28447373",
    "historical_depth_cm": 0,
    "risk_level": "unknown",
    "evacuation_route": "Move to nearest elevated area"
}

def find_zone(location: str) -> dict:
    """Keyword match location string against knowledge base."""
    location_lower = location.lower().strip()
    
    # Direct match first
    if location_lower in KNOWLEDGE_BASE:
        return KNOWLEDGE_BASE[location_lower]
    
    # Partial match — check if any key is contained in the location string
    for zone_key, zone_data in KNOWLEDGE_BASE.items():
        if zone_key in location_lower or location_lower in zone_key:
            return zone_data
    
    return DEFAULT_RESPONSE


@app.get("/health")
def health():
    return {"status": "healthy", "service": "rag-service", "zones_loaded": len(KNOWLEDGE_BASE)}


@app.post("/enrich")
def enrich_alert(payload: dict):
    location = payload.get("location", "")
    depth = payload.get("depth_cm", 0)

    if not location:
        logger.warning("No location in payload — returning defaults")
        zone_data = DEFAULT_RESPONSE
    else:
        zone_data = find_zone(location)
        logger.info(f"RAG lookup for '{location}' → shelter: {zone_data['shelter']}")

    payload["rag_shelter"] = zone_data["shelter"]
    payload["rag_ndrf_unit"] = zone_data["ndrf_unit"]
    payload["rag_historical_depth"] = zone_data["historical_depth_cm"]
    payload["rag_risk_level"] = zone_data["risk_level"]
    payload["rag_evacuation_route"] = zone_data["evacuation_route"]
    payload["rag_enriched"] = True

    return payload