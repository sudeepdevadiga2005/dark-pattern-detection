import pandas as pd
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def train_model(data_path='training_data.tsv', model_dir='trust_pipeline/models'):
    """
    Trains a Logistic Regression model for Dark Pattern Detection.
    Saves the model, vectorizer, and evaluation stats to disk.
    """
    if not os.path.exists(data_path):
        logging.error(f"Training data not found at {data_path}. Please provide training_data.tsv.")
        return False
        
    logging.info(f"Loading dataset from {data_path}...")
    try:
        # Use sep='\t' for TSV files
        df = pd.read_csv(data_path, sep='\t')
    except Exception as e:
        logging.error(f"Failed to load TSV: {e}")
        return False

    # Preprocessing
    df['text'] = df['text'].astype(str).str.lower().str.strip()
    # Map labels to numeric if they are strings
    df['label'] = pd.to_numeric(df['label'], errors='coerce').fillna(0).astype(int)

    logging.info(f"Dataset Size: {len(df)} samples.")
    
    # Split Data
    X_train, X_test, y_train, y_test = train_test_split(
        df['text'], 
        df['label'], 
        test_size=0.2, 
        random_state=42,
        stratify=df['label']
    )

    # Vectorization (TF-IDF)
    logging.info("Vectorizing text using TF-IDF...")
    vectorizer = TfidfVectorizer(
        max_features=5000, 
        ngram_range=(1, 2), 
        stop_words='english'
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    
    # Train Model (Logistic Regression)
    logging.info("Training Logistic Regression model...")
    model = LogisticRegression(class_weight='balanced', max_iter=1000)
    model.fit(X_train_vec, y_train)

    # Create model directory if it doesn't exist
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    # Save Artifacts
    logging.info(f"Saving artifacts to {model_dir}...")
    with open(os.path.join(model_dir, 'model.pkl'), 'wb') as f:
        pickle.dump(model, f)
    with open(os.path.join(model_dir, 'vectorizer.pkl'), 'wb') as f:
        pickle.dump(vectorizer, f)
    
    logging.info("Training Complete. Model is ready for evaluation.")
    return True

if __name__ == "__main__":
    train_model()
