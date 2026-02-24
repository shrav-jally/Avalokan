from flask import Flask, jsonify, session, url_for, redirect, request
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from functools import wraps
import os

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


def _parse_csv_env(var_name: str, default: list[str]) -> list[str]:
    raw = os.getenv(var_name)
    if not raw:
        return default
    parts = [p.strip() for p in raw.split(',')]
    return [p for p in parts if p]


if load_dotenv is not None:
    # Load environment variables from backend/.env when present.
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=env_path)

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


@app.route('/api/dashboard/metrics', methods=['GET'])
@admin_required
def get_metrics():
    # Mock data for government e-consultation analytics
    data = {
        "totalDrafts": 142,
        "totalComments": 8540,
        "activeConsultations": 24,
        "sentimentDistribution": {
            "positive": 45,
            "neutral": 35,
            "negative": 20
        }
    }
    return jsonify(data)

@app.route('/api/dashboard/detailed-metrics', methods=['GET'])
def get_detailed_metrics():
    # Mock data for draft-wise engagement
    drafts = [
        {"id": "D-2026-001", "title": "Public Health Bill v1.2", "comments": 2450, "sentiment": {"pos": 1200, "neu": 850, "neg": 400}},
        {"id": "D-2026-002", "title": "Urban Transport Policy", "comments": 1820, "sentiment": {"pos": 600, "neu": 920, "neg": 300}},
        {"id": "D-2026-003", "title": "Data Privacy Framework", "comments": 3100, "sentiment": {"pos": 1100, "neu": 700, "neg": 1300}},
        {"id": "D-2026-004", "title": "Green Energy Initiative", "comments": 950, "sentiment": {"pos": 700, "neu": 200, "neg": 50}},
        {"id": "D-2026-005", "title": "Education Reform Act", "comments": 1560, "sentiment": {"pos": 800, "neu": 460, "neg": 300}},
        {"id": "D-2026-006", "title": "Cyber Security Guidelines", "comments": 2100, "sentiment": {"pos": 900, "neu": 800, "neg": 400}},
        {"id": "D-2026-007", "title": "Fisheries Management", "comments": 450, "sentiment": {"pos": 200, "neu": 150, "neg": 100}},
    ]
    return jsonify(drafts)

@app.route('/api/global/draft-comment-volume', methods=['GET'])
def get_global_draft_comment_volume():
    # Expanded dataset for scrollable charts and sorting demonstration
    # release_order: higher means newer
    data = [
        {"draft_id": "D-2026-012", "draft_title": "Coastal Protection Regulation", "total_comments": 4200, "positive_count": 1512, "neutral_count": 714, "negative_count": 2016, "release_order": 12}, # 36%, 17%, 48%
        {"draft_id": "D-2026-011", "draft_title": "Electronic ID Standards", "total_comments": 1200, "positive_count": 804, "neutral_count": 300, "negative_count": 96, "release_order": 11}, # 67%, 25%, 8%
        {"draft_id": "D-2026-010", "draft_title": "Public Health Bill v1.2", "total_comments": 2450, "positive_count": 1200, "neutral_count": 857, "negative_count": 392, "release_order": 10}, # 49%, 35%, 16%
        {"draft_id": "D-2026-009", "draft_title": "Urban Transport Policy", "total_comments": 1820, "positive_count": 600, "neutral_count": 928, "negative_count": 291, "release_order": 9}, # 33%, 51%, 16%
        {"draft_id": "D-2026-008", "draft_title": "Data Privacy Framework", "total_comments": 3100, "positive_count": 1085, "neutral_count": 713, "negative_count": 1302, "release_order": 8}, # 35%, 23%, 42%
        {"draft_id": "D-2026-007", "draft_title": "Green Energy Initiative", "total_comments": 950, "positive_count": 703, "neutral_count": 200, "negative_count": 47, "release_order": 7}, # 74%, 21%, 5%
        {"draft_id": "D-2026-006", "draft_title": "Education Reform Act", "total_comments": 1560, "positive_count": 795, "neutral_count": 452, "negative_count": 296, "release_order": 6}, # 51%, 29%, 19%
        {"draft_id": "D-2026-005", "draft_title": "Mining Safety Protocol", "total_comments": 600, "positive_count": 198, "neutral_count": 102, "negative_count": 300, "release_order": 5}, # 33%, 17%, 50%
        {"draft_id": "D-2026-004", "draft_title": "Telecomm Infrastructure", "total_comments": 2100, "positive_count": 1407, "neutral_count": 504, "negative_count": 210, "release_order": 4}, # 67%, 24%, 10%
        {"draft_id": "D-2026-003", "draft_title": "Aviation Noise Policy", "total_comments": 2800, "positive_count": 504, "neutral_count": 504, "negative_count": 1792, "release_order": 3}, # 18%, 18%, 64%
        {"draft_id": "D-2026-002", "draft_title": "Waste Management Plan", "total_comments": 1300, "positive_count": 897, "neutral_count": 299, "negative_count": 104, "release_order": 2}, # 69%, 23%, 8%
        {"draft_id": "D-2026-001", "draft_title": "Initial Agriculture Reform", "total_comments": 3500, "positive_count": 1190, "neutral_count": 490, "negative_count": 1785, "release_order": 1}, # 34%, 14%, 51%
    ]
    return jsonify(data)

@app.route('/api/policies', methods=['GET'])
def get_policies():
    policies = [
        {"id": "D-2026-012", "title": "Coastal Protection Regulation", "summary": "Establishing regulatory frameworks for safeguarding coastal ecosystems and sustainable shoreline development."},
        {"id": "D-2026-011", "title": "Electronic ID Standards", "summary": "Technical requirements and privacy safeguards for the implementation of national electronic identification systems."},
        {"id": "D-2026-010", "title": "Public Health Bill v1.2", "summary": "Comprehensive legislative update addressing emergency response protocols and community health infrastructure."},
        {"id": "D-2026-009", "title": "Urban Transport Policy", "summary": "Framework for integrating sustainable public transit and reducing carbon emissions in metropolitan areas."},
        {"id": "D-2026-008", "title": "Data Privacy Framework", "summary": "Official guidelines for personal data protection, storage, and cross-border data transfer protocols."},
        {"id": "D-2026-007", "title": "Green Energy Initiative", "summary": "Incentives and regulatory requirements for transitioning national power grids to renewable energy sources."},
    ]
    return jsonify(policies)

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

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'true').lower() in ('1', 'true', 'yes', 'on')
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(debug=debug, host=host, port=port)
