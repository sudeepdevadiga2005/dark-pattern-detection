import sys
import os
import subprocess
import time
import requests
import getpass
import json
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("""
    \033[96m====================================================
    \033[94m   ANTI-FRAUD DETECTION SYSTEM v2.0 - LAUNCHER
    \033[96m====================================================\033[0m
    """)

def login_admin():
    print("\n\033[93m[ADMIN SECURITY GATEWAY]\033[0m")
    email = input("Enter Admin Email: ").strip()
    
    print("\033[90m[Note: Visible password input enabled for compatibility]\033[0m")
    password = input("Enter Admin Password: ").strip()
    
    # Direct DB Check for Launcher
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("\033[91m[!] MONGO_URI not found. Please check your .env file.\033[0m")
        return False

    try:
        client = MongoClient(mongo_uri)
        # Check both admin and user databases for admin privileges
        admin_db = client["dark-pattern-admin"]
        admins_col = admin_db["admins"]
        
        user_db = client["dark-pattern-users"] 
        users_col = user_db["users"]
        
        # Check admins_col first
        user = admins_col.find_one({'email': email})
        if not user:
            # Fallback to users_col (Legacy/Initial)
            user = users_col.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            is_admin = user.get('is_admin', False) or (user.get('email') == "admin@neuroshield.com")
            if is_admin:
                print("\033[92m[✓] Access Granted. Identity Verified.\033[0m")
                return True
            else:
                print("\033[91m[!] Access Denied. User does not have Administrator privileges.\033[0m")
                return False
        else:
            print("\033[91m[!] Invalid Credentials. Access Denied.\033[0m")
            return False
    except Exception as e:
        print(f"\033[91m[!] Database Error: {e}\033[0m")
        return False

def register_admin():
    print("\n\033[95m[REGISTER NEW ADMINISTRATOR]\033[0m")
    email = input("Enter new Admin Email: ").strip()
    password = input("Enter new Admin Password: ").strip()
    
    if not email or not password:
        print("\033[91m[!] Email and Password cannot be empty.\033[0m")
        return
        
    mongo_uri = os.getenv("MONGO_URI")
    try:
        client = MongoClient(mongo_uri)
        # Save to both if needed, but primary administrative archive is dark-pattern-admin
        admin_db = client["dark-pattern-admin"] 
        admins_col = admin_db["admins"]
        
        # Check if user already exists
        if admins_col.find_one({'email': email}):
            print("\033[91m[!] An account with this email already exists in admin archive.\033[0m")
            return
            
        hashed_password = generate_password_hash(password)
        
        admins_col.insert_one({
            'username': 'ADMIN OF DARK PATERN DETECTION',
            'name': 'ADMIN OF DARK PATERN DETECTION',
            'email': email,
            'password': hashed_password,
            'is_admin': True,
            'created_at': datetime.datetime.now()
        })
        print("\033[92m[✓] Administrator 'ADMIN OF DARK PATERN DETECTION' registered successfully!\033[0m")
        
    except Exception as e:
        print(f"\033[91m[!] Database Error: {e}\033[0m")

def is_server_running():
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=1)
        return response.status_code == 200
    except:
        return False

def main():
    clear_screen()
    print_banner()
    
    server_online = is_server_running()
    
    if server_online:
        print("\n\033[93m[!] Operational Clusters already online.\033[0m Re-synchronizing dashboard...")
        import webbrowser
        webbrowser.open("http://localhost:5173/") # Open Client
        webbrowser.open("http://localhost:5174/") # Open Admin
    else:
        print("\n\033[94m[✓] INITIALIZING FULL SYSTEM CLUSTERS (RE-STARTING ENGINE)...\033[0m")
        print("\033[90m[Note: Initializing ML model and secure database tunnel. Estimated time: 8s]\033[0m")
        
        # High-Velocity Automatic Startup
        if os.name == 'nt':
            # Use cmd /c to ensure npm run dev-all is executed directly
            cmd = 'npm run dev-all'
            subprocess.Popen(f'start cmd /k "{cmd}"', shell=True)
        else:
            subprocess.Popen(["npm", "run", "dev-all"])
            
        print("\n\033[92m[✓] Neural Pulse Sent. Monitoring Startup Sequence...\033[0m")
        
        # Wait and verify
        for i in range(15):
            time.sleep(1)
            if is_server_running():
                print("\n\033[92m[✓] ALL SYSTEM CHANNELS: ONLINE\033[0m")
                print("\033[96mClient Console: http://localhost:5173/\033[0m")
                print("\033[93mAdmin Dashboard: http://localhost:5174/\033[0m")
                print("\n\033[90mLauncher exiting... Clusters remain active in the new window.\033[0m")
                break
            if i == 14:
                print("\n\033[93m[!] Pulse Delay: Server is still initializing. Check terminal logs.\033[0m")
                
    time.sleep(2)
    sys.exit()

if __name__ == "__main__":
    main()
