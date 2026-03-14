import os
import json
import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, make_response, send_from_directory
from flask_cors import CORS, cross_origin
from scraper import analyze_url, analyze_text, fetch_with_rotation
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from dotenv import load_dotenv
import random
import time
import smtplib
import ssl
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Configure folders for serving React
dist_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist')
app = Flask(__name__, static_folder=dist_folder)
app.secret_key = os.getenv("APP_SESSION_KEY", "default-secret-key-keep-it-safe")

# Broad CORS for production stability
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://web-production-caeac.up.railway.app",
    "http://web-production-caeac.up.railway.app"
])

# Session Configuration
app.config.update(
    SESSION_COOKIE_SAMESITE='Lax', 
    SESSION_COOKIE_SECURE=True,    # Enforce HTTPS on Railway
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
            session['user'] = user['username']
            session['session_id'] = new_session_id
            
            response = make_cookie_response({'success': True, 'user': user['username']})
            response.set_cookie('user', user['username'], max_age=3600*24, samesite='Lax') # 1 day
            return response
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    return jsonify({'message': 'Login API is active. Use POST to authenticate.'})

def make_cookie_response(data):
    from flask import make_response
    return make_response(jsonify(data))

# OTP STORAGE (In-memory for simplicity, or use a dedicated collection)
otps = {} 

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email', '').strip()
    user = users_col.find_one({'email': email})
    
    if not user:
        return jsonify({'success': False, 'message': 'Email not found'}), 404
        
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    expiry = time.time() + 120 # 2 minutes expiry
    
    otps[email] = {'otp': otp, 'expiry': expiry, 'attempts': 0}
    
    # Try sending email
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_APP_PASSWORD")
    
    if smtp_email and smtp_password and smtp_email != 'your_email@gmail.com':
        try:
            msg = MIMEMultipart()
            msg['From'] = f"Dark Pattern Detection <{smtp_email}>"
            msg['To'] = email
            msg['Subject'] = 'Your OTP Verification Code'
            body = f'Your one-time password (OTP) is: {otp}. Do not share this code.\n\nIt expires in 120 seconds.'
            msg.attach(MIMEText(body, 'plain'))
            
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(smtp_email, smtp_password)
                server.sendmail(smtp_email, email, msg.as_string())
            print(f"DEBUG: Email OTP sent to {email}")
            return jsonify({'success': True, 'message': 'OTP sent to email'})
        except Exception as e:
            print(f"EMAIL ERROR: {e}")
            return jsonify({'success': False, 'message': 'Failed to send email. Ensure SMTP is configured correctly.'}), 500
    else:
        # Fallback to demo mode if no email configured
        print(f"DEBUG: OTP for {email} is {otp}")
        return jsonify({'success': True, 'message': 'OTP generated (Email not configured, check console)', 'debug_otp': otp})

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')
    
    otp_data = otps.get(email)
    if not otp_data:
        return jsonify({'success': False, 'message': 'No OTP requested for this email'}), 400
        
    if time.time() > otp_data['expiry']:
        del otps[email]
        return jsonify({'success': False, 'message': 'OTP expired'}), 400
        
    if otp_data.get('attempts', 0) >= 3:
        del otps[email]
        return jsonify({'success': False, 'message': 'Maximum attempt fails. Please request a new OTP.'}), 400
        
    if otp_input != otp_data['otp']:
        otp_data['attempts'] = otp_data.get('attempts', 0) + 1
        if otp_data['attempts'] >= 3:
            del otps[email]
            return jsonify({'success': False, 'message': 'Maximum attempt fails. Please request a new OTP.'}), 400
        remaining = 3 - otp_data['attempts']
        return jsonify({'success': False, 'message': f'Invalid OTP. {remaining} attempt(s) remaining.'}), 400
        
    return jsonify({'success': True, 'message': 'OTP verified'})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')
    new_password = data.get('new_password')
    
    otp_data = otps.get(email)
    # Check attempts again just in case
    if not otp_data or time.time() > otp_data['expiry']:
        if email in otps:
            del otps[email]
        return jsonify({'success': False, 'message': 'OTP expired or not requested'}), 400
        
    if otp_data.get('attempts', 0) >= 3:
        del otps[email]
        return jsonify({'success': False, 'message': 'Maximum attempt fails. Please request a new OTP.'}), 400
        
    if otp_input != otp_data['otp']:
        otp_data['attempts'] = otp_data.get('attempts', 0) + 1
        if otp_data['attempts'] >= 3:
            del otps[email]
            return jsonify({'success': False, 'message': 'Maximum attempt fails. Please request a new OTP.'}), 400
        return jsonify({'success': False, 'message': 'Invalid OTP'}), 400
        
    hashed_password = generate_password_hash(new_password)
    users_col.update_one({'email': email}, {'$set': {'password': hashed_password}})
    
    del otps[email] # Clear OTP after use
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
    history = list(analyses_col.find({'username': username}).sort('timestamp', -1).limit(10))
    # Convert MongoDB objects to JSON-serializable format
    for item in history:
        item['_id'] = str(item['_id'])
    return jsonify({'user': username, 'history': history})

@app.route('/api/get-history')
@login_required
def get_history():
    username = session.get('user')
    history = list(analyses_col.find({'username': username}).sort('timestamp', -1).limit(10))
    for item in history:
        item['_id'] = str(item['_id'])
    return jsonify(history)

@app.route('/api/clear-history', methods=['POST'])
@login_required
def clear_user_history():
    username = session.get('user')
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

if __name__ == '__main__':
    app.run(debug=False, port=5000)
