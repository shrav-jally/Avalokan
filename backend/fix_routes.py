import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

metrics = '''@app.route("/api/dashboard/metrics", methods=["GET"])
def get_metrics():
    total_drafts = drafts_col.count_documents({})
    total_comments = comments_col.count_documents({})
    active_consultations = drafts_col.count_documents({"status": "open"})
    
    aggr = list(comments_col.aggregate([{"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}]))
    
    pos = 0; neu = 0; neg = 0
    for a in aggr:
        if a.get("_id") == "POSITIVE": pos = a["count"]
        elif a.get("_id") == "NEUTRAL": neu = a["count"]
        elif a.get("_id") == "NEGATIVE": neg = a["count"]
        
    total_sent = pos + neu + neg
    if total_sent > 0:
        pos_pct = round((pos / total_sent) * 100)
        neu_pct = round((neu / total_sent) * 100)
        neg_pct = round((neg / total_sent) * 100)
    else: pos_pct = neu_pct = neg_pct = 0
    
    data = {
        "totalDrafts": total_drafts,
        "totalComments": total_comments,
        "activeConsultations": active_consultations,
        "sentimentDistribution": {"positive": pos_pct, "neutral": neu_pct, "negative": neg_pct}
    }
    return jsonify(data)'''

text = re.sub(r"@app\.route\('/api/dashboard/metrics', methods=\['GET'\]\).*?def get_metrics\(\):.*?return jsonify\(data\)", metrics, text, flags=re.DOTALL)

volume = '''@app.route("/api/global/draft-comment-volume", methods=["GET"])
def get_global_draft_comment_volume():
    pipeline = [
        {"$group": {"_id": "$draft_id", "total_comments": {"$sum": 1}, "positive_count": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "POSITIVE"]}, 1, 0 ] } }, "neutral_count": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "NEUTRAL"]}, 1, 0 ] } }, "negative_count": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "NEGATIVE"]}, 1, 0 ] } }}},
        {"$lookup": {"from": "drafts", "localField": "_id", "foreignField": "draft_id", "as": "draft_info"}},
        { "$unwind": { "path": "$draft_info", "preserveNullAndEmptyArrays": True } },
        { "$sort": { "draft_info.published_date": -1, "_id": -1 } }
    ]
    aggr = list(comments_col.aggregate(pipeline))
    data = []
    for idx, doc in enumerate(aggr):
        draft_info = doc.get("draft_info", {})
        data.append({
            "draft_id": doc["_id"],
            "draft_title": draft_info.get("title", doc["_id"]),
            "total_comments": doc["total_comments"],
            "positive_count": doc["positive_count"],
            "neutral_count": doc["neutral_count"],
            "negative_count": doc["negative_count"],
            "release_order": len(aggr) - idx
        })
    return jsonify(data)'''

text = re.sub(r"@app\.route\('/api/global/draft-comment-volume', methods=\['GET'\]\).*?def get_global_draft_comment_volume\(\):.*?return jsonify\(data\)", volume, text, flags=re.DOTALL)

policies = '''@app.route("/api/policies", methods=["GET"])
def get_policies():
    policies = list(policies_col.find({}, {"_id": 0}).sort("created_at", -1))
    data = []
    for p in policies:
        data.append({
            "id": p.get("policy_id"),
            "title": p.get("title"),
            "summary": p.get("summary")
        })
    return jsonify(data)'''

text = re.sub(r"@app\.route\('/api/policies', methods=\['GET'\]\).*?def get_policies\(\):.*?return jsonify\(policies\)", policies, text, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated app.py successfully.')
