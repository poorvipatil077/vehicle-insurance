import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import os

# Create a sample dataset if not exists
DATASET_PATH = 'dataset/insurance.csv'
if not os.path.exists(DATASET_PATH):
    data = {
        'age': [25, 45, 35, 50, 23],
        'policy_state': [1, 2, 1, 3, 2],
        'policy_deductable': [500, 1000, 500, 2000, 500],
        'incident_type': [1, 2, 1, 1, 2],
        'fraud_reported': [0, 1, 0, 1, 0]
    }
    df = pd.DataFrame(data)
    df.to_csv(DATASET_PATH, index=False)
else:
    df = pd.read_csv(DATASET_PATH)

# Train a simple model with more features or data
X = df.drop('fraud_reported', axis=1)
y = df['fraud_reported']

print(f"Dataset shape: {df.shape}")
print("Training model...")

# Ensure the model is robust
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Save the model
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model')
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

model_file = os.path.join(MODEL_DIR, 'fraud_model.pkl')
with open(model_file, 'wb') as f:
    pickle.dump(model, f)

print(f"Model trained successfully and saved to: {model_file}")

print("Model trained and saved successfully.")
