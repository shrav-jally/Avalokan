import os
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

# Database setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/avalokan_db")
client = MongoClient(MONGO_URI)
db = client.get_database("avalokan_db")

policies_col = db.policies
drafts_col = db.drafts
comments_col = db.comments

def run_migration():
    """
    Clears existing mock databases and populates a mock Policy with linked Drafts
    and corresponding Comments, mimicking real data to test the frontend's LinkedPoliciesModal.
    """
    print("Clearing database...")
    policies_col.delete_many({})
    drafts_col.delete_many({})
    comments_col.delete_many({})

    # 1. Create a single root Policy
    policy_id = "POL-PUBLIC-HEALTH-2026"
    policy = {
        "policy_id": policy_id,
        "title": "Public Health Emergency Framework",
        "summary": "Establishing regulatory frameworks for safeguarding communities during national health crises.",
        "created_at": datetime.now(timezone.utc) - timedelta(days=400)
    }
    policies_col.insert_one(policy)
    print(f"Created Policy: {policy_id}")

    # 2. Create versioned Drafts linked to this Policy
    # We will simulate 3 versions of the document (v1.0, v1.2, v2.0)
    mock_drafts = [
        {
            "draft_id": "D-2024-005",
            "policy_id": policy_id,
            "title": "Public Health Bill v1.0",
            "version_number": 1.0,
            "status": "superseded",
            "published_date": datetime.now(timezone.utc) - timedelta(days=360)
        },
        {
            "draft_id": "D-2025-089",
            "policy_id": policy_id,
            "title": "Public Health Bill v1.2",
            "version_number": 1.2,
            "status": "superseded",
            "published_date": datetime.now(timezone.utc) - timedelta(days=180)
        },
        {
            "draft_id": "D-2026-012",
            "policy_id": policy_id,
            "title": "Public Health Emergency Framework v2.0",
            "version_number": 2.0,
            "status": "open",
            "published_date": datetime.now(timezone.utc) - timedelta(days=10)
        }
    ]
    drafts_col.insert_many(mock_drafts)
    print(f"Inserted {len(mock_drafts)} Drafts linked to {policy_id}")

    # 3. Create mock Comments mapping to those specific drafts to show sentiment change
    # Note: We are generating processed_at and confidence_score properties.
    mock_comments = []

    # v1.0 feedback simulation (mostly negative)
    for i in range(50):
        sentiment = "NEGATIVE" if i < 35 else "NEUTRAL" if i < 45 else "POSITIVE"
        mock_comments.append({
            "comment_id": f"C-24-05-{i}",
            "draft_id": "D-2024-005",
            "text": "Simulated feedback for v1.0",
            "sentiment": sentiment,
            "sentiment_score": 0.85,
            "summary": "Mock summary",
            "is_toxic": False,
            "toxicity_score": 0.1,
            "processed_at": datetime.now(timezone.utc) - timedelta(days=300),
            "confidence_score": 0.9,
            "created_at": datetime.now(timezone.utc) - timedelta(days=300)
        })

    # v1.2 feedback simulation (mixed/improving)
    for i in range(50):
        sentiment = "NEGATIVE" if i < 20 else "NEUTRAL" if i < 35 else "POSITIVE"
        mock_comments.append({
            "comment_id": f"C-25-89-{i}",
            "draft_id": "D-2025-089",
            "text": "Simulated feedback for v1.2",
            "sentiment": sentiment,
            "sentiment_score": 0.9,
            "summary": "Mock summary",
            "is_toxic": False,
            "toxicity_score": 0.1,
            "processed_at": datetime.now(timezone.utc) - timedelta(days=150),
            "confidence_score": 0.92,
            "created_at": datetime.now(timezone.utc) - timedelta(days=150)
        })

    # v2.0 feedback simulation (mostly positive)
    for i in range(50):
        sentiment = "NEGATIVE" if i < 10 else "NEUTRAL" if i < 20 else "POSITIVE"
        mock_comments.append({
            "comment_id": f"C-26-12-{i}",
            "draft_id": "D-2026-012",
            "text": "Simulated feedback for v2.0",
            "sentiment": sentiment,
            "sentiment_score": 0.95,
            "summary": "Mock summary",
            "is_toxic": False,
            "toxicity_score": 0.1,
            "processed_at": datetime.now(timezone.utc) - timedelta(days=5),
            "confidence_score": 0.88,
            "created_at": datetime.now(timezone.utc) - timedelta(days=5)
        })

    comments_col.insert_many(mock_comments)
    print(f"Inserted {len(mock_comments)} processed Comments demonstrating sentiment tracking.")
    print("Migration complete. The mock historical data is ready to be fetched.")

if __name__ == "__main__":
    run_migration()
