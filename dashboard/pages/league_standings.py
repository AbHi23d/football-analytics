"""League Standings page."""

import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.data_collection import DatabaseManager
from src.preprocessing import clean_standings_data

c1, c2 = st.columns([6, 1])
with c1:
    st.title("League Standings")
    st.markdown("Historical Premier League tables.")

try:
    db = DatabaseManager()

    col1, col2 = st.columns(2)
    with col1:
        selected_competition = st.selectbox(
            "Competition", ["PL"],
            format_func=lambda x: "Premier League" if x == "PL" else x
        )
    with col2:
        seasons = list(range(2024, 2014, -1))
        selected_season = st.selectbox(
            "Season", seasons,
            format_func=lambda x: f"{x}–{x+1}"
        )

    standings = db.get_standings(selected_competition, selected_season)

    if not standings:
        st.warning(f"⚠️ No standings data available for {selected_season}–{selected_season+1}.")
    else:
        standings_df = clean_standings_data(standings)

        st.write("")

        # Top Performers Native Metrics
        st.subheader("Season Highlights")
        c1, c2, c3 = st.columns(3)
        
        champ = standings_df.iloc[0]
        c1.metric("Champions", champ['team_name'], f"{champ['points']} pts")

        top_attack = standings_df.nlargest(1, 'goals_for').iloc[0]
        c2.metric("Top Attack", top_attack['team_name'], f"{top_attack['goals_for']} GF")

        top_def = standings_df.nsmallest(1, 'goals_against').iloc[0]
        c3.metric("Best Defence", top_def['team_name'], f"-{top_def['goals_against']} GA", delta_color="inverse")

        st.write("")
        
        # Display simple native dataframe instead of plotly table for data analyst view
        display_df = standings_df[[
            'position', 'team_name', 'played_games', 'won', 'draw',
            'lost', 'goals_for', 'goals_against', 'goal_difference', 'points'
        ]].rename(columns={
            'position': 'Pos', 'team_name': 'Team', 'played_games': 'P',
            'won': 'W', 'draw': 'D', 'lost': 'L', 'goals_for': 'GF',
            'goals_against': 'GA', 'goal_difference': 'GD', 'points': 'Pts'
        })

        h_col1, h_col2 = st.columns([3, 1])
        with h_col1:
            st.subheader("Full Table")
        with h_col2:
            st.download_button(
                label="📥 Download Data",
                data=display_df.to_csv(index=False).encode('utf-8'),
                file_name=f"pl_standings_{selected_season}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=800
        )

except Exception as e:
    st.error(f"❌ Error loading standings: {str(e)}")
