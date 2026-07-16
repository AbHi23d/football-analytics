"""Feature engineering for match prediction models."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from ..data_collection.database import DatabaseManager
from ..preprocessing.data_cleaner import clean_match_data, get_recent_form
from ..analysis.statistics import ELORatingSystem, calculate_form_score


class FeatureEngineer:
    """Creates features for machine learning models."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize feature engineer."""
        self.db = db_manager or DatabaseManager()
        self.elo_system = ELORatingSystem()
    
    def create_match_features(self, matches_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create features for all matches in the dataset.
        
        Args:
            matches_df: DataFrame with match data
            
        Returns:
            DataFrame with engineered features
        """
        # Calculate ELO ratings
        elo_ratings = self.elo_system.calculate_ratings_from_matches(matches_df)
        
        features = []
        
        for idx, match in matches_df.iterrows():
            if match['status'] != 'FINISHED':
                continue
            
            # Get matches before this one
            past_matches = matches_df[matches_df['utc_date'] < match['utc_date']]
            
            # Create features for this match
            match_features = self._create_single_match_features(
                match,
                past_matches,
                elo_ratings
            )
            
            features.append(match_features)
        
        return pd.DataFrame(features)
    
    def _create_single_match_features(
        self, 
        match: pd.Series, 
        past_matches: pd.DataFrame,
        elo_ratings: Dict[int, float]
    ) -> Dict:
        """Create features for a single match."""
        home_id = match['home_team_id']
        away_id = match['away_team_id']
        
        # ELO ratings
        home_elo = elo_ratings.get(home_id, 1500)
        away_elo = elo_ratings.get(away_id, 1500)
        elo_diff = home_elo - away_elo
        
        # Recent form (last 5 matches)
        home_form = get_recent_form(past_matches, home_id, n_matches=5)
        away_form = get_recent_form(past_matches, away_id, n_matches=5)
        
        home_form_score = calculate_form_score(home_form)
        away_form_score = calculate_form_score(away_form)
        
        # Rolling statistics
        home_stats = self._calculate_rolling_stats(past_matches, home_id, window=5)
        away_stats = self._calculate_rolling_stats(past_matches, away_id, window=5)
        
        # Head-to-head
        h2h_stats = self._get_h2h_features(past_matches, home_id, away_id)
        
        # Target variables
        if match['result'] == 'HOME_WIN':
            target = 0
        elif match['result'] == 'DRAW':
            target = 1
        else:
            target = 2
        
        return {
            # Match info
            'match_id': match['id'],
            'home_team_id': home_id,
            'away_team_id': away_id,
            
            # ELO features
            'home_elo': home_elo,
            'away_elo': away_elo,
            'elo_diff': elo_diff,
            
            # Form features
            'home_form_score': home_form_score,
            'away_form_score': away_form_score,
            'form_diff': home_form_score - away_form_score,
            
            # Rolling statistics
            'home_avg_goals_scored': home_stats['avg_goals_scored'],
            'home_avg_goals_conceded': home_stats['avg_goals_conceded'],
            'away_avg_goals_scored': away_stats['avg_goals_scored'],
            'away_avg_goals_conceded': away_stats['avg_goals_conceded'],
            
            # Goal expectation
            'home_expected_goals': (home_stats['avg_goals_scored'] + away_stats['avg_goals_conceded']) / 2,
            'away_expected_goals': (away_stats['avg_goals_scored'] + home_stats['avg_goals_conceded']) / 2,
            
            # Points per game
            'home_ppg': home_stats['ppg'],
            'away_ppg': away_stats['ppg'],
            
            # Head-to-head
            'h2h_home_wins': h2h_stats['home_wins'],
            'h2h_away_wins': h2h_stats['away_wins'],
            'h2h_draws': h2h_stats['draws'],
            
            # Target
            'result': target,
            'home_goals': match['home_score'],
            'away_goals': match['away_score'],
            'total_goals': match['home_score'] + match['away_score']
        }
    
    def _calculate_rolling_stats(
        self, 
        matches_df: pd.DataFrame, 
        team_id: int, 
        window: int = 5
    ) -> Dict:
        """Calculate rolling statistics for a team."""
        team_matches = matches_df[
            ((matches_df['home_team_id'] == team_id) | 
             (matches_df['away_team_id'] == team_id)) &
            (matches_df['status'] == 'FINISHED')
        ].copy()
        
        if len(team_matches) == 0:
            return {
                'avg_goals_scored': 1.0,
                'avg_goals_conceded': 1.0,
                'ppg': 1.0
            }
        
        team_matches = team_matches.sort_values('utc_date', ascending=False).head(window)
        
        goals_scored = []
        goals_conceded = []
        points = []
        
        for _, match in team_matches.iterrows():
            is_home = match['home_team_id'] == team_id
            
            if is_home:
                goals_scored.append(match['home_score'])
                goals_conceded.append(match['away_score'])
                if match['result'] == 'HOME_WIN':
                    points.append(3)
                elif match['result'] == 'DRAW':
                    points.append(1)
                else:
                    points.append(0)
            else:
                goals_scored.append(match['away_score'])
                goals_conceded.append(match['home_score'])
                if match['result'] == 'AWAY_WIN':
                    points.append(3)
                elif match['result'] == 'DRAW':
                    points.append(1)
                else:
                    points.append(0)
        
        return {
            'avg_goals_scored': np.mean(goals_scored) if goals_scored else 1.0,
            'avg_goals_conceded': np.mean(goals_conceded) if goals_conceded else 1.0,
            'ppg': np.mean(points) if points else 1.0
        }
    
    def _get_h2h_features(
        self, 
        matches_df: pd.DataFrame, 
        home_id: int, 
        away_id: int
    ) -> Dict:
        """Get head-to-head features between two teams."""
        h2h = matches_df[
            ((matches_df['home_team_id'] == home_id) & (matches_df['away_team_id'] == away_id)) |
            ((matches_df['home_team_id'] == away_id) & (matches_df['away_team_id'] == home_id))
        ]
        
        home_wins = len(h2h[
            ((h2h['home_team_id'] == home_id) & (h2h['result'] == 'HOME_WIN')) |
            ((h2h['away_team_id'] == home_id) & (h2h['result'] == 'AWAY_WIN'))
        ])
        
        away_wins = len(h2h[
            ((h2h['home_team_id'] == away_id) & (h2h['result'] == 'HOME_WIN')) |
            ((h2h['away_team_id'] == away_id) & (h2h['result'] == 'AWAY_WIN'))
        ])
        
        draws = len(h2h[h2h['result'] == 'DRAW'])
        
        return {
            'home_wins': home_wins,
            'away_wins': away_wins,
            'draws': draws
        }
    
    def prepare_prediction_features(
        self, 
        home_team_id: int, 
        away_team_id: int
    ) -> Dict:
        """
        Prepare features for predicting a future match.
        
        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            
        Returns:
            Dictionary with features for prediction
        """
        all_matches = clean_match_data(self.db.get_all_matches())
        
        # Calculate current ELO ratings
        elo_ratings = self.elo_system.calculate_ratings_from_matches(all_matches)
        
        # Create features similar to training data
        features = self._create_single_match_features(
            pd.Series({
                'id': 0,
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'status': 'SCHEDULED',
                'result': None,
                'home_score': 0,
                'away_score': 0,
                'utc_date': pd.Timestamp.now()
            }),
            all_matches,
            elo_ratings
        )
        
        return features
