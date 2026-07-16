"""Team performance analysis functions."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from ..data_collection.database import DatabaseManager
from ..preprocessing.data_cleaner import clean_match_data, prepare_team_statistics, get_recent_form


class TeamAnalyzer:
    """Analyzes team performance and statistics."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize team analyzer."""
        self.db = db_manager or DatabaseManager()
    
    def get_team_overview(self, team_id: int) -> Dict:
        """
        Get comprehensive overview of team performance.
        
        Args:
            team_id: Team ID
            
        Returns:
            Dictionary with team overview statistics
        """
        team = self.db.get_team_by_id(team_id)
        if not team:
            return {}
        
        matches = self.db.get_team_matches(team_id)
        matches_df = clean_match_data(matches)
        
        stats = prepare_team_statistics(matches_df, team_id)
        form = get_recent_form(matches_df, team_id, n_matches=5)
        
        # Home vs Away performance
        home_matches = matches_df[matches_df['home_team_id'] == team_id]
        away_matches = matches_df[matches_df['away_team_id'] == team_id]
        
        home_stats = prepare_team_statistics(home_matches, team_id)
        away_stats = prepare_team_statistics(away_matches, team_id)
        
        return {
            'team': team,
            'overall_stats': stats,
            'home_stats': home_stats,
            'away_stats': away_stats,
            'recent_form': form,
            'form_string': ''.join(form)
        }
    
    def compare_teams(self, team1_id: int, team2_id: int) -> Dict:
        """
        Compare two teams head-to-head and overall statistics.
        
        Args:
            team1_id: First team ID
            team2_id: Second team ID
            
        Returns:
            Dictionary with comparison data
        """
        team1 = self.db.get_team_by_id(team1_id)
        team2 = self.db.get_team_by_id(team2_id)
        
        if not team1 or not team2:
            return {}
        
        # Overall statistics
        team1_matches = clean_match_data(self.db.get_team_matches(team1_id))
        team2_matches = clean_match_data(self.db.get_team_matches(team2_id))
        
        team1_stats = prepare_team_statistics(team1_matches, team1_id)
        team2_stats = prepare_team_statistics(team2_matches, team2_id)
        
        # Head-to-head
        h2h_matches = clean_match_data(self.db.get_head_to_head(team1_id, team2_id))
        h2h_stats = self._analyze_head_to_head(h2h_matches, team1_id, team2_id)
        
        # Recent form
        team1_form = get_recent_form(team1_matches, team1_id, n_matches=5)
        team2_form = get_recent_form(team2_matches, team2_id, n_matches=5)
        
        return {
            'team1': {
                'info': team1,
                'stats': team1_stats,
                'form': team1_form
            },
            'team2': {
                'info': team2,
                'stats': team2_stats,
                'form': team2_form
            },
            'head_to_head': h2h_stats
        }
    
    def _analyze_head_to_head(self, matches_df: pd.DataFrame, team1_id: int, team2_id: int) -> Dict:
        """Analyze head-to-head record between two teams."""
        if len(matches_df) == 0:
            return {
                'total_matches': 0,
                'team1_wins': 0,
                'team2_wins': 0,
                'draws': 0,
                'recent_matches': []
            }
        
        team1_wins = 0
        team2_wins = 0
        draws = 0
        
        for _, match in matches_df.iterrows():
            if match['status'] != 'FINISHED':
                continue
            
            if match['home_team_id'] == team1_id:
                if match['result'] == 'HOME_WIN':
                    team1_wins += 1
                elif match['result'] == 'AWAY_WIN':
                    team2_wins += 1
                else:
                    draws += 1
            else:
                if match['result'] == 'HOME_WIN':
                    team2_wins += 1
                elif match['result'] == 'AWAY_WIN':
                    team1_wins += 1
                else:
                    draws += 1
        
        # Get recent matches
        recent = matches_df.head(5).to_dict('records')
        
        return {
            'total_matches': len(matches_df[matches_df['status'] == 'FINISHED']),
            'team1_wins': team1_wins,
            'team2_wins': team2_wins,
            'draws': draws,
            'recent_matches': recent
        }
    
    def get_league_position_trend(self, team_id: int, competition: str, season: int) -> List[Dict]:
        """
        Get team's league position trend over the season (would require historical standings).
        
        Args:
            team_id: Team ID
            competition: Competition code
            season: Season year
            
        Returns:
            List of position data points
        """
        # This is a simplified version - in production would track standings over time
        standings = self.db.get_standings(competition, season)
        standings_df = pd.DataFrame(standings)
        
        if len(standings_df) == 0:
            return []
        
        team_standing = standings_df[standings_df['team_id'] == team_id]
        
        if len(team_standing) == 0:
            return []
        
        return team_standing.to_dict('records')
    
    def get_goal_statistics(self, team_id: int) -> Dict:
        """
        Get detailed goal-scoring statistics for a team.
        
        Args:
            team_id: Team ID
            
        Returns:
            Dictionary with goal statistics
        """
        matches = clean_match_data(self.db.get_team_matches(team_id))
        finished = matches[matches['status'] == 'FINISHED']
        
        if len(finished) == 0:
            return {}
        
        # Goals by half
        first_half_goals = []
        second_half_goals = []
        
        for _, match in finished.iterrows():
            is_home = match['home_team_id'] == team_id
            
            if is_home:
                if match['half_time_home'] >= 0:
                    first_half_goals.append(match['half_time_home'])
                    second_half_goals.append(match['home_score'] - match['half_time_home'])
            else:
                if match['half_time_away'] >= 0:
                    first_half_goals.append(match['half_time_away'])
                    second_half_goals.append(match['away_score'] - match['half_time_away'])
        
        stats = prepare_team_statistics(matches, team_id)
        
        return {
            'total_goals': stats['goals_scored'],
            'avg_goals_per_game': stats['avg_goals_scored'],
            'first_half_avg': np.mean(first_half_goals) if first_half_goals else 0,
            'second_half_avg': np.mean(second_half_goals) if second_half_goals else 0,
            'goals_conceded': stats['goals_conceded'],
            'avg_conceded_per_game': stats['avg_goals_conceded'],
            'clean_sheets': len(finished[
                ((finished['home_team_id'] == team_id) & (finished['away_score'] == 0)) |
                ((finished['away_team_id'] == team_id) & (finished['home_score'] == 0))
            ])
        }
