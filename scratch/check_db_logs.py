import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("MONGO_URI")
client = MongoClient(uri)
db = client["dark-pattern-users"]
analyses = db["analyses"]
users = db["users"]

print(f"Total Users: {users.count_documents({})}")
print(f"Total Scans (All users): {analyses.count_documents({})}")

print("\n--- SAMPLE SCAN RECORDS (FULL FIELDS) ---")
for scan in analyses.find().limit(3):
    print(f"Record: {scan}")

print("\n--- USER IDENTITY DATA ---")
for user in users.find():
    username = user.get('username')
    email = user.get('email')
    count = analyses.count_documents({'username': username})
    print(f"User: '{username}', Email: '{email}', Scans Found: {count}")
    
    # Try case-insensitive search if 0 found
    if count == 0 and username:
        insensitive_count = analyses.count_documents({'username': {'$regex': f'^{username}$', '$options': 'i'}})
        if insensitive_count > 0:
            print(f"  [!] ALERT: Found {insensitive_count} scans using a case-variant of this username.")
