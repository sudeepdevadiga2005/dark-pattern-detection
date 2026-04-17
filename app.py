import os
import json
import datetime
import random
import time
import smtplib
import ssl
import uuid
import threading
from flask import Flask, request, jsonify, session, make_response, send_from_directory
from flask_cors import CORS, cross_origin
from trust_pipeline.datasets import load_datasets
from trust_pipeline.pipeline import process_text, process_url_domain
from trust_pipeline.utils import detect_input_type
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import atexit
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suppress insecure request warnings globally
warnings.filterwarnings('ignore', category=InsecureRequestWarning)
from bson import ObjectId # Essential for database object manipulation


# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Configure folders for serving React
dist_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist')
app = Flask(__name__, static_folder=dist_folder)
app.secret_key = os.getenv("APP_SESSION_KEY", "default-secret-key-keep-it-safe")

# Load datasets for the trust pipeline
load_datasets()


# Define explicit allowed origins for credentialed cross-origin stability
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5000",
    "http://127.0.0.1:5000"
]

CORS(app, supports_credentials=True, origins=ALLOWED_ORIGINS)

# Session Configuration
# SameSite=Lax works correctly for same-origin requests (Vite proxy or production).
# SameSite=None requires Secure=True which only works on HTTPS, not localhost HTTP.
app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(days=7)
)

# MongoDB Setup - Build Safe
db = None
users_col = None
user_db = None

def get_next_sequence(name):
    """Generates a sequential integer identifier starting from 100000"""
    if user_db is None: return "000000"
    
    from pymongo import ReturnDocument
    # Atomic increment operation
    counter = user_db['counters'].find_one_and_update(
        {'_id': name},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    
    # If this is a fresh start, initialize sequence at 100,000
    if counter['seq'] < 100000:
        counter = user_db['counters'].find_one_and_update(
            {'_id': name},
            {'$set': {'seq': 100000}},
            return_document=ReturnDocument.AFTER
        )
    return str(counter['seq'])
analyses_col = None

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI)
        
        # Preserve legacy user data while isolating new administrative records
        user_db = client["dark-pattern-users"] 
        admin_db = client["dark-pattern-admin"]
        
        users_col = user_db["users"]       # Standard users (18+ entries found)
        admins_col = admin_db["admins"]     # Secure administrative archive
        analyses_col = user_db["analyses"] # Shared analytics namespace
        
        client.admin.command('ping')
        print("Database Connection: ONLINE (MongoDB Atlas)", flush=True)

        # ARCHIVE PERSISTENCE VERIFICATION: Track record state across restarts
        total_scans_detected = analyses_col.count_documents({})
        total_operatives_detected = users_col.count_documents({})
        print(f"AEGIS ARCHIVE SYNC: {total_scans_detected} neural scans and {total_operatives_detected} operatives synchronized.", flush=True)
        
        if total_scans_detected == 0:
            print("LOG WARNING: No historical scan data detected in the synchronized collection.", flush=True)

    except Exception as e:
        print(f"DATABASE ERROR: {e}", flush=True)
else:
    print("DATABASE WARNING: MONGO_URI not found. Database features will be disabled until configured.", flush=True)

def close_db_connection():
    global client
    if 'client' in globals() and client:
        print("Closing Database Connection...", flush=True)
        client.close()

atexit.register(close_db_connection)

@app.before_request
def log_session():
    # Helpful for debugging why login might "not work"
    print(f"--- Request: {request.method} {request.path} ---", flush=True)
    print(f"Session State: {'LOGGED IN as ' + session['user'] if 'user' in session else 'GUEST'}", flush=True)
    print(f"Origin: {request.headers.get('Origin')}", flush=True)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow access if EITHER a standard user is logged in OR an administrator
        is_standard_user = 'user' in session and 'session_id' in session
        is_admin_user = 'admin_user' in session and session.get('is_admin')

        if not is_standard_user and not is_admin_user:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
            
        # Verify if the current standard session_id matches the one in the database
        if is_standard_user and users_col is not None:
            lookup_query = {'email': session['email']} if 'email' in session else {'username': session['user']}
            user = users_col.find_one(lookup_query)
            if not user or user.get('session_id') != session['session_id']:
                # The session_id in DB is different (meaning they logged in elsewhere)
                # Selective Path Isolation: Only clear client-level keys, leaving the administrative session intact.
                session.pop('user', None)
                session.pop('session_id', None)
                session.pop('email', None)
                session.pop('client_id', None)
                
                # If they were ONLY a standard user, they are now fully logged out
                if not is_admin_user:
                    return jsonify({'success': False, 'message': 'Session expired or logged in from another device. Please login again.'}), 401
                
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # Use the existing SECRET_KEY from app config as the super_key for MongoDB
        super_key = app.secret_key
        
        if users_col is None:
            return jsonify({'success': False, 'message': 'Database connection error. Try again later.'}), 503

        if not all([username, email, password, confirm_password]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
            
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400

        # GLOBAL IDENTITY CHECK: Ensure the email isn't already used in EITHER collection
        exists_in_users = users_col.find_one({'email': email})
        exists_in_admins = admins_col.find_one({'email': email}) if admins_col is not None else None
        
        if exists_in_users or exists_in_admins:
            return jsonify({'success': False, 'message': 'This identity is already registered in our secure archives.'}), 400
            
        hashed_password = generate_password_hash(password)
        
        # Generate Sequential Unique Client ID (6 digits)
        client_id = get_next_sequence('client_id')
        
        # Save to MongoDB: Includes the super_key (which is the SECRET_KEY)
        users_col.insert_one({
            'username': username, 
            'email': email,
            'password': hashed_password,
            'super_key': super_key, 
            'client_id': client_id,
            'created_at': datetime.datetime.now()
        })
        
        # Create CSV file backup
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            csv_file = "user_backups.csv"
            file_exists = os.path.isfile(csv_file)
            with open(csv_file, "a", encoding='utf-8') as f:
                if not file_exists:
                    f.write("Timestamp,Username,Email,Password,Role\n")
                f.write(f'"{timestamp}","{username}","{email}","{password}","client"\n')
        except Exception:
            pass

        return jsonify({'success': True, 'message': 'Account created successfully'})
    return jsonify({'message': 'Signup API is active. Use POST to register.'})

@app.route('/api/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if users_col is None:
            return jsonify({'success': False, 'message': 'Database connection error. Try again later.'}), 503
            
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user = users_col.find_one({'email': email})
        
        # Strictly prevent administrators from logging into the standard client portal
        if user and user.get('is_admin', False):
            return jsonify({'success': False, 'message': 'Admin accounts must use the Administrative Security Gateway.'}), 403
            
        if user and check_password_hash(user['password'], password):
            # Generate a unique session ID for this specific login event
            new_session_id = str(uuid.uuid4())
            
            # Update the user's database record with this new session ID
            users_col.update_one(
                {'_id': user['_id']},
                {'$set': {'session_id': new_session_id}}
            )
            
            # Set the user and their unique session ID in their cookies
            session.permanent = True  # Make the cookie survive server restarts
            session['user'] = user['username']
            session['email'] = user['email']
            session['client_id'] = user.get('client_id', 'NS-GUEST')
            session['session_id'] = new_session_id
            
            response = make_cookie_response({'success': True, 'user': user['username']})
            response.set_cookie('user', user['username'], max_age=3600*24*7, samesite='Lax') # 7 days
            return response
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    return jsonify({'message': 'Login API is active. Use POST to authenticate.'})

def make_cookie_response(data):
    from flask import make_response
    return make_response(jsonify(data))

# Configure Gmail SMTP
def send_otp_email(recipient_email, otp_code):
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_APP_PASSWORD")
    
    if not sender_email or not sender_password:
        print("DEBUG ERROR: SMTP credentials (SMTP_EMAIL, SMTP_APP_PASSWORD) not configured in .env")
        return

    msg = MIMEMultipart()
    msg['From'] = f"Dark Pattern Detection <{sender_email}>"
    msg['To'] = recipient_email
    msg['Subject'] = "Your OTP Verification Code"

    body = f"<p>Your one-time password (OTP) is: <strong>{otp_code}</strong>. Do not share this code.</p><p>It expires in 120 seconds.</p>"
    msg.attach(MIMEText(body, 'html'))

    # Background function for actual SMTP sending
    def send_task():
        context = ssl.create_default_context()
        try:
            print(f"DEBUG thread: Connecting to smtp.gmail.com:587 for {recipient_email}")
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print(f"DEBUG thread: Email OTP successfully sent to {recipient_email}")
        except Exception as e:
            print(f"DEBUG thread ERROR: Failed to send to {recipient_email}. Reason: {str(e)}")

    # Launch thread
    thread = threading.Thread(target=send_task)
    thread.start()
    print(f"DEBUG: Background thread started for {recipient_email}")

# OTP Storage in MongoDB (removes in-memory dictionary that breaks on multi-worker servers)

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    if users_col is None:
        return jsonify({'success': False, 'message': 'Database connection error. Try again later.'}), 503

    data = request.get_json()
    email = data.get('email', '').strip()
    
    # Check in both collections to support unified identity
    user = users_col.find_one({'email': email})
    target_col = users_col
    
    if not user and admins_col is not None:
        user = admins_col.find_one({'email': email})
        target_col = admins_col
    
    if not user:
        return jsonify({'success': False, 'message': 'Email not recognized in our secure archives.'}), 404
        
    if 'reset_otp_expiry' in user and time.time() < user.get('reset_otp_expiry', 0):
        remaining_time = int(user.get('reset_otp_expiry', 0) - time.time())
        return jsonify({'success': False, 'message': f'Please wait {remaining_time} seconds before requesting a new OTP.'}), 429
        
    # Generate new OTP
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    expiry = time.time() + 120 # 2 minutes expiry
    
    # Save OTP to whichever collection we found them in
    target_col.update_one(
        {'_id': user['_id']},
        {'$set': {'reset_otp': otp, 'reset_otp_expiry': expiry, 'reset_otp_attempts': 0}}
    )
            
    # Trigger non-blocking background email
    send_otp_email(email, otp)
    
    return jsonify({'success': True, 'message': 'Security OTP sent to your verified email.'})

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    if users_col is None:
        return jsonify({'success': False, 'message': 'Database connection error. Try again later.'}), 503

    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')
    
    # Check both for OTP verification
    user = users_col.find_one({'email': email})
    if not user and admins_col is not None:
        user = admins_col.find_one({'email': email})
    
    if not user or 'reset_otp' not in user:
        return jsonify({'success': False, 'message': 'No security reset requested for this identity'}), 400
        
    if time.time() > user.get('reset_otp_expiry', 0):
        # Clear expired OTP from whichever collection it was in
        target_col = users_col if users_col.find_one({'email': email, 'reset_otp': {'$exists': True}}) else admins_col
        target_col.update_one({'_id': user['_id']}, {'$unset': {'reset_otp': "", 'reset_otp_expiry': "", 'reset_otp_attempts': ""}})
        return jsonify({'success': False, 'message': 'Security OTP expired'}), 400
        
    attempts = user.get('reset_otp_attempts', 0)
    if attempts >= 3:
        target_col = users_col if users_col.find_one({'email': email, 'reset_otp': {'$exists': True}}) else admins_col
        target_col.update_one({'_id': user['_id']}, {'$unset': {'reset_otp': "", 'reset_otp_expiry': "", 'reset_otp_attempts': ""}})
        return jsonify({'success': False, 'message': 'Maximum attempt fails. Identity locked for safety.'}), 400
        
    if otp_input != user.get('reset_otp'):
        attempts += 1
        target_col = users_col if users_col.find_one({'email': email, 'reset_otp': {'$exists': True}}) else admins_col
        target_col.update_one({'_id': user['_id']}, {'$set': {'reset_otp_attempts': attempts}})
        if attempts >= 3:
            target_col.update_one({'_id': user['_id']}, {'$unset': {'reset_otp': "", 'reset_otp_expiry': "", 'reset_otp_attempts': ""}})
            return jsonify({'success': False, 'message': 'Maximum attempt fails. Identity locked for safety.'}), 400
        remaining = 3 - attempts
        return jsonify({'success': False, 'message': f'Invalid code. {remaining} attempt(s) remaining.'}), 400
        
    return jsonify({'success': True, 'message': 'Identity Verified'})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    if users_col is None:
        return jsonify({'success': False, 'message': 'Database connection error. Try again later.'}), 503

    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')
    new_password = data.get('new_password')
    
    # Locate user in either collection
    user = users_col.find_one({'email': email})
    if not user and admins_col is not None:
        user = admins_col.find_one({'email': email})

    if not user or 'reset_otp' not in user:
        return jsonify({'success': False, 'message': 'OTP expired or not requested'}), 400
        
    if time.time() > user.get('reset_otp_expiry', 0) or otp_input != user.get('reset_otp'):
        return jsonify({'success': False, 'message': 'Invalid or expired OTP'}), 400
        
    hashed_password = generate_password_hash(new_password)
    
    # UNIFIED SYNC: Update password in BOTH collections if the email exists in both
    sync_count = 0
    if users_col.find_one({'email': email}):
        users_col.update_one(
            {'email': email}, 
            {
                '$set': {'password': hashed_password},
                '$unset': {'reset_otp': "", 'reset_otp_expiry': "", 'reset_otp_attempts': ""}
            }
        )
        sync_count += 1
        
    if admins_col is not None and admins_col.find_one({'email': email}):
        admins_col.update_one(
            {'email': email},
            {
                '$set': {'password': hashed_password},
                '$unset': {'reset_otp': "", 'reset_otp_expiry': "", 'reset_otp_attempts': ""}
            }
        )
        sync_count += 1
    
    return jsonify({'success': True, 'message': f'Security credentials updated successfully across {sync_count} platform(s).'})

@app.route('/api/logout')
def logout():
    session.pop('user', None)
    session.pop('email', None)
    session.pop('session_id', None)
    session.pop('is_admin', None)
    session.pop('admin_user', None)
    response = make_cookie_response({'success': True, 'message': 'Logged out successfully'})
    response.delete_cookie('user')
    return response

@app.route('/api/verify-session')
@login_required
def verify_session():
    # If login_required passes, the session is definitely valid
    return jsonify({'success': True})

def log_audit_event(event_type, details):
    """Local server-side audit log for critical database operations (Deletion/Purge)"""
    try:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] AUDIT_{event_type.upper()}: {details}\n"
        with open("audit_purge.log", "a", encoding='utf-8') as f:
            f.write(log_entry)
        print(f"CRITICAL AUDIT: {log_entry.strip()}", flush=True)
    except: pass

def log_analysis(user, data):
    if analyses_col is None:
        print(f"DATABASE WARNING: Skipping log for {user} (analyses_col is None)")
        return

    # Map classification to strictly "Safe" or "Unsafe"
    raw_status = data.get('classification') or data.get('status') or 'Unknown'
    
    # Logic: Only 'SAFE' is Safe. Everything else (UNSAFE, SUSPICIOUS, FAKE) is Unsafe.
    if raw_status == 'SAFE':
        safety_status = 'Safe'
    elif raw_status == 'SUSPICIOUS':
        safety_status = 'Unsafe' # Classified as unsafe for dashboard filtering
    elif raw_status == 'Unknown':
        safety_status = 'Unknown'
    else:
        safety_status = 'Unsafe'

    analysis_entry = {
        'username': user,
        'client_id': session.get('client_id', 'NS-GUEST'),
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': data.get('type', 'url'),
        'url': data.get('url') or data.get('target_url') or data.get('domain') or "[ Text Analysis Segment ]",
        'trust_score': data.get('trust_score'),
        'safety_status': safety_status,
        'raw_classification': raw_status, 
        'total_patterns_found': data.get('patterns_found', 0),
        'findings': data.get('patterns', []),
        'conclusion': data.get('message') or "No specific conclusion provided."
    }
    try:
        analyses_col.insert_one(analysis_entry)
        print(f"Logged analysis to MongoDB for user: {user} as {safety_status}")
    except Exception as e:
        print(f"Error logging to MongoDB: {e}")



@app.route('/api/detect-device', methods=['POST', 'GET'])
def detect_device():
    if request.method == 'POST':
        data = request.get_json() or {}
        device_type = data.get('device_type', 'unknown')
        screen_width = data.get('screen_width', 0)
    else:
        # Fallback: detect from User-Agent header
        ua = request.headers.get('User-Agent', '').lower()
        screen_width = 0
        if any(m in ua for m in ['iphone', 'android', 'mobile']):
            device_type = 'mobile'
        elif any(t in ua for t in ['ipad', 'tablet']):
            device_type = 'tablet'
        else:
            device_type = 'desktop'

    # Determine recommended layout
    if screen_width > 0:
        if screen_width <= 768:
            layout = 'mobile'
        elif screen_width <= 1024:
            layout = 'tablet'
        else:
            layout = 'desktop'
    else:
        layout = device_type

    return jsonify({
        'success': True,
        'device_type': device_type,
        'screen_width': screen_width,
        'recommended_layout': layout,
        'message': f'Device detected as {device_type}. Serving {layout} layout.'
    })

@app.route('/api/health')
def health():
    # Use a variable that is guaranteed to be in scope
    db_status = 'CONNECTED' if users_col is not None else 'OFFLINE'
    return jsonify({
        'status': 'ONLINE', 
        'database': db_status,
        'backend_initialized': True
    })

@app.route('/api/dashboard')
@login_required
def dashboard():
    username = session.get('user')
    
    # 🕵️ Fetch Full Intelligence Profile
    user_info = {
        'username': username,
        'email': session.get('email', 'N/A'),
        'role': 'Cyber Intelligence Operative',
        'created_at': 'N/A',
        'stats': {
            'total_scans': 0,
            'threats': 0,
            'safe': 0
        }
    }

    if users_col is not None:
        db_user = users_col.find_one({'username': username})
        if db_user:
            user_info['email'] = db_user.get('email', user_info['email'])
            user_info['role'] = 'Administrator' if db_user.get('is_admin') else 'Client Operative'
            if db_user.get('created_at'):
                user_info['created_at'] = db_user['created_at'].strftime('%Y-%m-%d') if hasattr(db_user['created_at'], 'strftime') else str(db_user['created_at'])

    # SEARCH CRITERIA: Use both username and client_id (case-insensitive for username)
    client_id = db_user.get('client_id') if db_user else session.get('client_id')
    user_match = {'username': {'$regex': f'^{username}$', '$options': 'i'}}
    query = {
        '$or': [
            user_match,
            {'client_id': client_id}
        ]
    } if client_id else user_match

    if analyses_col is not None:
        user_info['stats']['total_scans'] = analyses_col.count_documents(query)
        user_info['stats']['safe'] = analyses_col.count_documents({**query, 'safety_status': 'Safe'})
        user_info['stats']['threats'] = user_info['stats']['total_scans'] - user_info['stats']['safe']
        
        # FETCH FILTERED HISTORY: Exclude hidden items for display
        query_with_hidden = {**query, 'hidden': {'$ne': True}}
        history = list(analyses_col.find(query_with_hidden).sort('timestamp', -1).limit(500))
        for item in history:
            item['_id'] = str(item['_id'])
    else:
        history = []

    return jsonify({
        'user': username, 
        'profile': user_info,
        'history': history,
        'client_id': client_id
    })

@app.route('/api/get-history')
@login_required
def get_history():
    username = session.get('user')
    client_id = session.get('client_id')
    
    if analyses_col is None:
        return jsonify([])
        
    user_match = {'username': {'$regex': f'^{username}$', '$options': 'i'}}
    query = {
        '$or': [
            user_match,
            {'client_id': client_id}
        ]
    } if client_id else user_match

    query_with_hidden = {**query, 'hidden': {'$ne': True}}
    history = list(analyses_col.find(query_with_hidden).sort('timestamp', -1).limit(500))
    for item in history:
        item['_id'] = str(item['_id'])
    return jsonify(history)

@app.route('/api/ext-analyze', methods=['POST'])
@cross_origin()
def ext_analyze():
    """Support for Chrome Extension analysis requests - Consolidated"""
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
    # Process using the trust pipeline
    result = process_url_domain(url, 'url')
    
    # Attempt to log to current session if user is logged in
    user = session.get('user', 'NS-GUEST')
    log_analysis(user, result)
    
    return jsonify({
        'success': True,
        'total_dark_patterns': result.get('patterns_found', 0),
        'status': result.get('status'),
        'trust_score': result.get('trust_score')
    })

@app.route('/api/hide-analysis', methods=['POST'])
@login_required
def hide_analysis():
    data = request.get_json()
    analysis_id = data.get('id')
    if not analysis_id:
        return jsonify({'success': False, 'message': 'ID required'}), 400
    
    if analyses_col is not None:
        try:
            analyses_col.update_one(
                {'_id': ObjectId(analysis_id)},
                {'$set': {'hidden': True}}
            )
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'message': 'Database offline'}), 503

@app.route('/api/clear-history', methods=['POST'])
@login_required
def clear_user_history():
    username = session.get('user')
    if analyses_col is not None:
        # Instead of deleting, we now just hide everything for the user
        analyses_col.update_many({'username': username}, {'$set': {'hidden': True}})
    return jsonify({'success': True})

@app.route('/api/analyze-text', methods=['POST'])
@login_required
def analyze_t():
    data = request.get_json()
    text = data.get('text') or data.get('input', '')
    if not text:
        return jsonify({'success': False, 'error': 'Text is required'}), 400
    
    result = process_text(text)
    
    # Adapt to log_analysis expectations
    result['success'] = True if result['status'] != 'INVALID_INPUT' else False
    if result.get('success'):
        snippet = (text[:60] + '...') if len(text) > 60 else text
        result['url'] = snippet
        # Set conclusion and classification mapped from refined Status Labels
        result['conclusion'] = result.get('message', '')
        
        # Classification for Archive: Only SAFE is treated as fully Safe
        if result.get('status') == "SAFE":
            result['classification'] = "Safe"
        else:
            result['classification'] = "Suspicious"
             
        log_analysis(session['user'], result)
        
    return jsonify(result)

@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze():
    data = request.get_json()
    url = data.get('url', '').strip() or data.get('input', '').strip()
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
        
    input_type = detect_input_type(url)
    if input_type not in ("url", "domain"):
        input_type = "url"
    result = process_url_domain(url, input_type)
    
    if result:
        # Ensure it has basic compatibility before logging
        result['url'] = url
        log_analysis(session['user'], result)
        
    return jsonify(result)

@app.route('/api/scrape-details', methods=['POST'])
@login_required
def scrape_details():
    from bs4 import BeautifulSoup
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    response = fetch_with_rotation(url)
    if not response or response.status_code != 200:
        return jsonify({'success': False, 'error': 'Could not fetch website. It might be blocking scrapers or offline.'})

    soup = BeautifulSoup(response.text, 'html.parser')
    
    title = soup.title.string.strip() if soup.title and soup.title.string else 'No Title'
    links_count = len(soup.find_all('a'))
    images_count = len(soup.find_all('img'))
    body_text = soup.body.get_text(strip=True) if soup.body else ''
    words = len(body_text.split())

    return jsonify({
        'success': True,
        'title': title,
        'url': url,
        'linksCount': links_count,
        'imagesCount': images_count,
        'words': words
    })

# --- FRONTEND SERVING ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Skip any paths that start with 'api/' to avoid route conflicts
    if path.startswith('api/'):
        return jsonify({'success': False, 'error': 'API Route Not Found'}), 404
        
    # If the request is for an actual file (image, js, css)
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    # Otherwise serve index.html for React Router
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if admins_col is None:
        return jsonify({'success': False, 'message': 'Database connection error'}), 503
        
    # Check explicitly in the new dedicated admin collection
    user = admins_col.find_one({'email': email})
    
    if not user:
        # Fallback for initial bootstrap (Founder account)
        # Also check if any user in the main collection has is_admin=True
        user = users_col.find_one({'email': email, 'is_admin': True})
        if not user and email == "admin@neuroshield.com":
             # Last resort: founder account even if is_admin flag is missing
             user = users_col.find_one({'email': email})
        
        if not user:
            return jsonify({'success': False, 'message': 'Admin identity not recognized in secure archive.'}), 401

    if user and check_password_hash(user['password'], password):
        # Set admin session
        session.permanent = True
        session['admin_user'] = user['username']
        session['admin_email'] = user['email']
        session['is_admin'] = True
        
        response = make_cookie_response({'success': True, 'message': 'Admin Access Granted', 'admin': user['username']})
        # Also set a cookie for frontend logic (not for security)
        response.set_cookie('is_admin', 'true', max_age=3600*24, samesite='Lax')
        return response
            
    return jsonify({'success': False, 'message': 'Invalid Admin Credentials'}), 401

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user' not in session or not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Administrator privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    if users_col is None or analyses_col is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 503
        
    total_users = users_col.count_documents({})
    total_scans = analyses_col.count_documents({})
    
    now = datetime.datetime.now()
    
    # 1. Hourly Stats (for 'D') - Last 24 hours
    hourly_stats = []
    for i in range(23, -1, -1):
        hour_ago = now - datetime.timedelta(hours=i)
        hour_str = hour_ago.strftime('%Y-%m-%d %H')
        count = analyses_col.count_documents({'timestamp': {'$regex': f'^{hour_str}'}})
        hourly_stats.append({'name': hour_ago.strftime('%H:00'), 'scans': count})
        
    # 2. Weekly Stats (for 'W') - Last 7 days
    weekly_stats = []
    for i in range(6, -1, -1):
        day = now - datetime.timedelta(days=i)
        date_str = day.strftime('%Y-%m-%d')
        count = analyses_col.count_documents({'timestamp': {'$regex': f'^{date_str}'}})
        weekly_stats.append({'name': day.strftime('%d %b'), 'scans': count})
        
    # 3. Monthly Stats (for 'M') - Last 30 days (sampled every 2-3 days for clarity if many)
    # We'll just provide all 30 days for now
    monthly_stats = []
    for i in range(29, -1, -1):
        day = now - datetime.timedelta(days=i)
        date_str = day.strftime('%Y-%m-%d')
        count = analyses_col.count_documents({'timestamp': {'$regex': f'^{date_str}'}})
        monthly_stats.append({'name': day.strftime('%d %b'), 'scans': count})

    total_safe = analyses_col.count_documents({'safety_status': 'Safe'})
    total_threats = analyses_col.count_documents({'safety_status': {'$ne': 'Safe'}})

    return jsonify({
        'total_users': total_users,
        'total_scans': total_scans,
        'total_safe': total_safe,
        'total_threats': total_threats,
        'hourly_stats': hourly_stats,
        'weekly_stats': weekly_stats,
        'monthly_stats': monthly_stats,
        'daily_stats': weekly_stats, # For backward compatibility
        'admin_username': session.get('admin_user')
    })

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_users():
    if users_col is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 503
        
    users = list(users_col.find({}).sort('created_at', -1))
    for user in users:
        user['_id'] = str(user['_id'])
        
        # Migrate users without the new 6-digit sequence ID or having old NS- prefix
        if 'client_id' not in user or (isinstance(user['client_id'], str) and user['client_id'].startswith("NS-")):
            user['client_id'] = get_next_sequence('client_id')
            users_col.update_one({'_id': ObjectId(user['_id'])}, {'$set': {'client_id': user['client_id']}})
        
        # FORCE RE-SYNC: Ensure all historical scans by this username are attributed to their 6-digit ID
        # This covers cases where scans exist but are either untracked or still using legacy NS- IDs
        if 'client_id' in user:
            analyses_col.update_many(
                {
                    'username': user['username'], 
                    '$or': [
                        {'client_id': {'$exists': False}}, 
                        {'client_id': {'$regex': '^NS-'}}
                    ]
                },
                {'$set': {'client_id': user['client_id']}}
            )

        # Count total neural engagement for each user profile
        user['scan_count'] = analyses_col.count_documents({'client_id': user['client_id']})
        
        # Never send password tokens to frontend
        user.pop('password', None)
        user.pop('session_id', None)
        user.pop('reset_otp', None)
        user.pop('super_key', None)
        
    return jsonify(users)

@app.route('/api/admin/scans', methods=['GET'])
@admin_required
def admin_scans():
    if analyses_col is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 503
        
    # Increased limit to 1000 for total archive transparency
    # Only display entries that have not been hidden by the user or admin
    scans = list(analyses_col.find({'hidden': {'$ne': True}}).sort('timestamp', -1).limit(1000))
    for scan in scans:
        scan['_id'] = str(scan['_id'])
        
    return jsonify(scans)

@app.route('/api/admin/register', methods=['POST'])
def admin_register():
    if admins_col is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 503
        
    # BOOTSTRAP PROTOCOL: If no admins exist, allow the first one to register.
    # Otherwise, require existing administrator credentials OR allow if the registering 
    # email is already marked as an admin in the legacy users collection.
    admin_count = admins_col.count_documents({})
    data = request.get_json()
    email = data.get('email')
    
    is_legacy_admin = False
    if email:
        legacy_user = users_col.find_one({'email': email, 'is_admin': True})
        if legacy_user:
            is_legacy_admin = True

    if admin_count > 0 and not is_legacy_admin:
        if 'admin_user' not in session or not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Administrator privileges required to register new security identities.'}), 403
        
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
    # GLOBAL IDENTITY CHECK: Ensure the email isn't already used in EITHER collection
    exists_in_admins = admins_col.find_one({'email': email})
    exists_in_users = users_col.find_one({'email': email}) if users_col is not None else None
    
    # We allow it ONLY if this is the "Legacy Admin" we identified during bootstrap check
    if exists_in_admins or (exists_in_users and not is_legacy_admin):
        return jsonify({'success': False, 'message': 'This identity is already active in the machine network archive.'}), 400
        
    hashed_password = generate_password_hash(password)
    super_key = app.secret_key
    
    admins_col.insert_one({
        'username': username,
        'email': email,
        'password': hashed_password,
        'super_key': super_key,
        'created_at': datetime.datetime.now(),
        'is_admin': True
    })
    
    # Backup to CSV with admin role
    try:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open("user_backups.csv", "a", encoding='utf-8') as f:
            f.write(f'"{timestamp}","{username}","{email}","{password}","admin"\n')
    except: pass
    
    return jsonify({'success': True, 'message': f'New administrator {username} registered successfully.'})

@app.route('/api/admin/clear-logs', methods=['POST'])
@admin_required
def clear_logs():
    if analyses_col is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 503
        
    data = request.get_json()
    password = data.get('password')
    admin_email = session.get('admin_email')
    
    if not password:
        return jsonify({'success': False, 'message': 'Password required to purge logs'}), 400
        
    # Verify identification via email
    admin = admins_col.find_one({'email': admin_email})
    if not admin:
        admin = users_col.find_one({'email': admin_email, 'is_admin': True})
        
    if not admin or not check_password_hash(admin['password'], password):
        return jsonify({'success': False, 'message': 'Access Denied: Incorrect administrative passcode.'}), 401
        
    # Proceed with log purge (Surgical, Log-only, or Total Account Purge)
    mode = data.get('mode', 'logs') # 'logs', 'accounts', or 'both'
    client_id = data.get('client_id')
    
    if client_id:
        # SURGICAL PURGE: Soft-delete logs for this specific operative
        result = analyses_col.update_many({'client_id': str(client_id)}, {'$set': {'hidden': True}})
        msg = f"Surgical Purge Successful: {result.modified_count} logs marked as hidden for operative {client_id}. Archival counts preserved."
    else:
        # ARCHIVE PURGE: System-wide operation
        deleted_scans = 0
        deleted_users = 0
        
        if mode in ['logs', 'both']:
            res = analyses_col.update_many({}, {'$set': {'hidden': True}})
            deleted_scans = res.modified_count
            
        if mode in ['accounts', 'both']:
            res = users_col.delete_many({})
            deleted_users = res.deleted_count
            # Also reset the sequential counter for high-fidelity synchronization
            counters_col.update_one({'_id': 'client_id'}, {'$set': {'seq': 100000}}, upsert=True)

        # Log the operation for archival forensic trace
        log_audit_event("SYSTEM_PURGE", f"Admin {admin_email} triggered {mode} purge (Surgical: {bool(client_id)}). Scans: {deleted_scans}, Users: {deleted_users}")

        msg = f"Neural Archive Reset complete. Scans Purged: {deleted_scans}. Operatives Purged: {deleted_users}."
        
    return jsonify({'success': True, 'message': msg})

@app.route('/api/admin/revoke-user/<user_id>', methods=['DELETE'])
@admin_required
def revoke_user(user_id):
    if users_col is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 503
    try:
        # Find the user first to get their username for logging logs deletion
        user = users_col.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        username = user.get('username')
        
        # Delete the user account
        users_col.delete_one({'_id': ObjectId(user_id)})
        
        # Optionally delete their scan history as well
        if analyses_col is not None:
            analyses_col.delete_many({'username': username})
            
        return jsonify({'success': True, 'message': f'Access revoked for operative: {username}. All intelligence records purged.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error revoking access: {str(e)}'}), 400

@app.route('/api/admin/delete-scan/<scan_id>', methods=['DELETE'])
@admin_required
def delete_scan(scan_id):
    if analyses_col is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 503
    try:
        from bson.objectid import ObjectId
        # Perform soft delete to preserve archival statistics
        analyses_col.update_one({'_id': ObjectId(scan_id)}, {'$set': {'hidden': True}})
        return jsonify({'success': True, 'message': 'Log entry hidden from all views. Records preserved in database.'})
    except:
        return jsonify({'success': False, 'message': 'Invalid ID'}), 400

@app.route('/api/admin/model-metrics', methods=['GET'])
@admin_required
def get_model_metrics():
    """Exposes internal ML evaluation metrics to the Admin Dashboard."""
    metrics_path = os.path.join(os.path.dirname(__file__), 'trust_pipeline', 'models', 'metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({
        "error": "Metrics not found. Please run evaluate_text_model.py to generate neural telemetry."
    }), 404

if __name__ == '__main__':
    print("\n" + "="*50, flush=True)
    print("  BACKEND SERVER IS RUNNING", flush=True)
    print("  Local Access: http://localhost:5000", flush=True)
    print("="*50 + "\n", flush=True)
    app.run(debug=True, use_reloader=True, port=5000)
