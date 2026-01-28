# 🚀 Setup Guide - Football Analytics Platform

Complete setup instructions to get the project running on your machine.

---

## Prerequisites

- **Python 3.8+** installed
- **Git** installed

---

## Quick Start (5 Minutes)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/football-analytics.git
cd football-analytics
```

### 2. Set Up Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Data

The SQLite database with 3,800 matches is included:
```bash
ls -lh data/database/football.db
# Should show ~736 KB file
```

### 5. Train the Model

```bash
python train_model.py
```

**Output:**
- `models/simple_model.pkl` - Trained XGBoost model
- `models/features.json` - Feature list
- `models/model_metadata.json` - Model metadata

**Training time:** ~10-30 seconds

### 6. Run the Dashboard

```bash
streamlit run app_simple.py
```

Opens at `http://localhost:8501`

---

## Running Notebooks

### Start Jupyter

```bash
jupyter lab
# OR
jupyter notebook
```

### Notebook Execution Order

1. `01_exploratory_data_analysis.ipynb` - Understand the data
2. `02_feature_engineering.ipynb` - Create features
3. `03_model_development.ipynb` - Train and evaluate

---

## Troubleshooting

### "Module not found" Error
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Database Not Found
```bash
# Check database exists
ls data/database/football.db

# If missing, you may need to download it separately
# (See main README for download link)
```

### Streamlit Port Already in Use
```bash
# Use a different port
streamlit run app_simple.py --server.port 8502
```

### Model File Too Large for Git
```bash
# Install Git LFS
git lfs install
git lfs pull  # Download large files
```

---


## Next Steps

- ✅ **Run the dashboard** and explore predictions
- ✅ **Open notebooks** and walk through the analysis
- ✅ **Read the README** for project overview
- ✅ **Check out the code** in `utils.py` and `train_model.py`

---

## Need Help?

- 📖 Check the main [README.md](README.md)
- 🐛 Open an issue on GitHub
- 📧 Contact: dhindsaabhinav@gmail.com

---

**Estimated setup time:** 5-10 minutes  
**Difficulty:** Beginner-friendly 🟢
