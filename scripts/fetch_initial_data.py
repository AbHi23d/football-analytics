"""Script to fetch initial data from Football-Data.org API."""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_collection import DataFetcher

def main():
    """Fetch initial Premier League data for the last 2 seasons."""
    print("⚽ Football Analytics - Initial Data Fetch")
    print("=" * 50)
    
    fetcher = DataFetcher()
    
    # Fetch Premier League data for 2023 and 2024 seasons
    competition_code = "PL"  # Premier League
    seasons = [2023, 2024]
    
    try:
        fetcher.fetch_competition_data(competition_code, seasons)
        
        print("\n" + "=" * 50)
        print("✅ Data fetch completed successfully!")
        
        # Show summary
        summary = fetcher.get_competition_summary(competition_code)
        print(f"\n📊 Database Summary:")
        print(f"  Total matches: {summary['total_matches']}")
        print(f"  Finished matches: {summary['finished_matches']}")
        print(f"  Total teams: {summary['total_teams']}")
        print(f"  Total goals: {summary['total_goals']}")
        
    except Exception as e:
        print(f"\n❌ Error during data fetch: {e}")
        print("\nPlease ensure:")
        print("  1. You have set FOOTBALL_DATA_API_KEY in your .env file")
        print("  2. Your API key is valid")
        print("  3. You have an internet connection")
        sys.exit(1)

if __name__ == "__main__":
    main()
