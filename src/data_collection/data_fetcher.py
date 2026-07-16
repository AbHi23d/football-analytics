"""High-level data fetching functions for collecting football data."""

from typing import List, Dict, Optional
from tqdm import tqdm
from .api_client import FootballDataAPIClient
from .database import DatabaseManager


class DataFetcher:
    """Fetches and stores football data from API to database."""
    
    def __init__(self, api_client: Optional[FootballDataAPIClient] = None, 
                 db_manager: Optional[DatabaseManager] = None):
        """
        Initialize data fetcher.
        
        Args:
            api_client: API client instance
            db_manager: Database manager instance
        """
        self.api_client = api_client or FootballDataAPIClient()
        self.db = db_manager or DatabaseManager()
    
    def fetch_competition_data(self, competition_code: str, seasons: List[int]):
        """
        Fetch all data for a competition across multiple seasons.
        
        Args:
            competition_code: Competition code (e.g., 'PL')
            seasons: List of season years (e.g., [2023, 2024])
        """
        print(f"\n🏆 Fetching data for {competition_code}")
        
        for season in seasons:
            print(f"\n📅 Season {season}-{season+1}")
            
            # Fetch matches
            print("  📊 Fetching matches...")
            matches = self.api_client.get_competition_matches(
                competition_code=competition_code,
                season=season
            )
            
            print(f"  ✓ Found {len(matches)} matches")
            
            # Store teams and matches
            teams_stored = set()
            for match in tqdm(matches, desc="  💾 Storing matches", unit="match"):
                # Store teams
                home_team = match.get("homeTeam", {})
                away_team = match.get("awayTeam", {})
                
                if home_team.get("id") and home_team["id"] not in teams_stored:
                    self.db.insert_team(home_team)
                    teams_stored.add(home_team["id"])
                
                if away_team.get("id") and away_team["id"] not in teams_stored:
                    self.db.insert_team(away_team)
                    teams_stored.add(away_team["id"])
                
                # Store match
                self.db.insert_match(match)
            
            # Fetch and store standings
            print("  📈 Fetching standings...")
            standings_data = self.api_client.get_competition_standings(
                competition_code=competition_code,
                season=season
            )
            
            if standings_data and "standings" in standings_data:
                standings_list = standings_data["standings"]
                if standings_list and len(standings_list) > 0:
                    table = standings_list[0].get("table", [])
                    
                    for standing in tqdm(table, desc="  💾 Storing standings", unit="standing"):
                        self.db.insert_standing(competition_code, season, standing)
                    
                    print(f"  ✓ Stored standings for {len(table)} teams")
    
    def update_latest_matches(self, competition_code: str):
        """
        Update database with latest match results.
        
        Args:
            competition_code: Competition code (e.g., 'PL')
        """
        print(f"\n🔄 Updating latest matches for {competition_code}")
        
        # Fetch recent finished matches
        matches = self.api_client.get_competition_matches(
            competition_code=competition_code,
            status="FINISHED"
        )
        
        print(f"  ✓ Found {len(matches)} finished matches")
        
        for match in tqdm(matches, desc="  💾 Updating matches", unit="match"):
            self.db.insert_match(match)
        
        # Update standings
        print("  📈 Updating standings...")
        standings_data = self.api_client.get_competition_standings(competition_code)
        
        if standings_data and "standings" in standings_data:
            standings_list = standings_data["standings"]
            if standings_list and len(standings_list) > 0:
                table = standings_list[0].get("table", [])
                season = standings_data.get("season", {}).get("startDate", "")[:4]
                
                if season:
                    for standing in table:
                        self.db.insert_standing(competition_code, int(season), standing)
                    
                    print(f"  ✓ Updated standings for {len(table)} teams")
    
    def get_available_teams(self) -> List[Dict]:
        """
        Get list of all teams in database.
        
        Returns:
            List of team dictionaries
        """
        return self.db.get_all_teams()
    
    def get_competition_summary(self, competition_code: str) -> Dict:
        """
        Get summary statistics for a competition.
        
        Args:
            competition_code: Competition code
            
        Returns:
            Dictionary with summary statistics
        """
        matches = self.db.get_all_matches(competition=competition_code)
        teams = self.db.get_all_teams()
        
        finished_matches = [m for m in matches if m["status"] == "FINISHED"]
        
        return {
            "total_matches": len(matches),
            "finished_matches": len(finished_matches),
            "total_teams": len(teams),
            "total_goals": sum(
                (m["home_score"] or 0) + (m["away_score"] or 0) 
                for m in finished_matches
            )
        }
