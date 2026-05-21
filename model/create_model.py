from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
import joblib
import os

# Create fake training data
X, y = make_classification(
    n_samples=1000,
    n_features=3923,
    random_state=42
)

# Train model
model = RandomForestClassifier()

model.fit(X, y)

# Create model folder
os.makedirs("model", exist_ok=True)

# Save model
joblib.dump(model, "model/fraud_model.pkl")

print("✅ fraud_model.pkl created successfully")
