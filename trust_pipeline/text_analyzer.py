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
            logging.info("Aegis Security Engine: Model Loaded.")
        except Exception as e:
            logging.error(f"Asset load failed: {e}")

load_ml_assets()

def analyze_text_input(text, sensitivity_mode='balanced'):
    """
    AEGIS ADAPTIVE SECURITY ENGINE - v9.0 (FNR optimized)
    Implements Dynamic Thresholding (0.35/0.28/0.22) and multi-level heuristic signals.
    """
    if not text or len(text.strip()) < 3:
        return {"status": "SAFE", "trust_score": 100, "message": "No input detected.", "patterns_found": 0, "patterns": []}
        
    cleaned = text.strip()
    lower_text = cleaned.lower()
    
    # --- PHASE 1: REFINED HEURISTIC RULES (Reduced False Positives) ---
    categories = {
        "urgency": r"\bhurry\b|\bact immediately\b|\bexpires in \d+\b|\blimited time offer\b|\blast chance to buy\b|\burgent action required\b",
        "scarcity": r"\bonly \d+ left in stock\b|\blimited availability\b|\balmost sold out\b|\bwhile supplies last\b",
        "social_proof": r"\b\d+ people currently viewing\b|\bbestseller in your area\b|\bhigh demand item\b",
        "security_pressure": r"\baccount suspended\b|\bunauthorized access attempt\b|\bverify your identity now\b|\bsecurity compromise detected\b",
        "loss_aversion": r"\bdon['’]t miss out on this deal\b|\boffer expires soon\b|\byou will lose your progress\b"
    }
    
    found_categories = []
    all_patterns = [] # Objects with category and evidence
    
    for cat, pattern in categories.items():
        match = re.search(pattern, lower_text)
        if match:
            found_categories.append(cat)
            display_cat = cat.replace('_', ' ').capitalize()
            all_patterns.append({
                "category": display_cat,
                "evidence": match.group(0)
            })
            
    # --- PHASE 2: ADAPTIVE THRESHOLD TUNING ---
    # Standard threshold increased slightly to avoid hair-trigger suspicous flags
    base_threshold = 0.40 if sensitivity_mode == 'balanced' else 0.32
    
    # Dynamics: Strong rule signals reduce ML barrier
    if len(found_categories) >= 2 or re.search(r"security_pressure", "|".join(found_categories)):
        security_threshold = 0.25 
    elif len(found_categories) == 1:
        security_threshold = 0.35
    else:
        security_threshold = base_threshold

    # --- PHASE 3: CLASSIFIER PREDICTION ---
    ml_label = 0
    unsafe_prob = 0.0
    
    if _MODEL and _VECTORIZER:
        try:
            vec = _VECTORIZER.transform([lower_text])
            probs = _MODEL.predict_proba(vec)[0]
            unsafe_prob = float(probs[1])
            
            # Hybrid Decision Matrix
            if unsafe_prob >= security_threshold:
                ml_label = 1
            # If rules exist and ML is leaning towards unsafe, boost it
            elif unsafe_prob >= 0.30 and len(found_categories) >= 1:
                ml_label = 1
        except: pass

    # --- PHASE 4: FINAL DECISION (Hardened Against False Positives) ---
    force_unsafe = (sensitivity_mode == 'strict' and len(found_categories) >= 1)
    
    is_unsafe = (ml_label == 1) or (len(found_categories) >= 2) or force_unsafe
    
    # Suspicious requires EITHER:
    # 1. High-ish ML probability (>= 0.35)
    # 2. At least 1 rule match AND some ML signal (>= 0.15)
    is_suspicious = (not is_unsafe) and (
        (unsafe_prob >= 0.35) or 
        (len(found_categories) >= 1 and unsafe_prob >= 0.15)
    )
    
    # Textual reason summary (strings for overview)
    str_reasons = [p["category"] for p in all_patterns]
    safe_signals = [] # For highlighting positive markers
    
    if is_unsafe:
        status = "UNSAFE"
        # Highly dynamic score based on probability and rule density
        trust_score = int(max(5, (1 - unsafe_prob) * 30 - (len(found_categories) * 4)))
        
        display_reasons = []
        if ml_label == 1: 
            display_reasons.append("Classifier detected manipulative intent profile.")
            all_patterns.append({
                "category": "Neural classification",
                "evidence": "Deceptive design signature"
            })
            str_reasons.append("Neural classification")
                
        if found_categories: 
            display_reasons.append(f"Risk markers identified: {', '.join(str_reasons)}.")
        
        message = " | ".join(display_reasons)
    elif is_suspicious:
        status = "SUSPICIOUS"
        trust_score = int(70 - (unsafe_prob * 60))
        message = f"Potential threat marker found: {', '.join(str_reasons) if str_reasons else 'Neural pattern detection'}."
    else:
        status = "SAFE"
        # Dynamic high score: inversely proportional to any slight suspicion
        trust_score = int(100 - (unsafe_prob * 25)) 
        message = "No manipulative patterns or security threats were detected."
        
        # Add safety signals
        safe_signals.append("Neutral transactional tone")
        if unsafe_prob < 0.1: safe_signals.append("High confidence linguistic safety")
        if not found_categories: safe_signals.append("No psychological pressure markers found")

    # --- PHASE 5: DEBUG LOGGING ---
    logging.info(f"Analysis: Score={unsafe_prob:.3f} | Threshold={security_threshold} | Patterns={len(all_patterns)} | Result={status}")

    return {
        "status": status,
        "classification": status,
        "trust_score": trust_score,
        "message": message,
        "patterns_found": len(all_patterns),
        "patterns": all_patterns,
        "safe_signals": safe_signals, # NEW: Show the user why it is safe
        "model_confidence": f"{(1 - unsafe_prob)*100:.1f}%",
        "applied_threshold": security_threshold
    }
