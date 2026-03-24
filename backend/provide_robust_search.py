import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

search_route = '''@app.route("/api/comments/search", methods=["GET"])
def search_comments():
    # 1. Fetch parameters
    draft_id = request.args.get('draft_id')
    policy_id = request.args.get('policy_id') # Accept policy_id as fallback
    sentiment = request.args.get('sentiment')
    stakeholder_type = request.args.get('stakeholder_type')
    clause_ref = request.args.get('clause_ref')
    is_toxic = request.args.get('is_toxic')
    keyword = request.args.get('keyword')
    high_risk = request.args.get('high_risk', 'false').lower() == 'true'
    
    limit = int(request.args.get('limit', 10))
    skip = int(request.args.get('skip', 0))
    
    # 2. Build Query
    query = {}
    
    # Priority: if draft_id provided, use it. If policy_id provided, find its latest draft.
    if draft_id:
        query["draft_id"] = draft_id
    elif policy_id:
        latest = drafts_col.find_one({"policy_id": policy_id}, sort=[("version_number", -1)])
        if latest:
            query["draft_id"] = latest["draft_id"]
        else:
            return jsonify({"results": [], "totalCount": 0}), 200
            
    if sentiment:
        query["sentiment"] = sentiment.upper()
    
    if clause_ref:
        query["clause_ref"] = clause_ref
        
    if is_toxic is not None:
        query["is_toxic"] = is_toxic.lower() == 'true'
        
    if high_risk:
        query["sentiment"] = "NEGATIVE"
        query["is_toxic"] = True
        
    if keyword:
        query["text"] = {"$regex": keyword, "$options": "i"}
        
    # 3. Execute
    total_count = comments_col.count_documents(query)
    results = list(comments_col.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit))
    
    return jsonify({
        "results": results,
        "totalCount": total_count,
        "limit": limit,
        "skip": skip
    })

@app.route("/api/analytics/draft/<draft_id>", methods=["GET"])'''

text = text.replace('@app.route("/api/analytics/draft/<draft_id>", methods=["GET"])', search_route)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated app.py with the robust search and filter endpoint.")
