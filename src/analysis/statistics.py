"""Statistical calculations and metrics for football analytics."""

import pandas as pd
import numpy as np
from typing import Dict, List


class ELORatingSystem:
    """ELO rating system for team strength calculation."""
    
    def __init__(self, k_factor: int = 40, initial_rating: int = 1500):
        """
        Initialize ELO rating system.
        
        Args:
            k_factor: K-factor for rating updates
            initial_rating: Initial rating for new teams
        """
        self.k_factor = k_factor
        self.initial_rating = initial_rating
        self.ratings = {}
    
    def get_rating(self, team_id: int) -> int:
        """Get current rating for a team."""
        return self.ratings.get(team_id, self.initial_rating)
    
    def expected_score(self, rating_a: int, rating_b: int) -> float:
        """
        Calculate expected score for team A against team B.
        
        Args:
            rating_a: Team A's rating
            rating_b: Team B's rating
            
        Returns:
            Expected score (0 to 1)
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def update_ratings(self, team_a_id: int, team_b_id: int, score_a: int, score_b: int):
        """
        Update ratings after a match.
        
        Args:
            team_a_id: Team A ID
            team_b_id: Team B ID
            score_a: Team A's score
            score_b: Team B's score
        """
        rating_a = self.get_rating(team_a_id)
        rating_b = self.get_rating(team_b_id)
        
        expected_a = self.expected_score(rating_a, rating_b)
        expected_b = self.expected_score(rating_b, rating_a)
        
        # Actual result (1 for win, 0.5 for draw, 0 for loss)
        if score_a > score_b:
            actual_a, actual_b = 1.0, 0.0
        elif score_a < score_b:
            actual_a, actual_b = 0.0, 1.0
        else:
            actual_a, actual_b = 0.5, 0.5
        
        # Update ratings
        self.ratings[team_a_id] = rating_a + self.k_factor * (actual_a - expected_a)
        self.ratings[team_b_id] = rating_b + self.k_factor * (actual_b - expected_b)
    
    def calculate_ratings_from_matches(self, matches_df: pd.DataFrame) -> Dict[int, float]:
        """
        Calculate ELO ratings from historical matches.
        
        Args:
            matches_df: DataFrame with match data
            
        Returns:
            Dictionary mapping team IDs to ELO ratings
        """
        self.ratings = {}
        
        finished = matches_df[matches_df['status'] == 'FINISHED'].copy()
        finished = finished.sort_values('utc_date')
        
        for _, match in finished.iterrows():
            self.update_ratings(
                match['home_team_id'],
                match['away_team_id'],
                match['home_score'],
                match['away_score']
            )
        
        return self.ratings.copy()


def calculate_form_score(form: List[str]) -> float:
    """
    Calculate numerical form score from recent results.
    
    Args:
        form: List of results (e.g., ['W', 'D', 'L', 'W', 'W'])
        
    Returns:
        Form score (0 to 1)
    """
    if not form:
        return 0.5
    
    points = {'W': 1.0, 'D': 0.5, 'L': 0.0}
    scores = [points.get(result, 0.0) for result in form]
    
    # Weight recent matches more heavily
    weights = np.linspace(0.5, 1.0, len(scores))
    weighted_score = np.average(scores, weights=weights)
    
    return weighted_score


def calculate_home_advantage(matches_df: pd.DataFrame) -> float:
    """
    Calculate overall home advantage factor.
    
    Args:
        matches_df: DataFrame with match data
        
    Returns:
        Home advantage factor (goals scored advantage)
    """
    finished = matches_df[matches_df['status'] == 'FINISHED']
    
    if len(finished) == 0:
        return 0.0
    
    home_goals = finished['home_score'].mean()
    away_goals = finished['away_score'].mean()
    
    return home_goals - away_goals


def calculate_poisson_probabilities(avg_goals_home: float, avg_goals_away: float, 
                                    max_goals: int = 5) -> Dict:
    """
    Calculate match outcome probabilities using Poisson distribution.
    
    Args:
        avg_goals_home: Expected goals for home team
        avg_goals_away: Expected goals for away team
        max_goals: Maximum goals to consider
        
    Returns:
        Dictionary with win/draw/loss probabilities
    """
    from scipy.stats import poisson
    
    # Calculate probability matrix
    prob_matrix = np.zeros((max_goals + 1, max_goals + 1))
    
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            prob_matrix[i, j] = (
                poisson.pmf(i, avg_goals_home) * 
                poisson.pmf(j, avg_goals_away)
            )
    
    # Calculate outcome probabilities
    home_win = np.sum(np.tril(prob_matrix, -1))
    draw = np.sum(np.diag(prob_matrix))
    away_win = np.sum(np.triu(prob_matrix, 1))
    
    return {
        'home_win': home_win,
        'draw': draw,
        'away_win': away_win
    }


def calculate_team_strength(team_stats: Dict, elo_rating: float = None) -> float:
    """
    Calculate overall team strength score.
    
    Args:
        team_stats: Dictionary with team statistics
        elo_rating: Optional ELO rating
        
    Returns:
        Strength score (0 to 100)
    """
    # Base score from win rate and points
    win_rate = team_stats.get('win_rate', 0.0)
    ppg = team_stats.get('points', 0) / max(team_stats.get('total_matches', 1), 1)
    
    base_score = (win_rate * 50) + (ppg / 3 * 50)
    
    # Adjust for goals
    gd = team_stats.get('goal_difference', 0)
    gd_bonus = min(max(gd, -20), 20)  # Clamp between -20 and 20
    
    # Combine scores
    strength = base_score + gd_bonus
    
    # Scale to 0-100
    strength = max(0, min(100, strength))
    
    return strength


def calculate_momentum(form: List[str]) -> float:
    """
    Calculate momentum score based on recent form trend.
    
    Args:
        form: List of recent results (most recent first)
        
    Returns:
        Momentum score (-1 to 1, positive is improving)
    """
    if len(form) < 2:
        return 0.0
    
    points = {'W': 3, 'D': 1, 'L': 0}
    scores = [points.get(r, 0) for r in form]
    
    # Compare recent half vs earlier half
    mid = len(scores) // 2
    recent_avg = np.mean(scores[:mid]) if mid > 0 else 0
    earlier_avg = np.mean(scores[mid:]) if len(scores[mid:]) > 0 else 0
    
    # Normalize to -1 to 1
    momentum = (recent_avg - earlier_avg) / 3
    
    return max(-1, min(1, momentum))
