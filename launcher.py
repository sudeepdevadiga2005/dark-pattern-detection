import sys
import os
import subprocess
import time
import requests
import getpass
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import check_password_hash

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
        db = client["dark-pattern-users"] 
        users_col = db["users"]
        
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

def main():
    clear_screen()
    print_banner()
    
    print("Welcome Guardian. Select Operation Mode:")
    print("1. \033[94m[CLIENT MODE]\033[0m - Standard detection interface")
    print("2. \033[93m[ADMIN COMMAND CENTER]\033[0m - Real-time statistics & user reports")
    print("q. Exit")
    
    choice = input("\nChoice > ").strip().lower()
    
    if choice == '1':
        print("\n\033[94m[✓] Initializing Client Portals... Setting up secure tunnel.\033[0m")
        subprocess.run(["npm", "run", "dev-client"], shell=True)
    
    elif choice == '2':
        print("\n\033[93m[✓] Redirecting to Neural Command Center Security Gateway in Chrome...\033[0m")
        import webbrowser
        webbrowser.open("http://localhost:5173/admin")
        subprocess.run(["npm", "run", "dev-admin"], shell=True)
            
    elif choice == 'q':
        sys.exit()
    else:
        print("\033[91mInvalid Choice.\033[0m")
        time.sleep(1)
        main()

if __name__ == "__main__":
    main()
