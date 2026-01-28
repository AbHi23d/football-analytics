"""
Train Model Script

Run this to train the model from scratch using the data science approach.
Creates model files that the dashboard will use.
"""

import pandas as pd
import numpy as np
import pickle
import json
import os
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier

# Import our simple utilities
from utils import load_data, engineer_features

print("=" * 60)
print("FOOTBALL ANALYTICS - MODEL TRAINING")
print("=" * 60)

# =================================================================
# Step 1: Load and Prepare Data
# =================================================================

print("\n📊 Loading data...")
df = load_data()
print(f"✓ Loaded {len(df):,} matches")

print("\n🔧 Engineering features...")
df = engineer_features(df)
print("✓ Features calculated")

# =================================================================
# Step 2: Prepare for Training
# =================================================================

# Define features (15 explainable features)
FEATURES = [
    'elo_diff',              # 1. Team strength difference
    'form_diff',             # 2. Recent form difference
    'home_win_streak',       # 3. Home team winning streak (NEW)
    'away_win_streak',       # 4. Away team winning streak (NEW)
    'home_clean_sheets',     # 5. Home defensive momentum (NEW)
    'away_clean_sheets',     # 6. Away defensive momentum (NEW)
    'home_goals_avg',        # 7. Home attack strength
    'away_goals_avg',        # 8. Away attack strength
    'home_conceded_avg',     # 9. Home defense strength
    'away_conceded_avg',     # 10. Away defense strength
    'h2h_home_wins',         # 11. Historical home wins
    'h2h_away_wins',         # 12. Historical away wins
    'rest_days',             # 13. Recovery time
    'season_progress',       # 14. Point in season (0-1)
    'is_december',           # 15. Fixture congestion
]

print(f"\n📋 Using {len(FEATURES)} features:")
for i, feat in enumerate(FEATURES, 1):
    print(f"  {i}. {feat}")

# Map results to clean labels
result_map = {
    'HOME_TEAM': 'Home Win', 'H': 'Home Win',
    'AWAY_TEAM': 'Away Win', 'A': 'Away Win',
    'DRAW': 'Draw', 'D': 'Draw'
}
df['result'] = df['winner'].map(result_map)

# Prepare X and y
X = df[FEATURES].copy()
y = df['result'].copy()

# Remove any rows with missing values
mask = X.notna().all(axis=1) & y.notna()
X = X[mask]
y = y[mask]

print(f"\n✓ Training data: {len(X):,} samples")
print(f"  Classes: {y.value_counts().to_dict()}")

# =================================================================
# Step 3: Time-Based Train/Test Split
# =================================================================

# Sort by date to maintain temporal order
df_sorted = df.sort_values('utc_date').reset_index(drop=True)
X = df_sorted[FEATURES].copy()
y = df_sorted['result'].copy()

# Remove any rows with missing values
mask = X.notna().all(axis=1) & y.notna()
X = X[mask]
y = y[mask]

print(f"\n✓ Training data: {len(X):,} samples")
print(f"  Classes: {y.value_counts().to_dict()}")

# Time-based split: Train on past, test on future (80/20)
# This simulates real-world scenario: predict future from historical data
split_index = int(len(X) * 0.8)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]
y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

# Get date ranges for clarity
train_dates = df_sorted.loc[X_train.index, 'utc_date']
test_dates = df_sorted.loc[X_test.index, 'utc_date']

print(f"\n✓ Time-Based Split:")
print(f"  Train: {len(X_train):,} matches ({train_dates.min().date()} to {train_dates.max().date()})")
print(f"  Test:  {len(X_test):,} matches ({test_dates.min().date()} to {test_dates.max().date()})")
print(f"  → Predicting future from past (no data leakage!)")


# =================================================================
# Step 4: Train Model (XGBoost)
# =================================================================

print("\n🤖 Training XGBoost...")

# XGBoost requires numeric labels
le = LabelEncoder()
y_train_encoded = le.fit_transform(y_train)
y_test_encoded = le.transform(y_test)

model = XGBClassifier(
    n_estimators=100,
    max_depth=5,
    random_state=42,
    eval_metric='mlogloss',
    enable_categorical=False
)

model.fit(X_train, y_train_encoded)
print("✓ Model trained!")

# Store label encoder for later use
label_encoder = le

# =================================================================
# Step 5: Evaluate
# =================================================================

print("\n📊 Evaluating performance...")

# Test accuracy
y_pred_encoded = model.predict(X_test)
y_pred = le.inverse_transform(y_pred_encoded)
accuracy = accuracy_score(y_test, y_pred)
baseline = y_test.value_counts().max() / len(y_test)

print(f"\nTest Accuracy: {accuracy:.1%}")
print(f"Baseline (always 'Home Win'): {baseline:.1%}")
print(f"Improvement: +{(accuracy - baseline) * 100:.1f} percentage points")

# Cross-validation (need to encode y_train for CV)
cv_scores = cross_val_score(model, X_train, y_train_encoded, cv=5, scoring='accuracy')
print(f"\nCross-Validation (5-fold):")
print(f"  Mean: {cv_scores.mean():.1%} ± {cv_scores.std():.1%}")

# Classification report
print("\nDetailed Metrics:")
print(classification_report(y_test, y_pred))

# Feature importance
importance = pd.DataFrame({
    'feature': FEATURES,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nFeature Importance:")
print(importance.to_string(index=False))

# =================================================================
# Step 6: Save Model
# =================================================================

print("\n💾 Saving model...")

# Create models directory
os.makedirs('models', exist_ok=True)

# Save model
with open('models/simple_model.pkl', 'wb') as f:
    pickle.dump(model, f)
print("✓ Model saved: models/simple_model.pkl")

# Save feature list
with open('models/features.json', 'w') as f:
    json.dump(FEATURES, f)
print("✓ Features saved: models/features.json")

# Save metadata
metadata = {
    'accuracy': float(accuracy),
    'baseline': float(baseline),
    'cv_mean': float(cv_scores.mean()),
    'cv_std': float(cv_scores.std()),
    'n_features': len(FEATURES),
    'n_train': len(X_train),
    'n_test': len(X_test)
}

with open('models/model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("✓ Metadata saved: models/model_metadata.json")

# =================================================================
# Summary
# =================================================================

print("\n" + "=" * 60)
print("✅ MODEL TRAINING COMPLETE!")
print("=" * 60)
print(f"\nModel Performance:")
print(f"  • Accuracy: {accuracy:.1%}")
print(f"  • CV Score: {cv_scores.mean():.1%}")
print(f"  • Features: {len(FEATURES)}")
print(f"\nFiles Created:")
print(f"  • models/simple_model.pkl")
print(f"  • models/features.json")
print(f"  • models/model_metadata.json")
print(f"\nNext Step:")
print(f"  Run: streamlit run app_simple.py")
print("=" * 60)
