import requests
import re
from urllib.parse import urlparse
from trust_pipeline.config import REQUEST_TIMEOUT, TRUST_SCORE_LIKELY_SAFE, TRUST_SCORE_SUSPICIOUS

SHORTENERS = [
    'tinyurl.com', 'bit.ly', 't.co', 'cutt.ly', 'rb.gy', 
    'is.gd', 'shorturl.at', 'rebrand.ly', 'tiny.cc', 'ow.ly'
]

SUSPICIOUS_KEYWORDS = [
    'free', 'gift', 'reward', 'claim', 'win', 'urgent', 'verify', 
    'limited', 'offer', 'discount', 'login', 'update', 'account', 
    'cashback', 'bonus', 'coupon', 'secure', 'payment', 'bank', 
    'kyc', 'validation', 'alert', 'notice', 'official-update'
]

def internet_verify_official(user_input, domain=None):
    """
    Silent backend-only verification.
    """
    findings = []
    is_official = False
    status = "UNKNOWN"
    trust_score = 50
    message = "Inconclusive results from live network verification."

    target = domain or user_input
    if not domain:
        return {
            "status": status, "trust_score": trust_score, "message": message,
            "findings": findings, "is_official": is_official, "source": "internet_verification"
        }

    fetch_url = "https://" + domain
    try:
        resp = requests.get(fetch_url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        text = resp.text[:10000].lower()
        title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip().lower() if title_match else ""

        findings.append(f"Network check: Domain responded with status {resp.status_code}.")

        official_signals = ["official site", "official website", "copyright 2024", "privacy policy", "contact us"]
        suspicious_signals = [f" {kw} " for kw in SUSPICIOUS_KEYWORDS]

        official_score = sum(1 for sig in official_signals if sig in text or sig in title)
        suspicious_score = sum(1 for sig in suspicious_signals if sig in text or sig in title)

        if resp.status_code == 200 and official_score >= 2 and suspicious_score < 2:
            is_official = True
            status = "LIKELY_SAFE"
            trust_score = TRUST_SCORE_LIKELY_SAFE
            message = "Domain shows signs of traditional official residency."
        elif suspicious_score >= 3:
            status = "SUSPICIOUS"
            trust_score = 45
            message = "Live analysis detected high density of psychological trigger words."
            findings.append("Extreme density of scam-related keywords.")
        else:
            findings.append("No definitive official indicators found on target residence.")
    except Exception as e:
        error_msg = str(e).lower()
        if any(err in error_msg for err in ["nameresolutionerror", "failed to resolve", "not found"]):
            status = "FAKE"
            trust_score = 10
            message = "DNS resolution failed. Target does not exist on the public internet."
        else:
            status = "SUSPICIOUS"
            trust_score = 40
            message = "Network connection failed or was refused by target."

    return {
        "status": status, "trust_score": trust_score, "message": message,
        "findings": findings, "is_official": is_official, "source": "internet_verification"
    }

def analyze_url_rules(domain, normalized_url):
    """
    Comprehensive multi-layer URL structure analysis.
    """
    findings = []
    deductions = 0
    is_shortened = False
    
    if not domain:
        return {"risk_score": 0, "findings": findings, "is_shortened": False}

    # 1. Shortener Detection
    if domain.lower() in SHORTENERS:
        is_shortened = True
        deductions += 40
        findings.append("Shortened URL service detected (Hides destination).")

    # 2. Keyword Check (Full URL)
    from trust_pipeline.utils import ensure_scheme
    full_url = ensure_scheme(normalized_url) 
    lower_url = full_url.lower()
    found_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in lower_url]
    if found_keywords:
        risk_inc = len(found_keywords) * 12
        deductions += risk_inc
        findings.append(f"Suspicious terms found in URL: {', '.join(found_keywords)}.")

    # 3. Path & Parameter Analysis
    parsed = urlparse(full_url)
    path = parsed.path.lower()
    query = parsed.query.lower()
    
    deceptive_patterns = ["verify", "login", "account", "secure", "update", "billing", "payment"]
    for pattern in deceptive_patterns:
        if f"/{pattern}" in path:
            deductions += 20
            findings.append(f"Deceptive path segment detected: '/{pattern}'.")
        if f"{pattern}=" in query:
            deductions += 15
            findings.append(f"Sensitive query parameter found: '{pattern}='.")

    if len(path) > 50 and any(c.isdigit() for c in path):
        deductions += 10
        findings.append("Excessively long randomized path string (Common in phishing).")

    if domain.count("-") >= 2:
        deductions += 15
        findings.append("Domain contains excessive hyphens (Impersonation pattern).")

    # 4. Brand Impersonation
    popular_brands = ["amazon", "flipkart", "google", "paypal", "apple", "netflix", "microsoft", "facebook", "instagram"]
    for brand in popular_brands:
        if brand in domain.lower():
            official_check = any(domain.lower() == f"{brand}.{tld}" for tld in ["com", "in", "net", "org", "io"])
            if not official_check and not domain.lower().endswith(f".{brand}.com"):
                deductions += 55
                findings.append(f"Possible impersonation of trusted brand: '{brand}'.")

    return {
        "risk_score": deductions, 
        "findings": findings, 
        "is_shortened": is_shortened
    }
