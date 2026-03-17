import os
import torch
from transformers import pipeline

# Set a local cache directory to avoid redundant downloads
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".model_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

class SentimentAnalyzer:
    def __init__(self):
        # Using the requested model
        self.device = 0 if torch.cuda.is_available() else -1
        self.pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=self.device,
            model_kwargs={"cache_dir": CACHE_DIR}
        )

    def analyze(self, text: str):
        # Truncate to maximum 512 tokens to avoid length errors
        result = self.pipeline(text, truncation=True, max_length=512)[0]
        return result['label'], result['score']

class CommentSummarizer:
    def __init__(self):
        # Using T5-small as requested
        self.device = 0 if torch.cuda.is_available() else -1
        self.pipeline = pipeline(
            "summarization",
            model="t5-small",
            device=self.device,
            model_kwargs={"cache_dir": CACHE_DIR}
        )

    def summarize(self, text: str):
        # T5 expects a task prefix
        input_text = f"summarize: {text}"
        # Setting max_length and min_length; these can be adjusted as needed
        result = self.pipeline(input_text, max_length=50, min_length=10, truncation=True)[0]
        return result['summary_text']

class ToxicityDetector:
    def __init__(self):
        # Using a popular toxicity model
        self.device = 0 if torch.cuda.is_available() else -1
        self.pipeline = pipeline(
            "text-classification",
            model="unitary/toxic-bert",
            device=self.device,
            model_kwargs={"cache_dir": CACHE_DIR}
        )

    def is_toxic(self, text: str):
        result = self.pipeline(text, truncation=True, max_length=512)[0]
        # unitary/toxic-bert typically labels toxic as 'toxic', 'severe_toxic', etc.
        # It's a multilabel model so we check for toxicity in the label.
        is_toxic = result['label'] == 'toxic' and result['score'] > 0.5
        return is_toxic, result['score']

# Global singletons for lazy initialization
_sentiment_analyzer = None
_comment_summarizer = None
_toxicity_detector = None

def _get_analyzers():
    """Lazy-load the models to save memory and avoid importing on boot if not used."""
    global _sentiment_analyzer, _comment_summarizer, _toxicity_detector
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    if _comment_summarizer is None:
        _comment_summarizer = CommentSummarizer()
    if _toxicity_detector is None:
        _toxicity_detector = ToxicityDetector()
    return _sentiment_analyzer, _comment_summarizer, _toxicity_detector

def process_comment(text: str) -> dict:
    """
    Takes raw text and returns a JSON-serializable structured object with sentiment, 
    summary, and toxicity flags.
    """
    # Handle empty/short text robustly
    clean_text = text.strip() if text else ""
    if not clean_text:
        return {
            "text": clean_text,
            "sentiment": "NEUTRAL",
            "sentiment_score": 0.0,
            "summary": "",
            "is_toxic": False,
            "toxicity_score": 0.0,
            "error": "Empty text provided"
        }

    sentiment_analyzer, comment_summarizer, toxicity_detector = _get_analyzers()

    # 1. Toxicity Check
    is_toxic_flag, tox_score = toxicity_detector.is_toxic(clean_text)

    # 2. Sentiment Check
    sent_label, sent_score = sentiment_analyzer.analyze(clean_text)

    # 3. Summarization Check
    # Summarize only if text is longer than roughly 15 words; otherwise, just return text as summary
    if len(clean_text.split()) > 15:
        summary = comment_summarizer.summarize(clean_text)
    else:
        summary = clean_text

    return {
        "text": clean_text,
        "sentiment": sent_label,
        "sentiment_score": float(sent_score),
        "summary": summary,
        "is_toxic": bool(is_toxic_flag),
        "toxicity_score": float(tox_score)
    }
