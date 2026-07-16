# Improving Model Performance - Recommendations Guide

## 🎯 Current Model Performance

**Baseline Metrics:**
- Match Outcome Accuracy: ~50-60%
- Score Prediction RMSE: ~2 goals
- This is **competitive with industry standards** for football prediction

---

## 🚀 Improvement Strategies

### 1. **Feature Engineering Improvements**

#### Add More Advanced Features

```python
# In src/models/feature_engineering.py

# 1. Add streak features
def calculate_streak(matches_df, team_id):
    """Calculate current winning/losing streak"""
    recent = get_recent_form(matches_df, team_id, 10)
    streak = 0
    for result in recent:
        if result == 'W':
            streak += 1
        else:
            break
    return streak

# 2. Add rest days
def calculate_rest_days(match_date, previous_match_date):
    """Days since last match"""
    return (match_date - previous_match_date).days

# 3. Add league position difference
def get_position_difference(standings, home_id, away_id):
    """Difference in league positions"""
    home_pos = standings[standings['team_id'] == home_id]['position'].iloc[0]
    away_pos = standings[standings['team_id'] == away_id]['position'].iloc[0]
    return home_pos - away_pos

# 4. Add motivation factors
def calculate_motivation(team_position, match_importance):
    """Teams fighting relegation or for championships play differently"""
    if team_position <= 4:  # Champions League spots
        return 1.2
    elif team_position >= 18:  # Relegation zone
        return 1.3
    return 1.0
```

#### Expected Goals (xG) Model

```python
# Create a separate xG model based on shot quality
def calculate_expected_goals(shots, shot_locations, shot_types):
    """
    Implement Poisson or neural network-based xG model
    """
    # This would require shot-level data (available in premium APIs)
    pass
```

---

### 2. **Model Architecture Enhancements**

#### Ensemble Methods

```python
# In src/models/match_predictor.py

from sklearn.ensemble import VotingClassifier, StackingClassifier
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression

class ImprovedMatchPredictor:
    def __init__(self):
        # Create ensemble of models
        self.ensemble = VotingClassifier(
            estimators=[
                ('rf', RandomForestClassifier(n_estimators=200)),
                ('xgb', XGBClassifier(n_estimators=200)),
                ('lr', LogisticRegression())
            ],
            voting='soft'  # Use probability averaging
        )
    
    # Alternative: Stacking
    def create_stacking_model(self):
        base_models = [
            ('rf', RandomForestClassifier(n_estimators=100)),
            ('xgb', XGBClassifier(n_estimators=100))
        ]
        
        return StackingClassifier(
            estimators=base_models,
            final_estimator=LogisticRegression(),
            cv=5
        )
```

#### Deep Learning Approach

```python
# Install: pip install tensorflow

import tensorflow as tf
from tensorflow import keras

def create_neural_network():
    model = keras.Sequential([
        keras.layers.Dense(128, activation='relu', input_shape=(17,)),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dense(3, activation='softmax')  # Win/Draw/Loss
    ])
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model
```

---

### 3. **Hyperparameter Optimization**

```python
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

# Current model uses default parameters
# Optimize them instead:

param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 15, 20, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'max_features': ['auto', 'sqrt', 'log2'],
    'class_weight': ['balanced', None]
}

grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1
)

grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_

print(f"Best parameters: {grid_search.best_params_}")
print(f"Best CV score: {grid_search.best_score_:.2%}")
```

---

### 4. **Data Augmentation**

#### Maximize Available Data

```python
# 1. Fetch more leagues
LEAGUES = ['PL', 'ELC', 'PD', 'SA', 'BL1', 'FL1']  # Premier, Championship, La Liga, Serie A, Bundesliga, Ligue 1

# 2. Fetch more historical seasons
SEASONS = [2019, 2020, 2021, 2022, 2023, 2024]

# 3. Use reverse fixtures
def augment_with_reverse(features_df):
    """Create additional samples by swapping home/away"""
    reversed_df = features_df.copy()
    
    # Swap home/away columns
    reversed_df['home_elo'], reversed_df['away_elo'] = reversed_df['away_elo'], reversed_df['home_elo']
    reversed_df['home_form_score'], reversed_df['away_form_score'] = reversed_df['away_form_score'], reversed_df['home_form_score']
    # ... swap all features
    
    # Flip the result
    reversed_df['result'] = reversed_df['result'].map({0: 2, 1: 1, 2: 0})
    
    return pd.concat([features_df, reversed_df])
```

---

### 5. **External Data Sources**

#### Weather Data

```python
# Install: pip install python-weather

import python_weather

async def get_weather_for_match(match_date, venue_city):
    """Weather affects match outcomes"""
    async with python_weather.Client() as client:
        weather = await client.get(venue_city)
        
        return {
            'temperature': weather.temperature,
            'precipitation': weather.precipitation,
            'wind_speed': weather.wind_speed
        }

# Add to features:
# - 'is_rainy': binary
# - 'temperature': continuous
# - 'wind_speed': continuous
```

#### Betting Odds

```python
# Betting markets are highly efficient predictors

def fetch_betting_odds(match_id):
    """
    Use odds as features - bookmakers have sophisticated models
    Premium API: odds-api.com
    """
    # Convert odds to implied probabilities
    home_odds = 2.1  # Example
    draw_odds = 3.5
    away_odds = 3.2
    
    return {
        'home_implied_prob': 1 / home_odds,
        'draw_implied_prob': 1 / draw_odds,
        'away_implied_prob': 1 / away_odds
    }

# These can be very powerful features!
```

#### Player Data

```python
# Upgrade to premium Football-Data.org API or use other sources

def get_squad_value(team_id):
    """Total market value of squad"""
    # From transfermarkt.com (web scraping)
    pass

def get_injury_info(team_id, match_date):
    """Key players injured"""
    # Number of injured starters
    pass
```

---

### 6. **Class Imbalance Handling**

```python
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline

# Handle imbalanced classes (if draws are less common)
over = SMOTE(sampling_strategy=0.5)
under = RandomUnderSampler(sampling_strategy=0.8)

pipeline = Pipeline([
    ('over', over),
    ('under', under)
])

X_resampled, y_resampled = pipeline.fit_resample(X_train, y_train)
```

---

### 7. **Time-Based Validation**

```python
# Use time-series cross-validation instead of random split

from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)

for train_idx, test_idx in tscv.split(features_df):
    X_train = features_df.iloc[train_idx][feature_cols]
    X_test = features_df.iloc[test_idx][feature_cols]
    
    # Train model
    model.fit(X_train, y_train)
    
    # Evaluate on future matches only
    score = model.score(X_test, y_test)
```

---

### 8. **Feature Selection**

```python
from sklearn.feature_selection import SelectKBest, f_classif, RFE

# 1. Statistical selection
selector = SelectKBest(score_func=f_classif, k=10)
X_selected = selector.fit_transform(X, y)

# 2. Recursive feature elimination
rfe = RFE(RandomForestClassifier(), n_features_to_select=10)
X_selected = rfe.fit_transform(X, y)

print("Selected features:", rfe.support_)
```

---

### 9. **Calibration**

```python
from sklearn.calibration import CalibratedClassifierCV

# Make probability predictions more reliable
calibrated_model = CalibratedClassifierCV(
    self.outcome_model,
    method='isotonic',  # or 'sigmoid'
    cv=5
)

calibrated_model.fit(X_train, y_train)

# Now probabilities are better calibrated
```

---

## 📊 Expected Improvements

| Strategy | Expected Accuracy Gain | Difficulty |
|----------|----------------------|------------|
| Hyperparameter tuning | +2-5% | Easy |
| Ensemble methods | +3-7% | Medium |
| More historical data | +5-10% | Easy |
| Betting odds integration | +10-15% | Medium |
| Player-level data | +5-10% | Hard |
| Weather data | +1-3% | Medium |
| Deep learning | +0-8% | Hard |
| xG model | +5-10% | Hard |

**Realistic Target:** 65-75% accuracy (from current 50-60%)

---

## 🎯 Quick Wins (Implement First)

1. **Hyperparameter Tuning** (1 hour)
   - Use GridSearchCV on RandomForest
   - Expected: +2-3% accuracy

2. **Add More Historical Data** (30 min)
   - Fetch 2019-2024 seasons
   - Expected: +5% accuracy

3. **Ensemble Model** (2 hours)
   - Combine RandomForest + XGBoost
   - Expected: +3-5% accuracy

4. **Better Feature Engineering** (3 hours)
   - Add streaks, rest days, league position
   - Expected: +3-5% accuracy

---

## 🔧 Implementation Template

```python
# src/models/improved_predictor.py

class ImprovedMatchPredictor(MatchPredictor):
    """Enhanced predictor with multiple improvements"""
    
    def __init__(self):
        super().__init__()
        
        # Use ensemble
        self.outcome_model = VotingClassifier(
            estimators=[
                ('rf', RandomForestClassifier(n_estimators=200, max_depth=15)),
                ('xgb', XGBClassifier(n_estimators=200, max_depth=10))
            ],
            voting='soft'
        )
    
    def create_enhanced_features(self, home_id, away_id):
        """Add advanced features"""
        base_features = super().prepare_prediction_features(home_id, away_id)
        
        # Add new features
        enhanced = {
            **base_features,
            'home_streak': self.calculate_streak(home_id),
            'away_streak': self.calculate_streak(away_id),
            'position_diff': self.get_position_diff(home_id, away_id),
            'home_motivation': self.calculate_motivation(home_id),
            'away_motivation': self.calculate_motivation(away_id)
        }
        
        return enhanced
```

---

## 📚 Resources

- **Research Papers**: "A Machine Learning Framework for Sport Result Prediction"
- **Kaggle Competitions**: European Soccer Database
- **APIs**: 
  - Football-Data.org (premium)
  - API-Football
  - The Odds API
- **Books**: "The Numbers Game" by Anderson & Sally

---

## ⚠️ Important Notes

1. **Diminishing Returns**: Getting above 70% is extremely difficult due to football's inherent randomness
2. **Overfitting Risk**: More features can hurt if not careful
3. **Data Quality**: Better data > Better algorithms
4. **Reality Check**: Even professional betting models rarely exceed 75% accuracy

---

## 🎓 Conclusion

The current model is already **well-designed and competitive**. The biggest gains will come from:
1. ✅ More data (seasons, leagues)
2. ✅ Ensemble methods
3. ✅ Hyperparameter tuning
4. ✅ External data (betting odds, weather, players)

Focus on **quick wins first**, then explore advanced techniques if needed.
