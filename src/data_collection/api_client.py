"""API client for Football-Data.org."""

import os
import time
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class FootballDataAPIClient:
    """Client for interacting with Football-Data.org API."""
    
    BASE_URL = "https://api.football-data.org/v4"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            api_key: API key for Football-Data.org. If None, reads from environment.
        """
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set FOOTBALL_DATA_API_KEY in .env file")
        
        self.headers = {
            "X-Auth-Token": self.api_key
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Rate limiting (free tier: 10 requests/minute)
        self.last_request_time = 0
        self.min_request_interval = 6.5  # seconds between requests
    
    def _rate_limit(self):
        """Implement rate limiting to avoid hitting API limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a request to the API with error handling and retry logic.
        
        Args:
            endpoint: API endpoint (e.g., '/competitions/PL/matches')
            params: Optional query parameters
            
        Returns:
            JSON response as dictionary
        """
        self._rate_limit()
        url = f"{self.BASE_URL}{endpoint}"
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Too many requests
                    wait_time = 60
                    print(f"Rate limit hit. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 404:
                    print(f"Endpoint not found: {url}")
                    return {}
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))  # Exponential backoff
                else:
                    raise
        
        return {}
    
    def get_competitions(self) -> List[Dict]:
        """
        Get list of available competitions.
        
        Returns:
            List of competition dictionaries
        """
        data = self._make_request("/competitions")
        return data.get("competitions", [])
    
    def get_competition_standings(self, competition_code: str, season: Optional[int] = None) -> Dict:
        """
        Get standings for a specific competition.
        
        Args:
            competition_code: Competition code (e.g., 'PL' for Premier League)
            season: Optional season year (e.g., 2023)
            
        Returns:
            Standings data
        """
        endpoint = f"/competitions/{competition_code}/standings"
        params = {"season": season} if season else None
        return self._make_request(endpoint, params)
    
    def get_competition_matches(
        self, 
        competition_code: str, 
        season: Optional[int] = None,
        status: Optional[str] = None,
        matchday: Optional[int] = None
    ) -> List[Dict]:
        """
        Get matches for a specific competition.
        
        Args:
            competition_code: Competition code (e.g., 'PL' for Premier League)
            season: Optional season year (e.g., 2023)
            status: Optional match status ('SCHEDULED', 'FINISHED', 'IN_PLAY')
            matchday: Optional matchday number
            
        Returns:
            List of match dictionaries
        """
        endpoint = f"/competitions/{competition_code}/matches"
        params = {}
        if season:
            params["season"] = season
        if status:
            params["status"] = status
        if matchday:
            params["matchday"] = matchday
            
        data = self._make_request(endpoint, params)
        return data.get("matches", [])
    
    def get_team(self, team_id: int) -> Dict:
        """
        Get information about a specific team.
        
        Args:
            team_id: Team ID
            
        Returns:
            Team data
        """
        endpoint = f"/teams/{team_id}"
        return self._make_request(endpoint)
    
    def get_match(self, match_id: int) -> Dict:
        """
        Get detailed information about a specific match.
        
        Args:
            match_id: Match ID
            
        Returns:
            Match data
        """
        endpoint = f"/matches/{match_id}"
        return self._make_request(endpoint)
    
    def get_team_matches(
        self, 
        team_id: int,
        season: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get matches for a specific team.
        
        Args:
            team_id: Team ID
            season: Optional season year
            status: Optional match status
            limit: Maximum number of matches to return
            
        Returns:
            List of match dictionaries
        """
        endpoint = f"/teams/{team_id}/matches"
        params = {"limit": limit}
        if season:
            params["season"] = season
        if status:
            params["status"] = status
            
        data = self._make_request(endpoint, params)
        return data.get("matches", [])
