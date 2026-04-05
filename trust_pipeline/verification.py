import requests
import re
from trust_pipeline.config import REQUEST_TIMEOUT, TRUST_SCORE_LIKELY_SAFE, TRUST_SCORE_SUSPICIOUS

def internet_verify_official(user_input, domain=None):
    """
    Silent backend-only verification.
    This logic verifies domains over the internet for standard official structure
    without using commercial APIs to protect client privacy.
    """
    findings = []
    is_official = None
    status = "UNKNOWN"
    trust_score = 50
    message = "This input was not found in local datasets, and the external verification was inconclusive."

    target = domain or user_input
    if not domain:
        # If it's pure text, external verification uses a different approach or delegates back
        return {
            "status": status, "trust_score": trust_score, "message": message,
            "findings": findings, "is_official": is_official, "source": "internet_verification"
        }

    fetch_url = "https://" + domain
    try:
        resp = requests.get(fetch_url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        text = resp.text[:5000].lower()
        title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip().lower() if title_match else ""

        findings.append(f"Fetched homepage successfully with status {resp.status_code}.")

        official_signals = ["official site", "official website", "welcome to", "about us"]
        suspicious_signals = ["verify your account", "urgent action required", "claim reward", "update payment", "limited time only", "login now"]

        official_score = sum(1 for sig in official_signals if sig in text or sig in title)
        suspicious_score = sum(1 for sig in suspicious_signals if sig in text or sig in title)

        if resp.status_code == 200 and official_score >= 1 and suspicious_score == 0:
            is_official = True
            status = "LIKELY_SAFE"
            trust_score = TRUST_SCORE_LIKELY_SAFE
            message = "The input was not found in local datasets, but external verification suggests it may be official."
            findings.append("Official-style signals found on the fetched homepage.")
        elif suspicious_score >= 1:
            is_official = False
            status = "SUSPICIOUS"
            trust_score = TRUST_SCORE_SUSPICIOUS
            message = "The input was not found in local datasets, and external verification found suspicious signals."
            findings.append("Suspicious wording found on the fetched homepage.")
        else:
            findings.append("No strong official or suspicious signals were detected.")
    except Exception as e:
        findings.append(f"External verification failed: {str(e)}")

    return {
        "status": status, "trust_score": trust_score, "message": message,
        "findings": findings, "is_official": is_official, "source": "internet_verification"
    }

def analyze_url_rules(domain, normalized_url):
    """
    Applies pure rule-based evaluation of URL strings to identify suspicious patterns 
    like multiple hyphens or deceptive wording.
    """
    findings = []
    risk_score = 0
    if not domain:
        return {"risk_score": risk_score, "findings": findings}
        
    if domain.count("-") >= 2:
        risk_score += 15
        findings.append("Domain contains multiple hyphens.")
        
    suspicious_words = ["login", "verify", "secure", "update", "bonus", "reward", "claim"]
    lower_url = (normalized_url or "").lower()
    for word in suspicious_words:
        if word in lower_url:
            risk_score += 10
            findings.append(f"Suspicious term '{word}' found in URL.")
            
    return {"risk_score": risk_score, "findings": findings}
