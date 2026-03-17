import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

detailed_metrics_new = '''@app.route('/api/dashboard/detailed-metrics', methods=['GET'])
def get_detailed_metrics():
    # Fetch real drafts and aggregate their sentiment counts
    pipeline = [
        {"$group": {
            "_id": "$draft_id",
            "comments": {"$sum": 1},
            "pos": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "POSITIVE"]}, 1, 0 ] } },
            "neu": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "NEUTRAL"]}, 1, 0 ] } },
            "neg": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "NEGATIVE"]}, 1, 0 ] } }
        }},
        {"$lookup": {
            "from": "drafts",
            "localField": "_id",
            "foreignField": "draft_id",
            "as": "draft_info"
        }},
        { "$unwind": { "path": "$draft_info", "preserveNullAndEmptyArrays": True } },
        { "$limit": 3 }
    ]
    aggr = list(comments_col.aggregate(pipeline))
    results = []
    for doc in aggr:
        info = doc.get("draft_info", {})
        results.append({
            "id": doc["_id"],
            "title": info.get("title", doc["_id"]),
            "comments": doc["comments"],
            "sentiment": {
                "pos": doc["pos"],
                "neu": doc["neu"],
                "neg": doc["neg"]
            }
        })
    return jsonify(results)'''

text = re.sub(r"@app\.route\('/api/dashboard/detailed-metrics', methods=\['GET'\]\).*?return jsonify\(drafts\)", detailed_metrics_new, text, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated /api/dashboard/detailed-metrics in app.py.")
