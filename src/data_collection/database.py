"""Database manager for storing and retrieving football data."""

import os
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json


class DatabaseManager:
    """Manages SQLite database for football analytics data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path:
            self.db_path = db_path
        elif os.getenv("DATABASE_PATH"):
            self.db_path = os.getenv("DATABASE_PATH")
        else:
            # Resolve absolute path relative to this file, works from any working dir
            _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.db_path = os.path.join(_root, "data", "database", "football.db")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Teams table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                short_name TEXT,
                tla TEXT,
                crest TEXT,
                venue TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY,
                competition TEXT,
                season INTEGER,
                matchday INTEGER,
                utc_date TIMESTAMP,
                status TEXT,
                home_team_id INTEGER,
                away_team_id INTEGER,
                home_team_name TEXT,
                away_team_name TEXT,
                home_score INTEGER,
                away_score INTEGER,
                half_time_home INTEGER,
                half_time_away INTEGER,
                winner TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (home_team_id) REFERENCES teams(id),
                FOREIGN KEY (away_team_id) REFERENCES teams(id)
            )
        """)
        
        # Standings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS standings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition TEXT,
                season INTEGER,
                team_id INTEGER,
                team_name TEXT,
                position INTEGER,
                played_games INTEGER,
                won INTEGER,
                draw INTEGER,
                lost INTEGER,
                points INTEGER,
                goals_for INTEGER,
                goals_against INTEGER,
                goal_difference INTEGER,
                form TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id),
                UNIQUE(competition, season, team_id)
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(utc_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches(home_team_id, away_team_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season, competition)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_standings_season ON standings(season, competition)")
        
        conn.commit()
        conn.close()
    
    def insert_team(self, team_data: Dict):
        """Insert or update a team."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO teams (id, name, short_name, tla, crest, venue, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            team_data.get("id"),
            team_data.get("name"),
            team_data.get("shortName"),
            team_data.get("tla"),
            team_data.get("crest"),
            team_data.get("venue"),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def insert_match(self, match_data: Dict):
        """Insert or update a match."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        score = match_data.get("score", {})
        full_time = score.get("fullTime", {})
        half_time = score.get("halfTime", {})
        
        cursor.execute("""
            INSERT OR REPLACE INTO matches (
                id, competition, season, matchday, utc_date, status,
                home_team_id, away_team_id, home_team_name, away_team_name,
                home_score, away_score, half_time_home, half_time_away, winner, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_data.get("id"),
            match_data.get("competition", {}).get("code"),
            match_data.get("season", {}).get("startDate", "")[:4] if match_data.get("season") else None,
            match_data.get("matchday"),
            match_data.get("utcDate"),
            match_data.get("status"),
            match_data.get("homeTeam", {}).get("id"),
            match_data.get("awayTeam", {}).get("id"),
            match_data.get("homeTeam", {}).get("name"),
            match_data.get("awayTeam", {}).get("name"),
            full_time.get("home"),
            full_time.get("away"),
            half_time.get("home"),
            half_time.get("away"),
            score.get("winner"),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def insert_standing(self, competition: str, season: int, standing_data: Dict):
        """Insert or update team standing."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        team = standing_data.get("team", {})
        
        cursor.execute("""
            INSERT OR REPLACE INTO standings (
                competition, season, team_id, team_name, position,
                played_games, won, draw, lost, points,
                goals_for, goals_against, goal_difference, form, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            competition,
            season,
            team.get("id"),
            team.get("name"),
            standing_data.get("position"),
            standing_data.get("playedGames"),
            standing_data.get("won"),
            standing_data.get("draw"),
            standing_data.get("lost"),
            standing_data.get("points"),
            standing_data.get("goalsFor"),
            standing_data.get("goalsAgainst"),
            standing_data.get("goalDifference"),
            standing_data.get("form"),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def get_all_teams(self) -> List[Dict]:
        """Get all teams from database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teams ORDER BY name")
        teams = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return teams
    
    def get_all_matches(self, competition: Optional[str] = None, season: Optional[int] = None) -> List[Dict]:
        """Get all matches, optionally filtered by competition and season."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM matches WHERE 1=1"
        params = []
        
        if competition:
            query += " AND competition = ?"
            params.append(competition)
        if season:
            query += " AND season = ?"
            params.append(season)
        
        query += " ORDER BY utc_date DESC"
        
        cursor.execute(query, params)
        matches = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return matches
    
    def get_team_matches(self, team_id: int, limit: Optional[int] = None) -> List[Dict]:
        """Get matches for a specific team."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM matches 
            WHERE home_team_id = ? OR away_team_id = ?
            ORDER BY utc_date DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (team_id, team_id))
        matches = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return matches
    
    def get_head_to_head(self, team1_id: int, team2_id: int) -> List[Dict]:
        """Get head-to-head matches between two teams."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM matches 
            WHERE (home_team_id = ? AND away_team_id = ?)
               OR (home_team_id = ? AND away_team_id = ?)
            ORDER BY utc_date DESC
        """, (team1_id, team2_id, team2_id, team1_id))
        
        matches = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return matches
    
    def get_standings(self, competition: str, season: int) -> List[Dict]:
        """Get standings for a competition and season."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM standings 
            WHERE competition = ? AND season = ?
            ORDER BY position
        """, (competition, season))
        
        standings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return standings
    
    def get_match_count(self) -> int:
        """Get total number of matches in database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM matches")
        count = cursor.fetchone()["count"]
        conn.close()
        return count
    
    def get_team_by_id(self, team_id: int) -> Optional[Dict]:
        """Get team by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
        team = cursor.fetchone()
        conn.close()
        return dict(team) if team else None
    
    def get_team_by_name(self, name: str) -> Optional[Dict]:
        """Get team by name."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teams WHERE name LIKE ? OR short_name LIKE ?", 
                      (f"%{name}%", f"%{name}%"))
        team = cursor.fetchone()
        conn.close()
        return dict(team) if team else None
