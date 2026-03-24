from pymongo import MongoClient
import os
from datetime import datetime, timezone
from typing import Optional, List, Literal

try:
    from dotenv import load_dotenv
    # Load environment variables from backend/.env when present.
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=env_path)
except Exception:
    pass

try:
    from pydantic import BaseModel, Field
except ImportError:
    pass

# MongoDB Connection String
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/avalokan_db")

# Initialize client globally but connect lazily
client = MongoClient(MONGO_URI)
db = client.get_database()

print(f"Connected to MongoDB: {db.name} @ {MONGO_URI.split('@')[-1].split('/')[0] if '@' in MONGO_URI else 'localhost'}")

# For MongoDB we can manage schemas by establishing indexes and validation, 
# or strictly via the Pydantic models. We'll use Pydantic models for type safety 
# across the application and to document the shape of our data.

class Policy(BaseModel):
    """
    The Parent overarching regulatory initiative.
    """
    policy_id: str = Field(description="Unique ID for the policy")
    title: str
    summary: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Draft(BaseModel):
    """
    A specific versioned document within a Policy.
    """
    draft_id: str = Field(description="Unique ID for this draft version")
    policy_id: str = Field(description="Links to the parent Policy")
    title: str
    version_number: float = Field(description="Strict float version number (e.g., 1.0, 1.2)")
    status: Literal['open', 'closed', 'superseded'] = Field(
        default='open',
        description="Status of this draft's consultation window."
    )
    published_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Comment(BaseModel):
    """
    Stakeholder feedback submission.
    """
    comment_id: str = Field(description="Unique ID for the comment")
    draft_id: str = Field(description="Links to the specific Draft")
    text: str
    clause_ref: Optional[str] = Field(default=None, description="Reference to a specific legal clause or section (e.g., Section 135)")
    
    # AI Engine Outputs
    sentiment: Literal['POSITIVE', 'NEUTRAL', 'NEGATIVE'] = 'NEUTRAL'
    sentiment_score: float = 0.0
    summary: str = ""
    is_toxic: bool = False
    toxicity_score: float = 0.0
    
    # Audit & Process fields
    processed_at: Optional[datetime] = Field(
        default=None, 
        description="Timestamp indicating when the AI engine analyzed the text"
    )
    confidence_score: Optional[float] = Field(
        default=0.0,
        description="Confidence score string tying back to model assertions"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

def setup_db(db):
    """
    Helper function to establish required indexes and validation rules 
    on the MongoDB natively if it's the first time running.
    """
    db.policies.create_index("policy_id", unique=True)
    db.drafts.create_index("draft_id", unique=True)
    db.drafts.create_index([("policy_id", 1), ("version_number", -1)])
    db.comments.create_index("comment_id", unique=True)
    db.comments.create_index("draft_id")

# Expose collections
policies_col = db.policies
drafts_col = db.drafts
comments_col = db.comments
draft_analysis_col = db.draft_analysis
