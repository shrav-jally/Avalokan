import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

analytics_routes = '''
@app.route("/api/analytics/global", methods=["GET"])
def get_global_analytics():
    total_comments = comments_col.count_documents({})
    aggr = list(comments_col.aggregate([
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
    ]))
    
    # Calculate percentages for Chart.js/Recharts
    counts = { "POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0 }
    for a in aggr:
        if a["_id"] in counts:
            counts[a["_id"]] = a["count"]
            
    total = sum(counts.values())
    sentiment_data = [
        {"name": "Positive", "value": round((counts["POSITIVE"]/total)*100) if total > 0 else 0},
        {"name": "Neutral", "value": round((counts["NEUTRAL"]/total)*100) if total > 0 else 0},
        {"name": "Negative", "value": round((counts["NEGATIVE"]/total)*100) if total > 0 else 0}
    ]
    
    return jsonify({
        "totalComments": total_comments,
        "sentimentDistribution": sentiment_data
    })

@app.route("/api/analytics/draft/<draft_id>", methods=["GET"])
def get_draft_analytics(draft_id):
    # Sentiment Breakdown
    aggr = list(comments_col.aggregate([
        {"$match": {"draft_id": draft_id}},
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
    ]))
    
    counts = { "POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0 }
    for a in aggr:
        if a["_id"] in counts:
            counts[a["_id"]] = a["count"]
            
    # Word Frequency (Basic)
    all_comments = list(comments_col.find({"draft_id": draft_id}, {"text": 1}))
    word_counts = {}
    stopwords = {"the", "and", "is", "a", "in", "it", "of", "to", "for", "on", "with", "as", "at", "by", "an", "this", "that", "be", "was", "are"}
    
    for c in all_comments:
        words = c.get("text", "").lower().split()
        for w in words:
            clean_w = "".join(filter(str.isalnum, w))
            if clean_w and clean_w not in stopwords and len(clean_w) > 3:
                word_counts[clean_w] = word_counts.get(clean_w, 0) + 1
                
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    word_freq = [{"text": w, "value": c} for w, c in sorted_words]
    
    # Combined Summary
    # In a real app, we might use a separate aggregation or LLM call. 
    # For now, we fetch the 3 most "representative" (longest) summaries.
    summaries = list(comments_col.find({"draft_id": draft_id, "summary": {"$ne": ""}}).sort("sentiment_score", -1).limit(5))
    combined_summary = " ".join([s["summary"] for s in summaries if s.get("summary")])
    
    return jsonify({
        "draft_id": draft_id,
        "sentiment": [
            {"name": "Positive", "value": counts["POSITIVE"]},
            {"name": "Neutral", "value": counts["NEUTRAL"]},
            {"name": "Negative", "value": counts["NEGATIVE"]}
        ],
        "wordCloud": word_freq,
        "combinedSummary": combined_summary or "No summary available for this draft yet."
    })

if __name__ == '__main__':'''

text = text.replace("if __name__ == '__main__':", analytics_routes)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated app.py with real analytics routes.")
