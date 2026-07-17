"""Main Streamlit application for Football Analytics."""

import streamlit as st
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

st.set_page_config(
    page_title="Football Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Premier League Branding ───────────────────────────────────────────────────
# Native Streamlit logo for the top left of the sidebar
logo_path = os.path.join(os.path.dirname(__file__), "assets", "pl_logo.svg")
st.logo(logo_path)

# Hide default top padding for a cleaner UI (but keep header so sidebar toggle works)
st.markdown("""
<style>
    .block-container {padding-top: 1rem !important;}
    h1 {color: #37003C !important;}
    [data-testid="stMetricValue"] {
        color: #37003C;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ── Use Native Streamlit Navigation (v1.36+) ──────────────────────────────────
pg = st.navigation([
    st.Page("pages/home.py", title="Home", icon="🏠"),
    st.Page("pages/match_predictor.py", title="Match Predictor", icon="🔮"),
    st.Page("pages/team_analysis.py", title="Team Analysis", icon="📊"),
    st.Page("pages/league_standings.py", title="League Standings", icon="🏆")
])

st.sidebar.markdown("""
<div style="margin-top: 45vh;">
    <h3 style="margin-bottom: 5px;">👨‍💻 Built by Abhi</h3>
    <a href="https://www.linkedin.com/in/abhidhindsa" target="_blank" style="text-decoration: none; font-weight: bold; color: #1c83e1;">LinkedIn</a> &nbsp;&middot;&nbsp; 
    <a href="https://github.com/AbHi23d" target="_blank" style="text-decoration: none; font-weight: bold; color: #1c83e1;">GitHub</a>
</div>
""", unsafe_allow_html=True)

pg.run()
