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
        if 'user' not in session or 'session_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
            
        # Verify if the current session_id matches the one in the database
        if users_col is not None:
            lookup_query = {'email': session['email']} if 'email' in session else {'username': session['user']}
            user = users_col.find_one(lookup_query)
            if not user or user.get('session_id') != session['session_id']:
                # The session_id in DB is different (meaning they logged in elsewhere)
                # Selective Path Isolation: Only clear client-level keys, leaving the administrative session intact.
                session.pop('user', None)
                session.pop('session_id', None)
                session.pop('email', None)
                session.pop('client_id', None)
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

        if users_col.find_one({'email': email}):
            return jsonify({'success': False, 'message': 'Email address already recorded in neural archive.'}), 400
            
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
        
        # Create CSV file backup: username, email, and RAW password. No super_key.
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            csv_file = "user_backups.csv"
            file_exists = os.path.isfile(csv_file)
            with open(csv_file, "a", encoding='utf-8') as f:
                if not file_exists:
                    f.write("Timestamp,Username,Email,Password,Role\n")
                # Escaping commas by wrapping in quotes for basic CSV safety
                f.write(f'"{timestamp}","{username}","{email}","{password}","client"\n')
        except Exception as e:
            print(f"BACKUP ERROR: {e}")

        return jsonify({'success': True, 'message': 'User created successfully'})
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
    user = users_col.find_one({'email': email})
    
    if not user:
        return jsonify({'success': False, 'message': 'Email not found'}), 404
        
    if 'reset_otp_expiry' in user and time.time() < user.get('reset_otp_expiry', 0):
        remaining_time = int(user.get('reset_otp_expiry', 0) - time.time())
        return jsonify({'success': False, 'message': f'Please wait {remaining_time} seconds before requesting a new OTP.'}), 429
        
    # Generate new OTP
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    expiry = time.time() + 120 # 2 minutes expiry
    
    # Save OTP to MongoDB first
    if users_col is not None:
        users_col.update_one(
            {'_id': user['_id']},
            {'$set': {'reset_otp': otp, 'reset_otp_expiry': expiry, 'reset_otp_attempts': 0}}
        )
            
    # Trigger non-blocking background email
    send_otp_email(email, otp)
    
    return jsonify({'success': True, 'message': 'OTP sent to your email.'})

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    if users_col is None:
        return jsonify({'success': False, 'message': 'Database connection error. Try again later.'}), 503

    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')
    
    user = users_col.find_one({'email': email})
    if not user or 'reset_otp' not in user:
        return jsonify({'success': False, 'message': 'No OTP requested for this email'}), 400
        
    if time.time() > user.get('reset_otp_expiry', 0):
        # Expiry reached, clear OTP data
        users_col.update_one({'_id': user['_id']}, {'$unset': {'reset_otp': "", 'reset_otp_expiry': "", 'reset_otp_attempts': ""}})
        return jsonify({'success': False, 'message': 'OTP expired'}), 400
        
    attempts = user.get('reset_otp_attempts', 0)
    if attempts >= 3:
        users_col.update_one({'_id': user['_id']}, {'$unset': {'reset_otp': "", 'reset_otp_expiry': "", 'reset_otp_attempts': ""}})
        return jsonify({'success': False, 'message': 'Maximum attempt fails. Please request a new OTP.'}), 400
        
    if otp_input != user.get('reset_otp'):
        attempts += 1
        users_col.update_one({'_id': user['_id']}, {'$set': {'reset_otp_attempts': attempts}})
        if attempts >= 3:
            users_col.update_one({'_id': user['_id']}, {'$unset': {'reset_otp': "", 'reset_otp_expiry': "", 'reset_otp_attempts': ""}})
            return jsonify({'success': False, 'message': 'Maximum attempt fails. Please request a new OTP.'}), 400
        remaining = 3 - attempts
        return jsonify({'success': False, 'message': f'Invalid OTP. {remaining} attempt(s) remaining.'}), 400
        
    return jsonify({'success': True, 'message': 'OTP verified'})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    if users_col is None:
        return jsonify({'success': False, 'message': 'Database connection error. Try again later.'}), 503

    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')
    new_password = data.get('new_password')
    
    user = users_col.find_one({'email': email})
    if not user or 'reset_otp' not in user:
        return jsonify({'success': False, 'message': 'OTP expired or not requested'}), 400
        
    if time.time() > user.get('reset_otp_expiry', 0) or otp_input != user.get('reset_otp'):
        users_col.update_one({'_id': user['_id']}, {'$unset': {'reset_otp': "", 'reset_otp_expiry': "", 'reset_otp_attempts': ""}})
        return jsonify({'success': False, 'message': 'Invalid or expired OTP'}), 400
        
    hashed_password = generate_password_hash(new_password)
    users_col.update_one(
        {'_id': user['_id']}, 
        {
            '$set': {'password': hashed_password},
            '$unset': {'reset_otp': "", 'reset_otp_expiry': "", 'reset_otp_attempts': ""}
        }
    )
    
    return jsonify({'success': True, 'message': 'Password reset successfully'})

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

def log_analysis(user, data):
    if analyses_col is None:
        print(f"DATABASE WARNING: Skipping log for {user} (analyses_col is None)")
        return

    # Map classification to strictly "Safe" or "Unsafe"
    raw_status = data.get('classification') or data.get('status') or 'Unknown'
    
    # Logic: Only 'Safe' is Safe. Everything else (Scam, Fake, Suspicious) is Unsafe.
    if raw_status == 'Safe':
        safety_status = 'Safe'
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
        'raw_classification': raw_status, # Preserve the original classification for detail
        'total_patterns_found': data.get('total_patterns_found') if data.get('total_patterns_found') is not None else data.get('total_patterns'),
        'findings': data.get('findings'),
        'conclusion': data.get('security_warning') or data.get('conclusion_from_internet') or "No specific conclusion provided."
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
    # Fetch history from MongoDB
    if analyses_col is None:
        return jsonify({'user': username, 'history': []})
        
    history = list(analyses_col.find({'username': username}).sort('timestamp', -1).limit(10))
    # Convert MongoDB objects to JSON-serializable format
    for item in history:
        item['_id'] = str(item['_id'])
    return jsonify({'user': username, 'history': history})

@app.route('/api/get-history')
@login_required
def get_history():
    username = session.get('user')
    if analyses_col is None:
        return jsonify([])
        
    history = list(analyses_col.find({'username': username}).sort('timestamp', -1).limit(10))
    for item in history:
        item['_id'] = str(item['_id'])
    return jsonify(history)

@app.route('/api/clear-history', methods=['POST'])
@login_required
def clear_user_history():
    username = session.get('user')
    if analyses_col is not None:
        analyses_col.delete_many({'username': username})
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
        # Set conclusion and classification mapped from status
        result['conclusion'] = result.get('message', '')
        result['classification'] = "Safe" if result.get('status') == "SAFE" or result.get('status') == "LOW_RISK_TEXT" else "Suspicious"
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
    
    # Adapt to log_analysis expectations
    result['success'] = True if result['status'] != 'INVALID_INPUT' else False
    if result.get('success'):
        if 'url' not in result: 
            result['url'] = result.get('normalized_url') or url
        # Define compatibility fields
        result['classification'] = "Safe" if result.get('status') in ("SAFE", "LIKELY_SAFE") else "Suspicious" if result.get('status') == "SUSPICIOUS" else "Unknown"
        result['security_warning'] = result.get('message', '')
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

@app.route('/api/ext-analyze', methods=['POST'])
@cross_origin()
def ext_analyze():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    input_type = detect_input_type(url)
    if input_type not in ("url", "domain"):
        input_type = "url"
    result = process_url_domain(url, input_type)
    result['success'] = True if result['status'] != 'INVALID_INPUT' else False
    # Optionally, we can log it with a dummy user 'extension_user'
    # if result.get('success'):
    #     log_analysis('extension_user', result)
        
    return jsonify(result)

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
    scans = list(analyses_col.find({}).sort('timestamp', -1).limit(1000))
    for scan in scans:
        scan['_id'] = str(scan['_id'])
        
    return jsonify(scans)

@app.route('/api/admin/register', methods=['POST'])
def admin_register():
    if admins_col is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 503
        
    # BOOTSTRAP PROTOCOL: If no admins exist, allow the first one to register.
    # Otherwise, require existing administrator credentials.
    admin_count = admins_col.count_documents({})
    if admin_count > 0:
        if 'admin_user' not in session or not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Administrator privileges required to register new security identities.'}), 403
        
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
    if admins_col.find_one({'email': email}):
        return jsonify({'success': False, 'message': 'Admin already exists'}), 400
        
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
        # SURGICAL PURGE: Only logs for this specific operative
        result = analyses_col.delete_many({'client_id': str(client_id)})
        msg = f"Surgical Purge Successful: {result.deleted_count} logs removed for operative {client_id}."
    else:
        # ARCHIVE PURGE: System-wide operation
        deleted_scans = 0
        deleted_users = 0
        
        if mode in ['logs', 'both']:
            res = analyses_col.delete_many({})
            deleted_scans = res.deleted_count
            
        if mode in ['accounts', 'both']:
            res = users_col.delete_many({})
            deleted_users = res.deleted_count
            # Also reset the sequential counter for high-fidelity synchronization
            counters_col.update_one({'_id': 'client_id'}, {'$set': {'seq': 100000}}, upsert=True)

        msg = f"Neural Archive Reset complete. Scans Purged: {deleted_scans}. Operatives Purged: {deleted_users}."
        
    return jsonify({'success': True, 'message': msg})

@app.route('/api/admin/delete-scan/<scan_id>', methods=['DELETE'])
@admin_required
def delete_scan(scan_id):
    if analyses_col is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 503
    try:
        from bson.objectid import ObjectId
        analyses_col.delete_one({'_id': ObjectId(scan_id)})
        return jsonify({'success': True, 'message': 'Log entry purged.'})
    except:
        return jsonify({'success': False, 'message': 'Invalid ID'}), 400

if __name__ == '__main__':
    print("\n" + "="*50, flush=True)
    print("  BACKEND SERVER IS RUNNING", flush=True)
    print("  Local Access: http://localhost:5000", flush=True)
    print("="*50 + "\n", flush=True)
    app.run(debug=True, port=5000)
