import sqlite3
import pandas as pd
import os

def setup_database():
    """
    Initialize the SQLite database schema and load initial data.
    """
    db_path = 'data/database/football.db'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create matches table
    print("Creating matches table...")
    c.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY,
        season INTEGER,
        matchday INTEGER,
        utc_date TIMESTAMP,
        home_team_name TEXT,
        away_team_name TEXT,
        home_score INTEGER,
        away_score INTEGER,
        half_time_home INTEGER,
        half_time_away INTEGER,
        winner TEXT,
        status TEXT,
        total_goals INTEGER,
        goal_difference INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes for performance
    print("Creating indexes...")
    c.execute('CREATE INDEX IF NOT EXISTS idx_utc_date ON matches(utc_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_season ON matches(season)')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {db_path}")

if __name__ == "__main__":
    setup_database()
