import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

get_draft_analytics_new = '''@app.route("/api/analytics/draft/<draft_id>", methods=["GET"])
def get_draft_analytics(draft_id):
    # Determine search strategy
    # If the draft_id provided is a policy_id, pick the latest draft
    policy = policies_col.find_one({"policy_id": draft_id})
    actual_draft_id = draft_id
    if policy:
        latest_draft = drafts_col.find_one({"policy_id": draft_id}, sort=[("version_number", -1)])
        if latest_draft:
            actual_draft_id = latest_draft["draft_id"]

    # Sentiment Breakdown
    aggr = list(comments_col.aggregate([
        {"$match": {"draft_id": actual_draft_id}},
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
    ]))
    
    counts = { "POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0 }
    for a in aggr:
        if a["_id"] in counts:
            counts[a["_id"]] = a["count"]
            
    # Word Frequency per Sentiment
    stopwords = {"the", "and", "is", "a", "in", "it", "of", "to", "for", "on", "with", "as", "at", "by", "an", "this", "that", "be", "was", "are", "have", "will", "from", "their", "more", "should", "than", "could", "also"}
    
    word_clouds = {}
    for s in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
        comm_list = list(comments_col.find({"draft_id": actual_draft_id, "sentiment": s}, {"text": 1}))
        wc = {}
        for c in comm_list:
            words = c.get("text", "").lower().split()
            for w in words:
                clean_w = "".join(filter(str.isalnum, w))
                if clean_w and clean_w not in stopwords and len(clean_w) > 3:
                    wc[clean_w] = wc.get(clean_w, 0) + 1
        sorted_wc = sorted(wc.items(), key=lambda x: x[1], reverse=True)[:20]
        word_clouds[s.lower()] = [{"text": w, "value": c} for w, c in sorted_wc]

    # Combined Summary
    summaries = list(comments_col.find({"draft_id": actual_draft_id, "summary": {"$ne": ""}}).sort("sentiment_score", -1).limit(5))
    summary_text = " ".join([s["summary"] for s in summaries if s.get("summary")])
    
    return jsonify({
        "draft_id": actual_draft_id,
        "sentiment": [
            {"name": "Positive", "value": counts["POSITIVE"]},
            {"name": "Neutral", "value": counts["NEUTRAL"]},
            {"name": "Negative", "value": counts["NEGATIVE"]}
        ],
        "wordCloud": word_clouds,
        "combinedSummary": summary_text or "No summary available for this draft yet."
    })'''

text = re.sub(r"@app\.route\('/api/analytics/draft/<draft_id>', methods=\['GET'\]\).*?for s in summaries if s\.get\(\"summary\"\)\]\)\n\s+return jsonify\(.*?\}\)", get_draft_analytics_new, text, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated /api/analytics/draft route in app.py with robust draft_id detection and multi-cloud support.")
