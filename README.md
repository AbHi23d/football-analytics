# ⚽ Football Analytics Platform

> *End-to-end data science project predicting Premier League match outcomes*

This project demonstrates a complete data science workflow, from data collection to deployment. It uses XGBoost to predict football match outcomes with 52.8% accuracy through strict temporal validation.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-red.svg)
![ML](https://img.shields.io/badge/ML-XGBoost-green.svg)

## 📊 Project Overview

- **3,800** Premier League matches (2015-2025, 10 complete seasons)
- **15** engineered features (ELO ratings, rolling averages, momentum, temporal context)
- **52.8%** prediction accuracy (clean time-based validation, zero data leakage)
- **XGBoost** classifier with hyperparameter tuning
- **Interactive dashboard** built with Streamlit

---

## 🎯 Key Features

**Data Engineering:**
- CSV data collection and processing
- SQLite database with optimized schema
- ETL pipeline with data validation

**Machine Learning:**
- 15 custom engineered features (80% custom implementations)
- Time-based train/test split (2015-2023 train, 2023-2025 test)
- Zero data leakage (all rolling features use `.shift(1)`)
- XGBoost with 52.8% accuracy vs 43.4% baseline (+9.3 points)
- Cross-validation: 47.4% ± 2.8%

**Production:**
- Interactive Streamlit dashboard
- Reproducible training pipeline
- Model versioning and metadata tracking
- Tableau-ready data exports

---

## 📸 See It In Action

### Dashboard Overview
Interactive metrics and visualizations showing match statistics and trends.

![Dashboard](docs/screenshots/dashboard.png)

### Match Predictor
Select any two teams and get instant win/draw/loss probabilities with clear predictions.

![Match Predictor](docs/screenshots/match_predictor.png)

---

### Prerequisites
- Python 3.8+
- Virtual environment recommended

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/football-analytics.git
cd football-analytics

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run app_simple.py
```

The database is included, so no data fetching required!

---

## 📈 Model Performance

### Results

| Metric | Value |
|--------|-------|
| **Test Accuracy** | 52.8% |
| **Cross-Validation** | 47.4% ± 2.8% |
| **Baseline** | 43.4% (always predict home) |
| **Improvement** | +9.3 percentage points |
| **Algorithm** | XGBoost Classifier |

### Why 52.8% is Good

- **Beats random guessing** (33%) by 18.8 points
- **Beats naive baseline** by 9.3 points
- **Honest evaluation** with strict temporal validation
- **No data leakage** - provably clean features
- **Competitive with published research** (53-58% range)

Football is inherently unpredictable. Our model demonstrates real predictive capability on unseen future data.

---

## 🔬 Feature Engineering

**From Raw Data to Features:**
The database contains basic match statistics (17 columns). We engineered 15 predictive features:

### Top 10 Features by Importance

| Rank | Feature | Importance | Type |
|------|---------|------------|------|
| 1 | elo_diff | 0.127 | Standard |
| 2 | away_goals_avg | 0.067 | **Custom** |
| 3 | h2h_home_wins | 0.066 | Standard |
| 4 | rest_days | 0.066 | **Custom** |
| 5 | season_progress | 0.066 | **Custom** |
| 6 | home_goals_avg | 0.065 | **Custom** |
| 7 | away_clean_sheets | 0.064 | **Custom** |
| 8 | away_win_streak | 0.063 | **Custom** |
| 9 | home_conceded_avg | 0.063 | **Custom** |
| 10 | form_diff | 0.063 | Standard |

**12 of 15 features (80%)** are custom implementations beyond basic statistics.

### Data Leakage Prevention

All features use only historical data:
- **Rolling averages:** `.shift(1)` ensures no current match data
- **ELO ratings:** Updated sequentially after each match
- **Streaks/form:** Calculated from past matches only
- **Time-based split:** Train on 2015-2022, test on 2023-2024
Current Ongoing Season : 2025
---

## 📁 Project Structure

```
football-analytics/
├── data/
│   └── database/
│       └── football.db              # 3,800 matches (2015-2024)
│
├── models/
│   ├── simple_model.pkl             # Trained XGBoost (52.8%)
│   ├── features.json                # 15 feature names
│   └── model_metadata.json          # Training metrics
│
├── notebooks/
│   ├── 01_exploratory_data_analysis.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_development.ipynb
│
├── utils.py                         # Feature engineering functions
├── train_model.py                   # Production training script
├── app_simple.py                    # Streamlit dashboard
└── README.md                        # This file
```

---

## 💻 Technical Stack

**Data & ML:**
- Python 3.8+, pandas, NumPy
- SQLite for data storage
- scikit-learn, XGBoost
- Jupyter notebooks

**Visualization:**
- Streamlit (interactive dashboard)
- Plotly (dynamic charts)
- Matplotlib/Seaborn

---

## 🎓 Skills Demonstrated

### Data Engineering
- ETL pipeline development
- Database design and optimization
- Data validation and cleaning

### Data Science
- Exploratory analysis with SQL
- Feature engineering (15 custom features)
- Statistical validation

### Machine Learning
- Model selection (tested RF, GradientBoosting, XGBoost)
- Hyperparameter tuning
- Time-based cross-validation
- Data leakage prevention

### Software Engineering
- Clean, modular code
- Reproducible workflows
- Production-ready scripts
- Comprehensive documentation

---

## 📊 Key Results

- **52.8% accuracy** on 3-class prediction (time-based validation)
- **+9.3 points** over baseline
- **Zero data leakage** (proven with `.shift(1)` operations)
- **3,800 matches** from 10 complete seasons
- **15 engineered features** (80% custom)
- **Complete documentation** with notebooks and scripts

---

## 🎯 For Recruiters & Hiring Managers

**This project demonstrates:**

✅ **End-to-end thinking** - Data collection through deployment  
✅ **SQL proficiency** - Direct database queries and optimization  
✅ **Python expertise** - pandas, scikit-learn, XGBoost, Streamlit  
✅ **ML fundamentals** - Feature engineering, validation, leakage prevention  
✅ **Production mindset** - Reproducible scripts, clean code, documentation  
✅ **Communication** - Clear notebooks, visualizations, README

**Complexity:**
- 3,800 data points processed
- 15 engineered features
- 52.8% accuracy with clean validation

---

## 🚧 Future Enhancements

**Production Readiness:**
- Deploy to cloud (Streamlit Cloud/Heroku)
- Automate data updates
- CI/CD pipeline
- Model versioning

**Model Improvements:**
- Player-level statistics
- External data (weather, injuries)
- Team Analytics
- New leagues (La Liga, Bundesliga and more!)


---

## 📖 Documentation

- `SETUP_GUIDE.md` - Complete installation and setup instructions
- `LICENSE` - MIT License for open source use

---

## 📧 Connect

**Built by:** [Abhinav Dhindsa]
**Contact:** [dhindsaabhinav@gmail.com]  
**LinkedIn:** [www.linkedin.com/in/abhidhindsa]

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

**This project demonstrates skills applicable to data science roles.**

*Last Updated: January 2026*
