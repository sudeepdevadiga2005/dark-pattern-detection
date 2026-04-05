import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Dataset paths
# Fallback to the provided CSV names if they exist in the root directory
VERIFIED_CSV = os.path.join(BASE_DIR, "valid_domains.csv")
FAKE_CSV = os.path.join(BASE_DIR, "updated_categories.csv")

# Connectivity config
REQUEST_TIMEOUT = 6

# Scoring constraints and Risk thresholds
TRUST_SCORE_VERIFIED = 98
TRUST_SCORE_FAKE_EXACT = 5
TRUST_SCORE_FAKE_DOMAIN = 10
TRUST_SCORE_LIKELY_SAFE = 75
TRUST_SCORE_SUSPICIOUS = 25
TRUST_SCORE_TEXT_LOW_RISK = 70
TRUST_SCORE_TEXT_POTENTIALLY_SUSPICIOUS = 45
TRUST_SCORE_TEXT_SUSPICIOUS = 20
