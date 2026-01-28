"""
Generate Tableau/PowerBI Export Files
Simple SQL transformations to create BI-ready CSV files
"""

import sqlite3
import pandas as pd
from pathlib import Path

# Configuration
DB_PATH = 'data/database/football.db'
EXPORT_DIR = 'tableau_exports'

def create_export_directory():
    """Create export directory if it doesn't exist"""
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    print(f"✅ Export directory ready: {EXPORT_DIR}/")


def export_matches():
    """
    Export match-level data with derived columns for visualization
    """
    print("\n📊 Exporting matches...")
    
    query = """
    SELECT 
        season,
        matchday,
        DATE(utc_date) as match_date,
        strftime('%Y', utc_date) as year,
        strftime('%m', utc_date) as month,
        CASE 
            WHEN CAST(strftime('%m', utc_date) AS INTEGER) BETWEEN 8 AND 12 
            THEN 'H1' 
            ELSE 'H2' 
        END as season_half,
        home_team_name,
        away_team_name,
        home_score,
        away_score,
        half_time_home,
        half_time_away,
        CASE 
            WHEN winner = 'HOME_TEAM' OR winner = 'H' THEN 'Home Win'
            WHEN winner = 'AWAY_TEAM' OR winner = 'A' THEN 'Away Win'
            ELSE 'Draw'
        END as winner,
        (home_score + away_score) as total_goals,
        (home_score - away_score) as goal_difference,
        CASE 
            WHEN (home_score + away_score) = 0 THEN '0 Goals'
            WHEN (home_score + away_score) BETWEEN 1 AND 2 THEN '1-2 Goals'
            WHEN (home_score + away_score) BETWEEN 3 AND 4 THEN '3-4 Goals'
            ELSE '5+ Goals'
        END as goals_category
    FROM matches
    WHERE status = 'FINISHED'
    ORDER BY utc_date, id
    """
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Save to CSV
    df.to_csv(f'{EXPORT_DIR}/matches.csv', index=False)
    print(f"   ✓ Exported {len(df):,} matches")
    
    return df


def export_team_statistics():
    """
    Export team performance statistics aggregated by season
    Calculates wins, losses, draws, goals, and points
    """
    print("\n📈 Exporting team statistics...")
    
    query = """
    WITH home_stats AS (
        -- Aggregate home performance
        SELECT 
            season,
            home_team_name as team,
            COUNT(*) as home_matches,
            SUM(CASE WHEN winner IN ('HOME_TEAM', 'H') THEN 1 ELSE 0 END) as home_wins,
            SUM(CASE WHEN winner IN ('DRAW', 'D') THEN 1 ELSE 0 END) as home_draws,
            SUM(CASE WHEN winner IN ('AWAY_TEAM', 'A') THEN 1 ELSE 0 END) as home_losses,
            SUM(home_score) as home_goals_scored,
            SUM(away_score) as home_goals_conceded
        FROM matches
        WHERE status = 'FINISHED'
        GROUP BY season, home_team_name
    ),
    away_stats AS (
        -- Aggregate away performance
        SELECT 
            season,
            away_team_name as team,
            COUNT(*) as away_matches,
            SUM(CASE WHEN winner IN ('AWAY_TEAM', 'A') THEN 1 ELSE 0 END) as away_wins,
            SUM(CASE WHEN winner IN ('DRAW', 'D') THEN 1 ELSE 0 END) as away_draws,
            SUM(CASE WHEN winner IN ('HOME_TEAM', 'H') THEN 1 ELSE 0 END) as away_losses,
            SUM(away_score) as away_goals_scored,
            SUM(home_score) as away_goals_conceded
        FROM matches
        WHERE status = 'FINISHED'
        GROUP BY season, away_team_name
    )
    -- Combine home and away stats
    SELECT 
        h.season,
        h.team,
        (h.home_matches + a.away_matches) as total_matches,
        (h.home_wins + a.away_wins) as total_wins,
        (h.home_draws + a.away_draws) as total_draws,
        (h.home_losses + a.away_losses) as total_losses,
        ((h.home_wins + a.away_wins) * 3 + (h.home_draws + a.away_draws)) as points,
        (h.home_goals_scored + a.away_goals_scored) as goals_scored,
        (h.home_goals_conceded + a.away_goals_conceded) as goals_conceded,
        (h.home_goals_scored + a.away_goals_scored - h.home_goals_conceded - a.away_goals_conceded) as goal_difference,
        h.home_matches,
        h.home_wins,
        h.home_draws,
        h.home_losses,
        h.home_goals_scored,
        h.home_goals_conceded,
        a.away_matches,
        a.away_wins,
        a.away_draws,
        a.away_losses,
        a.away_goals_scored,
        a.away_goals_conceded,
        ROUND((h.home_wins + a.away_wins) * 100.0 / (h.home_matches + a.away_matches), 2) as win_percentage,
        ROUND((h.home_goals_scored + a.away_goals_scored) * 1.0 / (h.home_matches + a.away_matches), 2) as avg_goals_scored,
        ROUND((h.home_goals_conceded + a.away_goals_conceded) * 1.0 / (h.home_matches + a.away_matches), 2) as avg_goals_conceded
    FROM home_stats h
    JOIN away_stats a ON h.season = a.season AND h.team = a.team
    ORDER BY h.season DESC, points DESC, goal_difference DESC
    """
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Save to CSV
    df.to_csv(f'{EXPORT_DIR}/team_statistics.csv', index=False)
    print(f"   ✓ Exported {len(df):,} team-season records")
    
    return df


def export_season_summary():
    """
    Export league-wide statistics for each season
    """
    print("\n📅 Exporting season summaries...")
    
    query = """
    SELECT 
        season,
        COUNT(*) as total_matches,
        COUNT(DISTINCT home_team_name) as teams_count,
        SUM(home_score + away_score) as total_goals,
        ROUND(AVG(home_score + away_score), 2) as avg_goals_per_match,
        SUM(CASE WHEN winner IN ('HOME_TEAM', 'H') THEN 1 ELSE 0 END) as home_wins,
        SUM(CASE WHEN winner IN ('AWAY_TEAM', 'A') THEN 1 ELSE 0 END) as away_wins,
        SUM(CASE WHEN winner IN ('DRAW', 'D') THEN 1 ELSE 0 END) as draws,
        ROUND(SUM(CASE WHEN winner IN ('HOME_TEAM', 'H') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as home_win_pct,
        ROUND(SUM(CASE WHEN winner IN ('AWAY_TEAM', 'A') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as away_win_pct,
        ROUND(SUM(CASE WHEN winner IN ('DRAW', 'D') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as draw_pct,
        MAX(home_score + away_score) as highest_scoring_match
    FROM matches
    WHERE status = 'FINISHED'
    GROUP BY season
    ORDER BY season DESC
    """
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Save to CSV
    df.to_csv(f'{EXPORT_DIR}/season_summary.csv', index=False)
    print(f"   ✓ Exported {len(df)} season summaries")
    
    return df


def export_head_to_head():
    """
    Export head-to-head matchup records between teams
    """
    print("\n⚔️  Exporting head-to-head records...")
    
    query = """
    WITH all_matchups AS (
        -- Home matches for team A
        SELECT 
            home_team_name as team_a,
            away_team_name as team_b,
            CASE WHEN winner IN ('HOME_TEAM', 'H') THEN 1 ELSE 0 END as team_a_wins,
            CASE WHEN winner IN ('AWAY_TEAM', 'A') THEN 1 ELSE 0 END as team_b_wins,
            CASE WHEN winner IN ('DRAW', 'D') THEN 1 ELSE 0 END as draws,
            home_score as team_a_goals,
            away_score as team_b_goals
        FROM matches
        WHERE status = 'FINISHED'
        
        UNION ALL
        
        -- Away matches for team A
        SELECT 
            away_team_name as team_a,
            home_team_name as team_b,
            CASE WHEN winner IN ('AWAY_TEAM', 'A') THEN 1 ELSE 0 END as team_a_wins,
            CASE WHEN winner IN ('HOME_TEAM', 'H') THEN 1 ELSE 0 END as team_b_wins,
            CASE WHEN winner IN ('DRAW', 'D') THEN 1 ELSE 0 END as draws,
            away_score as team_a_goals,
            home_score as team_b_goals
        FROM matches
        WHERE status = 'FINISHED'
    )
    SELECT 
        team_a,
        team_b,
        COUNT(*) as total_matches,
        SUM(team_a_wins) as team_a_wins,
        SUM(team_b_wins) as team_b_wins,
        SUM(draws) as draws,
        SUM(team_a_goals) as team_a_goals,
        SUM(team_b_goals) as team_b_goals,
        ROUND(SUM(team_a_wins) * 100.0 / COUNT(*), 2) as team_a_win_pct
    FROM all_matchups
    WHERE team_a < team_b  -- Avoid duplicate pairings
    GROUP BY team_a, team_b
    HAVING COUNT(*) >= 5  -- Only teams that played 5+ times
    ORDER BY total_matches DESC, team_a, team_b
    """
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Save to CSV
    df.to_csv(f'{EXPORT_DIR}/head_to_head.csv', index=False)
    print(f"   ✓ Exported {len(df):,} head-to-head matchups")
    
    return df


def main():
    """
    Generate all Tableau/PowerBI export files
    """
    print("=" * 60)
    print("🚀 Generating BI Export Files")
    print("=" * 60)
    
    # Create directory
    create_export_directory()
    
    # Run all exports
    matches_df = export_matches()
    stats_df = export_team_statistics()
    summary_df = export_season_summary()
    h2h_df = export_head_to_head()
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Export Complete!")
    print("=" * 60)
    print(f"\n📂 Files saved to: {EXPORT_DIR}/")
    print(f"\n📊 Summary:")
    print(f"   • {len(matches_df):,} match records")
    print(f"   • {len(stats_df):,} team-season statistics")
    print(f"   • {len(summary_df)} season summaries")
    print(f"   • {len(h2h_df):,} head-to-head matchups")
    print("\n💡 Ready for Tableau Desktop or Power BI")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
