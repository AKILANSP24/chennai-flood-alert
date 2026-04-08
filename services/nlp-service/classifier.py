import logging
from transformers import pipeline

logger = logging.getLogger(__name__)

try:
    classifier_pipeline = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1
    )
    logger.info("BART classifier loaded successfully")
except Exception as e:
    logger.warning(f"BART load failed, bypass mode: {e}")
    classifier_pipeline = None

def is_flood_related(text: str) -> bool:
    if not text:
        return False
    if not classifier_pipeline:
        return True
    try:
        result = classifier_pipeline(
            text,
            ["flood emergency or heavy rain", "casual conversation"]
        )
        score = dict(zip(result['labels'], result['scores']))
        return score.get("flood emergency or heavy rain", 0) > 0.5
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return True