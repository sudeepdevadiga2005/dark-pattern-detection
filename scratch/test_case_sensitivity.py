import sys
import os

# Add the project root to sys.path to allow imports from trust_pipeline
sys.path.append(os.getcwd())

from trust_pipeline.pipeline import process_url_domain
from trust_pipeline.datasets import load_datasets

# Load datasets to populate VERIFIED_DOMAINS
load_datasets()


test_cases = [
    "amazon.com",
    "amazOn.com",
    "GOOGLE.COM",
    "google.com"
]

for tc in test_cases:
    print(f"\nTESTING: {tc}")
    result = process_url_domain(tc, 'url')
    print(f"Status: {result['status']}")
    print(f"Trust Score: {result['trust_score']}")
    print(f"Reasons: {result['reason']}")
