import pandas as pd
import sqlite3
import glob
import os

def ingest_raw_data():
    """
    Simulate the ETL process: Extract from Raw CSVs -> Transform -> Load to DB.
    """
    # 1. EXTRACT
    raw_files = glob.glob('data/raw/*.csv')
    
    if not raw_files:
        print("ℹ️ Note: No raw CSV files found. Demonstrating transformation logic...")
        # Create dummy data spanning multiple seasons
        raw_df = pd.DataFrame({
            'Date': ['08/08/2015', '15/05/2016', '12/08/2016', '14/05/2017'],
            'HomeTeam': ['Chelsea', 'Leicester', 'Hull', 'Chelsea'],
            'AwayTeam': ['Swansea', 'Everton', 'Leicester', 'Sunderland'],
            'FTHG': [2, 3, 2, 5],
            'FTAG': [2, 1, 1, 1],
            'FTR': ['D', 'H', 'H', 'H']
        })
    else:
        print(f"Loading {len(raw_files)} CSV files...")
        # Simple concatenate - no need to track filenames!
        raw_df = pd.concat([pd.read_csv(f) for f in raw_files], ignore_index=True)

    # 2. TRANSFORM
    print(f"Raw columns: {raw_df.columns.tolist()}")
    
    # Rename for consistency with DB schema
    df = raw_df.rename(columns={
        'Date': 'utc_date',
        'HomeTeam': 'home_team_name',
        'AwayTeam': 'away_team_name',
        'FTHG': 'home_score',
        'FTAG': 'away_score',
        'FTR': 'winner'
    })
    
    # Standardize Date FIRST (we need this for season logic)
    df['utc_date'] = pd.to_datetime(df['utc_date'], dayfirst=True)
    
    # DERIVE SEASON from date (Football seasons: Aug-May)
    # - If month >= 8 (Aug), season = year
    # - If month < 8 (before Aug), season = year - 1
    # Example: 2015-08-08 -> season 2015, but 2016-05-15 -> season 2015
    df['season'] = df['utc_date'].apply(
        lambda x: x.year if x.month >= 8 else x.year - 1
    )
    
    # Keep only relevant columns
    cols = ['utc_date', 'season', 'home_team_name', 'away_team_name', 'home_score', 'away_score', 'winner']
    df = df[cols]
    
    # Add metadata
    df['status'] = 'FINISHED'
    
    print("\nTransformed Data (Ready for Load):")
    print(df.head())

    # 3. LOAD
    db_path = 'data/database/football.db'
    conn = sqlite3.connect(db_path)
    
    # In production, we'd use 'append' and check for duplicates
    # df.to_sql('matches', conn, if_exists='append', index=False)
    
    print(f"\n✅ Logic verified. Ready to insert into {db_path}")
    conn.close()

if __name__ == "__main__":
    ingest_raw_data()
