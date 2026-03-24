from database import draft_analysis_col, comments_col
import pymongo

def fast_sync():
    print("--- 🚀 Quick Metric Sync Starting ---")
    drafts = list(draft_analysis_col.find())
    synced = 0
    for d in drafts:
        draft_id = d.get('draft_id')
        if not draft_id: continue
        
        # 1. Recalculate sentiment spread
        aggr = list(comments_col.aggregate([
            {"$match": {"draft_id": draft_id}},
            {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
        ]))
        
        counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
        for a in aggr:
            s = a["_id"].upper() if a["_id"] else "NEUTRAL"
            if s in counts:
                counts[s] = a["count"]
        
        # 2. Recalculate total comments
        total = sum(counts.values())
        
        # 3. Update the analysis document
        draft_analysis_col.update_one(
            {"draft_id": draft_id},
            {"$set": {
                "sentiment_counts": counts,
                "comment_count": total
            }}
        )
        synced += 1
        print(f"✅ Sync complete for {draft_id}: {total} comments")
        
    print(f"--- 🎉 Total Synced: {synced} ---")

if __name__ == "__main__":
    fast_sync()
