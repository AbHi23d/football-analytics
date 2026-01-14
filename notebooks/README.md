# Notebooks

This folder is ready for your Jupyter notebooks.

## Getting Started

Create notebooks for your analysis workflow as needed.

### Suggested Structure:

1. **Data Exploration** - Load and explore the 3,800 matches
2. **Feature Engineering** - Create predictive features
3. **Model Development** - Train and evaluate models
4. **Business Insights** - Answer stakeholder questions

### Quick Start

```python
# In your notebook
import sys
sys.path.append('..')

from utils import load_data, engineer_features

# Load data
df = load_data()
df = engineer_features(df)

# Start analyzing!
```

### Using Your Trained Model

```python
from utils import load_model, predict_match

# Load model
model = load_model()

# Make prediction
result = predict_match('Manchester City', 'Liverpool')
print(result)
```

---

**All old notebooks are in `archive/old_notebooks/` for reference.**
