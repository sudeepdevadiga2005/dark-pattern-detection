from trust_pipeline.utils import detect_input_type, extract_domain_from_anything, normalize_full_url
from trust_pipeline.datasets import (
    lookup_verified_domain,
    lookup_fake_domain,
    lookup_fake_exact_url,
    VERIFIED_DOMAINS
)
from trust_pipeline.verification import internet_verify_official, analyze_url_rules
from trust_pipeline.text_analyzer import analyze_text_input
import difflib

def analyze_input(user_input):
    original_input = user_input.strip() if user_input else ""
    input_type = detect_input_type(original_input)

    if input_type == "invalid":
        return {
            "status": "INVALID_INPUT",
            "trust_score": 0,
            "message": "Please enter a valid URL, domain, or meaningful text.",
            "findings": []
        }

    if input_type in ("url", "domain"):
        return process_url_domain(original_input, input_type)
    return process_text(original_input)

def process_url_domain(original_input, input_type):
    original_domain = extract_domain_from_anything(original_input, preserve_case=True)

    if not original_domain:
        return {
            "status": "Suspicious",
            "classification": "SUSPICIOUS",
            "trust_score": 0,
            "reason": ["Invalid domain structure"],
            "patterns": ["Invalid domain structure"],
            "patterns_found": 1,
            "type": "url",
            "url": original_input,
            "message": "Invalid domain structure"
        }

    # Domain matching should always use normalized lowercase
    normalized_domain = original_domain.strip().lower()

    reasons = []
    is_impersonation = False
    case_manipulation = False

    # STEP 3: Case Manipulation Check
    if original_domain != normalized_domain:
        reasons.append(f"Case manipulation detected: '{original_domain}' contains unusual casing.")
        case_manipulation = True

    # Dataset checks
    is_in_verified = lookup_verified_domain(normalized_domain)
    is_in_fake = lookup_fake_domain(normalized_domain)
    is_exact_fake_url = lookup_fake_exact_url(original_input)

    # Specific check: if it's in verified but casing is wrong, it's a spoofing attempt
    if is_in_verified and case_manipulation:
        reasons.append("Potential Spoofing Attempt: Casing does not match the official record.")

    # Impersonation / typo similarity
    if not is_in_verified and not is_in_fake:
        for trusted in VERIFIED_DOMAINS:
            ratio = difflib.SequenceMatcher(None, normalized_domain, trusted).ratio()
            if 0.85 < ratio < 1.0:
                reasons.append(f"Impersonation risk: similar to trusted domain '{trusted}'")
                is_impersonation = True
                break

    # Rule-based URL analysis
    rule_results = analyze_url_rules(normalized_domain, original_input)
    for f in rule_results.get("findings", []):
        if f not in reasons:
            reasons.append(f)

    # Decision logic
    if is_exact_fake_url:
        status = "Unsafe"
        trust_score = 5
        reasons.insert(0, "Exact malicious URL match found")

    elif is_in_fake:
        status = "Unsafe"
        trust_score = 10
        reasons.insert(0, "Domain identified in malicious blacklist")

    elif is_in_verified and case_manipulation:
        # It's a verified domain but casing is manipulated (e.g. amazOn.com)
        status = "Suspicious"
        trust_score = 30
        
    elif is_impersonation:
        status = "Suspicious"
        trust_score = 25

    elif case_manipulation:
        # Casing is weird but it's not a known brand yet, still suspicious
        status = "Suspicious"
        trust_score = 45

    elif rule_results.get("risk_score", 0) > 0:
        status = "Suspicious"
        trust_score = max(30, 70 - rule_results["risk_score"])

    elif is_in_verified:
        status = "Safe"
        trust_score = 95
        reasons.insert(0, "Exact match with trusted dataset")

    else:
        status = "Suspicious"
        trust_score = 50
        reasons.append("Domain not found in trusted dataset")

    # Internet verification for unknown or mid-confidence cases
    if status == "Suspicious" and 20 < trust_score < 90:
        verify_data = internet_verify_official(original_input, domain=normalized_domain)
        for f in verify_data.get("findings", []):
            if f not in reasons:
                reasons.append(f)

        if verify_data.get("status") == "FAKE":
            status = "Unsafe"
            trust_score = min(trust_score, 10)
            if "DNS resolution failed. Target does not exist on the public internet." not in reasons:
                reasons.append("DNS resolution failed. Target does not exist on the public internet.")

    # Remove duplicates
    unique_reasons = []
    seen = set()
    for r in reasons:
        if r not in seen:
            unique_reasons.append(r)
            seen.add(r)

    return {
        "status": status,
        "classification": status.upper(),
        "trust_score": max(0, min(100, trust_score)),
        "reason": unique_reasons,
        "patterns": unique_reasons,
        "patterns_found": len(unique_reasons),
        "type": "url",
        "url": original_input,
        "message": " | ".join(unique_reasons) if unique_reasons else "Verified"
    }


def process_text(original_input):
    text_result = analyze_text_input(original_input)
    return {
        "status": text_result["status"],
        "trust_score": text_result["trust_score"],
        "message": text_result["message"],
        "pattern_found": text_result["message"], # Compatibility mapping
        "reason": text_result["message"], # Compatibility mapping
        "patterns": text_result["patterns"],
        "patterns_found": text_result["patterns_found"],
        "type": "text",
        "url": original_input[:50] + "..."
    }
