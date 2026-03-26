import json
import logging
import requests

logger = logging.getLogger(__name__)

# Docker-compose hostname for the ollama container
OLLAMA_URL = "http://ollama:11434/api/generate"
# Standard weights defined in the deployment strategy
OLLAMA_MODEL = "llama3.2:3b"

SYSTEM_PROMPT = """You parse Chennai flood reports. Extract ONLY:
{"event": "flood|rain|none", "severity": "critical|high|medium|low", "water_depth_cm": <integer_or_null>, "location_desc": "string"}
Return ONLY valid JSON, nothing else!"""

def extract_structured_data(text: str) -> dict:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": text,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "format": "json" # Ollama force JSON mechanism
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        response_text = result.get("response", "{}")
        # Validate that Ollama actually returned valid JSON
        structured_data = json.loads(response_text)
        return structured_data
    except Exception as e:
        logger.error(f"Ollama extraction failed: {e}")
        return {
            "event": "none",
            "severity": "low",
            "water_depth_cm": None,
            "location_desc": ""
        }
