import sys
import os
sys.path.append(os.getcwd())
from trust_pipeline.text_analyzer import analyze_text_input
import json

test_cases = [
    "Hurry! Your trial expires soon.",           # Urgency
    "Only 3 left in stock - buy now!",           # Scarcity
    "Account blocked. Verify identity now.",      # Security Pressure
    "Others are viewing this right now.",        # Social Proof
    "Don't lose your discount. Act fast!",       # Loss Aversion
    "Click here for free coins.",                # Low ML (usually)
    "This is a normal message about a meeting."   # Safe
]

print(f"{'INPUT':<40} | {'STATUS':<10} | {'SCORE':<6}")
print("-" * 65)

for text in test_cases:
    res = analyze_text_input(text)
    print(f"{text[:38]:<40} | {res['status']:<10} | {res['model_confidence']}")
