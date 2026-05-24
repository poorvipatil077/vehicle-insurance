import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
import os

# Create a sample dataset if not exists
DATASET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset', 'insurance.csv')
if not os.path.exists(os.path.dirname(DATASET_PATH)):
    os.makedirs(os.path.dirname(DATASET_PATH))

if not os.path.exists(DATASET_PATH):
    data = {
        'age': [25, 45, 35, 50, 23, 30, 40, 55, 20, 48],
        'accidents': [0, 1, 0, 2, 0, 1, 0, 3, 0, 1],
        'vehicle_age': [2, 10, 5, 12, 1, 6, 8, 15, 1, 11],
        'fraud_reported': [0, 1, 0, 1, 0, 0, 0, 1, 0, 1]
    }
    df = pd.DataFrame(data)
    df.to_csv(DATASET_PATH, index=False)
else:
    df = pd.read_csv(DATASET_PATH)

# Train a robust model
X = df.drop('fraud_reported', axis=1)
y = df['fraud_reported']

print(f"Dataset shape: {df.shape}")
print("Training model...")

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Save the model
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model')
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

model_file = os.path.join(MODEL_DIR, 'fraud_model.pkl')
joblib.dump(model, model_file)

print(f"Model trained successfully and saved to: {model_file}")
