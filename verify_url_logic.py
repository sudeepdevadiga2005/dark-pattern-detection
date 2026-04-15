import sys
import os

# Add the current directory to sys.path so we can import from trust_pipeline
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trust_pipeline.pipeline import process_url_domain
from trust_pipeline.utils import detect_input_type

def run_aegis_verification():
    print("\n" + "="*50)
    print("      AEGIS SECURE CONSOLE - URL VERIFIER")
    print("="*50 + "\n")
    
    target = input("Enter target URL or Domain: ").strip()
    if not target:
        print("Error: No target provided.")
        return

    input_type = detect_input_type(target)
    if input_type not in ("url", "domain"):
        print("Error: Invalid URL or Domain format.")
        return

    print(f"\nScanning {target}...")
    result = process_url_domain(target, input_type)

    print(f"\n--- [ ANALYSIS RESULT: {result['status']} ] ---")
    print(f"Trust Score: {result['trust_score']}%")
    print(f"Risk Level:  {result['risk_level']}")
    print(f"Analysis:    {result['message']}")
    
    if result['findings']:
        print("\nIntelligence Rationale:")
        for f in result['findings']:
            print(f"  [!] {f}")
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    try:
        run_aegis_verification()
    except KeyboardInterrupt:
        print("\nScan aborted.")
