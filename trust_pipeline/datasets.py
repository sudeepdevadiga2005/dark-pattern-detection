import os
import csv
from trust_pipeline.config import VERIFIED_CSV, FAKE_CSV
from trust_pipeline.utils import clean_surrounding_punctuation, extract_domain_from_anything, normalize_full_url

# Global Datasets
VERIFIED_DOMAINS = set()
FAKE_DOMAINS = {}
FAKE_URLS = {}

def load_datasets():
    """Load both datasets into memory on startup."""
    global VERIFIED_DOMAINS, FAKE_DOMAINS, FAKE_URLS
    VERIFIED_DOMAINS = load_verified_domains(VERIFIED_CSV)
    FAKE_DOMAINS, FAKE_URLS = load_fake_dataset(FAKE_CSV)

def load_verified_domains(csv_path):
    verified = set()
    if not os.path.exists(csv_path):
        print(f"[WARN] Verified CSV not found: {csv_path}")
        return verified
        
    print(f"[INFO] Loading verified domains from {csv_path}...")
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            
            # Use the most likely column that contains domains.
            value = row[0].strip().lower()
            if not value or value in ("domain", "url", "website"):
                continue
                
            cleaned = clean_surrounding_punctuation(value)
            domain = extract_domain_from_anything(cleaned)
            if domain:
                verified.add(domain)
    print(f"[INFO] Loaded {len(verified)} verified domains.")
    return verified

def load_fake_dataset(csv_path):
    fake_domains = {}
    fake_urls = {}
    if not os.path.exists(csv_path):
        print(f"[WARN] Fake CSV not found: {csv_path}")
        return fake_domains, fake_urls
        
    print(f"[INFO] Loading fake/suspicious domains from {csv_path}...")
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            normalized_row = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items()}
            
            raw_domain = normalized_row.get("domain") or normalized_row.get("website") or normalized_row.get("site") or ""
            raw_url = normalized_row.get("url") or normalized_row.get("exact_url") or ""
            category = normalized_row.get("category") or normalized_row.get("type") or "suspicious"

            if raw_domain:
                clean_domain = extract_domain_from_anything(raw_domain.lower())
                if clean_domain:
                    fake_domains[clean_domain] = category
            if raw_url:
                normalized_exact_url = normalize_full_url(raw_url)
                if normalized_exact_url:
                    fake_urls[normalized_exact_url] = category
                    
    print(f"[INFO] Loaded {len(fake_domains)} fake domains and {len(fake_urls)} fake exact URLs.")
    return fake_domains, fake_urls

def lookup_verified_domain(domain):
    if not domain:
        return False
    return domain.lower() in VERIFIED_DOMAINS

def lookup_fake_domain(domain):
    if not domain:
        return None
    return FAKE_DOMAINS.get(domain.lower())

def lookup_fake_exact_url(normalized_url):
    if not normalized_url:
        return None
    return FAKE_URLS.get(normalized_url)
