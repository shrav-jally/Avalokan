import os
try:
    from dotenv import load_dotenv
    # Load environment variables from backend/.env when present at the earliest point.
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=env_path)
except Exception:  # pragma: no cover
    load_dotenv = None

from flask import Flask, jsonify, session, url_for, redirect, request
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from functools import wraps
import uuid
from datetime import datetime, timezone, timedelta
from database import policies_col, drafts_col, comments_col
from ai_engine import process_comment
from report_generator import generate_draft_report
from flask import send_file

def _parse_csv_env(var_name: str, default: list[str]) -> list[str]:
    raw = os.getenv(var_name)
    if not raw:
        return default
    parts = [p.strip() for p in raw.split(',')]
    return [p for p in parts if p]

app = Flask(__name__)

# Secret key must come from environment (.env) so it isn't committed.
_secret_key = os.getenv('FLASK_SECRET_KEY', '')
if not _secret_key:
    raise RuntimeError('Missing FLASK_SECRET_KEY. Set it in backend/.env (see backend/.env.example).')
app.secret_key = _secret_key

# Strict CORS policy for credentials
cors_origins = _parse_csv_env('CORS_ORIGINS', ["http://127.0.0.1:5173", "http://localhost:5173"])
CORS(app, supports_credentials=True, origins=cors_origins)

# OAuth Configuration
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID', '')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET', '')

frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Admin Allowlist (Mock RBAC)
ADMIN_ALLOWLIST = _parse_csv_env(
    'ADMIN_ALLOWLIST',
    [
        'shravya.jallepally@gmail.com',  # Primary Admin
        'test@example.com',
        'admin@avalokan.gov',
    ],
)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized', 'message': 'Please log in'}), 401
        
        user_email = session['user'].get('email')
        if user_email not in ADMIN_ALLOWLIST:
             return jsonify({'error': 'Forbidden', 'message': 'Access denied. Admin role required.'}), 403
             
        return f(*args, **kwargs)
    return decorated_function

# Auth Routes
@app.route('/login')
def login():
    if not app.config.get('GOOGLE_CLIENT_ID') or not app.config.get('GOOGLE_CLIENT_SECRET'):
        return jsonify({
            'error': 'OAuth is not configured',
            'message': 'Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env'
        }), 500
    redirect_uri = url_for('auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            session['user'] = user_info
            
            # Use frontend URL proper for redirect
            return redirect(f'{frontend_url}/')
        return jsonify({'error': 'Authentication failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.pop('user', None)
    return jsonify({'status': 'success', 'message': 'Logged out successfully'})

@app.route('/api/auth/status')
def auth_status():
    if 'user' in session:
        user = session['user']
        is_admin = user.get('email') in ADMIN_ALLOWLIST
        return jsonify({
            'isAuthenticated': True,
            'user': user,
            'role': 'admin' if is_admin else 'user',
            'isAuthorized': is_admin
        })
    return jsonify({'isAuthenticated': False, 'role': 'guest'})


@app.route("/api/dashboard/metrics", methods=["GET"])
def get_metrics():
    total_drafts = drafts_col.count_documents({})
    total_comments = comments_col.count_documents({})
    active_consultations = drafts_col.count_documents({"status": "open"})
    
    aggr = list(comments_col.aggregate([{"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}]))
    
    pos = 0; neu = 0; neg = 0
    for a in aggr:
        if a.get("_id") == "POSITIVE": pos = a["count"]
        elif a.get("_id") == "NEUTRAL": neu = a["count"]
        elif a.get("_id") == "NEGATIVE": neg = a["count"]
        
    total_sent = pos + neu + neg
    if total_sent > 0:
        pos_pct = round((pos / total_sent) * 100)
        neu_pct = round((neu / total_sent) * 100)
        neg_pct = round((neg / total_sent) * 100)
    else: pos_pct = neu_pct = neg_pct = 0
    
    data = {
        "totalDrafts": total_drafts,
        "totalComments": total_comments,
        "activeConsultations": active_consultations,
        "sentimentDistribution": {"positive": pos_pct, "neutral": neu_pct, "negative": neg_pct}
    }
    return jsonify(data)

@app.route('/api/dashboard/detailed-metrics', methods=['GET'])
def get_detailed_metrics():
    # Fetch real drafts and aggregate their sentiment counts
    pipeline = [
        {"$group": {
            "_id": "$draft_id",
            "comments": {"$sum": 1},
            "pos": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "POSITIVE"]}, 1, 0 ] } },
            "neu": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "NEUTRAL"]}, 1, 0 ] } },
            "neg": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "NEGATIVE"]}, 1, 0 ] } }
        }},
        {"$lookup": {
            "from": "drafts",
            "localField": "_id",
            "foreignField": "draft_id",
            "as": "draft_info"
        }},
        { "$unwind": { "path": "$draft_info", "preserveNullAndEmptyArrays": True } },
        { "$limit": 3 }
    ]
    aggr = list(comments_col.aggregate(pipeline))
    results = []
    for doc in aggr:
        info = doc.get("draft_info", {})
        results.append({
            "id": doc["_id"],
            "title": info.get("title", doc["_id"]),
            "comments": doc["comments"],
            "sentiment": {
                "pos": doc["pos"],
                "neu": doc["neu"],
                "neg": doc["neg"]
            }
        })
    return jsonify(results)

@app.route("/api/global/draft-comment-volume", methods=["GET"])
def get_global_draft_comment_volume():
    pipeline = [
        {"$group": {"_id": "$draft_id", "total_comments": {"$sum": 1}, "positive_count": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "POSITIVE"]}, 1, 0 ] } }, "neutral_count": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "NEUTRAL"]}, 1, 0 ] } }, "negative_count": { "$sum": { "$cond": [ {"$eq": ["$sentiment", "NEGATIVE"]}, 1, 0 ] } }}},
        {"$lookup": {"from": "drafts", "localField": "_id", "foreignField": "draft_id", "as": "draft_info"}},
        { "$unwind": { "path": "$draft_info", "preserveNullAndEmptyArrays": True } },
        { "$sort": { "draft_info.published_date": -1, "_id": -1 } }
    ]
    aggr = list(comments_col.aggregate(pipeline))
    data = []
    for idx, doc in enumerate(aggr):
        draft_info = doc.get("draft_info", {})
        data.append({
            "draft_id": doc["_id"],
            "draft_title": draft_info.get("title", doc["_id"]),
            "total_comments": doc["total_comments"],
            "positive_count": doc["positive_count"],
            "neutral_count": doc["neutral_count"],
            "negative_count": doc["negative_count"],
            "release_order": len(aggr) - idx
        })
    return jsonify(data)

@app.route("/api/policies", methods=["GET"])
def get_policies():
    policies = list(policies_col.find({}, {"_id": 0}).sort("created_at", -1))
    data = []
    for p in policies:
        data.append({
            "id": p.get("policy_id"),
            "title": p.get("title"),
            "summary": p.get("summary")
        })
    return jsonify(data)

@app.route('/api/analytics/compare-linked/<policy_id>', methods=['GET'])
def compare_linked_policy(policy_id):
    # Mock data showing sentiment trends for linked policies
    mock_chains = {
        "D-2026-012": [
            {"id": "D-2024-005", "version": "v1.0", "positive": 1500, "neutral": 800, "negative": 1200},
            {"id": "D-2025-089", "version": "v1.1", "positive": 1700, "neutral": 750, "negative": 1100},
            {"id": "D-2026-012", "version": "v2.0", "positive": 2100, "neutral": 700, "negative": 800},
        ],
        "D-2026-010": [
            {"id": "D-2023-100", "version": "v1.0", "positive": 1000, "neutral": 500, "negative": 900},
            {"id": "D-2026-010", "version": "v1.2", "positive": 1200, "neutral": 857, "negative": 392},
        ]
    }
    
    chain = mock_chains.get(policy_id, [])
    # If not in mock data, generate a generic mock chain so the chart always displays data
    if not chain:
        # Build a generic 3-iteration history showing sentiment improvement
        chain = [
            {"id": f"{policy_id}-v1", "version": "v1.0", "positive": 600, "neutral": 400, "negative": 1500},
            {"id": f"{policy_id}-v1.5", "version": "v1.5", "positive": 1100, "neutral": 600, "negative": 900},
            {"id": policy_id, "version": "v2.0", "positive": 2400, "neutral": 850, "negative": 300},
        ]
        
    return jsonify({"policyId": policy_id, "chain": chain})

@app.route('/api/analyze/bulk', methods=['POST'])
def bulk_analyze():
    data = request.json
    comments = data.get('comments', [])
    
    results = []
    docs_to_insert = []
    
    for c in comments:
        draft_id = c.get('draft_id')
        text = c.get('text', '')
        
        # Analyze comment
        analysis = process_comment(text)
        
        # Create full document
        doc = {
            "comment_id": str(uuid.uuid4()),
            "draft_id": draft_id,
            "text": text,
            "sentiment": analysis.get('sentiment', 'NEUTRAL'),
            "sentiment_score": analysis.get('sentiment_score', 0.0),
            "summary": analysis.get('summary', ''),
            "is_toxic": analysis.get('is_toxic', False),
            "toxicity_score": analysis.get('toxicity_score', 0.0),
            "processed_at": datetime.now(timezone.utc),
            "confidence_score": analysis.get('sentiment_score', 0.0),
            "created_at": datetime.now(timezone.utc)
        }
        docs_to_insert.append(doc)
        results.append(doc)
        
    if docs_to_insert:
        comments_col.insert_many(docs_to_insert)
        
    return jsonify({"inserted_count": len(docs_to_insert), "results": results})

@app.route('/api/analytics/trend/<policy_id>', methods=['GET'])
def policy_sentiment_trend(policy_id):
    # Find all drafts for this policy
    drafts = list(drafts_col.find({"policy_id": policy_id}).sort("version_number", 1))
    
    if not drafts:
        return jsonify({"policyId": policy_id, "chain": []})
        
    chain = []
    for d in drafts:
        draft_id = d.get('draft_id')
        version = f"v{d.get('version_number', 1.0)}"
        
        # Aggregate sentiment for this draft
        aggr = list(comments_col.aggregate([
            {"$match": {"draft_id": draft_id}},
            {"$group": {
                "_id": "$sentiment",
                "count": {"$sum": 1}
            }}
        ]))
        
        sentiment_counts = { "POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0 }
        for a in aggr:
            if a["_id"] in sentiment_counts:
                sentiment_counts[a["_id"]] = a["count"]
                
        chain.append({
            "id": draft_id,
            "version": version,
            "positive": sentiment_counts["POSITIVE"],
            "neutral": sentiment_counts["NEUTRAL"],
            "negative": sentiment_counts["NEGATIVE"]
        })
        
    return jsonify({"policyId": policy_id, "chain": chain})

@app.route('/api/comments/search', methods=['GET'])
def search_comments():
    sentiment = request.args.get('sentiment')
    policy_id = request.args.get('policy_id')
    is_toxic = request.args.get('is_toxic')
    keyword = request.args.get('keyword')
    
    query = {}
    
    if policy_id:
        # Find all drafts for this policy
        drafts = list(drafts_col.find({"policy_id": policy_id}, {"draft_id": 1}))
        draft_ids = [d['draft_id'] for d in drafts]
        if draft_ids:
            query['draft_id'] = {"$in": draft_ids}
        else:
            # If no drafts exist for the policy, return empty
            return jsonify({"results": []})
            
    if sentiment:
        query['sentiment'] = sentiment.upper()
        
    if is_toxic is not None:
        query['is_toxic'] = is_toxic.lower() == 'true'
        
    if keyword:
        query['text'] = {"$regex": keyword, "$options": "i"}
        
    # Optional pagination
    limit = int(request.args.get('limit', 50))
    skip = int(request.args.get('skip', 0))
    
    results_cursor = comments_col.find(query).sort("created_at", -1).skip(skip).limit(limit)
    
    results = []
    for doc in results_cursor:
        # Format the document for JSON serialization
        results.append({
            "comment_id": doc.get('comment_id', ''),
            "draft_id": doc.get('draft_id', ''),
            "text": doc.get('text', ''),
            "sentiment": doc.get('sentiment', 'NEUTRAL'),
            "sentiment_score": doc.get('sentiment_score', 0.0),
            "summary": doc.get('summary', ''),
            "is_toxic": doc.get('is_toxic', False),
            "toxicity_score": doc.get('toxicity_score', 0.0)
        })
        
    return jsonify({"results": results})

@app.route('/api/reports/generate/<draft_id>', methods=['GET'])
def generate_report(draft_id):
    draft = drafts_col.find_one({"draft_id": draft_id})
    if not draft:
        return jsonify({"error": "Draft not found"}), 404
        
    comments = list(comments_col.find({"draft_id": draft_id}))
    pdf_buffer = generate_draft_report(draft, comments)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Report_{draft_id}.pdf",
        mimetype='application/pdf'
    )

@app.route("/api/drafts", methods=["GET"])
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

@app.route("/api/home/notifications", methods=["GET"])
def get_home_notifications():
    # Return a few recent comments and newly created policies as "notifications"
    recent_comments = list(comments_col.find().sort("created_at", -1).limit(3))
    recent_policies = list(policies_col.find().sort("created_at", -1).limit(2))
    
    notifications = []
    for c in recent_comments:
        notifications.append({
            "type": "comment",
            "title": f"New Comment on {c.get('draft_id', 'Draft')}",
            "message": c.get('summary', c.get('text', ''))[:100],
            "timestamp": "Recent",
            "class": "dot-new" if c.get('sentiment') == 'POSITIVE' else ("dot-urgent" if c.get('sentiment') == 'NEGATIVE' else "dot-normal")
        })
        
    for p in recent_policies:
        notifications.append({
            "type": "policy",
            "title": "New Policy Created",
            "message": f"The policy '{p.get('title')}' was successfully added to the system.",
            "timestamp": "New",
            "class": "dot-new"
        })
        
    return jsonify(notifications)

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'true').lower() in ('1', 'true', 'yes', 'on')
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(debug=debug, host=host, port=port)
