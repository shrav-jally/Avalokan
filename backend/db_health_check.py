import os
from database import policies_col, drafts_col, comments_col

def check_health():
    p_count = policies_col.count_documents({})
    d_count = drafts_col.count_documents({})
    c_count = comments_col.count_documents({})
    analyzed_count = comments_col.count_documents({"sentiment": {"$ne": None}})
    
    print("--- 🏥 Database Health Summary ---")
    print(f"Total Policies in Atlas: {p_count}")
    print(f"Total Drafts: {d_count}")
    print(f"Total Comments: {c_count}")
    print(f"Comments with AI Analysis: {analyzed_count} ({(analyzed_count/c_count)*100:.1f}%)" if c_count > 0 else "No comments found.")
    
    # Check for sentiment distribution in P-2026-002
    target_policy = "P-2026-002"
    p_drafts = list(drafts_col.find({"policy_id": target_policy}))
    p_draft_ids = [d["draft_id"] for d in p_drafts]
    p_comments_count = comments_col.count_documents({"draft_id": {"$in": p_draft_ids}})
    
    print(f"\n--- 📈 Targeted Integrity: Digital Competition Bill ({target_policy}) ---")
    print(f"Versions Found: {len(p_draft_ids)}")
    print(f"Comments Associated: {p_comments_count}")
    if p_comments_count > 0:
        pos = comments_col.count_documents({"draft_id": {"$in": p_draft_ids}, "sentiment": "POSITIVE"})
        neu = comments_col.count_documents({"draft_id": {"$in": p_draft_ids}, "sentiment": "NEUTRAL"})
        neg = comments_col.count_documents({"draft_id": {"$in": p_draft_ids}, "sentiment": "NEGATIVE"})
        print(f"Sentiment Spread: Pos: {pos}, Neu: {neu}, Neg: {neg}")
    else:
        print("ALERT: No comments found for this policy in Atlas.")

if __name__ == "__main__":
    check_health()
