# Football Analytics & Prediction

[![Python](https://img.shields.io/badge/Python-3.9-blue?style=flat-square)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?style=flat-square)](https://streamlit.io)
[![SQL](https://img.shields.io/badge/SQL-Portfolio-orange?style=flat-square)](sql_analysis.md)

Hi! Thanks for stopping by. This is an end-to-end data analytics and machine learning project I built to analyze the English Premier League. 

I wanted to build something that handles the entire data lifecycle: from pulling raw API data, cleaning it, and storing it in a relational database, to building predictive models and serving everything in an interactive web dashboard.

> **[🚀 Check out the Live Dashboard (Streamlit)](https://premier-league-football.streamlit.app/)**  
> **[📈 View the Live Dashboard (Tableau)](https://public.tableau.com/app/profile/abhinav.dhindsa/viz/SoccerAnalyticsDashboard_17740438732160/Dashboard2)**  
> **[🗄️ View my SQL Portfolio (14 complex queries)](sql_analysis.md)**

---

## 📊 What's inside?

The dashboard is split into three main tools:
- **Match Predictor**: A machine learning ensemble (XGBoost + Random Forest) that predicts win probabilities and scorelines for any matchup.
- **Team Analysis**: Deep dives into specific clubs to see their recent form, home/away splits, and head-to-head records.
- **League Standings**: Historical tables for the last 10 seasons, complete with European qualification zones.

*Note for recruiters: If you're looking for my database skills, check out the [`sql_analysis.md`](sql_analysis.md) file in this repo to see the advanced SQL (CTEs, Window Functions, etc.) I wrote to analyze the dataset.*

## 💾 The Data

I built the dataset from scratch using the free tier of the Football-Data.org API. 
- **Scope**: 10 full Premier League seasons (2015–2025)
- **Size**: 3,800+ finished matches and 34 unique clubs
- **Storage**: Cleaned and stored in a local SQLite database (`football.db`)

## 🧠 How the ML works

I wanted to keep the modeling grounded in reality. The predictions are driven by 17 custom features I engineered for each match, including:
- Dynamic ELO ratings
- Rolling form scores (last 5 games)
- Home/Away goal averages
- Head-to-head history

The model achieves ~50% accuracy on match outcomes (Win/Draw/Loss), outperforming the 45% "always pick the home team" baseline — a result in line with published benchmarks for this type of prediction problem, which is inherently difficult given football's low-scoring, high-variance nature.

---

## 🛠️ Tech Stack

- **Data Processing**: Python, Pandas
- **Machine Learning**: scikit-learn, XGBoost
- **Database**: SQLite, SQL
- **Frontend & Viz**: Streamlit, Plotly

## 💻 Running it locally

If you want to spin this up on your own machine, I've included the pre-populated database in the repo so you don't have to worry about API keys or rate limits.

```bash
git clone https://github.com/AbHi23d/football-analytics.git
cd football-analytics
pip install -r requirements.txt
streamlit run dashboard/app.py
```
