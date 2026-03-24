import os
import sys
import uuid
import random
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

from faker import Faker
fake = Faker()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/avalokan_db")

def confirm_deletion():
    print(f"WARNING: The script will clear ALL existing data in the database at {MONGO_URI}.")
    if "--force" in sys.argv:
        print("Force flag detected. Proceeding...")
        return True
    
    choice = input("Enter 'yes' to proceed: ")
    return choice.lower() == 'yes'

def generate_comments_for_draft(draft_id, published_date):
    comments_to_insert = []
    
    # Requirements: 50-100 comments
    num_comments = random.randint(50, 100)
    
    legal_terms = ["compliance", "penalty", "MSME", "timeline", "Section 135", "audit", "regulatory burden", "registration process", "tax incentives"]
    stakeholders = ["CA", "Company", "Citizen"]
    sentiments = ["POSITIVE", "NEGATIVE", "NEUTRAL"]
    # Persona Logic: 30% Positive, 50% Negative, 20% Neutral.
    weights = [0.30, 0.50, 0.20]
    
    for _ in range(num_comments):
        sentiment = random.choices(sentiments, weights=weights)[0]
        term = random.choice(legal_terms)
        person = random.choice(stakeholders)
        
        is_toxic = False
        if sentiment == "POSITIVE":
            text = f"As a {person}, I fully support this. The proposed changes regarding {term} seem beneficial."
            summary = f"Supports {term} changes."
        elif sentiment == "NEGATIVE":
            text = f"This update on {term} is overly complex and hurts every {person}. It adds unnecessary administrative burden."
            summary = f"Criticizes {term} complexity."
            if random.random() < 0.15: # 15% of negative are toxic
                is_toxic = True
                text = f"This is completely ridiculous! The {term} requirement is a total disaster and shows incompetence, penalizing any hardworking {person}."
                summary = f"Strongly opposes {term} changes (High Risk)."
        else:
            text = f"A {person} might need more time. Could we get additional clarity on the new {term} framework?"
            summary = f"Requests clarity on {term}."
                
        full_text = f"{text} {fake.sentence()}"

        comment_doc = {
            "comment_id": str(uuid.uuid4()),
            "draft_id": draft_id,
            "text": full_text,
            "clause_ref": term if "Section" in term else f"Section {random.randint(1, 150)}",
            "stakeholder_type": person,
            "sentiment": sentiment,
            "sentiment_score": random.uniform(0.7, 0.99),
            "summary": summary,
            "is_toxic": is_toxic,
            "toxicity_score": random.uniform(0.8, 0.99) if is_toxic else random.uniform(0.0, 0.2),
            "processed_at": datetime.now(timezone.utc),
            "confidence_score": random.uniform(0.85, 0.98),
            "created_at": published_date + timedelta(days=random.randint(1, 28))
        }
        comments_to_insert.append(comment_doc)
        
    return comments_to_insert

def seed():
    if not confirm_deletion():
        print("Seeding aborted.")
        return

    client = MongoClient(MONGO_URI)
    db = client.get_database()

    print("Clearing 'policies', 'drafts', and 'comments' collections...")
    db.policies.delete_many({})
    db.drafts.delete_many({})
    db.comments.delete_many({})

    # Real-ish government/legal titles
    policy_titles = [
        "MCA-21 System Revamp and Simplification",
        "Digital Competition Bill",
        "Corporate Social Responsibility (Section 135) Updates",
        "MSME Registration and Verification Framework",
        "Start-up Tax Exemption Enhancements",
        "Foreign Direct Investment Policy Overhaul",
        "Insolvency and Bankruptcy Code Amendments",
        "Data Protection and Privacy Compliance For Corporates",
        "Sustainable Finance and ESG Reporting",
        "Corporate Governance Code Modernization"
    ]

    policies_to_insert = []
    drafts_to_insert = []
    comments_to_insert = []

    for idx, title in enumerate(policy_titles):
        policy_id = f"P-2026-00{idx+1}"
        policy_created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(60, 365))
        
        policy_doc = {
            "policy_id": policy_id,
            "title": title,
            "summary": f"A comprehensive framework regarding {title.lower()} to improve regulatory efficiency.",
            "created_at": policy_created_at
        }
        policies_to_insert.append(policy_doc)

        num_drafts = random.randint(1, 3)
        for i in range(1, num_drafts + 1):
            draft_id = f"{policy_id}-v{i}.0"
            if i == 1:
                status = 'closed'
            elif i == 2:
                status = 'open'
            else:
                status = 'open' if random.choice([True, False]) else 'superseded'

            draft_published_date = policy_created_at + timedelta(days=i*30)
            draft_doc = {
                "draft_id": draft_id,
                "policy_id": policy_id,
                "title": f"{title} Version {i}.0",
                "version_number": float(i),
                "status": status,
                "published_date": draft_published_date
            }
            drafts_to_insert.append(draft_doc)

            # Generate Comments
            draft_comments = generate_comments_for_draft(draft_id, draft_published_date)
            comments_to_insert.extend(draft_comments)

    print("Inserting seeded data...")
    if policies_to_insert:
        db.policies.insert_many(policies_to_insert)
    if drafts_to_insert:
        db.drafts.insert_many(drafts_to_insert)
    if comments_to_insert:
        db.comments.insert_many(comments_to_insert)

    print("====================================")
    print("Seed Complete!")
    print(f"- Inserted {len(policies_to_insert)} Policies")
    print(f"- Inserted {len(drafts_to_insert)} Drafts")
    print(f"- Inserted {len(comments_to_insert)} Comments")
    print("====================================")

if __name__ == '__main__':
    seed()
