import logging
from transformers import pipeline

logger = logging.getLogger(__name__)

# Load a zero-shot classifier using an indicative fast model
# We use xlm-roberta cross-lingual model structure for zero-shot text classification, 
# Since a finetuned binary text model isn't strictly defined locally in this workspace,
# we default to a standard zero-shot pipeline mapping to English/Tanglish constructs.

try:
    classifier_pipeline = pipeline("zero-shot-classification", model="vicgalle/xlm-roberta-large-xnli-anli", device=-1) # device -1 is CPU
except Exception as e:
    logger.warning(f"Failed to load XLM-RoBERTa model, falling back to bypass mode: {e}")
    classifier_pipeline = None

def is_flood_related(text: str) -> bool:
    if not text:
        return False
        
    if not classifier_pipeline:
        # Fallback to True if model could not be loaded on constrained CPU environments
        # (Allows Ollama to interpret later instead)
        return True
        
    candidate_labels = ["flood emergency or heavy rain", "casual talk or spam noise"]
    
    try:
        # Interpret semantic context (Zero shot)
        result = classifier_pipeline(text, candidate_labels)
        scores = dict(zip(result['labels'], result['scores']))
        
        # If flood is more probable than noise
        probability = scores.get("flood emergency or heavy rain", 0)
        return probability > 0.5
    except Exception as e:
        logger.error(f"Error classifying text: {e}")
        return True
