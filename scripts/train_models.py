"""Script to train machine learning models."""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import MatchPredictor

def main():
    """Train match prediction models."""
    print("🤖 Football Analytics - Model Training")
    print("=" * 50)
    
    predictor = MatchPredictor()
    
    try:
        metrics = predictor.train_models()
        
        if metrics:
            print("\n" + "=" * 50)
            print("✅ Model training completed!")
            print(f"\n📊 Model Performance:")
            print(f"  Outcome accuracy: {metrics['outcome_accuracy']:.2%}")
            print(f"  Cross-validation: {metrics['cv_mean']:.2%} (+/- {metrics['cv_std']*2:.2%})")
            print(f"  Score RMSE: {metrics['score_rmse']:.2f} goals")
            print(f"  Training samples: {metrics['training_samples']}")
        else:
            print("\n⚠️  No training data available. Please fetch data first:")
            print("  python scripts/fetch_initial_data.py")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error during model training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
