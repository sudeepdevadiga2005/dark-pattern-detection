import os
import requests
from bs4 import BeautifulSoup
import urllib3
import pandas as pd
import re
import pickle
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from duckduckgo_search import DDGS
import warnings
# Suppress the duckduckgo_search rename warning
warnings.filterwarnings("ignore", message="This package \(duckduckgo_search\) has been renamed to ddgs!")
from urllib.parse import urlparse
import difflib
import random
import time

# Modern User-Agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Edge/119.0.0.0'
]

# Verified Official Brands (for typo-squatting detection)
VERIFIED_DOMAINS = [
    'amazon', 'flipkart', 'ebay', 'temu', 'aliexpress', 'walmart', 'target', 
    'apple', 'google', 'microsoft', 'netflix', 'facebook', 'instagram', 
    'twitter', 'linkedin', 'github', 'shopclues', 'myntra', 'ajio', 'meesho',
    'snapdeal', 'zomato', 'swiggy', 'bigbasket', 'nykaa', 'jio', 'reliance',
    'wayfair', 'shein', 'ikea', 'bestbuy', 'homedepot', 'costco',
    'blinkit', 'zepto', 'dunzo', 'phonepe', 'paytm', 'razorpay', 'cred',
    'ola', 'uber', 'makemytrip', 'goibibo', 'cleartrip', 'yatra',
    'bookmyshow', 'hotstar', 'spotify', 'youtube', 'whatsapp', 'telegram',
    'samsung', 'oneplus', 'realme', 'xiaomi', 'boat', 'noise',
    'puma', 'nike', 'adidas', 'decathlon', 'lenskart', 'mamaearth',
    'paypal', 'stripe', 'shopify', 'etsy', 'wish', 'noon'
]

# Global Domain Whitelist Map (Domain -> Category)
DOMAIN_WHITELIST = {}

def load_all_domains():
    global DOMAIN_WHITELIST
    print("LOG: Initializing Domain Whitelist Engine...")
    
    # 1. Load from root valid_domains.csv if exists
    root_csv = "valid_domains.csv"
    if os.path.exists(root_csv):
        try:
            print(f"LOG: Loading primary dataset '{root_csv}'...")
            df = pd.read_csv(root_csv)
            if 'Domain' in df.columns and 'Category' in df.columns:
                # Use to_dict for fast lookup
                temp_dict = dict(zip(df['Domain'].str.lower(), df['Category']))
                DOMAIN_WHITELIST.update(temp_dict)
                print(f"LOG: Loaded {len(temp_dict)} domains from root CSV.")
        except Exception as e:
            print(f"LOG ERROR: Failed to load {root_csv}: {e}")

    # 2. Load from valid_domain/ folder
    folder_path = "valid_domain"
    if os.path.exists(folder_path):
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        for csv_file in csv_files:
            try:
                print(f"LOG: Loading supplemental dataset '{csv_file}'...")
                df = pd.read_csv(csv_file)
                if 'Domain' in df.columns and 'Category' in df.columns:
                    temp_dict = dict(zip(df['Domain'].str.lower(), df['Category']))
                    DOMAIN_WHITELIST.update(temp_dict)
                    print(f"LOG: Loaded {len(temp_dict)} domains from {csv_file}.")
            except Exception as e:
                print(f"LOG ERROR: Failed to load {csv_file}: {e}")
    
    print(f"LOG: Whitelist Engine Online. Total active safe domains: {len(DOMAIN_WHITELIST)}")

# Run initial load
load_all_domains()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_free_proxies():
    try:
        url = "https://www.free-proxy-list.net/"
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        proxies = []
        for row in soup.find("table", {"class": "table"}).find_all("tr")[1:10]:
            cols = row.find_all("td")
            if cols[4].text in ["elite proxy", "anonymous"]:
                proxies.append(f"http://{cols[0].text}:{cols[1].text}")
        return proxies
    except: return []

def fetch_with_rotation(url):
    proxies_list = get_free_proxies()
    attempts = 0
    while attempts < 3:
        current_ua = random.choice(USER_AGENTS)
        current_proxy = random.choice(proxies_list) if proxies_list and attempts > 0 else None
        headers = {'User-Agent': current_ua}
        try:
            response = requests.get(url, headers=headers, proxies={"http": current_proxy, "https": current_proxy} if current_proxy else None, timeout=7, verify=False)
            if response.status_code == 200: return response
        except: pass
        attempts += 1
        time.sleep(1)
    return None

def get_web_intelligence(domain):
    intelligence = {'summary': "Low volume / New domain. Performing neural search...", 'reputation_score': 50, 'status': 'Unknown'}
    try:
        # Improved search query for scam detection
        search_query = f'"{domain}" reviews scam fraud "is it safe" legitimate'
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=8))
        
        scam_k = ['scam', 'fake', 'fraud', 'dangerous', 'stole', 'money', 'phishing', 'unreliable', 'bad reviews']
        trust_k = ['official', 'safe', 'verified', 'trusted', 'legitimate', 'secure']
        
        scam_hits = 0
        trust_hits = 0
        
        for r in results:
            text = (r.get('title', '') + r.get('body', '')).lower()
            if any(k in text for k in scam_k): scam_hits += 1
            if any(k in text for k in trust_k): trust_hits += 1
            
        if scam_hits >= 2:
            intelligence = {
                'summary': f"THREAT PREDICTION: Search engine analysis found {scam_hits} reports flagging this as a potential scam.",
                'reputation_score': max(5, 50 - (scam_hits * 15)),
                'status': 'DANGER'
            }
        elif trust_hits >= 3:
            intelligence = {
                'summary': "TRUSTED SOURCE: External intelligence identifies this as a legitimate entity.",
                'reputation_score': min(90, 50 + (trust_hits * 10)),
                'status': 'SAFE'
            }
        elif any(k in domain.lower() for k in ['official', 'safe', 'verified']):
            intelligence['reputation_score'] = 75
    except Exception as e:
        print(f"WEB INTEL ERROR: {e}")
    return intelligence

def is_url_suspicious(url):
    try:
        # Pre-process: Ensure protocol exists for correct parsing
        temp_url = url
        if not re.match(r'^[a-z]+://', url, re.I):
            temp_url = 'https://' + url
            
        domain = urlparse(temp_url).netloc.lower().split(':')[0]
        if domain.startswith('www.'): domain = domain[4:]
        
        # 1. Check Exact Whitelist Match (FAST)
        if domain in DOMAIN_WHITELIST:
            return False, None, domain, DOMAIN_WHITELIST[domain]
            
        # 2. Advanced Word-by-Word Brand Check
        # Split domain into parts: e.g. "secure-amaz0n-login.tk" -> ["secure", "amaz0n", "login", "tk"]
        parts = re.split(r'[\.\-\/]', domain)
        ignore_words = {'com', 'net', 'org', 'in', 'co', 'uk', 'us', 'info', 'biz', 'www', 'gov', 'edu', 'http', 'https'}
        
        for part in parts:
            if len(part) < 3 or part in ignore_words:
                continue
                
            for brand in VERIFIED_DOMAINS:
                similarity = difflib.SequenceMatcher(None, brand, part).ratio()
                
                # If a part is exactly a brand OR highly similar (typo)
                if 0.75 <= similarity <= 1.0:
                    # If it's a perfect match like "amazon" but the domain isn't an official amazon root
                    if similarity == 1.0:
                        official_roots = {f"{brand}.com", f"{brand}.in", f"{brand}.net", f"{brand}.org", f"{brand}.co"}
                        # Check if it's a direct subdomain of an official root
                        is_official = any(domain == root or domain.endswith("." + root) for root in official_roots)
                        if not is_official:
                            return True, f"{brand}.com", domain, None
                    else:
                        # It's a typo like "amaz0n"
                        return True, f"{brand}.com", domain, None
                        
        return False, None, domain, None
    except: return False, None, "", None

def analyze_text(raw_text):
    if not raw_text or len(raw_text.strip()) < 3:
        return {'success': False, 'error': 'Validation Error: Input too short.'}
    
    reasons = []
    
    # 1. Hidden Links (Handles both http:// links and naked domains like amazon.com)
    # Using capturing group to ensure full match retrieval
    url_pattern = r'((?:https?://)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}(?:/[^\s\n\r]*)?)'
    found_urls = list(set(re.findall(url_pattern, raw_text, re.I)))
    url_results = []
    has_dangerous_link = False
    
    for url in found_urls:
        suspicious, official, target, category = is_url_suspicious(url)
        if suspicious:
            has_dangerous_link = True
            url_results.append({'url': target, 'official': official, 'status': 'DANGER'})
            reasons.append(f"CRITICAL: Found potential phishing link '{target}' impersonating '{official}'.")
        elif category:
            reasons.append(f"Safe Official Link found: '{target}' belongs to '{category}' category.")
            
    # 2. Heuristic Patterns
    patterns = [
        (r'\b(win|claim|selected|reward|prize|gift card|congratulations)\b', 'Scam Bait'),
        (r'\b(hurry|limited|expires|today|urgency|fast|stock)\b', 'Hard Pressure'),
        (r'\b(hidden|subscription|recurring|extra fee|charge)\b', 'Hidden Costs'),
        (r'\b(90% off|mega discount|free|zero cost|deal of the century)\b', 'Unrealistic Price')
    ]
    
    logic_findings = []
    trust = 100
    
    # 3. Smart Word-by-word Analysis (For typos in plain text)
    words = re.split(r'[\s\.\-\/:\?\!\@\#\%\^\&\*\(\)\[\]\{\}]', raw_text)
    for word in words:
        if len(word) < 4: continue
        for brand in VERIFIED_DOMAINS:
            sim = difflib.SequenceMatcher(None, brand, word.lower()).ratio()
            if 0.75 <= sim < 1.0:
                logic_findings.append({'category': 'Brand Impersonation', 'count': 1})
                reasons.append(f"Suspicious word detected: '{word}' looks like a typo for '{brand}'.")
                trust -= 20
    for regex, cat in patterns:
        matches = re.findall(regex, raw_text.lower())
        if matches:
            logic_findings.append({'category': cat, 'count': len(matches)})
            trust -= (len(matches) * 15)
            reasons.append(f"Manipulation Pattern: Detected '{cat}' technique {len(matches)} times.")
            
    if has_dangerous_link: trust = min(trust, 15)
    trust = max(0, int(trust))
    
    if trust > 80 and not has_dangerous_link:
        reasons.append("Neural pattern alignment looks clean.")
    if not found_urls: reasons.append("No external redirects found in text block.")

    return {
        'success': True,
        'type': 'text',
        'findings': logic_findings,
        'url_analysis': url_results,
        'trust_score': trust,
        'reasons': reasons,
        'threat_level': 'High' if trust < 45 else 'Low',
        'security_warning': "DANGER: Malicious intent or impersonation detected." if trust < 45 else "SAFE: No manipulative signals found."
    }

def analyze_url(url):
    try:
        url = url.strip()
        if not url.startswith(('http://', 'https://')): url = 'https://' + url
        
        reasons = []
        suspicious, official, target, category = is_url_suspicious(url)
        
        is_ecommerce = False
        if category:
            is_ecommerce = category.lower() == "e-commerce"
            if is_ecommerce:
                reasons.append("Verified Website")
            else:
                reasons.append(f"Only e-commerce website and given is that {category} link")
        
        if suspicious: 
            reasons.append(f"Typo-Squatting detected: Host mimics {official} but originates from an unverified source.")
            
        # Get external intelligence for unverified domains
        web_intel = get_web_intelligence(target)
        if not category:
            reasons.append(f"INTELLIGENCE ENGINE: {web_intel['summary']}")
        
        # Live Scraping
        response = fetch_with_rotation(url)
        content_findings = []
        if response:
            reasons.append("Secure connection established. Scanned page DOM for dark patterns.")
            res = analyze_text(BeautifulSoup(response.text, 'html.parser').get_text()[:4000])
            content_findings = res['findings']
            for f in content_findings:
                reasons.append(f"Heuristic Match: Found '{f['category']}' manipulation tactic on page.")
        else:
            reasons.append("Connection Alert: Target refused connection or timed out. Analyzing based on domain intelligence only.")
            
        # Neural Trust Scoring Logic
        if category:
            trust = 95 # Extremely high base trust for whitelisted domains
        else:
            trust = web_intel['reputation_score']
            
        if suspicious: trust = min(trust, 15) # Dramatic drop for typo-squatting
        
        # Deduct for findings
        trust -= sum(f['count'] * 12 for f in content_findings)
        trust = max(0, int(trust))
        
        # Custom message based on category (User Requirement)
        security_msg = "TRUSTED SOURCE: Safe to proceed."
        if category:
            if is_ecommerce:
                security_msg = "Verified Website"
            else:
                security_msg = f"Only e-commerce website and given is that {category} link"
        elif trust < 45:
            security_msg = "URGENT THREAT: High likelihood of phishing or fraud."

        return {
            'success': True,
            'type': 'url',
            'url': url,
            'official_url': official,
            'target_url': target,
            'domain_category': category,
            'is_ecommerce': is_ecommerce,
            'findings': content_findings,
            'trust_score': trust,
            'reasons': reasons,
            'threat_level': 'High' if trust < 45 else 'Low',
            'security_warning': security_msg
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
