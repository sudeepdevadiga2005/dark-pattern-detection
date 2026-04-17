import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("MONGO_URI")
client = MongoClient(uri)
user_db = client["dark-pattern-users"]
users_col = user_db["users"]
analyses_col = user_db["analyses"]

# Simulate /api/dashboard for 'sudeep'
username = 'sudeep'
print(f"--- Simulating Dashboard API for '{username}' ---")

db_user = users_col.find_one({'username': username})
if db_user:
    print(f"User found in DB: {db_user.get('username')}, Email: {db_user.get('email')}")
else:
    print("User NOT found in DB!")

history = list(analyses_col.find({'username': username}).sort('timestamp', -1).limit(500))
print(f"History items found: {len(history)}")

# Check for capitalization mismatch
insensitive_history = list(analyses_col.find({'username': {'$regex': f'^{username}$', '$options': 'i'}}))
print(f"Insensitive History items found: {len(insensitive_history)}")

# Check if scans are tied to client_id instead of username
if db_user and 'client_id' in db_user:
    client_id = db_user['client_id']
    id_history = list(analyses_col.find({'client_id': client_id}))
    print(f"History items found by client_id ({client_id}): {len(id_history)}")
