import os
try:
    from dotenv import load_dotenv
    # Load environment variables from backend/.env when present at the earliest point.
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=env_path)
except Exception:  # pragma: no cover
    load_dotenv = None

from flask import Flask, jsonify, session, url_for, redirect, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from functools import wraps
import spacy
try:
    nlp = spacy.load('en_core_web_sm')
except:
    nlp = None
import uuid
from bson import ObjectId
from datetime import datetime, timezone, timedelta
from database import policies_col, drafts_col, comments_col, draft_analysis_col, users_col
# Verified core dependencies loaded
from ai_engine import process_comment, process_batch, generate_draft_summary, generate_clause_summaries
from report_generator import generate_professional_report
from excel_generator import generate_excel_workbook
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
# cors_origins = _parse_csv_env('CORS_ORIGINS', ["http://127.0.0.1:5173", "http://localhost:5173"])
# Updated to global CORS per user request to resolve 500 preflight issues
CORS(app, supports_credentials=True)

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
        'ap10ashu@gmail.com'
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

# ── Auth Routes ──────────────────────────────────────────

# --- Local Signup ---
@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        stakeholder_type = data.get('stakeholder_type', '')

        if not all([name, email, password, stakeholder_type]):
            return jsonify({'error': 'All fields are required.'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters.'}), 400

        if users_col.find_one({'email': email}):
            return jsonify({'error': 'An account with this email already exists.'}), 409

        pw_hash = generate_password_hash(password)
        user_doc = {
            'email': email,
            'password_hash': pw_hash,
            'name': name,
            'stakeholder_type': stakeholder_type,
            'role': 'consumer',
            'auth_method': 'local',
            'created_at': datetime.now(timezone.utc)
        }
        users_col.insert_one(user_doc)

        # Auto-login after signup
        session['user'] = {'email': email, 'name': name}
        session['role'] = 'consumer'
        session['stakeholder_type'] = stakeholder_type
        session['needs_onboarding'] = False

        return jsonify({'status': 'success', 'message': 'Account created successfully.'}), 201
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'error': str(e)}), 500

# --- Local Login (Admin + Consumer) ---
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        requested_role = data.get('role', 'consumer')  # 'admin' or 'consumer'

        if not email or not password:
            return jsonify({'error': 'Email and password are required.'}), 400

        # Check if admin credentials
        if requested_role == 'admin':
            if email not in [a.lower() for a in ADMIN_ALLOWLIST]:
                return jsonify({'error': 'Access denied. This account is not on the admin allowlist.'}), 403
            # Try DB-based password first
            db_user = users_col.find_one({'email': email})
            if db_user and db_user.get('password_hash'):
                if not check_password_hash(db_user['password_hash'], password):
                    return jsonify({'error': 'Incorrect password.'}), 401
            # If no local account, reject (must use Google or set up account)
            elif not db_user:
                return jsonify({'error': 'No local account found. Please use Google login or contact your administrator.'}), 404

            session['user'] = {'email': email, 'name': db_user.get('name', email)}
            session['role'] = 'admin'
            session['needs_onboarding'] = False
            return jsonify({'status': 'success', 'role': 'admin'})

        # Consumer local login
        db_user = users_col.find_one({'email': email})
        if not db_user:
            return jsonify({'error': 'No account found with this email. Please register first.'}), 404

        if not db_user.get('password_hash'):
            return jsonify({'error': 'This account was created with Google. Please use the Google login button.'}), 400

        if not check_password_hash(db_user['password_hash'], password):
            return jsonify({'error': 'Incorrect password.'}), 401

        session['user'] = {'email': email, 'name': db_user.get('name', '')}
        session['role'] = 'consumer'
        session['stakeholder_type'] = db_user.get('stakeholder_type', '')
        session['needs_onboarding'] = not bool(db_user.get('stakeholder_type'))

        return jsonify({'status': 'success', 'role': 'consumer'})
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500

# --- Google OAuth: Admin path ---
@app.route('/auth/google/admin')
def google_login_admin():
    session['oauth_intent'] = 'admin'
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

# --- Google OAuth: Consumer path ---
@app.route('/auth/google/consumer')
def google_login_consumer():
    session['oauth_intent'] = 'consumer'
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

# Legacy /login route kept for backward compatibility
@app.route('/login')
def login():
    session['oauth_intent'] = 'consumer'
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth_callback():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')

        if not user_info:
            return jsonify({'error': 'Authentication failed'}), 400

        user_email = user_info.get('email', '').lower()
        intent = session.pop('oauth_intent', 'consumer')

        session['user'] = user_info

        if intent == 'admin':
            if user_email not in [a.lower() for a in ADMIN_ALLOWLIST]:
                session.clear()
                return redirect(f'{frontend_url}/?error=admin_access_denied')
            session['role'] = 'admin'
            session['needs_onboarding'] = False
        else:
            # Consumer Google login/signup
            db_user = users_col.find_one({'email': user_email})
            if db_user:
                session['role'] = 'consumer'
                session['stakeholder_type'] = db_user.get('stakeholder_type', '')
                session['needs_onboarding'] = not bool(db_user.get('stakeholder_type'))
                # Update auth_method to google if not set
                if db_user.get('auth_method') != 'google':
                    users_col.update_one({'email': user_email}, {'$set': {'auth_method': 'google'}})
            else:
                # New Google user — create account, needs stakeholder selection
                users_col.insert_one({
                    'email': user_email,
                    'password_hash': None,
                    'name': user_info.get('name', ''),
                    'stakeholder_type': '',
                    'role': 'consumer',
                    'auth_method': 'google',
                    'created_at': datetime.now(timezone.utc)
                })
                session['role'] = 'consumer'
                session['needs_onboarding'] = True

        return redirect(f'{frontend_url}/')
    except Exception as e:
        print(f"OAuth callback error: {e}")
        return redirect(f'{frontend_url}/?error=oauth_failed')

@app.route('/logout')
@app.route('/api/auth/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return jsonify({'status': 'success', 'message': 'Logged out successfully'})


@app.route('/api/auth/status')
def auth_status():
    if 'user' in session:
        user = session['user']
        role = session.get('role', 'user')
        is_admin = role == 'admin'
        needs_onboarding = session.get('needs_onboarding', False)
        
        return jsonify({
            'isAuthenticated': True,
            'user': user,
            'role': role,
            'isAuthorized': is_admin,
            'needsOnboarding': needs_onboarding,
            'stakeholderType': session.get('stakeholder_type')
        })
    return jsonify({'isAuthenticated': False, 'role': 'guest'})

@app.route('/api/auth/onboard', methods=['POST'])
def onboard_user():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    stakeholder_type = data.get('stakeholder_type')
    
    if not stakeholder_type:
        return jsonify({'error': 'Missing stakeholder_type'}), 400
        
    user_email = session['user'].get('email')
    
    users_col.update_one(
        {"email": user_email},
        {"$set": {
            "email": user_email,
            "name": session['user'].get('name', ''),
            "stakeholder_type": stakeholder_type,
            "created_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )
    
    session['needs_onboarding'] = False
    session['role'] = 'consumer'
    session['stakeholder_type'] = stakeholder_type
    
    return jsonify({"status": "success", "message": "Onboarding complete"})


@app.route("/api/dashboard/metrics", methods=["GET"])
def get_metrics():
    total_drafts = drafts_col.count_documents({})
    active_consultations = drafts_col.count_documents({"status": "open"})

    # Always count directly from the live comments collection so new
    # consumer submissions (not yet AI-processed) are included.
    total_comments = comments_col.count_documents({})

    # Sentiment breakdown from live comments collection (no cache dependency)
    sentiment_aggr = list(comments_col.aggregate([
        {"$group": {
            "_id": "$sentiment",
            "count": {"$sum": 1}
        }}
    ]))
    counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
    for a in sentiment_aggr:
        s = a.get("_id")
        if s and s in counts:
            counts[s] = a["count"]

    total_sent = sum(counts.values())
    if total_sent > 0:
        pos_pct = round((counts["POSITIVE"] / total_sent) * 100)
        neu_pct = round((counts["NEUTRAL"]  / total_sent) * 100)
        neg_pct = round((counts["NEGATIVE"] / total_sent) * 100)
    else:
        pos_pct = neu_pct = neg_pct = 0

    return jsonify({
        "totalDrafts": total_drafts,
        "totalComments": total_comments,
        "activeConsultations": active_consultations,
        "sentimentDistribution": {"positive": pos_pct, "neutral": neu_pct, "negative": neg_pct}
    })

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
        pid = p.get("policy_id")
        # Resolve the latest draft_id so the Admin PolicyDetail can query
        # comments using the exact same key the Consumer uses when submitting.
        latest_draft = drafts_col.find_one(
            {"policy_id": pid},
            sort=[("version_number", -1)]
        )
        data.append({
            "id": pid,
            "title": p.get("title"),
            "summary": p.get("summary"),
            "latest_draft_id": latest_draft.get("draft_id") if latest_draft else None
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
            
            # Use specific properties if edited, fallback sequentially
            if "startDate" in d and isinstance(d["startDate"], datetime):
                d["startDate"] = d["startDate"].strftime("%Y-%m-%d")
            else:
                d["startDate"] = d["uploadDate"]
                
            if "endDate" in d and isinstance(d["endDate"], datetime):
                d["endDate"] = d["endDate"].strftime("%Y-%m-%d")
            else:
                d["endDate"] = (d["published_date"] + timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            d["uploadDate"] = "2026-01-01"
            d["startDate"] = "2026-01-01"
            d["endDate"] = "2026-02-01"
            
        # UI expects "id" not "draft_id" or consistent with draft_id
        d["id"] = d.get("draft_id", "D-UNKNOWN")

        # Emit closed_at as ISO string for frontend date comparisons
        if "closed_at" in d and isinstance(d["closed_at"], datetime):
            d["closed_at"] = d["closed_at"].isoformat()
        elif "endDate" in d and isinstance(d.get("endDate"), str):
            # If no explicit closed_at, treat endDate as the closing boundary
            d.setdefault("closed_at", d["endDate"])
        
    return jsonify(drafts)

from dateutil import parser

@app.route("/api/admin/update-draft/<path:draft_id>", methods=["PUT", "POST"])
def update_draft_dates(draft_id):
    try:
        data = request.json
        print("Update Request Payload:", data)
        updates = {}

        # Handle date updates (optional)
        if data.get('startDate'):
            updates['startDate'] = parser.parse(data['startDate'])
            if not updates['startDate'].tzinfo:
                updates['startDate'] = updates['startDate'].replace(tzinfo=timezone.utc)
                
        if data.get('endDate'):
            end_date = parser.parse(data['endDate'])
            if not end_date.tzinfo:
                end_date = end_date.replace(tzinfo=timezone.utc)
            updates['endDate'] = end_date
            
            # Auto-Calculate Status
            closing_boundary = end_date.replace(hour=23, minute=59, second=59, microsecond=999000)
            now = datetime.now(timezone.utc)
            if now > closing_boundary:
                updates['status'] = 'closed'
                updates['closed_at'] = now
            else:
                updates['status'] = 'open'

        # Handle status toggle (open / closed)
        if 'status' in data and not data.get('endDate'):
            updates['status'] = data['status']

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        drafts_col.update_one(
            {"draft_id": draft_id},
            {"$set": updates}
        )
        return jsonify({"message": "Draft updated successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/analytics/global', methods=['GET'])
def get_global_analytics():
    # 1. Total Comments
    total_comments = comments_col.count_documents({})
    
    # 2. Volume Data (comment count per draft/policy)
    volume_pipeline = [
        {"$group": {"_id": "$draft_id", "total_comments": {"$sum": 1}}},
        {"$sort": {"total_comments": -1}},
        {"$limit": 10}
    ]
    volume_aggr = list(comments_col.aggregate(volume_pipeline))
    volume_data = []
    for v in volume_aggr:
        draft = drafts_col.find_one({"draft_id": v["_id"]})
        title = draft.get("title", v["_id"]) if draft else v["_id"]
        volume_data.append({
            "name": title,
            "draft_id": v["_id"],
            "total_comments": v["total_comments"]
        })
        
    # 3. Trend Data
    trend_pipeline = [
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}},
                "positive": {"$sum": {"$cond": [{"$eq": ["$sentiment", "POSITIVE"]}, 1, 0]}},
                "neutral": {"$sum": {"$cond": [{"$eq": ["$sentiment", "NEUTRAL"]}, 1, 0]}},
                "negative": {"$sum": {"$cond": [{"$eq": ["$sentiment", "NEGATIVE"]}, 1, 0]}}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    trend_aggr = list(comments_col.aggregate(trend_pipeline))
    
    trend_data = []
    for a in trend_aggr:
        if not a.get("_id"): continue
        total = a.get("positive", 0) + a.get("neutral", 0) + a.get("negative", 0)
        p = round((a.get("positive", 0) / total) * 100) if total > 0 else 0
        n = round((a.get("neutral", 0) / total) * 100) if total > 0 else 0
        neg = round((a.get("negative", 0) / total) * 100) if total > 0 else 0
        
        trend_data.append({
            "name": a.get("_id"),
            "positive": p,
            "neutral": n,
            "negative": neg
        })
        
    # 4. Sentiment Distribution
    sentiment_aggr = list(comments_col.aggregate([
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
    ]))
    
    counts = { "POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0 }
    for a in sentiment_aggr:
        if a["_id"] in counts:
            counts[a["_id"]] = a["count"]
            
    dist_total = sum(counts.values())
    sentiment_data = [
        {"name": "Positive", "value": round((counts["POSITIVE"]/dist_total)*100) if dist_total > 0 else 0},
        {"name": "Neutral", "value": round((counts["NEUTRAL"]/dist_total)*100) if dist_total > 0 else 0},
        {"name": "Negative", "value": round((counts["NEGATIVE"]/dist_total)*100) if dist_total > 0 else 0}
    ]
        
    return jsonify({
        "totalComments": total_comments,
        "volumeData": volume_data,
        "trendData": trend_data,
        "sentimentDistribution": sentiment_data
    })

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




@app.route("/api/comments/search", methods=["GET"])
def search_comments():
    # 1. Fetch parameters
    draft_id = request.args.get('draft_id')
    policy_id = request.args.get('policy_id') # Accept policy_id as fallback
    sentiment = request.args.get('sentiment')
    stakeholder_type = request.args.get('stakeholder_type')
    clause_ref = request.args.get('clause_ref')
    is_toxic = request.args.get('is_toxic')
    keyword = request.args.get('keyword')
    high_risk = request.args.get('high_risk', 'false').lower() == 'true'
    
    limit = int(request.args.get('limit', 10))
    skip = int(request.args.get('skip', 0))
    
    # 2. Build Query
    query = {}
    
    # Priority: if draft_id provided, use it. If policy_id provided, find its latest draft.
    if draft_id:
        query["draft_id"] = draft_id
    elif policy_id:
        latest = drafts_col.find_one({"policy_id": policy_id}, sort=[("version_number", -1)])
        if latest:
            query["draft_id"] = latest["draft_id"]
        else:
            return jsonify({"results": [], "totalCount": 0}), 200
            
    if sentiment:
        query["sentiment"] = sentiment.upper()
    
    if clause_ref:
        query["clause_ref"] = clause_ref
        
    if is_toxic is not None:
        query["is_toxic"] = is_toxic.lower() == 'true'
        
    if high_risk:
        query["sentiment"] = "NEGATIVE"
        query["is_toxic"] = True
        
    if keyword:
        # Match against both field names used across comment sources
        query["$or"] = [
            {"comment_text": {"$regex": keyword, "$options": "i"}},
            {"text": {"$regex": keyword, "$options": "i"}}
        ]
        
    # 3. Execute
    total_count = comments_col.count_documents(query)
    results = list(comments_col.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit))
    
    # 4. Calculate Distribution (ignoring active sentiment locks)
    aggr_query = query.copy()
    aggr_query.pop("sentiment", None)
    if high_risk:
        aggr_query.pop("is_toxic", None)

    distribution_aggr = list(comments_col.aggregate([
        {"$match": aggr_query},
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
    ]))
    
    dist_counts = { "POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0 }
    for a in distribution_aggr:
        s_id = a.get("_id")
        if s_id and s_id in dist_counts:
            dist_counts[s_id] = a["count"]
            
    dist_total = sum(dist_counts.values()) or 1
    sentiment_distribution = [
        {"name": "Positive", "value": round((dist_counts["POSITIVE"]/dist_total)*100)},
        {"name": "Neutral", "value": round((dist_counts["NEUTRAL"]/dist_total)*100)},
        {"name": "Negative", "value": round((dist_counts["NEGATIVE"]/dist_total)*100)}
    ]
    
    return jsonify({
        "results": results,
        "totalCount": total_count,
        "limit": limit,
        "skip": skip,
        "sentimentDistribution": sentiment_distribution
    })

@app.route("/api/analytics/wordcloud/<draft_id>", methods=["GET"])
def get_wordcloud_data(draft_id):
    # Fallback to latest draft if policy_id is sent
    policy = policies_col.find_one({"policy_id": draft_id})
    actual_draft_id = draft_id
    if policy:
        latest = drafts_col.find_one({"policy_id": draft_id}, sort=[("version_number", -1)])
        if latest: actual_draft_id = latest["draft_id"]

    comments = list(comments_col.find({"draft_id": actual_draft_id}, {"text": 1, "comment_text": 1, "sentiment": 1}))
    word_stats = {} # {word: {pos: 0, neu: 0, neg: 0, total: 0}}
    
    if nlp:
        for c in comments:
            txt = c.get("comment_text", c.get("text", ""))
            sent = c.get("sentiment", "NEUTRAL").lower()
            if not txt:
                continue
                
            doc = nlp(txt)
            for token in doc:
                if (token.pos_ in ["NOUN", "ADJ"]) and not token.is_stop and len(token.text) > 3:
                    word = token.text.lower()
                    if word not in word_stats:
                        word_stats[word] = {"positive": 0, "neutral": 0, "negative": 0, "total": 0}
                    if sent in word_stats[word]:
                        word_stats[word][sent] += 1
                    word_stats[word]["total"] += 1
                    
    # Sort and take top 50
    sorted_words = sorted(word_stats.items(), key=lambda x: x[1]["total"], reverse=True)[:50]
    
    results = []
    for word, stats in sorted_words:
        # Determine dominant sentiment
        dom_sent = "neutral"
        if stats["positive"] > stats["neutral"] and stats["positive"] > stats["negative"]:
            dom_sent = "positive"
        elif stats["negative"] > stats["positive"] and stats["negative"] > stats["neutral"]:
            dom_sent = "negative"
            
        results.append({
            "text": word,
            "value": stats["total"],
            "sentiment": dom_sent
        })
        
    return jsonify(results)

def _fetch_draft_analytics_payload(actual_draft_id):
    # Sentiment Breakdown
    aggr = list(comments_col.aggregate([
        {"$match": {"draft_id": actual_draft_id}},
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
    ]))
    
    counts = { "POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0 }
    for a in aggr:
        if a["_id"] in counts:
            counts[a["_id"]] = a["count"]
            
    # Word Frequency per Sentiment using spaCy
    word_clouds = []
    for s in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
        comm_list = list(comments_col.find({"draft_id": actual_draft_id, "sentiment": s}, {"text": 1, "comment_text": 1}))
        wc = {}
        if nlp:
            combined_text = ". ".join([c.get("comment_text", c.get("text", "")) for c in comm_list])
            if combined_text:
                doc = nlp(combined_text)
                for token in doc:
                    if (token.pos_ in ["NOUN", "ADJ"]) and not token.is_stop and len(token.text) > 3:
                        clean_w = token.text.lower()
                        wc[clean_w] = wc.get(clean_w, 0) + 1
        else:
            for c in comm_list:
                words = c.get("comment_text", c.get("text", "")).lower().split()
                for w in words:
                    clean_w = "".join(filter(str.isalnum, w))
                    if clean_w and len(clean_w) > 3:
                        wc[clean_w] = wc.get(clean_w, 0) + 1
                        
        sorted_wc = sorted(wc.items(), key=lambda x: x[1], reverse=True)[:20]
        for w, c in sorted_wc:
            word_clouds.append({"text": w, "value": c, "sentiment": s.lower()})

    exec_summary_doc = draft_analysis_col.find_one({"draft_id": actual_draft_id})
    exec_summary = exec_summary_doc.get("combined_summary") if exec_summary_doc else None

    summaries = list(comments_col.find({"draft_id": actual_draft_id, "summary": {"$ne": ""}}).sort("sentiment_score", -1).limit(5))
    heuristic_summary = " ".join([s["summary"] for s in summaries if s.get("summary")])
    
    return {
        "draft_id": actual_draft_id,
        "sentiment": [
            {"name": "Positive", "value": counts["POSITIVE"]},
            {"name": "Neutral", "value": counts["NEUTRAL"]},
            {"name": "Negative", "value": counts["NEGATIVE"]}
        ],
        "wordCloud": word_clouds,
        "combinedSummary": exec_summary or heuristic_summary or "No summary available for this draft yet.",
        "last_updated": exec_summary_doc.get("generated_at").isoformat() if exec_summary_doc and exec_summary_doc.get("generated_at") else None,
        "is_meta_summary": bool(exec_summary),
        "comment_count": counts["POSITIVE"] + counts["NEUTRAL"] + counts["NEGATIVE"],
        "clauseSummaries": generate_clause_summaries(actual_draft_id)
    }

def generate_clause_summaries(draft_id):
    pipeline = [
        {"$match": {"draft_id": draft_id, "clause_ref": {"$ne": None, "$ne": ""}}},
        {"$group": {
            "_id": "$clause_ref",
            "count": {"$sum": 1},
            "sentiment": {"$first": "$sentiment"},
            "summary": {"$first": "$text"}
        }}
    ]
    results = list(comments_col.aggregate(pipeline))
    formatted = []
    for r in results:
        formatted.append({
            "clause": r["_id"],
            "count": r["count"],
            "sentiment": r["sentiment"],
            "summary": f"Aggregated {r['count']} statements. Key note: '{str(r['summary'])[:80]}...'"
        })
    return formatted


@app.route("/api/analytics/draft/<draft_id>", methods=["GET"])
def get_draft_analytics(draft_id):
    try:
        policy = policies_col.find_one({"policy_id": draft_id})
        actual_draft_id = draft_id
        if policy:
            latest_draft = drafts_col.find_one({"policy_id": draft_id}, sort=[("version_number", -1)])
            if latest_draft:
                actual_draft_id = latest_draft["draft_id"]

        payload = _fetch_draft_analytics_payload(actual_draft_id)
        return jsonify(payload)
    except Exception as e:
        print(f"Error in get_draft_analytics: {e}")
        return jsonify({"error": "Failed to generate analytics", "message": str(e)}), 500

@app.route("/api/reports/pdf/<draft_id>", methods=["GET"])
def get_pdf_report(draft_id):
    """Generates and returns a professional PDF report for the draft."""
    draft = drafts_col.find_one({"draft_id": draft_id})
    if not draft:
        policy = policies_col.find_one({"policy_id": draft_id})
        if policy:
            draft = drafts_col.find_one({"policy_id": draft_id}, sort=[("version_number", -1)])
    
    if not draft:
        return jsonify({"error": "Draft not found"}), 404
        
    actual_draft_id = draft["draft_id"]
    analytics_payload = _fetch_draft_analytics_payload(actual_draft_id)
    
    pdf_buffer = generate_professional_report(draft, analytics_payload)
    
    filename = f"Consultation_Report_{actual_draft_id}.pdf"
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@app.route("/api/reports/excel/<draft_id>", methods=["GET"])
def get_excel_report(draft_id):
    """Generates and returns an Excel workbook for the draft consultation."""
    draft = drafts_col.find_one({"draft_id": draft_id})
    if not draft:
        policy = policies_col.find_one({"policy_id": draft_id})
        if policy:
            draft = drafts_col.find_one({"policy_id": draft_id}, sort=[("version_number", -1)])
    
    if not draft:
        return jsonify({"error": "Draft not found"}), 404
        
    actual_draft_id = draft["draft_id"]
    analytics_payload = _fetch_draft_analytics_payload(actual_draft_id)
    
    # Fetch all comments for Sheet 2
    raw_comments = list(comments_col.find({"draft_id": actual_draft_id}, {"_id": 0}))
    
    excel_buffer = generate_excel_workbook(draft, analytics_payload, raw_comments)
    
    filename = f"Consultation_Data_{actual_draft_id}.xlsx"
    return send_file(
        excel_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route("/api/analytics/policy-trend/<policy_id>", methods=["GET"])
def get_policy_trend(policy_id):
    """
    Calculates sentiment distribution across all draft versions of a policy.
    """
    # 1. Fetch all drafts for this policy sorted by version
    drafts = list(drafts_col.find({"policy_id": policy_id}).sort("version_number", 1))
    
    if not drafts:
        return jsonify([])

    draft_ids = [d["draft_id"] for d in drafts]
    
    # 2. Aggregate sentiment counts for all these drafts in one go
    pipeline = [
        {"$match": {"draft_id": {"$in": draft_ids}}},
        {"$group": {
            "_id": {"draft_id": "$draft_id", "sentiment": "$sentiment"},
            "count": {"$sum": 1}
        }}
    ]
    results = list(comments_col.aggregate(pipeline))
    
    # 3. Organize results into a lookup map
    stats_map = {}
    for r in results:
        d_id = r["_id"]["draft_id"]
        sent = r["_id"]["sentiment"]
        count = r["count"]
        
        if d_id not in stats_map:
            stats_map[d_id] = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0, "total": 0}
        
        if sent in stats_map[d_id]:
            stats_map[d_id][sent] = count
            stats_map[d_id]["total"] += count
        
    # 4. Build the final timeseries array
    trend_data = []
    for d in drafts:
        d_id = d["draft_id"]
        v = d.get("version_number", 1.0)
        s = stats_map.get(d_id, {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0, "total": 0})
        total = s["total"] or 1 # Avoid division by zero
        
        trend_data.append({
            "draft_id": d_id,
            "version": f"v{v}",
            "positive": round((s["POSITIVE"] / total) * 100),
            "negative": round((s["NEGATIVE"] / total) * 100),
            "neutral": round((s["NEUTRAL"] / total) * 100)
        })
        
    return jsonify(trend_data)

@app.route("/api/comments/upload", methods=["POST"])
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

@app.route("/api/system/status", methods=["GET"])
def get_system_status():
    return jsonify({
        "status": "healthy",
        "models": [
            {"name": "Sentiment", "id": "distilbert-base-uncased-finetuned-sst-2-english", "v": "1.0"},
            {"name": "Toxicity", "id": "unitary/toxic-bert", "v": "1.0"},
            {"name": "Summarizer", "id": "t5-small", "v": "1.1"}
        ],
        "last_refresh": datetime.now(timezone.utc).isoformat()
    })

@app.route("/api/analysis/summarize-draft/<draft_id>", methods=["POST"])
def trigger_draft_summary(draft_id):
    # Determine search strategy: if draft_id is actually a policy_id, pick the latest draft
    policy = policies_col.find_one({"policy_id": draft_id})
    actual_draft_id = draft_id
    if policy:
        latest = drafts_col.find_one({"policy_id": draft_id}, sort=[("version_number", -1)])
        if latest: actual_draft_id = latest["draft_id"]

    # Safety Check: comment_count > 10
    comment_count = comments_col.count_documents({"draft_id": actual_draft_id})
    if comment_count < 10:
        return jsonify({
            "error": "Not enough data", 
            "message": f"Draft only has {comment_count} comments. At least 10 comments are required for executive summarization."
        }), 400
        
    try:
        final_summary = generate_draft_summary(actual_draft_id)
        return jsonify({
            "status": "success",
            "draft_id": actual_draft_id,
            "executive_summary": final_summary
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/consumer/drafts", methods=["GET"])
def get_consumer_drafts():
    pipeline = [
        {"$match": {"status": "open"}},
        {"$lookup": {
            "from": "policies",
            "localField": "policy_id",
            "foreignField": "policy_id",
            "as": "policy_info"
        }},
        {"$unwind": {"path": "$policy_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "draft_id": 1,
            "policy_id": 1,
            "version": 1,
            "status": 1,
            "published_at": 1,
            "title": {"$ifNull": ["$policy_info.title", "Unknown Policy Title"]},
            "description": {"$ifNull": ["$policy_info.description", "No description available"]},
            "ministry": {"$ifNull": ["$policy_info.ministry", "Unknown Ministry"]}
        }},
        {"$sort": {"published_at": -1}}
    ]
    formatted_drafts = list(drafts_col.aggregate(pipeline))
    return jsonify(formatted_drafts)

@app.route("/api/consumer/submit-comment", methods=["POST"])
def submit_consumer_comment():
    print("Received Form Submission Attempt")
    try:
        data = request.json
        print("Received Comment:", data)
        draft_id = str(data.get('draft_id', ''))
        comment_text = data.get('comment_text', '')
        stakeholder_type = data.get('stakeholder_type', 'Citizen / NGO')
        
        if not draft_id or not comment_text:
            return jsonify({'error': 'Missing draft_id or comment_text'}), 400
            
        doc = {
            "comment_id": str(uuid.uuid4()),
            "draft_id": draft_id,
            "comment_text": comment_text,
            "stakeholder_type": stakeholder_type,
            "sentiment": "NEUTRAL",
            "sentiment_score": 0.5,
            "summary": "",
            "is_toxic": False,
            "toxicity_score": 0.0,
            "processed_at": datetime.now(timezone.utc),
            "confidence_score": 0.5,
            "created_at": datetime.now()
        }
        
        comments_col.insert_one(doc)
        return jsonify({"status": "success", "message": "Comment submitted successfully"}), 201
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'true').lower() in ('1', 'true', 'yes', 'on')
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(debug=debug, host=host, port=port)
