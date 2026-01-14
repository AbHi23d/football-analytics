"""
Helper Functions for Football Analytics

Simple, reusable functions for data loading, feature engineering, and predictions.
This is the data science approach - no classes, just functions.
"""

import pandas as pd
import numpy as np
import sqlite3
import os
import pickle
import json

# =================================================================
# DATA LOADING
# =================================================================

def load_data(db_path='data/database/football.db'):
    """
    Load match data from database.
    
    Returns:
        DataFrame with all finished matches
    """
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT *
    FROM matches
    WHERE status = 'FINISHED'
    ORDER BY utc_date
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Basic preparation
    df['utc_date'] = pd.to_datetime(df['utc_date'])
    df['total_goals'] = df['home_score'] + df['away_score']
    
    return df


# =================================================================
# FEATURE ENGINEERING
# =================================================================

def calculate_elo(df, k_factor=20):
    """Calculate ELO ratings for all teams."""
    elo_ratings = {}
    for team in pd.concat([df['home_team_name'], df['away_team_name']]).unique():
        elo_ratings[team] = 1500
    
    home_elos = []
    away_elos = []
    
    for idx, match in df.iterrows():
        home_team = match['home_team_name']
        away_team = match['away_team_name']
        
        home_elo = elo_ratings[home_team]
        away_elo = elo_ratings[away_team]
        
        home_elos.append(home_elo)
        away_elos.append(away_elo)
        
        # Expected outcome
        expected_home = 1 / (1 + 10**((away_elo - home_elo) / 400))
        
        # Actual outcome
        if match['winner'] in ['HOME_TEAM', 'H']:
            actual = 1
        elif match['winner'] in ['DRAW', 'D']:
            actual = 0.5
        else:
            actual = 0
        
        # Update ratings
        elo_ratings[home_team] += k_factor * (actual - expected_home)
        elo_ratings[away_team] += k_factor * ((1-actual) - (1-expected_home))
    
    return home_elos, away_elos


def calculate_form(df):
    """Calculate recent form (last 5 matches)."""
    df = df.sort_values('utc_date').copy()
    df['home_form'] = 0.0
    df['away_form'] = 0.0
    
    for team in df['home_team_name'].unique():
        team_matches = df[
            (df['home_team_name'] == team) | (df['away_team_name'] == team)
        ].copy()
        
        points = []
        for _, match in team_matches.iterrows():
            if match['home_team_name'] == team:
                if match['winner'] in ['HOME_TEAM', 'H']:
                    points.append(3)
                elif match['winner'] in ['DRAW', 'D']:
                    points.append(1)
                else:
                    points.append(0)
            else:
                if match['winner'] in ['AWAY_TEAM', 'A']:
                    points.append(3)
                elif match['winner'] in ['DRAW', 'D']:
                    points.append(1)
                else:
                    points.append(0)
        
        team_matches['points'] = points
        # Shift by 1 to use only PAST matches (prevents data leakage)
        team_matches['form'] = team_matches['points'].rolling(5, min_periods=1).mean().shift(1).fillna(0)
        
        for idx, row in team_matches.iterrows():
            if row['home_team_name'] == team:
                df.loc[idx, 'home_form'] = row['form']
            else:
                df.loc[idx, 'away_form'] = row['form']
    
    return df


def engineer_features(df):
    """
    Engineer all features for modeling.
    
    Creates 15 features:
    - ELO ratings (strength)
    - Recent form (momentum) 
    - Win streaks (hot/cold teams)
    - Clean sheets (defensive momentum)
    - Goal scoring/conceding averages (offense/defense)
    - Head-to-head history
    - Rest days (fatigue)
    - Season context
    
    Returns:
        DataFrame with features added
    """
    df = df.copy()
    df = df.sort_values('utc_date').reset_index(drop=True)
    
    # 1-2: ELO ratings
    df['home_elo'], df['away_elo'] = calculate_elo(df)
    df['elo_diff'] = df['home_elo'] - df['away_elo']
    
    # 3: Form (overall)
    df = calculate_form(df)
    df['form_diff'] = df['home_form'] - df['away_form']
    
    # 4-5: Win streaks (NEW)
    df['home_win_streak'] = 0
    df['away_win_streak'] = 0
    
    for team in df['home_team_name'].unique():
        team_matches = df[(df['home_team_name'] == team) | (df['away_team_name'] == team)].copy()
        
        streak = 0
        for idx in team_matches.index:
            match = df.loc[idx]
            
            # Check if team won
            if match['home_team_name'] == team:
                won = match['winner'] in ['HOME_TEAM', 'H']
                df.loc[idx, 'home_win_streak'] = streak
            else:
                won = match['winner'] in ['AWAY_TEAM', 'A']
                df.loc[idx, 'away_win_streak'] = streak
            
            # Update streak
            if won:
                streak += 1
            else:
                streak = 0
    
    # 6-7: Clean sheet streaks (NEW)
    df['home_clean_sheets'] = 0
    df['away_clean_sheets'] = 0
    
    for team in df['home_team_name'].unique():
        # Home clean sheets
        home_matches = df[df['home_team_name'] == team].copy()
        home_matches['clean'] = (home_matches['away_score'] == 0).astype(int)
        home_matches['clean_streak'] = home_matches['clean'].rolling(5, min_periods=1).sum().shift(1).fillna(0)
        
        for idx in home_matches.index:
            df.loc[idx, 'home_clean_sheets'] = home_matches.loc[idx, 'clean_streak']
        
        # Away clean sheets
        away_matches = df[df['away_team_name'] == team].copy()
        away_matches['clean'] = (away_matches['home_score'] == 0).astype(int)
        away_matches['clean_streak'] = away_matches['clean'].rolling(5, min_periods=1).sum().shift(1).fillna(0)
        
        for idx in away_matches.index:
            df.loc[idx, 'away_clean_sheets'] = away_matches.loc[idx, 'clean_streak']
    
    # 8-11: Rolling goal statistics
    for team in df['home_team_name'].unique():
        # Home matches
        home_mask = df['home_team_name'] == team
        # Shift by 1 to use only past match results
        df.loc[home_mask, 'home_goals_avg'] = df.loc[home_mask, 'home_score'].rolling(5, min_periods=1).mean().shift(1).fillna(0)
        df.loc[home_mask, 'home_conceded_avg'] = df.loc[home_mask, 'away_score'].rolling(5, min_periods=1).mean().shift(1).fillna(0)
        
        # Away matches
        away_mask = df['away_team_name'] == team
        df.loc[away_mask, 'away_goals_avg'] = df.loc[away_mask, 'away_score'].rolling(5, min_periods=1).mean().shift(1).fillna(0)
        df.loc[away_mask, 'away_conceded_avg'] = df.loc[away_mask, 'home_score'].rolling(5, min_periods=1).mean().shift(1).fillna(0)
    
    # Fill NaN with league averages
    df['home_goals_avg'] = df['home_goals_avg'].fillna(df['home_score'].mean())
    df['away_goals_avg'] = df['away_goals_avg'].fillna(df['away_score'].mean())
    df['home_conceded_avg'] = df['home_conceded_avg'].fillna(df['away_score'].mean())
    df['away_conceded_avg'] = df['away_conceded_avg'].fillna(df['home_score'].mean())
    df['home_clean_sheets'] = df['home_clean_sheets'].fillna(0)
    df['away_clean_sheets'] = df['away_clean_sheets'].fillna(0)
    
    # 12-13: Head-to-head record
    df['h2h_home_wins'] = 0
    df['h2h_away_wins'] = 0
    
    for idx in range(len(df)):
        match = df.iloc[idx]
        prior_h2h = df[(df.index < idx) &
                      (((df['home_team_name'] == match['home_team_name']) & 
                        (df['away_team_name'] == match['away_team_name'])) |
                       ((df['home_team_name'] == match['away_team_name']) & 
                        (df['away_team_name'] == match['home_team_name'])))]
        
        if len(prior_h2h) > 0:
            home_wins = len(prior_h2h[
                ((prior_h2h['home_team_name'] == match['home_team_name']) & 
                 (prior_h2h['winner'].isin(['HOME_TEAM', 'H']))) |
                ((prior_h2h['away_team_name'] == match['home_team_name']) & 
                 (prior_h2h['winner'].isin(['AWAY_TEAM', 'A'])))
            ])
            df.at[idx, 'h2h_home_wins'] = home_wins
            df.at[idx, 'h2h_away_wins'] = len(prior_h2h) - home_wins
    
    # 14: Rest days
    df['rest_days'] = 7.0
    for team in df['home_team_name'].unique():
        team_matches = df[(df['home_team_name'] == team) | (df['away_team_name'] == team)].copy()
        team_matches['days_since_last'] = team_matches['utc_date'].diff().dt.days
        
        for idx in team_matches.index:
            if pd.notna(team_matches.loc[idx, 'days_since_last']):
                df.loc[idx, 'rest_days'] = team_matches.loc[idx, 'days_since_last']
    
    df['rest_days'] = df['rest_days'].fillna(7.0).clip(0, 30)
    
    # 15: Season progress
    df = df.sort_values(['season', 'utc_date'])
    df['season_progress'] = df.groupby('season').cumcount() / df.groupby('season')['season'].transform('count')
    
    # Context features
    df['month'] = df['utc_date'].dt.month
    df['is_december'] = (df['month'] == 12).astype(int)
    
    return df


# =================================================================
# MODEL UTILITIES
# =================================================================

def load_model(model_path='models/simple_model.pkl'):
    """Load trained model from file."""
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model


def load_features():
    """Load feature list."""
    with open('models/features.json', 'r') as f:
        features = json.load(f)
    return features


def predict_match(home_team, away_team, df=None):
    """
    Predict outcome of a match.
    
    Args:
        home_team: Name of home team
        away_team: Name of away team
        df: Optional dataframe with historical data
        
    Returns:
        Dictionary with prediction and probabilities
    """
    # Load model and features
    model = load_model()
    features = load_features()
    
    # Load data if not provided
    if df is None:
        df = load_data()
        df = engineer_features(df)
    
    # Get latest stats for both teams
    home_recent = df[df['home_team_name'] == home_team].tail(1)
    away_recent = df[df['away_team_name'] == away_team].tail(1)
    
    if len(home_recent) == 0 or len(away_recent) == 0:
        return {'error': 'Team not found in database'}
    
    # Create feature vector with ALL 15 features in correct order
    feature_dict = {
        'elo_diff': home_recent['home_elo'].values[0] - away_recent['away_elo'].values[0],
        'form_diff': home_recent['home_form'].values[0] - away_recent['away_form'].values[0],
        'home_win_streak': home_recent['home_win_streak'].values[0],
        'away_win_streak': away_recent['away_win_streak'].values[0],
        'home_clean_sheets': home_recent['home_clean_sheets'].values[0],
        'away_clean_sheets': away_recent['away_clean_sheets'].values[0],
        'home_goals_avg': home_recent['home_goals_avg'].values[0],
        'away_goals_avg': away_recent['away_goals_avg'].values[0],
        'home_conceded_avg': home_recent['home_conceded_avg'].values[0],
        'away_conceded_avg': away_recent['away_conceded_avg'].values[0],
        'h2h_home_wins': home_recent['h2h_home_wins'].values[0],
        'h2h_away_wins': home_recent['h2h_away_wins'].values[0],
        'rest_days': 7,  # Default assumption
        'season_progress': pd.Timestamp.now().dayofyear / 365,
        'is_december': 1 if pd.Timestamp.now().month == 12 else 0
    }
    
    X = pd.DataFrame([feature_dict], columns=features)
    
    # Predict (XGBoost returns numeric, need to decode)
    prediction_encoded = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    
    # Decode prediction (XGBoost uses 0,1,2 for Away Win, Draw, Home Win)
    class_names = ['Away Win', 'Draw', 'Home Win']
    prediction = class_names[int(prediction_encoded)]
    
    return {
        'prediction': prediction,
        'home_win_prob': probabilities[2],  # Index 2 for Home Win
        'draw_prob': probabilities[1],      # Index 1 for Draw
        'away_win_prob': probabilities[0]   # Index 0 for Away Win
    }

