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
from scraper import analyze_url, analyze_text, fetch_with_rotation
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


# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Configure folders for serving React
dist_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist')
app = Flask(__name__, static_folder=dist_folder)
app.secret_key = os.getenv("APP_SESSION_KEY", "default-secret-key-keep-it-safe")

# Broad CORS for local ngrok demo and production stability
CORS(app, supports_credentials=True, origins=["*"])

# Session Configuration
app.config.update(
    SESSION_COOKIE_SAMESITE='Lax', 
    SESSION_COOKIE_SECURE=False,   # Set to False for local development over HTTP
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(days=7)
)

# MongoDB Setup - Build Safe
db = None
users_col = None
analyses_col = None

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI)
        db = client["dark-pattern-users"] 
        users_col = db["users"]
        analyses_col = db["analyses"]
        client.admin.command('ping')
        print("Database Connection: ONLINE (MongoDB Atlas)")
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
else:
    print("DATABASE WARNING: MONGO_URI not found. Database features will be disabled until configured.")

def close_db_connection():
    global client
    if 'client' in globals() and client:
        print("Closing Database Connection...")
        client.close()

atexit.register(close_db_connection)

@app.before_request
def log_session():
    # Helpful for debugging why login might "not work"
    print(f"--- Request: {request.method} {request.path} ---")
    print(f"Session State: {'LOGGED IN as ' + session['user'] if 'user' in session else 'GUEST'}")
    print(f"Origin: {request.headers.get('Origin')}")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or 'session_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
            
        # Verify if the current session_id matches the one in the database
        if users_col is not None:
            user = users_col.find_one({'username': session['user']})
            if not user or user.get('session_id') != session['session_id']:
                # The session_id in DB is different (meaning they logged in elsewhere)
                session.clear()
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

        if users_col.find_one({'$or': [{'username': username}, {'email': email}]}):
            return jsonify({'success': False, 'message': 'Username or Email already exists'}), 400
            
        hashed_password = generate_password_hash(password)
        
        # Save to MongoDB: Includes the super_key (which is the SECRET_KEY)
        users_col.insert_one({
            'username': username, 
            'email': email,
            'password': hashed_password,
            'super_key': super_key, 
            'created_at': datetime.datetime.now()
        })
        
        # Create CSV file backup: username, email, and RAW password. No super_key.
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            csv_file = "user_backups.csv"
            file_exists = os.path.isfile(csv_file)
            with open(csv_file, "a", encoding='utf-8') as f:
                if not file_exists:
                    f.write("Timestamp,Username,Email,Password\n")
                # Escaping commas by wrapping in quotes for basic CSV safety
                f.write(f'"{timestamp}","{username}","{email}","{password}"\n')
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
    session.pop('session_id', None)
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

    analysis_entry = {
        'username': user,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': data.get('type'),
        'url': data.get('url', 'N/A'),
        'trust_score': data.get('trust_score'),
        'safety_status': data.get('safety_status'),
        'total_patterns_found': data.get('total_patterns_found'),
        'findings': data.get('findings')
    }
    try:
        analyses_col.insert_one(analysis_entry)
        print(f"Logged analysis to MongoDB for user: {user}")
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
    return jsonify({'status': 'ONLINE', 'database': 'CONNECTED' if db else 'OFFLINE'})

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
    text = data.get('text')
    if not text:
        return jsonify({'success': False, 'error': 'Text is required'}), 400
    result = analyze_text(text)
    if result.get('success'):
        log_analysis(session['user'], result)
    return jsonify(result)

@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    result = analyze_url(url)
    if result.get('success'):
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
    
    # We add a fallback URL check since extensions pass raw URLs 
    result = analyze_url(url)
    
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
    
    if users_col is None:
        return jsonify({'success': False, 'message': 'Database connection error'}), 503
        
    user = users_col.find_one({'email': email})
    if user and check_password_hash(user['password'], password):
        # We check for explicitly 'is_admin' field or a specific 'founder' email
        # To bootstrap the first admin, we allow a specific email if no is_admin field exists
        is_admin = user.get('is_admin', False) or (user.get('email') == "admin@neuroshield.com")
        
        if is_admin:
            # Set admin session
            session.permanent = True
            session['admin_user'] = user['username']
            session['is_admin'] = True
            
            response = make_cookie_response({'success': True, 'message': 'Admin Access Granted', 'admin': user['username']})
            # Also set a cookie for frontend logic (not for security)
            response.set_cookie('is_admin', 'true', max_age=3600*24, samesite='Lax')
            return response
        else:
            return jsonify({'success': False, 'message': 'Access Denied: You do not have administrator privileges'}), 403
            
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
    
    # Calculate daily scan frequency for the last 7 days (for Recharts)
    now = datetime.datetime.now()
    daily_stats = []
    for i in range(6, -1, -1):
        day = now - datetime.timedelta(days=i)
        date_str = day.strftime('%Y-%m-%d')
        # Match 'timestamp' string in database: '2026-03-22 20:30:27'
        # We use regex to match just the date part
        count = analyses_col.count_documents({
            'timestamp': {'$regex': f'^{date_str}'}
        })
        daily_stats.append({
            'name': day.strftime('%d %b'),
            'scans': count
        })
        
    return jsonify({
        'total_users': total_users,
        'total_scans': total_scans,
        'daily_stats': daily_stats
    })

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_users():
    if users_col is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 503
        
    users = list(users_col.find({}).sort('created_at', -1).limit(50))
    for user in users:
        user['_id'] = str(user['_id'])
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
        
    # Get last 100 scans for the logging view
    scans = list(analyses_col.find({}).sort('timestamp', -1).limit(100))
    for scan in scans:
        scan['_id'] = str(scan['_id'])
        
    return jsonify(scans)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  BACKEND SERVER IS RUNNING")
    print("  Local Access: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)
