import re
from trust_pipeline.config import TRUST_SCORE_TEXT_LOW_RISK, TRUST_SCORE_TEXT_POTENTIALLY_SUSPICIOUS, TRUST_SCORE_TEXT_SUSPICIOUS

def analyze_text_input(text):
    """
    Dedicated text-only processing branch to identify dark patterns in textual data.
    Ensures raw strings don't leak into domain analyzers mistakenly.
    """
    cleaned = text.strip()
    lower_text = cleaned.lower()

    findings = []
    score = 0

    # Elevated heuristic regex patterns for sophisticated social engineering detection
    suspicious_patterns = [
        (r"\burgent\b", 12, "urgent"),
        (r"verify your account", 15, "verify your account"),
        (r"update payment", 15, "update payment"),
        (r"limited offer", 12, "limited offer"),
        (r"claim now", 12, "claim now"),
        (r"claim your reward", 15, "claim your reward"),
        (r"free.*gift card", 20, "free gift card promise"),
        (r"free reward", 15, "free reward"),
        (r"login immediately", 15, "login immediately"),
        (r"act now", 12, "act now urgency"),
        (r"expires at midnight", 15, "artificial expiration urgency"),
        (r"reply stop to opt[-\s]?out", 10, "automated SMS opt-out mimicry"),
        (r"confirm password", 20, "confirm password request"),
        (r"bank account", 10, "bank account reference"),
        (r"we['’]?ve selected you", 15, "random selection lottery scam pattern")
    ]

    for pattern, weight, label in suspicious_patterns:
        if re.search(pattern, lower_text):
            score += weight
            findings.append(f"Suspicious pattern detected: '{label}'")

    # Extract hidden or embedded URLs (often used to direct victims in SMS text scams)
    from trust_pipeline.utils import extract_domain_from_anything
    from trust_pipeline.datasets import lookup_verified_domain, lookup_fake_domain
    from trust_pipeline.verification import internet_verify_official
    
    urls_found = re.findall(r'(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?', cleaned)
    url_analysis = []
    
    if urls_found:
        valid_links = 0
        malicious_links = 0

        for u in urls_found:
            domain = extract_domain_from_anything(u)
            is_safe = False
            
            # Impersonation inference algorithm
            official_guess = "a legitimate secure service"
            if "amazon" in lower_text or "amzn" in u.lower():
                official_guess = "Amazon"
            elif "paypal" in lower_text:
                official_guess = "PayPal"
            elif "apple" in lower_text:
                official_guess = "Apple"
            elif "bank" in lower_text:
                official_guess = "your Financial Institution"
            
            if domain:
                if lookup_verified_domain(domain):
                    is_safe = True
                    official_guess = "Verified Official Domain"
                elif lookup_fake_domain(domain):
                    is_safe = False
                    malicious_links += 1
                else:
                    try:
                        v_res = internet_verify_official(u, domain=domain)
                        if v_res.get("status") in ("SAFE", "LIKELY_SAFE"):
                            is_safe = True
                            official_guess = "Verified Safe via Internet"
                        else:
                            malicious_links += 1
                    except Exception:
                        malicious_links += 1

            if is_safe:
                valid_links += 1
                url_analysis.append({
                    "url": u,
                    "official": official_guess,
                    "is_safe": True
                })
            else:
                url_analysis.append({
                    "url": u,
                    "official": official_guess,
                    "is_safe": False
                })

        if malicious_links > 0:
            score += 25
            findings.append(f"Contains strongly suspicious active links ({malicious_links})")
        elif valid_links > 0 and len(urls_found) == valid_links:
            findings.append(f"Embedded links verified as safe ({valid_links})")
            score = max(0, score - 15)

    if score >= 40:
        status = "SUSPICIOUS"
        trust_score = TRUST_SCORE_TEXT_SUSPICIOUS
        message = "This text closely matches high-risk phishing templates and social engineering tactics."
    elif score >= 15:
        status = "POTENTIALLY_SUSPICIOUS"
        trust_score = TRUST_SCORE_TEXT_POTENTIALLY_SUSPICIOUS
        message = "This text contains several suspicious signals and artificial urgency indicating a potential scam."
    else:
        # Prevent short randomly typed text like "qwerty" from attaining a safe score
        if len(lower_text) < 15 or len(cleaned.split()) < 3:
            status = "NOT_ENOUGH_DATA"
            trust_score = 0
            message = "Input is too short or lacks meaningful context for neural verification."
        else:
            status = "LOW_RISK_TEXT"
            trust_score = TRUST_SCORE_TEXT_LOW_RISK
            message = "No strong suspicious text patterns were detected."

    return {
        "status": status,
        "trust_score": trust_score,
        "message": message,
        "findings": findings,
        "source": "rule_engine_text",
        "is_official": None,
        "url_analysis": url_analysis,
        "type": "text"
    }
