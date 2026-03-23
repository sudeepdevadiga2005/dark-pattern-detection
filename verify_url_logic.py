import pandas as pd
from urllib.parse import urlparse
from duckduckgo_search import DDGS
import os

def check_url_status(url):
    # Step 0: Pre-process URL to get domain
    original_url = url
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
    except:
        domain = original_url.lower()

    # Step 1: Load Dataset 1 (valid_domains.csv)
    dataset_path = 'valid_domains.csv'
    found_in_dataset = False
    category = None

    if os.path.exists(dataset_path):
        try:
            # We only read necessary columns for speed if possible, 
            # but for 26MB pandas is fine.
            df = pd.read_csv(dataset_path)
            # Find the domain in the dataset
            match = df[df['Domain'].str.lower() == domain]
            if not match.empty:
                found_in_dataset = True
                category = match.iloc[0]['Category']
        except Exception as e:
            print(f"Error reading dataset: {e}")

    # Logic based on user requirements:
    if found_in_dataset:
        # 2nd step: Check if e-commerce
        # (Assuming 'E-commerce' is the category name in the dataset)
        if category.lower() == 'e-commerce':
            print("Verified Website")
        else:
            # "else founded url it did not e commerce then print only e commerce websitandgiven is that categry link"
            print(f"Only e-commerce website and given is that {category} link")
    else:
        # Step 3: "ordefault is not found in data setthen go to internet for more information"
        print(f"Domain '{domain}' not found in dataset. Fetching internet information...")
        try:
            with DDGS() as ddgs:
                # Searching for the domain to get context
                search_query = f"{domain} official website e-commerce info"
                results = list(ddgs.text(search_query, max_results=3))
                
                if results:
                    print("\n--- Internet Information ---")
                    for idx, r in enumerate(results, 1):
                        print(f"{idx}. {r['title']}")
                        print(f"   URL: {r['href']}")
                        print(f"   Snippet: {r['body'][:150]}...")
                else:
                    print("No information found on the internet.")
        except Exception as e:
            print(f"Internet search error: {e}")

if __name__ == "__main__":
    test_url = input("Enter the URL to verify: ").strip()
    if test_url:
        check_url_status(test_url)
    else:
        print("Please provide a valid URL.")
