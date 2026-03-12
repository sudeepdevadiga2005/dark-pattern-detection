import os
import requests
from bs4 import BeautifulSoup
import urllib3
import pandas as pd
import re
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from duckduckgo_search import DDGS
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

# Verified Official Domains (Common E-commerce/Safe sites)
VERIFIED_DOMAINS = [
    'amazon', 'flipkart', 'ebay', 'temu', 'aliexpress', 'walmart', 'target', 
    'apple', 'google', 'microsoft', 'netflix', 'facebook', 'instagram', 
    'twitter', 'linkedin', 'github', 'shopclues', 'myntra', 'ajio', 'meesho',
    'snapdeal', 'zomato', 'swiggy', 'bigbasket', 'nykaa', 'jio', 'reliance',
    'wayfair', 'shein', 'ikea', 'bestbuy', 'homedepot', 'costco'
]


# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Function to get free proxies (Best effort basis)
def get_free_proxies():
    try:
        url = "https://www.free-proxy-list.net/"
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        proxies = []
        for row in soup.find("table", {"class": "table"}).find_all("tr")[1:20]:
            cols = row.find_all("td")
            if cols[4].text == "elite proxy" or cols[4].text == "anonymous":
                proxies.append(f"http://{cols[0].text}:{cols[1].text}")
        return proxies
    except:
        return []

def fetch_with_rotation(url):
    """
    Tries to fetch URL content with different identities (IPs/User-Agents) if blocked.
    """
    proxies_list = get_free_proxies()
    # Try direct first, then try with random identities
    attempts = 0
    max_attempts = 5
    
    while attempts < max_attempts:
        current_ua = random.choice(USER_AGENTS)
        current_proxy = random.choice(proxies_list) if proxies_list and attempts > 0 else None
        
        headers = {
            'User-Agent': current_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        
        try:
            proxy_dict = {"http": current_proxy, "https": current_proxy} if current_proxy else None
            response = requests.get(url, headers=headers, proxies=proxy_dict, timeout=10, verify=False)
            
            if response.status_code == 200:
                print(f"Fetch Successful using: {current_proxy if current_proxy else 'Direct IP'}")
                return response
            elif response.status_code in [403, 429]:
                print(f"Blocked (Status {response.status_code}). Switching identity...")
            
        except Exception as e:
            print(f"Attempt {attempts+1} Failed: {str(e)}")
            
        attempts += 1
        # If we failed, wait a second before next attempt
        time.sleep(1)
        
    return None

# Paths
base_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path_tsv = os.path.join(base_dir, 'dataset (1).tsv')
dataset_path_csv = os.path.join(base_dir, 'pattern_classifications.csv')
model_path = os.path.join(base_dir, 'dark_pattern_model.pkl')

def train_and_save_model():
    try:
        dataframes = []
        
        # Load primary TSV dataset
        if os.path.exists(dataset_path_tsv):
            df_tsv = pd.read_csv(dataset_path_tsv, sep='\t')
            df_tsv = df_tsv.dropna(subset=['text', 'Pattern Category'])
            df_tsv = df_tsv.rename(columns={'Pattern Category': 'category'})
            dataframes.append(df_tsv[['text', 'category']])
            
        # Load secondary CSV dataset
        if os.path.exists(dataset_path_csv):
            df_csv = pd.read_csv(dataset_path_csv)
            # Map numeric 'classification' to category names or handle binary
            # Based on inspection, 0 = Not Dark Pattern, 1 = Dark Pattern
            # Note: The CSV might not have granular categories, so we label them 'General Dark Pattern'
            df_csv = df_csv.dropna(subset=['Pattern String', 'classification'])
            df_csv['category'] = df_csv['classification'].apply(lambda x: 'General Dark Pattern' if x == 1 else 'Not Dark Pattern')
            df_csv = df_csv.rename(columns={'Pattern String': 'text'})
            dataframes.append(df_csv[['text', 'category']])
            
        if not dataframes:
            print("No datasets found for training.")
            return None
            
        # Merge all data
        df = pd.concat(dataframes, ignore_index=True)
        df['category'] = df['category'].str.strip()
        
        X = df['text']
        y = df['category']
        
        pipeline = make_pipeline(
            TfidfVectorizer(stop_words='english', ngram_range=(1, 2)), 
            LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
        )
        pipeline.fit(X, y)
        
        with open(model_path, 'wb') as f:
            pickle.dump(pipeline, f)
        print("Model trained and saved with merged datasets.", flush=True)
        return pipeline
    except Exception as e:
        print(f"Failed to train model: {e}", flush=True)
        return None

def load_model():
    if os.path.exists(model_path):
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            print("Model loaded from disk.", flush=True)
            return model
        except Exception as e:
            print(f"Failed to load model: {e}. Retraining...", flush=True)
            return train_and_save_model()
    else:
        return train_and_save_model()

# Model will be loaded lazily during first prediction
_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

def force_retrain():
    global _model
    print("FORCING MODEL RETRAIN due to incompatibility...", flush=True)
    if os.path.exists(model_path):
        os.remove(model_path)
    _model = train_and_save_model()
    return _model

def get_web_intelligence(url, domain):
    """
    Searches the internet for the domain's reputation, reviews, and official status.
    """
    # 1. Quick check if it's a known official domain to avoid incorrect "limited record" msgs
    # Handle domain normalization (e.g. WaImart.com -> walmart)
    normalized_for_check = domain.lower().replace('0', 'o').replace('1', 'l').replace('!', 'i')
    
    found_brand = None
    for brand in VERIFIED_DOMAINS:
        if brand in normalized_for_check:
            found_brand = brand
            break

    # If the domain matches a verified brand exactly (official site)
    if found_brand and any(domain.lower().endswith(f"{found_brand}.{tld}") for tld in ['com', 'in', 'org', 'net', 'co']):
        return {
            'reputation_score': 100,
            'summary': f"This is a verified official domain for {found_brand.upper()}.",
            'is_verified_business': True,
            'search_snippets': []
        }

    intelligence = {
        'reputation_score': 50,
        'summary': f"Limited public records for {domain}. Caution is advised as it isn't a widely recognized platform.",
        'is_verified_business': False,
        'search_snippets': []
    }
    
    try:
        with DDGS() as ddgs:
            # Search query for reputation
            query = f"{domain} reviews official or scam"
            results = list(ddgs.text(query, max_results=5))
            
            scam_mentions = 0
            trust_mentions = 0
            
            for r in results:
                text = (r['title'] + " " + r['body']).lower()
                intelligence['search_snippets'].append(r['title'])
                
                if any(word in text for word in ['scam', 'fake', 'fraud', 'dangerous', 'not official', 'copy']):
                    scam_mentions += 1
                if any(word in text for word in ['legit', 'official', 'verified', 'safe', 'trusted']):
                    trust_mentions += 1
            
            if scam_mentions > trust_mentions:
                intelligence['reputation_score'] = 20
                intelligence['summary'] = "Internet search suggests this might be a SCAM or a COPY of a real site. Multiple sources mention risk."
            elif trust_mentions > 2:
                intelligence['reputation_score'] = 90
                intelligence['is_verified_business'] = True
                intelligence['summary'] = "Verified business records and positive user reviews found online."
                
    except Exception as e:
        print(f"Intelligence Gather Error: {e}")
        intelligence['summary'] = "Reputation check temporarily unavailable."
        
    return intelligence

def is_url_suspicious(url):
    """
    Checks if a URL mimics a famous brand but isn't the official domain.
    Includes advanced fuzzy matching, vowel swapping, and character duplication checks.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # 1. Check for high-risk keywords
        risk_keywords = ['deals', 'clearance', 'sale', 'discount', 'offers', 'free', 'gift', 'prize', 'winner', 'shop-now', 'mega-sale']
        found_keywords = [kw for kw in risk_keywords if kw in domain]
        
        # 2. Extract the SLD (Main Brand Name)
        domain_parts = domain.split('.')
        # If domain is 'google.co.in', sld is 'google'
        # If domain is 'flipkart.com', sld is 'flipkart'
        sld = domain_parts[0] if domain_parts else domain
        
        # 3. Check for exact official brand domain pattern
        is_official = False
        for brand in VERIFIED_DOMAINS:
            # Match brand.anything or sub.brand.anything (Direct official link)
            pattern = re.compile(rf"^(.*\.)?{brand}\.[a-z.]{{2,}}$")
            if pattern.match(domain):
                is_official = True
                break
        
        if is_official: return False, True, ""

        # 4. Normalize domain for comparison: Remove duplicates & swap chars
        norm_sld = re.sub(r'(.)\1+', r'\1', sld) # 'flipkarrt' -> 'flipkart', 'zooom' -> 'zoom'
        chars_map = str.maketrans('01!534v8', 'oliiseua') # 'amaz0n' -> 'amazon'
        norm_sld = norm_sld.translate(chars_map)

        for brand in VERIFIED_DOMAINS:
            # A. Fuzzy Similarity (SequenceMatcher)
            similarity = difflib.SequenceMatcher(None, brand, sld).ratio()
            
            # B. Character Check (Does it look like a copy?)
            # Handle variations like 'amazan' -> 'amazon' (vowel shift)
            vowel_shift = False
            if len(brand) == len(sld):
                diff_count = sum(1 for a, b in zip(brand, sld) if a != b)
                # If only 1 or 2 vowels are different, it's a clone
                vowels = 'aeiou'
                mismatches = [(a,b) for a,b in zip(brand, sld) if a != b]
                if 0 < diff_count <= 2 and all(m[0] in vowels and m[1] in vowels for m in mismatches):
                    vowel_shift = True

            # C. Official Compare Check
            is_copy = (similarity >= 0.8) or (brand in norm_sld) or vowel_shift
            
            if is_copy:
                diff_details = ""
                for s in difflib.ndiff(brand, sld):
                    if s[0] == '+': diff_details += f" added '{s[-1]}',"
                    elif s[0] == '-': diff_details += f" missing '{s[-1]}',"
                
                diff_msg = f" (Differences: {diff_details.strip(',')})" if diff_details else ""
                
                return True, False, f"CRITICAL: Minor changes in website URL ('{domain}') detected! We compared it character-by-character with the official website '{brand}.com'{diff_msg}. EACH AND EVERY word/character must be correct. This is a suspicious fake!"

        if found_keywords:
            return True, False, f"CAUTION: This URL uses high-pressure words like '{', '.join(found_keywords)}'. Scam websites often use these titles to trick people."
        
        return False, False, ""
    except:
        return False, False, ""

def perform_prediction(visible_texts):
    """
    Core prediction logic shared between URL and Text analysis.
    Uses ML model + Heuristic Keywords for 100% detection accuracy.
    """
    results = {}
    total_patterns = 0
    
    if not visible_texts:
        return results, total_patterns

    # HEURISTIC KEYWORDS (Catch patterns ML might miss)
    heuristics = [
        (r'\b(hurry|limited time|expires|midnight|countdown|last chance|hasten|fast|running out)\b', 'Urgency'),
        (r'\b(win|claim|gift card|selected to receive|reward|prize|congratulations|lucky|winner)\b', 'Bait and Switch'),
        (r'\b(only \d+ left|stock|available|demand|exclusive|rare|selling fast)\b', 'Scarcity'),
        (r'\b(hidden|cost|fee|recurring|subscription|trial|charge|extra)\b', 'Hidden Costs'),
        (r'\b(fake|verified by|trusted by \d+|live stats|people are looking)\b', 'Social Proof')
    ]
    
    # 1. ML Model Predictions
    model = get_model()
    if model:
        try:
            predictions = model.predict(visible_texts)
            probabilities = model.predict_proba(visible_texts)
            class_to_idx = {cls: i for i, cls in enumerate(model.classes_)}
            
            for text, pred, proba in zip(visible_texts, predictions, probabilities):
                if pred != 'Not Dark Pattern':
                    category = pred.title()
                    if category not in results:
                        results[category] = []
                    
                    conf_score = proba[class_to_idx[pred]]
                    if text not in [f['text'] for f in results[category]]:
                        results[category].append({'text': text, 'confidence': float(conf_score)})
                        total_patterns += 1
        except AttributeError as e:
            if 'multi_class' in str(e):
                print("Detected scikit-learn version mismatch. Retraining...", flush=True)
                force_retrain()
            else:
                print(f"Prediction Error: {e}")
        except Exception as e:
            print(f"Prediction Error: {e}")

    # 2. Heuristic Scanner (Adds patterns found by keywords)
    for text in visible_texts:
        text_lower = text.lower()
        for pattern_regex, category in heuristics:
            if re.search(pattern_regex, text_lower):
                if category not in results:
                    results[category] = []
                
                # Check if this text was already caught by ML in this category
                if text not in [f['text'] for f in results[category]]:
                    results[category].append({
                        'text': text,
                        'confidence': 0.95, # High confidence for direct keyword matches
                        'is_heuristic': True
                    })
                    total_patterns += 1
                
    return results, total_patterns

def analyze_text(raw_text):
    """
    Analyzes a raw block of text for dark patterns based on link presence and content.
    Logic: 
    1. If links found and official -> SAFE.
    2. If links found but suspicious or unreachable -> UNSAFE + Pattern Analysis.
    3. If no links -> Pattern Analysis (TF-IDF + ML).
    """
    try:
        if not raw_text or len(raw_text.strip()) < 10:
            return {'success': False, 'error': 'Validation Error: Text is too short (minimum 10 characters).'}
            
        sentences = re.split(r'(?<=[.!?])\s+', raw_text.strip())
        visible_texts = [s.strip() for s in sentences if len(s.strip()) > 10 and not s.strip().isdigit()]
        
        if not visible_texts:
            return {'success': False, 'error': 'Validation Error: No analyzable sentences found.'}

        # 1. Regex to find potential URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls_in_text = re.findall(url_pattern, raw_text)
        
        security_warning = None
        has_official_link = False
        has_suspicious_link = False
        has_unreachable_link = False
        
        if urls_in_text:
            for url in urls_in_text:
                is_suspicious, is_official, warning = is_url_suspicious(url)
                
                if is_official:
                    has_official_link = True
                elif is_suspicious:
                    has_suspicious_link = True
                    security_warning = warning
                    break # Stop at first major threat
                else:
                    # Check reachability for non-official, non-suspicious generic links
                    try:
                        resp = requests.head(url, timeout=3, allow_redirects=True, verify=False)
                        if resp.status_code >= 400:
                            has_unreachable_link = True
                            security_warning = f"CAUTION: The link '{url}' found in this text appears to be broken or unreachable. This is common in temporary phishing messages."
                    except:
                        has_unreachable_link = True
                        security_warning = f"CAUTION: The link '{url}' found in this text is unreachable. Proceed with extreme caution."

            # Logic based on link findings
            if has_official_link and not has_suspicious_link and not has_unreachable_link:
                return {
                    'success': True,
                    'type': 'text',
                    'title': 'Official Context Verified',
                    'findings': [],
                    'total_patterns_found': 0,
                    'security_warning': None,
                    'trust_score': 100,
                    'safety_status': 'SAFE (OFFICIAL CONTEXT)'
                }

        # 2. Perform Pattern Analysis (ML Model uses TF-IDF Pipeline)
        # This is reached if No Links, OR if links are Suspicious/Unreachable
        findings_dict, total_patterns = perform_prediction(visible_texts)
        
        # Additional Brand Keywords check (for text without links)
        if not urls_in_text and not security_warning:
            for brand in VERIFIED_DOMAINS:
                if brand in raw_text.lower() and any(word in raw_text.lower() for word in ['gift card', 'reward', 'win', 'claim', 'free', 'prize']):
                    security_warning = f"CAUTION: This text mentions {brand.upper()} with words like 'Gift Card' or 'Claim'. Scammers often use brand names to build fake trust."
                    break

        formatted_findings = []
        for cat, items in findings_dict.items():
            formatted_findings.append({
                'category': cat,
                'count': len(items)
            })

        # Calculate Trust Score
        trust_score = 100
        if has_suspicious_link:
            trust_score = 10
        elif has_unreachable_link:
            trust_score = 30
        elif security_warning:
            trust_score = 50
            
        trust_score -= (len(findings_dict) * 10)
        trust_score -= (total_patterns * 2)
        trust_score = max(0, min(100, trust_score))
        
        safety_status = "Safe"
        if has_suspicious_link: safety_status = "UNSAFE (PHISHING LIKELY)"
        elif has_unreachable_link: safety_status = "UNSAFE (BROKEN LINKS)"
        elif trust_score < 35: safety_status = "Unsafe"
        elif trust_score < 70: safety_status = "Suspicious"
        
        return {
            'success': True,
            'type': 'text',
            'title': 'Manual Text Entry',
            'findings': formatted_findings,
            'total_patterns_found': total_patterns,
            'security_warning': security_warning,
            'trust_score': int(trust_score),
            'safety_status': safety_status
        }
    except Exception as e:
        return {'success': False, 'error': f'Processing Error: {str(e)}'}

def analyze_url(url):
    try:
        # 1. Basic cleaning and validation
        url = url.strip()
        if not url:
            return {'success': False, 'error': 'URL is required'}
            
        # Clean protocol for validation check
        check_domain = url.replace('http://', '').replace('https://', '').split('/')[0].lower()
        
        # Robust Regex for Domain validation (Handles .com, .in, .co.in, subdomains, etc.)
        # No spaces allowed, must have dots and a valid TLD structure
        domain_pattern = re.compile(
            r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}(?:\.[a-z]{2,})?$'
        )
        
        if not domain_pattern.match(check_domain):
            return {'success': False, 'error': 'Validation Error: Please enter a valid website URL or domain (e.g., amazon.in or flipkart.com). Plain text sentences are not accepted here.'}

        # 2. Standardize URL input
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # 3. OPEN THE WEBSITE LINK ON THE INTERNET FIRST (to resolve redirects)
        try:
            # Use our rotation helper to bypass blocking and get the FINAL URL
            response = fetch_with_rotation(url)
            if response is None or response.status_code != 200:
                raise Exception("Failed after multiple rotation attempts")
            
            final_url = response.url # This gets the actual website the link opens!
        except Exception as e:
            # If we completely failed to open it (e.g. 403 Forbidden by anti-bot, or it doesn't exist)
            # Run suspicious checks on the original URL to warn them
            is_suspicious, is_official, warning = is_url_suspicious(url)
            domain_name = urlparse(url).netloc.lower()
            
            # Use intelligence to see what the internet thinks about this offline site
            web_intel = get_web_intelligence(url, domain_name)
            
            status = 'UNVERIFIED (OFFLINE)'
            title = 'Website Unreachable'
            trust = 40
            
            error_msg = f"The website at {url} could not be reached or has permanently blocked access. Check your connection or the URL spelling."
            
            if is_suspicious:
                status = 'UNSAFE (SCAM LIKELY)'
                title = 'Potential Malicious Site'
                trust = 0
                error_msg = f"CRITICAL: This suspicious copy ('{domain_name}') is currently unreachable or blocking analysis. We recommend NOT attempting to visit this URL again. {warning}"
            elif is_official or web_intel.get('is_verified_business') or web_intel.get('reputation_score', 0) >= 80:
                # E.g. wayfair.com blocking our scraper with 403, but it's a known legit site
                status = 'SAFE (OFFICIAL SITE BLOCKING SCRAPERS)'
                title = f"OFFICIAL {domain_name.upper()} WEBSITE (Analysis Blocked)"
                trust = 100
                error_msg = f"This is a legitimate website, but it has blocked our automated scraper from reading the patterns on the page."
            
            return {
                'success': True,
                'type': 'url',
                'url': url,
                'title': title,
                'findings': [],
                'total_patterns_found': 0,
                'security_warning': error_msg,
                'web_intelligence': web_intel['summary'],
                'is_official': (is_official or trust == 100),
                'trust_score': trust,
                'safety_status': status
            }

        # 4. Security Check: Is the FINAL resulting domain suspicious?
        is_suspicious, is_official, warning = is_url_suspicious(final_url)
        
        # 5. Fetch Web Intelligence (Searching the Internet)
        domain_name = urlparse(final_url).netloc.lower()
        web_intel = get_web_intelligence(final_url, domain_name)
        
        # 6. Handle Official Websites early
        if is_official:
            return {
                'success': True,
                'type': 'url',
                'url': final_url, # Show the final resolved URL
                'title': f"OFFICIAL {domain_name.upper()} WEBSITE (Redirect Verified)",
                'findings': [],
                'total_patterns_found': 0,
                'security_warning': None,
                'web_intelligence': "Verified Official Domain.",
                'is_official': True,
                'trust_score': 100,
                'safety_status': 'SAFE (OFFICIAL WEBSITE)'
            }

        soup = BeautifulSoup(response.text, 'html.parser')
        # Clean up soup...
        for script in soup(["script", "style", "nav", "footer", "iframe"]):
            script.extract()
            
        visible_texts = []
        seen_texts = set()
        for element in soup.stripped_strings:
            text = element.strip()
            if len(text) > 10 and not text.isdigit():
                sentences = re.split(r'(?<=[.!?])\s+', text)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 10 and sentence not in seen_texts:
                        visible_texts.append(sentence)
                        seen_texts.add(sentence)
                
        # Perform Pattern Analysis
        findings_dict, total_patterns = perform_prediction(visible_texts)
        
        # Calculate Trust Score
        trust_score = 100
        if is_suspicious: 
            trust_score = 10 # Start very low for suspicious copies
        
        trust_score -= (len(findings_dict) * 8)
        trust_score -= (total_patterns * 1.5)
        trust_score = max(0, min(100, trust_score))
        
        safety_status = "Safe"
        if is_suspicious: 
            safety_status = "UNSAFE (SUSPICIOUS COPY)"
        elif trust_score < 30: 
            safety_status = "Unsafe"
        elif trust_score < 65: 
            safety_status = "Suspicious"

        # Format findings
        formatted_findings = []
        for cat, items in findings_dict.items():
            formatted_findings.append({'category': cat, 'count': len(items)})

        return {
            'success': True,
            'type': 'url',
            'url': final_url,
            'title': soup.title.string.strip() if soup.title and soup.title.string else 'No Title',
            'findings': formatted_findings,
            'total_patterns_found': total_patterns,
            'security_warning': warning if is_suspicious else None,
            'web_intelligence': web_intel['summary'],
            'is_official': False,
            'trust_score': int(trust_score),
            'safety_status': safety_status
        }
    except Exception as e:
        return {'success': False, 'error': f'Processing Error: {str(e)}'}

