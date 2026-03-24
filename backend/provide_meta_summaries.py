import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update imports
if "from database import policies_col, drafts_col, comments_col" in text:
    text = text.replace("from database import policies_col, drafts_col, comments_col", "from database import policies_col, drafts_col, comments_col, draft_analysis_col")
if "from ai_engine import process_comment, process_batch" in text:
    text = text.replace("from ai_engine import process_comment, process_batch", "from ai_engine import process_comment, process_batch, generate_draft_summary")

# 2. Add New Summarization Route
trigger_summary_route = '''@app.route("/api/analysis/summarize-draft/<draft_id>", methods=["POST"])
def trigger_draft_summary(draft_id):
    # Safety Check: comment_count > 10
    comment_count = comments_col.count_documents({"draft_id": draft_id})
    if comment_count < 10:
        return jsonify({
            "error": "Not enough data", 
            "message": f"Draft only has {comment_count} comments. At least 10 comments are required for executive summarization."
        }), 400
        
    try:
        final_summary = generate_draft_summary(draft_id)
        return jsonify({
            "status": "success",
            "draft_id": draft_id,
            "executive_summary": final_summary
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':'''

text = text.replace("if __name__ == '__main__':", trigger_summary_route)

# 3. Update Existing GET /api/analytics/draft Route to include combined_summary and stats
update_analytics_route_logic = '''    # Fetch Hierarchical Executive Summary if it exists
    exec_summary_doc = draft_analysis_col.find_one({"draft_id": actual_draft_id})
    exec_summary = exec_summary_doc.get("combined_summary") if exec_summary_doc else None

    # Combined Summary Fallback (Standard heuristic from earlier task)
    summaries = list(comments_col.find({"draft_id": actual_draft_id, "summary": {"$ne": ""}}).sort("sentiment_score", -1).limit(5))
    heuristic_summary = " ".join([s["summary"] for s in summaries if s.get("summary")])
    
    return jsonify({
        "draft_id": actual_draft_id,
        "sentiment": [
            {"name": "Positive", "value": counts["POSITIVE"]},
            {"name": "Neutral", "value": counts["NEUTRAL"]},
            {"name": "Negative", "value": counts["NEGATIVE"]}
        ],
        "wordCloud": word_clouds,
        "combinedSummary": exec_summary or heuristic_summary or "No summary available for this draft yet.",
        "is_meta_summary": bool(exec_summary),
        "comment_count": counts["POSITIVE"] + counts["NEUTRAL"] + counts["NEGATIVE"]
    })'''

text = re.sub(r"# Combined Summary.*?return jsonify\(\{.*?\}\)", update_analytics_route_logic, text, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated app.py with the dynamic executive summarization trigger.")
