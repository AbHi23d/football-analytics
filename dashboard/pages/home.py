"""Home page."""

import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# Load data
try:
    from src.data_collection import DatabaseManager
    import pandas as pd
    db = DatabaseManager()
    match_count = db.get_match_count()
    
    conn = db.get_connection()
    club_count = pd.read_sql("SELECT count(DISTINCT team_id) as c FROM standings;", conn).iloc[0]['c']
    goal_count = pd.read_sql("SELECT sum(home_score + away_score) as g FROM matches;", conn).iloc[0]['g']
    conn.close()
except Exception:
    match_count = 3800
    club_count = 34
    goal_count = 10754

import base64

# Load Logo
logo_path = os.path.join(os.path.dirname(__file__), "../assets/pl_logo.svg")
with open(logo_path, "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()

# Native Hero Title inside Columns
c1, c2 = st.columns([6, 1])
with c1:
    st.title("Premier League Analytics")
    st.markdown("2015 – 2025 · English Premier League · Built in Python & SQL")
with c2:
    st.markdown(f'<img src="data:image/svg+xml;base64,{logo_b64}" style="width: 120px; float: right;">', unsafe_allow_html=True)

st.write("")

# Stats strip
st.markdown(f"""
<div class="pg-stat-strip">
    <div class="pg-stat">
        <div class="pg-stat-number">{match_count:,}</div>
        <div class="pg-stat-label">Matches in dataset</div>
    </div>
    <div class="pg-stat">
        <div class="pg-stat-number">10</div>
        <div class="pg-stat-label">Seasons covered</div>
    </div>
    <div class="pg-stat">
        <div class="pg-stat-number">{club_count}</div>
        <div class="pg-stat-label">Clubs tracked</div>
    </div>
    <div class="pg-stat">
        <div class="pg-stat-number">{goal_count:,}</div>
        <div class="pg-stat-label">Goals scored</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation Cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="pg-card">
        <div class="pg-card-label">Data</div>
        <div class="pg-card-title">League Standings</div>
        <div class="pg-card-desc">Browse the final table for any season from 2015 to 2025, including points, goals, and goal difference.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("View Standings →", use_container_width=True, type="primary"):
        st.switch_page("pages/league_standings.py")

with col2:
    st.markdown("""
    <div class="pg-card">
        <div class="pg-card-label">Analysis</div>
        <div class="pg-card-title">Team Performance</div>
        <div class="pg-card-desc">Explore win rates, scoring trends, home and away splits, and head-to-head records for any club.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("Analyse a Team →", use_container_width=True, type="primary"):
        st.switch_page("pages/team_analysis.py")

with col3:
    st.markdown("""
    <div class="pg-card">
        <div class="pg-card-label">Predictive</div>
        <div class="pg-card-title">Match Predictor</div>
        <div class="pg-card-desc">Select any two clubs to get a probability forecast powered by our machine learning ensemble.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("Run a Prediction →", use_container_width=True, type="primary"):
        st.switch_page("pages/match_predictor.py")


# Inject CSS at the absolute bottom of the document to prevent Streamlit from generating invisible vertical wrapper divs inside the page flow
st.markdown("""
<style>
.pg-stat-strip {
    display: flex;
    gap: 0;
    border-top: 1px solid #e2e2e2;
    border-bottom: 1px solid #e2e2e2;
    padding: 1.4rem 0;
    margin-bottom: 3rem;
}
.pg-stat {
    flex: 1;
    padding: 0 2rem 0 0;
    border-right: 1px solid #e8e8e8;
    margin-right: 2rem;
}
.pg-stat:last-child {
    border-right: none;
    margin-right: 0;
}
.pg-stat-number {
    font-size: 2.2rem;
    font-weight: 600;
    color: #15181B;
    line-height: 1;
    margin-bottom: 0.3rem;
    letter-spacing: -0.02em;
}
.pg-stat-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #999;
    font-weight: 500;
}

.pg-card {
    background: #fff;
    border: 1px solid #e8e8e8;
    border-top: 2px solid #37003C;
    padding: 1.6rem 1.4rem 1.4rem 1.4rem;
    height: 100%;
}
.pg-card-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #37003C;
    margin-bottom: 0.7rem;
    font-weight: 500;
}
.pg-card-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #111;
    margin-bottom: 0.6rem;
    line-height: 1.3;
}
.pg-card-desc {
    font-size: 0.85rem;
    color: #666;
    line-height: 1.5;
    margin-bottom: 1.2rem;
    min-height: 4rem;
}
</style>
""", unsafe_allow_html=True)
