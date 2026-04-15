import pandas as pd
import pickle
import os
import json
import numpy as np
import sys
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
import logging

# Add project root to path for local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def augment_text(text):
    """Simple synonym replacement for key dark pattern triggers."""
    synonyms = {
        "hurry": "quick",
        "act now": "move fast",
        "limited": "restricted",
        "only": "just",
        "expires": "ends",
        "urgent": "critical"
    }
    new_text = text
    for word, syn in synonyms.items():
        if word in text:
            new_text = new_text.replace(word, syn)
    return new_text

def run_feedback_cycle(data_path='training_data.tsv', model_dir='trust_pipeline/models'):
    """
    AEGIS PRODUCTION EVALUATION PIPELINE - v9.0
    Final technical alignment for Logistic Regression & TF-IDF vectorization.
    """
    fn_log_path = os.path.join(model_dir, 'false_negatives.log')
    
    # --- PHASE 1: CONSUME FN LOG & AUGMENT ---
    if os.path.exists(fn_log_path):
        with open(fn_log_path, 'r', encoding='utf-8') as f:
            missed_threats = [line.strip() for line in f if line.strip()]
        
        if missed_threats:
            df = pd.read_csv(data_path, sep='\t')
            new_rows = []
            
            existing_texts = set(df['text'].tolist())
            for threat in missed_threats:
                if threat not in existing_texts:
                    new_rows.append({'text': threat, 'label': 1, 'Pattern Category': 'Log Feedback'})
                    aug = augment_text(threat)
                    if aug != threat:
                        new_rows.append({'text': aug, 'label': 1, 'Pattern Category': 'Augmented'})
            
            if new_rows:
                new_df = pd.DataFrame(new_rows)
                df = pd.concat([df, new_df], ignore_index=True)
                df.drop_duplicates(subset=['text'], inplace=True)
                df.to_csv(data_path, sep='\t', index=False)
            open(fn_log_path, 'w').close()

    # --- PHASE 2: RE-TRAIN ---
    from trust_pipeline.train_text_model import train_model
    train_model(data_path, model_dir)

    # --- PHASE 3: SCIENTIFIC EVALUATION ---
    model_path = os.path.join(model_dir, 'model.pkl')
    vec_path = os.path.join(model_dir, 'vectorizer.pkl')
    with open(model_path, 'rb') as f: model = pickle.load(f)
    with open(vec_path, 'rb') as f: vectorizer = pickle.load(f)
    
    df = pd.read_csv(data_path, sep='\t')
    test_size = 0.2
    X_train, X_test, y_train, y_test = train_test_split(
        df['text'], df['label'], test_size=test_size, random_state=42, stratify=df['label']
    )
    
    X_test_vec = vectorizer.transform(X_test)
    probs = model.predict_proba(X_test_vec)[:, 1]
    
    # Baseline threshold for evaluation report
    BASELINE_THRESHOLD = 0.35 
    y_pred = (probs >= BASELINE_THRESHOLD).astype(int)

    # Calculate Confusion Matrix
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    tn, fp, fn, tp = int(tn), int(fp), int(fn), int(tp)
    
    # derive all metrics directly from confusion matrix to ensure 100% consistency
    total = tn + fp + fn + tp
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

    # Data-driven technical status message
    if fnr < 0.02:
        status_msg = "Strong detection performance with minimal missed threats."
        risk_lvl = "Safe"
    elif fnr < 0.05:
        status_msg = "Moderate risk: some unsafe cases still undetected."
        risk_lvl = "Warning"
    else:
        status_msg = "High risk: detection improvement required. Missed threat rate is critical."
        risk_lvl = "Critical"

    metrics = {
        "model_name": "Aegis Classifier v9.0",
        "status": "Operational",
        "status_message": status_msg,
        "algorithm": "Logistic Regression",
        "vectorizer": "TF-IDF (ngram_range=(1,2))",
        "positive_class": "UNSAFE (Label 1)",
        "threshold_config": "Adaptive (Base: 0.35 | Signal-Adjusted: 0.28/0.22)",
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "false_positive_rate": float(fpr),
        "false_negative_rate": float(fnr),
        "confusion_matrix": {
            "tn": tn, "fp": fp, "fn": fn, "tp": tp
        },
        "risk_level": risk_lvl,
        "metadata": {
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "test_split": f"{int(test_size*100)}%",
            "total_samples": len(df)
        },
        "last_evaluated": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    metrics_path = os.path.join(model_dir, 'metrics.json')
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4)
        
    logging.info(f"Evaluation Cycle v9.0 Complete. FNR: {fnr*100:.2f}% | Risk: {risk_lvl}")
    return metrics

if __name__ == "__main__":
    run_feedback_cycle()
