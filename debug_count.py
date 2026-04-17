import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["dark-pattern-users"]
users_col = db["users"]
analyses_col = db["analyses"]

u_count = users_col.count_documents({})
a_count = analyses_col.count_documents({})
print(f"DEBUG: Users in DB: {u_count}")
print(f"DEBUG: Scans in DB: {a_count}")
