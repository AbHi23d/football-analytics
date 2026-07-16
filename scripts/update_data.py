"""Script to update database with latest match results."""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_collection import DataFetcher

def main():
    """Update database with latest matches."""
    print("🔄 Football Analytics - Data Update")
    print("=" * 50)
    
    fetcher = DataFetcher()
    
    competition_code = "PL"  # Premier League
    
    try:
        fetcher.update_latest_matches(competition_code)
        
        print("\n" + "=" * 50)
        print("✅ Data update completed!")
        
        # Show summary
        summary = fetcher.get_competition_summary(competition_code)
        print(f"\n📊 Database Summary:")
        print(f"  Total matches: {summary['total_matches']}")
        print(f"  Finished matches: {summary['finished_matches']}")
        
    except Exception as e:
        print(f"\n❌ Error during update: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
