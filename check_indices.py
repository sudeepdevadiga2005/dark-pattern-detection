import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["dark-pattern-users"]
analyses_col = db["analyses"]

indices = analyses_col.index_information()
print("DEBUG: Indices on analyses collection:")
for name, info in indices.items():
    print(f"  {name}: {info}")
