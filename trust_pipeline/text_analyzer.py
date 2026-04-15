import re
import os
import pickle
import logging

# Paths to ML artifacts
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'model.pkl')
VEC_PATH = os.path.join(MODEL_DIR, 'vectorizer.pkl')

_MODEL = None
_VECTORIZER = None

def load_ml_assets():
    global _MODEL, _VECTORIZER
    if os.path.exists(MODEL_PATH) and os.path.exists(VEC_PATH):
        try:
            with open(MODEL_PATH, 'rb') as f: _MODEL = pickle.load(f)
            with open(VEC_PATH, 'rb') as f: _VECTORIZER = pickle.load(f)
            logging.info("Aegis Intelligence v7.0: Security Engine Ready.")
        except Exception as e:
            logging.error(f"Asset load failed: {e}")

load_ml_assets()

def analyze_text_input(text, sensitivity_mode='balanced'):
    """
    AEGIS ADAPTIVE SECURITY ENGINE - v7.0 (Extreme Recall Focus)
    Implements Dynamic Thresholding, Confidence Boosting, and Category-Based Overrides.
    """
    if not text or len(text.strip()) < 3:
        return {"status": "SAFE", "trust_score": 100, "message": "No input detected.", "patterns_found": 0, "patterns": []}
        
    cleaned = text.strip()
    lower_text = cleaned.lower()
    
    # --- PHASE 1: EXPANDED PATTERN CATEGORIZATION ---
    categories = {
        "urgency": r"\bhurry\b|\bact now\b|\bexpires\b|\blast chance\b|\bquick\b|\bright now\b",
        "scarcity": r"\bonly \d+ left\b|\balmost gone\b|\blimited stock\b|\bfew remaining\b",
        "social_proof": r"\bpeople are viewing\b|\busers bought\b|\bjoined recently\b",
        "security_pressure": r"\baccount suspended\b|\bunauthorized access\b|\bverify identity\b|\brevoke\b",
        "loss_aversion": r"\bdon['’]t miss\b|\byou will lose\b|\bsave now\b|\bdon['’]t let this slip\b"
    }
    
    found_categories = []
    all_patterns = []
    for cat, pattern in categories.items():
        if re.search(pattern, lower_text):
            found_categories.append(cat)
            all_patterns.append(cat.replace('_', ' ').capitalize())
            
    # --- PHASE 2: ADAPTIVE DYNAMIC THRESHOLDING ---
    # Default thresholds based on sensitivity mode
    base_threshold = 0.35 if sensitivity_mode == 'balanced' else 0.28
    
    # Dynamics: Stronger rules → Lower ML barrier
    if len(found_categories) >= 2:
        security_threshold = 0.22 # Extremely sensitive if multiple patterns exist
    elif len(found_categories) == 1:
        security_threshold = 0.28
    else:
        security_threshold = base_threshold

    # --- PHASE 3: NEURAL PREDICTION & CONFIDENCE BOOSTING ---
    ml_label = 0
    unsafe_prob = 0.0
    
    if _MODEL and _VECTORIZER:
        try:
            vec = _VECTORIZER.transform([lower_text])
            probs = _MODEL.predict_proba(vec)[0]
            unsafe_prob = float(probs[1])
            
            # Confidence Boosting Logic:
            # If ML is borderline (e.g. 0.25) but rules found 1+ pattern, escalate to UNSAFE.
            if unsafe_prob >= security_threshold:
                ml_label = 1
            elif unsafe_prob >= 0.25 and len(found_categories) >= 1:
                ml_label = 1 # Boost borderline case due to rule support
        except: pass

    # --- PHASE 4: FINAL CLASSIFICATION (High-Security Priority) ---
    is_unsafe = (ml_label == 1) or (len(found_categories) >= 2)
    is_suspicious = (not is_unsafe) and (len(found_categories) == 1 or unsafe_prob >= 0.20)
    
    if is_unsafe:
        status = "UNSAFE"
        trust_score = max(5, 25 - (len(found_categories) * 6))
        
        reasons = []
        if ml_label == 1: reasons.append("Neural layer detected manipulative intent profile.")
        if len(found_categories) >= 2: reasons.append(f"Multiple risk markers: {', '.join(all_patterns)}.")
        elif found_categories: reasons.append(f"Risk signal detected: {all_patterns[0]}.")
        
        message = " | ".join(reasons)
    elif is_suspicious:
        status = "SUSPICIOUS"
        trust_score = int(60 - (unsafe_prob * 10))
        message = f"Potential threat marker found: {', '.join(all_patterns)}."
    else:
        status = "SAFE"
        trust_score = int(90 + (unsafe_prob * 10)) if unsafe_prob < 0.2 else 95
        message = "No manipulative patterns or security threats were detected."

    return {
        "status": status,
        "classification": status,
        "trust_score": trust_score,
        "message": message,
        "patterns_found": len(all_patterns),
        "patterns": all_patterns,
        "neural_safety": f"{(1 - unsafe_prob)*100:.1f}%",
        "applied_threshold": security_threshold
    }
