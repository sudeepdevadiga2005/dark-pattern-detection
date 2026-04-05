from trust_pipeline.utils import detect_input_type, extract_domain_from_anything, normalize_full_url
from trust_pipeline.datasets import lookup_verified_domain, lookup_fake_domain, lookup_fake_exact_url
from trust_pipeline.verification import internet_verify_official, analyze_url_rules
from trust_pipeline.text_analyzer import analyze_text_input
from trust_pipeline.config import (
    TRUST_SCORE_VERIFIED,
    TRUST_SCORE_FAKE_EXACT,
    TRUST_SCORE_FAKE_DOMAIN
)

def analyze_input(user_input):
    """
    The main orchestrator handling step-by-step resolution.
    It routes the original input to the appropriate pipeline and returns a unified JSON format response block.
    """
    original_input = user_input.strip() if user_input else ""
    input_type = detect_input_type(original_input)

    if input_type == "invalid":
        return {
            "original_input": original_input,
            "input_type": "invalid",
            "normalized_url": None,
            "domain": None,
            "status": "INVALID_INPUT",
            "trust_score": 0,
            "category": None,
            "source": "invalid_input",
            "message": "Please enter a valid URL, domain, or meaningful text.",
            "findings": [],
            "is_official": None
        }

    # URL / DOMAIN PIPELINE
    if input_type in ("url", "domain"):
        return process_url_domain(original_input, input_type)

    # PLAIN TEXT PIPELINE
    return process_text(original_input)


def process_url_domain(original_input, input_type):
    """
    Dedicated logic sequence for URLs/Domains: Lookups followed by verify-fallbacks.
    """
    domain = extract_domain_from_anything(original_input)
    normalized_url = normalize_full_url(original_input)

    # Base response
    resp = {
        "original_input": original_input,
        "input_type": input_type,
        "normalized_url": normalized_url,
        "domain": domain,
        "category": None,
        "findings": [],
        "is_official": None
    }

    if not domain:
        resp.update({
            "status": "INVALID_INPUT",
            "trust_score": 0,
            "source": "invalid_input",
            "message": "The URL/domain format could not be parsed correctly."
        })
        return resp

    # 1. Dataset Match: Verified
    if lookup_verified_domain(domain):
        resp.update({
            "status": "SAFE",
            "trust_score": TRUST_SCORE_VERIFIED,
            "category": "verified",
            "source": "verified_dataset",
            "message": "This domain exists in the verified safe-domain dataset.",
            "findings": ["Domain matched verified dataset."],
            "is_official": True
        })
        return resp

    # 2. Dataset Match: Fake Exact URL
    fake_exact_category = lookup_fake_exact_url(normalized_url)
    if fake_exact_category:
        resp.update({
            "status": "SUSPICIOUS",
            "trust_score": TRUST_SCORE_FAKE_EXACT,
            "category": fake_exact_category,
            "source": "fake_dataset_exact_url",
            "message": "This exact URL matched the suspicious/fake dataset.",
            "findings": ["Exact URL matched fake dataset."],
            "is_official": False
        })
        return resp

    # 3. Dataset Match: Fake Domain
    fake_domain_category = lookup_fake_domain(domain)
    if fake_domain_category:
        resp.update({
            "status": "SUSPICIOUS",
            "trust_score": TRUST_SCORE_FAKE_DOMAIN,
            "category": fake_domain_category,
            "source": "fake_dataset_domain",
            "message": "This domain matched the suspicious/fake dataset.",
            "findings": ["Domain matched fake dataset."],
            "is_official": False
        })
        return resp

    # 4. Internet verification (Fallback)
    verify_result = internet_verify_official(original_input, domain=domain)
    
    # 5. Rule parsing for heuristics
    url_rule_result = analyze_url_rules(domain, normalized_url)

    findings = verify_result["findings"] + url_rule_result["findings"]
    final_status = verify_result["status"]
    final_score = verify_result["trust_score"]

    if url_rule_result["risk_score"] >= 20 and final_status == "LIKELY_SAFE":
        final_status = "POTENTIALLY_SUSPICIOUS"
        final_score = min(final_score, 55)
        findings.append("URL rule engine reduced confidence due to structural risk signals.")
    elif url_rule_result["risk_score"] >= 20 and final_status == "UNKNOWN":
        final_status = "POTENTIALLY_SUSPICIOUS"
        final_score = 40
        findings.append("URL rule engine found multiple suspicious URL features.")

    resp.update({
        "status": final_status,
        "trust_score": final_score,
        "source": verify_result["source"],
        "message": verify_result["message"],
        "findings": findings,
        "is_official": verify_result["is_official"]
    })
    return resp

def process_text(original_input):
    """
    Direct route handling purely linguistic content analysis logic.
    """
    text_result = analyze_text_input(original_input)
    return {
        "original_input": original_input,
        "input_type": "text",
        "normalized_url": None,
        "domain": None,
        "status": text_result["status"],
        "trust_score": text_result["trust_score"],
        "category": None,
        "source": text_result["source"],
        "message": text_result["message"],
        "findings": text_result["findings"],
        "is_official": text_result["is_official"]
    }
