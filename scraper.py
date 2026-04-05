import os
import requests
from bs4 import BeautifulSoup
import urllib3
import pandas as pd
import re
import pickle
import glob

from duckduckgo_search import DDGS
import warnings
# Suppress the duckduckgo_search rename warning
warnings.filterwarnings("ignore", message="This package \(duckduckgo_search\) has been renamed to ddgs!")
import urllib.parse
try:
    import tldextract
    USE_TLD_EXTRACT = True
except ImportError:
    USE_TLD_EXTRACT = False
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

# Verified Official Brands (for typo-squatting / impersonation detection)
VERIFIED_DOMAINS = [
    # Global E-Commerce
    'amazon', 'ebay', 'temu', 'aliexpress', 'walmart', 'target',
    'wayfair', 'shein', 'ikea', 'bestbuy', 'homedepot', 'costco',
    'shopify', 'etsy', 'wish', 'noon',
    # Indian E-Commerce & Retail
    'flipkart', 'shopclues', 'myntra', 'ajio', 'meesho', 'snapdeal',
    'nykaa', 'reliance', 'fabindia', 'tanishq', 'westside', 'pantaloons',
    'lifestyle', 'pepperfry', 'urban', 'firstcry', 'tatacliq', 'vijaysales',
    # Food & Delivery
    'zomato', 'swiggy', 'bigbasket', 'blinkit', 'zepto', 'dunzo',
    # Finance & Payments
    'phonepe', 'paytm', 'razorpay', 'cred', 'paypal', 'stripe',
    'gpay', 'mobikwik', 'freecharge',
    # Travel & Entertainment
    'ola', 'uber', 'makemytrip', 'goibibo', 'cleartrip', 'yatra',
    'bookmyshow', 'hotstar', 'spotify', 'youtube',
    # Social & Tech
    'apple', 'google', 'microsoft', 'netflix', 'facebook', 'instagram',
    'twitter', 'linkedin', 'github', 'whatsapp', 'telegram',
    'jio', 'airtel', 'vodafone', 'bsnl',
    # Sports & Events
    'iplt20', 'ipl', 'icc-cricket', 'bcci', 'fifa', 'nba', 'espncricinfo', 'cricbuzz',
    # Devices & Fashion
    'samsung', 'oneplus', 'realme', 'xiaomi', 'boat', 'noise',
    'puma', 'nike', 'adidas', 'decathlon', 'lenskart', 'mamaearth',
]

# Global Domain Whitelist Map (Domain -> Category)
DOMAIN_WHITELIST = {}

def load_all_domains():
    global DOMAIN_WHITELIST
    print("LOG: Initializing Domain Whitelist Engine...", flush=True)
    
    root_csv = "valid_domains.csv"
    if os.path.exists(root_csv):
        try:
            print(f"LOG: Loading primary dataset '{root_csv}'...", flush=True)
            with open(root_csv, mode='r', encoding='utf-8') as f:
                # Skip header
                header = f.readline()
                for line in f:
                    parts = line.strip().split(',', 1)
                    if len(parts) == 2:
                        DOMAIN_WHITELIST[parts[0].lower()] = parts[1]
            print(f"LOG: Loaded root CSV. Current active domains: {len(DOMAIN_WHITELIST)}", flush=True)
        except Exception as e:
            print(f"LOG ERROR: Failed to load {root_csv}: {e}", flush=True)

    folder_path = "valid_domain"
    if os.path.exists(folder_path):
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        for csv_file in csv_files:
            try:
                print(f"LOG: Loading supplemental dataset '{csv_file}'...", flush=True)
                with open(csv_file, mode='r', encoding='utf-8') as f:
                    f.readline() # Header
                    for line in f:
                        parts = line.strip().split(',', 1)
                        if len(parts) == 2:
                            DOMAIN_WHITELIST[parts[0].lower()] = parts[1]
            except Exception as e:
                print(f"LOG ERROR: Failed to load {csv_file}: {e}", flush=True)
    
    print(f"LOG: Whitelist Engine Online. Total active safe domains: {len(DOMAIN_WHITELIST)}", flush=True)

# Run initial load
load_all_domains()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_url(url):
    try:
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        meaningful_query = {k: v for k, v in query.items() if not k.lower().startswith(('utm_', 'session', 'sid', 'tracker', 'ref'))}
        clean_query = urllib.parse.urlencode(meaningful_query, doseq=True)
        return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, clean_query, ''))
    except:
        return url

def extract_domain(url):
    if USE_TLD_EXTRACT:
        ext = tldextract.extract(url)
        return f"{ext.domain}.{ext.suffix}".lower()
    else:
        domain = urllib.parse.urlparse(url).netloc.lower().split(':')[0]
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain

DOMAIN_BLACKLIST = {}
FULL_URL_BLACKLIST = {}

def load_fake_domains():
    global DOMAIN_BLACKLIST, FULL_URL_BLACKLIST
    print("LOG: Initializing Domain Blacklist Engine...", flush=True)
    root_csv = "updated_categories.csv"
    if os.path.exists(root_csv):
        try:
            print(f"LOG: Loading fake dataset '{root_csv}'...", flush=True)
            with open(root_csv, mode='r', encoding='utf-8') as f:
                # Attempt to find header columns via first line
                header = f.readline().lower().split(',')
                url_idx = -1
                cat_idx = -1
                for i, col in enumerate(header):
                    if 'url' in col: url_idx = i
                    if 'cat' in col: cat_idx = i
                
                if url_idx == -1: 
                    print("LOG ERROR: 'url' column not found in fake dataset.", flush=True)
                    return

                count_domains = 0
                count_urls = 0
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) <= url_idx: continue
                    
                    url = parts[url_idx].strip().lower()
                    cat = parts[cat_idx].strip() if cat_idx != -1 and len(parts) > cat_idx else 'General'
                    
                    if url:
                        FULL_URL_BLACKLIST[url] = cat
                        count_urls += 1
                        
                        # Faster domain extraction for pre-loading
                        # Instead of full extract_domain, let's just use urlparse if possible
                        try:
                            # Strip protocol for urlparse
                            temp = url
                            if "://" not in temp: temp = "http://" + temp
                            netloc = temp.split('://', 1)[1].split('/', 1)[0].split(':', 1)[0]
                            if netloc.startswith('www.'): netloc = netloc[4:]
                            domain = netloc.lower()
                            
                            if domain and domain not in DOMAIN_WHITELIST:
                                DOMAIN_BLACKLIST[domain] = cat
                                count_domains += 1
                        except: pass
                
                print(f"LOG: Loaded {count_domains} domains and {count_urls} exact URLs into Blacklist from {root_csv}.", flush=True)
        except Exception as e:
            print(f"LOG ERROR: Failed to load {root_csv}: {e}", flush=True)

load_fake_domains()

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

# Global cache for proxies
CACHED_PROXIES = []
LAST_PROXY_REFRESH = 0

def fetch_with_rotation(url):
    global CACHED_PROXIES, LAST_PROXY_REFRESH
    
    # Refresh proxies only if list is empty or older than 10 minutes
    if not CACHED_PROXIES or (time.time() - LAST_PROXY_REFRESH > 600):
        CACHED_PROXIES = get_free_proxies()
        LAST_PROXY_REFRESH = time.time()
        
    attempts = 0
    while attempts < 2: # Reduced attempts for faster turnaround
        current_ua = random.choice(USER_AGENTS)
        current_proxy = random.choice(CACHED_PROXIES) if CACHED_PROXIES and attempts > 0 else None
        headers = {'User-Agent': current_ua}
        try:
            # Reduced timeout slightly for 15-20sec total budget
            response = requests.get(url, headers=headers, proxies={"http": current_proxy, "https": current_proxy} if current_proxy else None, timeout=6, verify=False)
            if response.status_code == 200: return response
        except: pass
        attempts += 1
        if attempts < 2: time.sleep(0.5)
    return None

def get_web_intelligence(domain):
    intelligence = {
        'summary': "Unverified Domain: Low search volume or new entity.", 
        'reputation_score': 50, 
        'status': 'Unknown',
        'conclusion': "No definitive reports found. Proceed with caution on non-whitelisted domains."
    }
    try:
        # Optimized search query for fast consensus
        search_query = f'"{domain}" reviews scam fraud'
        # Reduced search results to speed up analysis
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=4))
        
        scam_k = ['scam', 'fake', 'fraud', 'dangerous', 'stole', 'money', 'phishing', 'unreliable', 'bad reviews', 'dont use', 'warn', 'suspicious']
        trust_k = ['official', 'safe', 'verified', 'trusted', 'legitimate', 'secure', 'authentic', 'genuine']
        
        scam_hits = []
        trust_hits = []
        
        for r in results:
            title = r.get('title', '')
            body = r.get('body', '')
            full_text = (title + " " + body).lower()
            
            # Simple summarizer selection
            if any(k in full_text for k in scam_k):
                scam_hits.append(f"{title}: {body[:150]}...")
            if any(k in full_text for k in trust_k):
                trust_hits.append(f"{title}: {body[:150]}...")
            
        if len(scam_hits) >= 2:
            intelligence = {
                'summary': f"THREAT PREDICTION: Search engine analysis found {len(scam_hits)} reports flagging this as a potential scam.",
                'reputation_score': max(5, 50 - (len(scam_hits) * 15)),
                'status': 'DANGER',
                'conclusion': f"Neural Forensic Scan confirmed multiple threat signals from internet sources. Key reports indicate: {scam_hits[0]}"
            }
        elif len(trust_hits) >= 3:
            intelligence = {
                'summary': "TRUSTED SOURCE: External intelligence identifies this as a legitimate entity.",
                'reputation_score': min(90, 50 + (len(trust_hits) * 10)),
                'status': 'SAFE',
                'conclusion': f"Verified by search engine consensus as a legitimate entity. External reports: {trust_hits[0]}"
            }
        elif any(k in domain.lower() for k in ['official', 'safe', 'verified']):
            intelligence['reputation_score'] = 75
    except Exception as e:
        print(f"WEB INTEL ERROR: {e}")
    return intelligence

# TLDs almost exclusively used for phishing / spam sites
SUSPICIOUS_TLDS = {
    'club', 'xyz', 'tk', 'ml', 'ga', 'cf', 'gq', 'pw', 'top', 'icu',
    'buzz', 'surf', 'rest', 'fun', 'site', 'online', 'store', 'live',
    'click', 'link', 'tech', 'vip', 'win', 'bid', 'loan', 'trade',
    'review', 'stream', 'download', 'party', 'racing', 'accountant',
}

# Substrings often found in malicious/generic scam domains
SCAMMY_DOMAIN_KEYWORDS = {
    'online', 'shop', 'deal', 'discount', 'free', 'reward', 'claim', 'gift',
    'win', 'verify', 'update', 'login', 'account', 'security', 'official-update',
    'support', 'service', 'pay', 'billing', 'invoice', 'shipping', 'track'
}

def is_url_suspicious(url):
    try:
        # Pre-process: Ensure protocol exists for correct parsing
        temp_url = url
        if not re.match(r'^[a-z]+://', url, re.I):
            temp_url = 'https://' + url
            
        domain = extract_domain(temp_url)
        clean_target = temp_url.lower().strip()
        
        # Safe-guard for copy-pasting raw CSV lines into the dashboard by accident
        if ',' in clean_target:
            parts = clean_target.rsplit(',', 1)
            maybe_cat = parts[-1].strip()
            if maybe_cat in ['general', 'technology', 'finance', 'e-commerce', 'travel', 'news']:
                clean_target = parts[0].strip()
        
        # 0. Check Exact Full URL Blacklist Match (PRIORITY 0)
        # Prevents Verified Domains (like dropbox.com) from bypassing malicious payload links
        if clean_target in FULL_URL_BLACKLIST:
            return True, None, domain, FULL_URL_BLACKLIST[clean_target]
        
        # 1. Check Exact Whitelist Match (FAST)
        if domain in DOMAIN_WHITELIST:
            # 🎾 High-Fidelity Override: Force prominent sports domains to the Sports category
            # This corrects for technical mislabeling in the root CSV (e.g. iplt20.com)
            if domain == 'iplt20.com' or domain == 'ipl.com' or domain == 'icc-cricket.com':
                return False, None, domain, 'Sports'
            return False, None, domain, DOMAIN_WHITELIST[domain]
            
        # 1.5 Check Exact Blacklist Match (FAST)
        if domain in DOMAIN_BLACKLIST:
            return True, None, domain, DOMAIN_BLACKLIST[domain]
        
        # 2. Suspicious TLD Check — flag risky TLDs immediately
        tld = domain.rsplit('.', 1)[-1] if '.' in domain else ''
        if tld in SUSPICIOUS_TLDS:
            # Still try to identify what brand it's impersonating
            parts = re.split(r'[\.\-\/]', domain)
            ignore_words = {'com', 'net', 'org', 'in', 'co', 'uk', 'us', 'info', 'biz',
                           'www', 'gov', 'edu', 'http', 'https'} | SUSPICIOUS_TLDS
            for part in parts:
                if len(part) < 3 or part in ignore_words:
                    continue
                for brand in VERIFIED_DOMAINS:
                    sim = difflib.SequenceMatcher(None, brand, part).ratio()
                    if sim >= 0.75:
                        return True, f"{brand}.com", domain, None
            # Even if no brand match, the TLD itself is suspicious
            return True, None, domain, None
            
        # 3. Advanced Word-by-Word Brand Check
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
                            # It is a perfect, genuine brand match
                            return False, None, domain, "Verified Website"
                    else:
                        # It's a typo like "amaz0n"
                        return True, f"{brand}.com", domain, None
                        
        # 4. Generic Scammy Keywords in Domain
        scam_hit_count = sum(1 for k in SCAMMY_DOMAIN_KEYWORDS if k in domain.lower())
        if scam_hit_count >= 2:
            return False, None, domain, "Potential Scam Domain" # Flag for lower scoring

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
        (r'\b(hurry|limited|expires|today|urgency|fast|stock|countdown|only \d+ left|ends soon)\b', 'Urgency Messaging'),
        (r'\b(hidden|subscription|recurring|extra fee|charge|processing fee|convenience fee)\b', 'Hidden Costs'),
        (r'\b(i don\'t want to|no thanks i prefer|cancel is hard|call to cancel)\b', 'Confirmshaming / Difficult Cancellation'),
        (r'\b(must agree|mandatory|cannot skip|required to proceed)\b', 'Forced Action'),
        (r'\b(pre-selected|opt-out|checked by default|subscribe me)\b', 'Preselected Options / Misleading Design'),
        (r'\b(90% off|mega discount|free|zero cost|deal of the century|unbelievable price)\b', 'Unrealistic Price'),
        (r'\b(items? (?:still )?available|your cart|don\'t miss out|forget something)\b', 'Urgency / Cart Bait')
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

    if trust >= 70:
        classification = "Safe"
        sec_msg = "SAFE: No manipulative signals found. Safe to proceed."
    elif trust < 30:
        classification = "Scam"
        sec_msg = "URGENT THREAT: High likelihood of phishing or fraud."
    else:
        classification = "Suspicious"
        sec_msg = "CAUTION: Manipulative signals detected. Proceed carefully."

    # Final override for plain text impersonation
    if any(f['category'] == 'Brand Impersonation' for f in logic_findings):
        classification = "Fake"
        trust = min(trust, 25)
        sec_msg = "🚨 FAKE ALERT: Brand impersonation detected in text."

    return {
        'success': True,
        'type': 'text',
        'findings': logic_findings,
        'url_analysis': url_results,
        'trust_score': trust,
        'reasons': reasons,
        'classification': classification,
        'security_warning': sec_msg
    }

def detect_website_category(soup, url):
    content = ""
    if soup:
        if soup.title and soup.title.string:
            content += soup.title.string.lower() + " "
        for h in soup.find_all(['h1', 'h2', 'meta']):
            if h.name == 'meta' and h.get('name') == 'description':
                content += str(h.get('content', '')).lower() + " "
            elif h.name in ['h1', 'h2']:
                content += h.get_text().lower() + " "
        content += soup.get_text()[:2000].lower()
    else:
        content = url.lower()
        
    categories = {
        'E-Commerce': ['buy', 'cart', 'checkout', 'discount', 'sale', 'price', 'offer', 'shop', 'product', 'amazon', 'retail', 'flipkart'],
        'Banking/Finance': ['bank', 'account', 'loan', 'interest', 'credit card', 'payment', 'transaction', 'net banking', 'finance', 'wealth'],
        'Social Media': ['post', 'share', 'like', 'comment', 'follow', 'profile', 'message', 'feed', 'facebook', 'instagram', 'twitter'],
        'Technology': ['software', 'cloud', 'ai', 'electronics', 'devices', 'hardware', 'tech', 'app', 'computer', 'system', 'api', 'programming'],
        'Education': ['course', 'syllabus', 'exam', 'university', 'college', 'learning', 'tutorial', 'school', 'academy'],
        'Government': ['gov', 'ministry', 'scheme', 'public service', 'policy', 'registration', 'official portal'],
        'News/Media': ['news', 'headline', 'breaking', 'article', 'report', 'journalism', 'daily', 'times', 'bbc'],
        'Sports': ['match', 'score', 'team', 'player', 'cricket', 'football', 'tournament', 'ipl', 'sports', 'stadium'],
        'Entertainment': ['movie', 'show', 'video', 'music', 'celebrity', 'streaming', 'netflix', 'disney', 'cinema'],
        'Healthcare': ['hospital', 'clinic', 'medical', 'pharmacy', 'health', 'doctor', 'care', 'medicine'],
        'Travel': ['booking', 'flight', 'hotel', 'trip', 'tourism', 'destination', 'tour', 'holiday', 'vacation']
    }
    
    best_match = None
    max_hits = 0
    words = set(re.findall(r'\b[a-z]{3,}\b', content))
    
    for cat, keywords in categories.items():
        hits = sum(1 for k in keywords if k in content or k in words)
        if hits > max_hits:
            max_hits = hits
            best_match = cat
            
    if max_hits >= 2 or (not soup and max_hits >= 1):
        return best_match
    # 🕵️ Critical Audit Update: Do not return a generic category for unknown domains
    # This prevents the UI from mislabeling them as "Verified Official"
    return None

def analyze_url(url):
    try:
        url = url.strip()
        if not url.startswith(('http://', 'https://')): url = 'https://' + url
        cleaned_url = clean_url(url)
        
        reasons = []
        if cleaned_url != url:
            reasons.append("Normalized URL: removed unnecessary parameters and fragments.")
            
        # === STAGE 1: AUTHENTICITY ===
        suspicious, official, target, category = is_url_suspicious(cleaned_url)
        
        authenticity_status = "Unknown"
        if suspicious:
            authenticity_status = "Fake Domain"
        elif category:
            authenticity_status = "Verified Domain"
            
        is_ecommerce = False
        if category:
            is_ecommerce = category.lower() in ("e-commerce", "ecommerce", "shopping")
            reasons.append("Authenticity Check: Domain verified officially.")
        
        if suspicious: 
            reasons.append(f"Authenticity Check: Typo-Squatting detected. Host mimics {official} but originates from an unverified source.")
            
        web_intel = {'summary': '', 'reputation_score': 50}
        if not category and not suspicious:
            # Get external intelligence for unverified domains
            web_intel = get_web_intelligence(target)
            reasons.append(f"Authenticity Check (Intel): {web_intel['summary']}")
            if web_intel['reputation_score'] >= 70:
                authenticity_status = "Likely Official"
            elif web_intel['reputation_score'] < 45:
                authenticity_status = "Suspicious"
        
        # === STAGE 2: DARK-PATTERN DETECTION ===
        content_findings = []
        scraped_details = None
        dark_pattern_status = "None Detected"
        is_fallback = False
        
        # Initialize trust engine with neutral baseline
        trust = web_intel.get('reputation_score', 50)
        if authenticity_status in ["Fake Domain", "Fake", "Suspicious"]:
            dark_pattern_status = "Skipped"
            if not category:
                category = detect_website_category(None, target)
                is_ecommerce = category == "E-Commerce"
            reasons.append("Dark-Pattern Scan: Skipped due to unsafe / suspicious authenticity status.")
        else:
            # Live Scraping
            response = fetch_with_rotation(cleaned_url)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if not category:
                    category = detect_website_category(soup, target)
                    is_ecommerce = category == "E-Commerce"
                    reasons.append("Intelligent Detection: Online database content analyzed.")
                    
                res = analyze_text(soup.get_text()[:4000])
                content_findings = res['findings']
                
                scraped_details = {
                    'title': soup.title.string.strip() if soup.title and soup.title.string else 'No Title',
                    'linksCount': len(soup.find_all('a')),
                    'imagesCount': len(soup.find_all('img')),
                    'words': len(soup.body.get_text(strip=True).split()) if soup.body else len(soup.get_text(strip=True).split())
                }
                
                if content_findings:
                    # 🛡️ Neural Guard: Do not flag "Brand Impersonation" on WHITELISTED domains.
                    # This now correctly protects sites like iplt20.com (Matches by Whitelist Category)
                    # AND sites like google.com (Matches by Official Brand Tag).
                    if not suspicious and (official or category):
                        content_findings = [f for f in content_findings if (f['category'] != 'Brand Impersonation' or target == 'iplt20.com')]
                    
                    if content_findings:
                        dark_pattern_status = "Manipulative Patterns Found"
                        for f in content_findings:
                            reasons.append(f"Heuristic Match: Found '{f['category']}' manipulation tactic on page.")
                    else:
                        dark_pattern_status = "None Detected"
                        # Extra safeguard: Whitelisted domains should always have Low risk if no other patterns found
                        if not suspicious and (official or category):
                            trust = max(trust, 85)
                            classification = "Safe"
                else:
                    pass # Only output actual detected anomalies
            else:
                is_fallback = True
                dark_pattern_status = "Scan Failed/Blocked"
                if not category:
                    category = detect_website_category(None, target)
                    is_ecommerce = category == "E-Commerce"
                    reasons.append("Intelligent Detection (Fallback): Analyzed domain structure.")
                reasons.append("It have limited information, it did not have any much more information.")
            
        # === FINAL SCORING & CLASSIFICATION ===
        if suspicious:
            # Immediately lock trust to 0 — no further scoring can override this
            trust = 0
            impersonating = f" impersonating '{official}'" if official else ""
            reasons.append(f"🚨 FAKE SITE DETECTED: '{target}' is a phishing/scam domain{impersonating}.")
            reasons.append("⛔ Do NOT enter any personal details, passwords, or payment info on this site.")
        elif category:
            trust = 95  # Extremely high base trust for whitelisted domains
        else:
            trust = web_intel['reputation_score']
            
            # Penalize generic/scammy-sounding domains that aren't whitelisted
            scam_keywords_in_target = sum(1 for k in ['online', 'mart', 'easy', 'shop', 'deal', 'cheap'] if k in target.lower())
            if scam_keywords_in_target >= 2:
                trust -= 20
                reasons.append(f"Authenticity Check: Domain name contains generic marketing/scam keywords '{scam_keywords_in_target}'.")

            if is_fallback and trust >= 50:
                # Decrease confidence for fallback mode if no threat/category is known
                trust = min(trust, 55) # Lowered from 65 to keep it in Suspicious area
        
        # Deduct for content findings (only if not already flagged as fake)
        if not suspicious:
            penalty = sum(f['count'] * 12 for f in content_findings)
            trust -= penalty
            if authenticity_status in ["Official", "Verified Domain"] and penalty > 0:
                # Rule: Verified domain but heuristic scores indicate risk.
                # Reduce prediction confidence to prevent false positives, cap floor at 50 (Uncertain)
                trust = max(trust, 50)
        trust = max(0, int(trust))
        
        # Security message && Classification
        if trust >= 70:
            classification = "Safe"
            if category:
                security_msg = "✅ Verified Official Website"
            else:
                security_msg = "TRUSTED SOURCE: Safe to proceed."
        elif trust < 30:
            classification = "Scam"
            security_msg = "URGENT THREAT: High likelihood of phishing or fraud."
        else:
            classification = "Suspicious"
            if category:
                security_msg = "CAUTION: Verified domain, but contains manipulative/dark patterns."
            else:
                security_msg = "CAUTION: Result is partial or uncertain. Proceed carefully."

        # MANDATORY OVERRIDE FOR FAKE/PHISHING DOMAINS
        if suspicious:
            classification = "Fake"
            trust = 0
            security_msg = "⛔ DANGER: This is a FAKE/PHISHING site. Do NOT proceed."

        # === STRICT TRUST SCORE & RISK LEVEL ===
        # Ranges: Verified (85-95), Normal (70-85), Suspicious (40-70), Scam (<40)
        risk_level = "Low"
        if trust >= 85:
            risk_level = "Low"
            classification = "Safe"
        elif trust >= 70:
            risk_level = "Low"
            classification = "Safe"
        elif trust >= 40:
            risk_level = "Medium"
            classification = "Suspicious"
        else:
            risk_level = "High"
            classification = "Scam"

        # Step 2: Whitelist logic
        is_verified_like = False
        if (official or authenticity_status in ["Verified Domain", "Likely Official"]) and not suspicious:
            is_verified_like = True
            struc_auth = "Verified Domain"
            struc_conf = "High"
            # Ensure high base trust for verified domains as per strict rules
            trust = max(trust, 85)
            risk_level = "Low"
            classification = "Safe"
        # Step 3: Blacklist logic
        elif suspicious:
            is_verified_like = False
            struc_auth = "Unverified Domain"
            struc_conf = "High"
            risk_level = "High"
            classification = "Fake"
            trust = min(trust, 25)
        # Step 4: Intelligence fallback
        else:
            struc_auth = "Not in dataset"
            struc_conf = "Medium" if trust >= 50 else "Low"
        
        # FINAL STRICTURE: DO NOT penalize Sports/News for normal promotions
        if category in ["Sports", "News/Media"]:
            if trust < 70 and not suspicious:
                trust = 85
                risk_level = "Low"
                classification = "Safe"
                reasons.append("STRICT MODE: Normal promotions on sports/news content are NOT flagged as manipulation.")

        # Bundle the final comprehensive forensic payload
        return {
            'success': True,
            'type': 'url',
            
            # --- UPDATED STRICT FORMAT ---
            'is_verified_like': is_verified_like,
            'risk_level': risk_level,
            'status': classification,
            'trust_score': int(trust),
            'dark_patterns': [f['category'] for f in content_findings] if content_findings else [],
            'reasoning': reasons,
            # -----------------------------------
            
            # Maintain Legacy Compatibility
            'authenticity': struc_auth,
            'confidence': struc_conf,
            'url': cleaned_url,
            'official_url': official,
            'target_url': target,
            'is_ecommerce': is_ecommerce,
            'findings': content_findings,
            'reasons': reasons,
            'conclusion_from_internet': web_intel.get('conclusion') if not category and not suspicious else None,
            'classification': classification,
            'authenticity_status': authenticity_status,
            'dark_pattern_status': dark_pattern_status,
            'security_warning': security_msg,
            'scraped_details': scraped_details
        }
    except Exception as e:
        import traceback
        print(f"CRITICAL ANALYZER ERROR: {traceback.format_exc()}")
        return {'success': False, 'error': f"Neural Bridge Failure: {str(e)}"}
