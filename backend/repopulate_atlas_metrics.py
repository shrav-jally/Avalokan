from database import drafts_col, comments_col, draft_analysis_col
from datetime import datetime, timezone

def repopulate():
    print("--- 🚀 Repopulating Atlas Cache from Comments ---")
    drafts = list(drafts_col.find({}))
    total_repopulated = 0
    
    for d in drafts:
        draft_id = d.get('draft_id')
        if not draft_id: continue
        
        # Calculate sentiment from the 1600 comments
        aggr = list(comments_col.aggregate([
            {"$match": {"draft_id": draft_id}},
            {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
        ]))
        
        counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
        for a in aggr:
            s = str(a.get("_id", "NEUTRAL")).upper()
            if s in counts:
                counts[s] = a["count"]
                
        # Calculate total
        total = sum(counts.values())
        
        # Upsert into Cache
        draft_analysis_col.update_one(
            {"draft_id": draft_id},
            {"$set": {
                "draft_id": draft_id,
                "sentiment_counts": counts,
                "comment_count": total,
                "combined_summary": "Initial summary. Full analysis pending...",
                "generated_at": datetime.now(timezone.utc),
                "keywords": ["policy", "legal", "draft"] # Default placeholders
            }},
            upsert=True
        )
        total_repopulated += 1
        print(f"📊 Processed {draft_id}: {total} comments")
        
    print(f"--- 🎉 Total Repopulated: {total_repopulated} ---")

if __name__ == "__main__":
    repopulate()
