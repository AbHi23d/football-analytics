"""Match prediction models using machine learning."""

import os
import pickle
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
from xgboost import XGBClassifier
from .feature_engineering import FeatureEngineer
from ..data_collection.database import DatabaseManager
from ..preprocessing.data_cleaner import clean_match_data


class MatchPredictor:
    """Predicts match outcomes and scores using machine learning."""
    
    FEATURE_COLUMNS = [
        'home_elo', 'away_elo', 'elo_diff',
        'home_form_score', 'away_form_score', 'form_diff',
        'home_avg_goals_scored', 'home_avg_goals_conceded',
        'away_avg_goals_scored', 'away_avg_goals_conceded',
        'home_expected_goals', 'away_expected_goals',
        'home_ppg', 'away_ppg',
        'h2h_home_wins', 'h2h_away_wins', 'h2h_draws'
    ]
    
    def __init__(self, db_manager: DatabaseManager = None, model_path: str = None):
        """
        Initialize match predictor.
        
        Args:
            db_manager: Database manager instance
            model_path: Path to save/load models
        """
        self.db = db_manager or DatabaseManager()
        self.feature_engineer = FeatureEngineer(self.db)
        self.model_path = model_path or "models/saved"
        
        # Models
        self.outcome_model = None  # Classifies Win/Draw/Loss
        self.score_model = None    # Predicts goals
        self.scaler = StandardScaler()
        
        os.makedirs(self.model_path, exist_ok=True)
    
    def train_models(self, test_size: float = 0.2, random_state: int = 42) -> Dict:
        """
        Train prediction models on historical data.
        
        Args:
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary with training metrics
        """
        print("📊 Preparing training data...")
        
        # Load and prepare data
        all_matches = clean_match_data(self.db.get_all_matches())
        features_df = self.feature_engineer.create_match_features(all_matches)
        
        if len(features_df) == 0:
            print("❌ No training data available")
            return {}
        
        print(f"✓ Created {len(features_df)} training samples")
        
        # Prepare features and targets
        X = features_df[self.FEATURE_COLUMNS].values
        y_outcome = features_df['result'].values
        y_home_goals = features_df['home_goals'].values
        y_away_goals = features_df['away_goals'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train_outcome, y_test_outcome = train_test_split(
            X_scaled, y_outcome, test_size=test_size, random_state=random_state
        )
        
        _, _, y_train_home, y_test_home = train_test_split(
            X_scaled, y_home_goals, test_size=test_size, random_state=random_state
        )
        
        _, _, y_train_away, y_test_away = train_test_split(
            X_scaled, y_away_goals, test_size=test_size, random_state=random_state
        )
        
        # Train outcome classifier with ensemble
        print("\n🔮 Training ensemble prediction model (RandomForest + XGBoost)...")
        self.outcome_model = VotingClassifier(
            estimators=[
                ('rf', RandomForestClassifier(
                    n_estimators=200,
                    max_depth=15,
                    min_samples_split=5,
                    random_state=random_state,
                    class_weight='balanced'
                )),
                ('xgb', XGBClassifier(
                    n_estimators=200,
                    max_depth=10,
                    learning_rate=0.1,
                    random_state=random_state,
                    eval_metric='logloss'
                ))
            ],
            voting='soft'  # Use probability averaging
        )
        self.outcome_model.fit(X_train, y_train_outcome)
        
        # Evaluate outcome model
        y_pred_outcome = self.outcome_model.predict(X_test)
        outcome_accuracy = accuracy_score(y_test_outcome, y_pred_outcome)
        
        print(f"✓ Outcome model accuracy: {outcome_accuracy:.2%}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.outcome_model, X_scaled, y_outcome, cv=5)
        print(f"✓ Cross-validation accuracy: {cv_scores.mean():.2%} (+/- {cv_scores.std() * 2:.2%})")
        
        # Train score predictor (combined for simplicity)
        print("\n⚽ Training score prediction model...")
        y_train_total = y_train_home + y_train_away
        y_test_total = y_test_home + y_test_away
        
        self.score_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=random_state
        )
        self.score_model.fit(X_train, y_train_total)
        
        # Evaluate score model
        y_pred_total = self.score_model.predict(X_test)
        score_mse = mean_squared_error(y_test_total, y_pred_total)
        score_rmse = np.sqrt(score_mse)
        
        print(f"✓ Score model RMSE: {score_rmse:.2f} goals")
        
        # Feature importance (from RandomForest component)
        rf_model = self.outcome_model.named_estimators_['rf']
        feature_importance = pd.DataFrame({
            'feature': self.FEATURE_COLUMNS,
            'importance': rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n📈 Top 5 most important features:")
        for idx, row in feature_importance.head(5).iterrows():
            print(f"  {row['feature']}: {row['importance']:.3f}")
        
        # Save models
        self.save_models()
        
        return {
            'outcome_accuracy': outcome_accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'score_rmse': score_rmse,
            'feature_importance': feature_importance,
            'training_samples': len(features_df)
        }
    
    def predict_match(
        self, 
        home_team_id: int, 
        away_team_id: int
    ) -> Dict:
        """
        Predict outcome and score for a match.
        
        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            
        Returns:
            Dictionary with predictions
        """
        if self.outcome_model is None:
            self.load_models()
        
        # Prepare features
        features = self.feature_engineer.prepare_prediction_features(
            home_team_id, away_team_id
        )
        
        X = np.array([[features[col] for col in self.FEATURE_COLUMNS]])
        X_scaled = self.scaler.transform(X)
        
        # Predict outcome probabilities
        outcome_probs = self.outcome_model.predict_proba(X_scaled)[0]
        
        # Predict score
        predicted_total_goals = self.score_model.predict(X_scaled)[0]
        
        # Estimate individual scores based on expected goals
        home_ratio = features['home_expected_goals'] / (
            features['home_expected_goals'] + features['away_expected_goals'] + 0.01
        )
        
        predicted_home_goals = predicted_total_goals * home_ratio
        predicted_away_goals = predicted_total_goals * (1 - home_ratio)
        
        # Round the baseline goals
        home_g = round(predicted_home_goals)
        away_g = round(predicted_away_goals)
        
        # Force scoreline to match the classifier's most likely outcome
        # Target Encoding: 0=HOME_WIN, 1=DRAW, 2=AWAY_WIN
        best_outcome = np.argmax(outcome_probs)
        if best_outcome == 0: # Home Win expected
            if home_g <= away_g:
                home_g = away_g + 1
        elif best_outcome == 2: # Away Win expected
            if away_g <= home_g:
                away_g = home_g + 1
        elif best_outcome == 1: # Draw expected
            avg_g = round((home_g + away_g) / 2)
            home_g = avg_g
            away_g = avg_g
            
        return {
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'home_win_prob': outcome_probs[0],
            'draw_prob': outcome_probs[1],
            'away_win_prob': outcome_probs[2],
            'predicted_home_goals': home_g,
            'predicted_away_goals': away_g,
            'predicted_score': f"{home_g}-{away_g}",
            'confidence': max(outcome_probs),
            'features': features
        }
    
    def save_models(self):
        """Save trained models to disk."""
        if self.outcome_model is None:
            print("⚠️  No models to save")
            return
        
        with open(f"{self.model_path}/outcome_model.pkl", 'wb') as f:
            pickle.dump(self.outcome_model, f)
        
        with open(f"{self.model_path}/score_model.pkl", 'wb') as f:
            pickle.dump(self.score_model, f)
        
        with open(f"{self.model_path}/scaler.pkl", 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print(f"✓ Models saved to {self.model_path}")
    
    def load_models(self):
        """Load trained models from disk."""
        try:
            with open(f"{self.model_path}/outcome_model.pkl", 'rb') as f:
                self.outcome_model = pickle.load(f)
            
            with open(f"{self.model_path}/score_model.pkl", 'rb') as f:
                self.score_model = pickle.load(f)
            
            with open(f"{self.model_path}/scaler.pkl", 'rb') as f:
                self.scaler = pickle.load(f)
            
            print(f"✓ Models loaded from {self.model_path}")
        except FileNotFoundError:
            print("⚠️  No saved models found. Please train models first.")
