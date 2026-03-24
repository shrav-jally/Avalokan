import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure process_batch is imported
if "from ai_engine import process_comment" in text:
    text = text.replace("from ai_engine import process_comment", "from ai_engine import process_comment, process_batch")

new_upload_route = '''@app.route("/api/comments/upload", methods=["POST"])
def upload_comments():
    data = request.json
    comments = data.get('comments', [])
    draft_id = data.get('draft_id')
    
    if not comments or not draft_id:
        return jsonify({"error": "Missing comments or draft_id"}), 400
        
    comment_texts = [c.get('text', '') for c in comments]
    
    analyzed_docs = []
    try:
        # 1. Process batch through AI Engine
        ai_results = process_batch(comment_texts)
        
        for idx, res in enumerate(ai_results):
            analyzed_docs.append({
                "comment_id": str(uuid.uuid4()),
                "draft_id": draft_id,
                "text": comment_texts[idx],
                "sentiment": res.get("sentiment", "NEUTRAL").upper(),
                "sentiment_score": res.get("sentiment_score", 0.0),
                "is_toxic": res.get("is_toxic", False),
                "toxicity_score": res.get("toxicity_score", 0.0),
                "summary": res.get("summary", ""),
                "created_at": datetime.now(timezone.utc),
                "processed_at": datetime.now(timezone.utc)
            })
    except Exception as e:
        # 3. Fallback: Save with 'pending' status if AI fails
        print(f"AI Engine Error: {e}")
        for text_val in comment_texts:
            analyzed_docs.append({
                "comment_id": str(uuid.uuid4()),
                "draft_id": draft_id,
                "text": text_val,
                "sentiment": "PENDING",
                "sentiment_score": 0.0,
                "is_toxic": False,
                "summary": "",
                "created_at": datetime.now(timezone.utc),
                "error": str(e)
            })
            
    # 2. Save to MongoDB
    if analyzed_docs:
        comments_col.insert_many(analyzed_docs)
        
    return jsonify({
        "status": "success",
        "processed_count": len(analyzed_docs),
        "message": f"Successfully uploaded {len(analyzed_docs)} comments."
    })

if __name__ == '__main__':'''

text = text.replace("if __name__ == '__main__':", new_upload_route)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated app.py with /api/comments/upload.")
