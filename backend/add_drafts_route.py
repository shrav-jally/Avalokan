import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_route = '''@app.route("/api/drafts", methods=["GET"])
def get_all_drafts():
    # Fetch all drafts from database
    drafts = list(drafts_col.find({}, {"_id": 0}).sort("published_date", -1))
    
    # Format dates as YYYY-MM-DD
    for d in drafts:
        if "published_date" in d and isinstance(d["published_date"], datetime):
            d["uploadDate"] = d["published_date"].strftime("%Y-%m-%d")
            d["startDate"] = d["published_date"].strftime("%Y-%m-%d")
            end_date = d["published_date"] + timedelta(days=30)
            d["endDate"] = end_date.strftime("%Y-%m-%d")
        else:
            d["uploadDate"] = "2026-01-01"
            d["startDate"] = "2026-01-01"
            d["endDate"] = "2026-02-01"
            
        # UI expects "id" not "draft_id" or consistent with draft_id
        d["id"] = d.get("draft_id", "D-UNKNOWN")
        
    return jsonify(drafts)

if __name__ == '__main__':'''

text = text.replace("if __name__ == '__main__':", new_route)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated app.py with /api/drafts.")
