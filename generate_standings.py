import sqlite3
import pandas as pd

def generate_standings():
    conn = sqlite3.connect('data/database/football.db')
    
    # Read matches
    matches = pd.read_sql("SELECT * FROM matches WHERE status = 'FINISHED'", conn)
    
    # Initialize standings list
    standings = []
    
    # Process each season
    for season in matches['season'].unique():
        season_matches = matches[matches['season'] == season]
        
        team_stats = {}
        
        for _, match in season_matches.iterrows():
            home = match['home_team_id']
            away = match['away_team_id']
            
            home_name = match['home_team_name']
            away_name = match['away_team_name']
            
            if home not in team_stats:
                team_stats[home] = {'team_name': home_name, 'P': 0, 'W': 0, 'D': 0, 'L': 0, 'GF': 0, 'GA': 0, 'Pts': 0}
            if away not in team_stats:
                team_stats[away] = {'team_name': away_name, 'P': 0, 'W': 0, 'D': 0, 'L': 0, 'GF': 0, 'GA': 0, 'Pts': 0}
            
            home_goals = match['home_score']
            away_goals = match['away_score']
            
            team_stats[home]['P'] += 1
            team_stats[away]['P'] += 1
            
            team_stats[home]['GF'] += home_goals
            team_stats[home]['GA'] += away_goals
            
            team_stats[away]['GF'] += away_goals
            team_stats[away]['GA'] += home_goals
            
            if home_goals > away_goals:
                team_stats[home]['W'] += 1
                team_stats[home]['Pts'] += 3
                team_stats[away]['L'] += 1
            elif away_goals > home_goals:
                team_stats[away]['W'] += 1
                team_stats[away]['Pts'] += 3
                team_stats[home]['L'] += 1
            else:
                team_stats[home]['D'] += 1
                team_stats[home]['Pts'] += 1
                team_stats[away]['D'] += 1
                team_stats[away]['Pts'] += 1
                
        # Convert to dataframe to sort
        season_df = pd.DataFrame.from_dict(team_stats, orient='index')
        season_df.index.name = 'team_id'
        season_df = season_df.reset_index()
        
        season_df['GD'] = season_df['GF'] - season_df['GA']
        
        # Sort by Pts (desc), GD (desc), GF (desc)
        season_df = season_df.sort_values(by=['Pts', 'GD', 'GF'], ascending=[False, False, False]).reset_index(drop=True)
        
        season_df['position'] = season_df.index + 1
        season_df['season'] = season
        season_df['competition'] = 'PL' # Use PL as the standard competition code
        
        # Add to total standings
        standings.append(season_df)
    
    if standings:
        final_standings = pd.concat(standings)
        
        # Clear existing standings
        cursor = conn.cursor()
        cursor.execute("DELETE FROM standings")
        
        # Insert new standings
        for _, row in final_standings.iterrows():
            cursor.execute("""
                INSERT INTO standings (
                    competition, season, position, team_id, team_name,
                    played_games, won, draw, lost, points, goals_for, goals_against, goal_difference
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['competition'], row['season'], row['position'], row['team_id'], row['team_name'],
                row['P'], row['W'], row['D'], row['L'], row['Pts'], row['GF'], row['GA'], row['GD']
            ))
            
        conn.commit()
        print(f"Generated and inserted {len(final_standings)} standings rows across {len(standings)} seasons.")
    
    conn.close()

if __name__ == "__main__":
    generate_standings()
