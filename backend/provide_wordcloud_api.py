import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

wordcloud_route = '''@app.route("/api/analytics/wordcloud/<draft_id>", methods=["GET"])
def get_wordcloud_data(draft_id):
    # Fallback to latest draft if policy_id is sent
    policy = policies_col.find_one({"policy_id": draft_id})
    actual_draft_id = draft_id
    if policy:
        latest = drafts_col.find_one({"policy_id": draft_id}, sort=[("version_number", -1)])
        if latest: actual_draft_id = latest["draft_id"]

    comments = list(comments_col.find({"draft_id": actual_draft_id}, {"text": 1, "sentiment": 1}))
    word_stats = {} # {word: {pos: 0, neu: 0, neg: 0, total: 0}}
    
    if nlp:
        # Batch process for performance
        batch_text = ". ".join([c.get("text", "") for c in comments[:200]]) # Limit to 200 for speed
        doc = nlp(batch_text)
        
        # We need to map tokens back to sentiment, but for simplicity in a global cloud:
        # We'll re-process individual comments or use the global frequencies.
        # User requested per-word dominant sentiment.
        
        for c in comments:
            txt = c.get("text", "")
            sent = c.get("sentiment", "NEUTRAL").lower()
            doc = nlp(txt)
            for token in doc:
                if (token.pos_ in ["NOUN", "ADJ"]) and not token.is_stop and len(token.text) > 3:
                    word = token.text.lower()
                    if word not in word_stats:
                        word_stats[word] = {"positive": 0, "neutral": 0, "negative": 0, "total": 0}
                    word_stats[word][sent] += 1
                    word_stats[word]["total"] += 1
                    
    # Sort and take top 50
    sorted_words = sorted(word_stats.items(), key=lambda x: x[1]["total"], reverse=True)[:50]
    
    results = []
    for word, stats in sorted_words:
        # Determine dominant sentiment
        dom_sent = "neutral"
        if stats["positive"] > stats["neutral"] and stats["positive"] > stats["negative"]:
            dom_sent = "positive"
        elif stats["negative"] > stats["positive"] and stats["negative"] > stats["neutral"]:
            dom_sent = "negative"
            
        results.append({
            "text": word,
            "value": stats["total"],
            "sentiment": dom_sent
        })
        
    return jsonify(results)

@app.route("/api/analytics/draft/<draft_id>", methods=["GET"])'''

text = text.replace('@app.route("/api/analytics/draft/<draft_id>", methods=["GET"])', wordcloud_route)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated app.py with the specialized interactive wordcloud endpoint.")
