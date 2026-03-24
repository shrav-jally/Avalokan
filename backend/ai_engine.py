import os
import torch
from transformers import pipeline

# Set a local cache directory to avoid redundant downloads
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".model_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

class SentimentAnalyzer:
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        self.pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=self.device,
            model_kwargs={"cache_dir": CACHE_DIR}
        )

    def analyze(self, text: str):
        result = self.pipeline(text, truncation=True, max_length=512)[0]
        # Map binary LABEL_0/LABEL_1 or POSITIVE/NEGATIVE to Pos/Neg/Neu
        # This specific model is binary (POS/NEG), so we map accordingly.
        label = result['label']
        if label.upper() == 'POSITIVE':
            return "Positive", result['score']
        elif label.upper() == 'NEGATIVE':
            return "Negative", result['score']
        return "Neutral", result['score']

class ToxicityDetector:
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        self.pipeline = pipeline(
            "text-classification",
            model="unitary/toxic-bert",
            device=self.device,
            model_kwargs={"cache_dir": CACHE_DIR}
        )

    def detect(self, text: str):
        result = self.pipeline(text, truncation=True, max_length=512)[0]
        # Flag if score > 0.7
        is_toxic = result['score'] > 0.7
        return is_toxic, result['score']

class Summarizer:
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        self.pipeline = pipeline(
            "summarization",
            model="t5-small",
            device=self.device,
            model_kwargs={"cache_dir": CACHE_DIR}
        )

    def summarize(self, text: str):
        if len(text.split()) < 10:
            return text
        result = self.pipeline(f"summarize: {text}", max_length=30, min_length=5, truncation=True)[0]
        return result['summary_text']

class HierarchicalSummarizer:
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        self.pipeline = pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6",
            device=self.device,
            model_kwargs={"cache_dir": CACHE_DIR}
        )

    def summarize_text_block(self, text, max_len=150):
        if not text.strip(): return ""
        if len(text.split()) < 30: return text
        try:
            res = self.pipeline(text, max_length=max_len, min_length=30, truncation=True)[0]
            return res['summary_text']
        except Exception:
            return text[:500]

# Lazy Initialization
_sentiment = None
_toxic = None
_summary = None
_meta_summarizer = None

def _init_models():
    global _sentiment, _toxic, _summary, _meta_summarizer
    if _sentiment is None: _sentiment = SentimentAnalyzer()
    if _toxic is None: _toxic = ToxicityDetector()
    if _summary is None: _summary = Summarizer()
    if _meta_summarizer is None: _meta_summarizer = HierarchicalSummarizer()

def process_batch(comment_texts):
    """Runs AI pipeline in a loop for a batch of texts."""
    _init_models()
    results = []
    for text in comment_texts:
        # Standard cleaning
        text = text.strip()
        if not text: continue
        
        s_label, s_score = _sentiment.analyze(text)
        t_flag, t_score = _toxic.detect(text)
        summary = _summary.summarize(text)
        
        results.append({
            "text": text,
            "sentiment": s_label.upper(),
            "sentiment_score": float(s_score),
            "is_toxic": bool(t_flag),
            "toxicity_score": float(t_score),
            "summary": summary
        })
    return results

def generate_draft_summary(draft_id):
    """
    Consolidates feedback into a hierarchical Meta-Summary.
    """
    from database import comments_col, draft_analysis_col
    from datetime import datetime, timezone
    
    _init_models()
    
    # 1. Fetch AI-generated comment summaries and sentiments
    comments = list(comments_col.find({"draft_id": draft_id}, {"summary": 1, "sentiment": 1}))
    all_summaries = [c.get("summary", "") for c in comments if c.get("summary")]
    
    # Calculate sentiment distribution for caching
    sent_counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
    for c in comments:
        s = c.get("sentiment", "NEUTRAL").upper()
        if s in sent_counts:
            sent_counts[s] += 1
    
    if not all_summaries:
        return "No summary data found for this draft."
        
    # 2. Chunking (Combine into 500-word blocks)
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for s in all_summaries:
        word_count = len(s.split())
        if current_word_count + word_count > 500:
            chunks.append(" ".join(current_chunk))
            current_chunk = [s]
            current_word_count = word_count
        else:
            current_chunk.append(s)
            current_word_count += word_count
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    # 3. Hierarchical Summarization
    intermediate_summaries = []
    for chunk in chunks:
        res = _meta_summarizer.summarize_text_block(chunk, max_len=150)
        intermediate_summaries.append(res)
        
    # Final Meta-Summarization (Target 5 sentences)
    meta_input = " ".join(intermediate_summaries)
    final_executive_summary = _meta_summarizer.summarize_text_block(meta_input, max_len=250)
    
    # 3.5 Generate Keywords using SpaCy against the chunks
    import spacy
    try:
        nlp = spacy.load('en_core_web_sm')
        meta_doc = nlp(meta_input)
        kw_counts = {}
        for token in meta_doc:
            if token.pos_ in ["NOUN", "ADJ"] and not token.is_stop and len(token.text) > 3:
                w = token.text.lower()
                kw_counts[w] = kw_counts.get(w, 0) + 1
        top_keywords = [k for k, v in sorted(kw_counts.items(), key=lambda x: x[1], reverse=True)[:15]]
    except:
        top_keywords = []

    # 4. Save to MongoDB
    analysis_doc = {
        "draft_id": draft_id,
        "combined_summary": final_executive_summary,
        "keywords": top_keywords,
        "sentiment_counts": sent_counts,
        "generated_at": datetime.now(timezone.utc),
        "comment_count": len(comments),
        "chunk_count": len(chunks)
    }
    
    draft_analysis_col.update_one(
        {"draft_id": draft_id},
        {"$set": analysis_doc},
        upsert=True
    )
    
    return final_executive_summary

def generate_clause_summaries(draft_id):
    """
    Groups comments by clause_ref and generates a 1-sentence mini-summary.
    """
    from database import comments_col
    _init_models()
    
    # 1. Fetch comments with a clause reference (map nulls to General Suggestions)
    pipeline = [
        {"$match": {"draft_id": draft_id}},
        {"$group": {
            "_id": {"$ifNull": ["$clause_ref", "General Suggestions"]},
            "comments": {"$push": "$text"},
            "sentiments": {"$push": "$sentiment"}
        }}
    ]
    
    clause_groups = list(comments_col.aggregate(pipeline))
    results = []
    
    for group in clause_groups:
        clause = group["_id"]
        # Use first 3 representative comments for the summary to keep it snappy
        combined_context = ". ".join(group["comments"][:3])
        
        # Calculate dominant sentiment
        s_counts = {}
        for s in group["sentiments"]:
            s_counts[s] = s_counts.get(s, 0) + 1
        dominant_sentiment = max(s_counts, key=s_counts.get) if s_counts else "NEUTRAL"
        
        # Generate 1-sentence mini-summary using the fast summarizer
        summary = _summary.summarize(combined_context)
        
        results.append({
            "clause": clause,
            "summary": summary,
            "sentiment": dominant_sentiment.lower(),
            "count": len(group["comments"])
        })
        
    return sorted(results, key=lambda x: x["count"], reverse=True)

def process_comment(text: str) -> dict:
    """Legacy wrapper for backward compatibility."""
    return process_batch([text])[0]
