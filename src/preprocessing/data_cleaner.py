"""Data cleaning and preprocessing functions."""

import pandas as pd
from typing import List, Dict
from datetime import datetime


def clean_match_data(matches: List[Dict]) -> pd.DataFrame:
    """
    Clean and transform match data into a pandas DataFrame.
    
    Args:
        matches: List of match dictionaries from database
        
    Returns:
        Cleaned DataFrame with match data
    """
    if not matches:
        return pd.DataFrame()
    
    df = pd.DataFrame(matches)
    
    # Convert date to datetime
    if 'utc_date' in df.columns:
        df['utc_date'] = pd.to_datetime(df['utc_date'])
        df['date'] = df['utc_date'].dt.date
        df['year'] = df['utc_date'].dt.year
        df['month'] = df['utc_date'].dt.month
    
    # Handle missing scores (scheduled matches)
    df['home_score'] = df['home_score'].fillna(-1).astype(int)
    df['away_score'] = df['away_score'].fillna(-1).astype(int)
    
    # Create result column for finished matches
    df['result'] = None
    finished = df['status'] == 'FINISHED'
    df.loc[finished & (df['home_score'] > df['away_score']), 'result'] = 'HOME_WIN'
    df.loc[finished & (df['home_score'] < df['away_score']), 'result'] = 'AWAY_WIN'
    df.loc[finished & (df['home_score'] == df['away_score']), 'result'] = 'DRAW'
    
    # Calculate total goals
    df['total_goals'] = df.apply(
        lambda x: x['home_score'] + x['away_score'] if x['home_score'] >= 0 else 0, 
        axis=1
    )
    
    # Sort by date
    df = df.sort_values('utc_date', ascending=False).reset_index(drop=True)
    
    return df


def clean_standings_data(standings: List[Dict]) -> pd.DataFrame:
    """
    Clean and transform standings data into a pandas DataFrame.
    
    Args:
        standings: List of standing dictionaries from database
        
    Returns:
        Cleaned DataFrame with standings data
    """
    if not standings:
        return pd.DataFrame()
    
    df = pd.DataFrame(standings)
    
    # Ensure numeric columns are properly typed
    numeric_cols = ['position', 'played_games', 'won', 'draw', 'lost', 
                   'points', 'goals_for', 'goals_against', 'goal_difference']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    # Calculate additional metrics
    if 'played_games' in df.columns and df['played_games'].sum() > 0:
        df['win_rate'] = (df['won'] / df['played_games']).fillna(0)
        df['points_per_game'] = (df['points'] / df['played_games']).fillna(0)
    
    # Sort by position
    df = df.sort_values('position').reset_index(drop=True)
    
    return df


def prepare_team_statistics(matches_df: pd.DataFrame, team_id: int) -> Dict:
    """
    Calculate statistics for a specific team from match data.
    
    Args:
        matches_df: DataFrame with match data
        team_id: Team ID
        
    Returns:
        Dictionary with team statistics
    """
    # Filter matches for this team
    team_matches = matches_df[
        (matches_df['home_team_id'] == team_id) | 
        (matches_df['away_team_id'] == team_id)
    ].copy()
    
    finished_matches = team_matches[team_matches['status'] == 'FINISHED'].copy()
    
    if len(finished_matches) == 0:
        return {
            'total_matches': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_scored': 0,
            'goals_conceded': 0,
            'win_rate': 0.0,
            'avg_goals_scored': 0.0,
            'avg_goals_conceded': 0.0
        }
    
    # Calculate statistics
    home_matches = finished_matches[finished_matches['home_team_id'] == team_id]
    away_matches = finished_matches[finished_matches['away_team_id'] == team_id]
    
    # Wins, draws, losses
    home_wins = len(home_matches[home_matches['result'] == 'HOME_WIN'])
    away_wins = len(away_matches[away_matches['result'] == 'AWAY_WIN'])
    wins = home_wins + away_wins
    
    draws = len(finished_matches[finished_matches['result'] == 'DRAW'])
    losses = len(finished_matches) - wins - draws
    
    # Goals
    goals_scored = (
        home_matches['home_score'].sum() + 
        away_matches['away_score'].sum()
    )
    goals_conceded = (
        home_matches['away_score'].sum() + 
        away_matches['home_score'].sum()
    )
    
    total_matches = len(finished_matches)
    
    return {
        'total_matches': total_matches,
        'wins': wins,
        'draws': draws,
        'losses': losses,
        'goals_scored': int(goals_scored),
        'goals_conceded': int(goals_conceded),
        'goal_difference': int(goals_scored - goals_conceded),
        'win_rate': wins / total_matches if total_matches > 0 else 0.0,
        'avg_goals_scored': goals_scored / total_matches if total_matches > 0 else 0.0,
        'avg_goals_conceded': goals_conceded / total_matches if total_matches > 0 else 0.0,
        'points': wins * 3 + draws
    }


def get_recent_form(matches_df: pd.DataFrame, team_id: int, n_matches: int = 5) -> List[str]:
    """
    Get recent form (W/D/L) for a team.
    
    Args:
        matches_df: DataFrame with match data
        team_id: Team ID
        n_matches: Number of recent matches to consider
        
    Returns:
        List of results (e.g., ['W', 'W', 'D', 'L', 'W'])
    """
    team_matches = matches_df[
        ((matches_df['home_team_id'] == team_id) | 
         (matches_df['away_team_id'] == team_id)) &
        (matches_df['status'] == 'FINISHED')
    ].copy()
    
    team_matches = team_matches.sort_values('utc_date', ascending=False).head(n_matches)
    
    form = []
    for _, match in team_matches.iterrows():
        if match['home_team_id'] == team_id:
            if match['result'] == 'HOME_WIN':
                form.append('W')
            elif match['result'] == 'DRAW':
                form.append('D')
            else:
                form.append('L')
        else:  # Away team
            if match['result'] == 'AWAY_WIN':
                form.append('W')
            elif match['result'] == 'DRAW':
                form.append('D')
            else:
                form.append('L')
    
    return form


def calculate_rolling_stats(matches_df: pd.DataFrame, team_id: int, window: int = 5) -> pd.DataFrame:
    """
    Calculate rolling statistics for a team.
    
    Args:
        matches_df: DataFrame with match data
        team_id: Team ID
        window: Rolling window size
        
    Returns:
        DataFrame with rolling statistics
    """
    team_matches = matches_df[
        ((matches_df['home_team_id'] == team_id) | 
         (matches_df['away_team_id'] == team_id)) &
        (matches_df['status'] == 'FINISHED')
    ].copy()
    
    team_matches = team_matches.sort_values('utc_date').reset_index(drop=True)
    
    # Create columns for team-specific goals
    team_matches['team_goals'] = team_matches.apply(
        lambda x: x['home_score'] if x['home_team_id'] == team_id else x['away_score'],
        axis=1
    )
    team_matches['opponent_goals'] = team_matches.apply(
        lambda x: x['away_score'] if x['home_team_id'] == team_id else x['home_score'],
        axis=1
    )
    team_matches['points'] = team_matches.apply(
        lambda x: 3 if (x['home_team_id'] == team_id and x['result'] == 'HOME_WIN') or 
                      (x['away_team_id'] == team_id and x['result'] == 'AWAY_WIN')
                 else 1 if x['result'] == 'DRAW' else 0,
        axis=1
    )
    
    # Calculate rolling averages
    team_matches['rolling_goals_scored'] = team_matches['team_goals'].rolling(window=window, min_periods=1).mean()
    team_matches['rolling_goals_conceded'] = team_matches['opponent_goals'].rolling(window=window, min_periods=1).mean()
    team_matches['rolling_points'] = team_matches['points'].rolling(window=window, min_periods=1).mean()
    
    return team_matches
