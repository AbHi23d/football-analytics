"""Team Analysis page."""

import streamlit as st
import sys
import os
import plotly.graph_objects as go

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.data_collection import DatabaseManager
from src.analysis import TeamAnalyzer
from src.visualization import create_team_performance_chart, create_form_chart, create_comparison_radar

c1, c2 = st.columns([6, 1])
with c1:
    st.title("Team Analysis")
    st.markdown("Deep-dive into team performance metrics.")

try:
    db = DatabaseManager()
    teams = db.get_all_teams()

    if not teams:
        st.error("❌ No teams found in database.")
    else:
        team_names = {team['name']: team['id'] for team in teams}
        sorted_names = sorted(team_names.keys())

        selected_team = st.selectbox("Select a team", sorted_names, key="selected_team")
        team_id = team_names[selected_team]

        analyzer = TeamAnalyzer(db)
        overview = analyzer.get_team_overview(team_id)

        if not overview:
            st.warning("⚠️ No data available for this team.")
        else:
            stats = overview['overall_stats']

            # KPI Band
            cols = st.columns(5)
            cols[0].metric("Matches", stats['total_matches'])
            cols[1].metric("Wins", stats['wins'])
            cols[2].metric("Draws", stats['draws'])
            cols[3].metric("Losses", stats['losses'])
            cols[4].metric("Points", stats['points'])

            h_col1, h_col2 = st.columns([3, 1])
            with h_col1:
                st.write("")
            with h_col2:
                import pandas as pd
                st.download_button(
                    label="📥 Export Stats",
                    data=pd.DataFrame([stats]).to_csv(index=False).encode('utf-8'),
                    file_name=f"{selected_team}_stats.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            st.write("")

            tab1, tab2, tab3 = st.tabs(["Performance Overview", "Home vs Away", "Head-to-Head Compare"])

            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(create_team_performance_chart(stats, selected_team), use_container_width=True)
                with col2:
                    form = overview.get('recent_form', [])
                    if form:
                        st.plotly_chart(create_form_chart(form, selected_team), use_container_width=True)
                    else:
                        st.info("No recent form data available.")

            with tab2:
                home_stats = overview.get('home_stats', {})
                away_stats = overview.get('away_stats', {})

                if home_stats and away_stats:
                    c1, c2 = st.columns(2)
                    with c1:
                        with st.container(border=True):
                            st.subheader("Home Record")
                            st.write(f"**Matches:** {home_stats.get('total_matches', 0)}")
                            st.write(f"**Wins:** {home_stats.get('wins', 0)}")
                            st.write(f"**Draws:** {home_stats.get('draws', 0)}")
                            st.write(f"**Losses:** {home_stats.get('losses', 0)}")
                            st.write(f"**Goals For:** {home_stats.get('goals_scored', 0)}")
                            st.write(f"**Goals Against:** {home_stats.get('goals_conceded', 0)}")
                    with c2:
                        with st.container(border=True):
                            st.subheader("Away Record")
                            st.write(f"**Matches:** {away_stats.get('total_matches', 0)}")
                            st.write(f"**Wins:** {away_stats.get('wins', 0)}")
                            st.write(f"**Draws:** {away_stats.get('draws', 0)}")
                            st.write(f"**Losses:** {away_stats.get('losses', 0)}")
                            st.write(f"**Goals For:** {away_stats.get('goals_scored', 0)}")
                            st.write(f"**Goals Against:** {away_stats.get('goals_conceded', 0)}")
                else:
                    st.info("Home/Away breakdown not available.")

            with tab3:
                other_teams = [n for n in sorted_names if n != selected_team]
                other_team = st.selectbox("Compare with", other_teams, key="compare_team")
                other_id = team_names[other_team]

                comparison = analyzer.compare_teams(team_id, other_id)
                if comparison:
                    st.plotly_chart(
                        create_comparison_radar(
                            comparison['team1']['stats'],
                            comparison['team2']['stats'],
                            selected_team, other_team
                        ),
                        use_container_width=True
                    )

                    h2h = comparison.get('head_to_head', {})
                    if h2h.get('total_matches', 0) > 0:
                        st.subheader("Head-to-Head Totals")
                        c1, c2, c3 = st.columns(3)
                        c1.metric(f"{selected_team} Wins", h2h['team1_wins'])
                        c2.metric("Draws", h2h['draws'])
                        c3.metric(f"{other_team} Wins", h2h['team2_wins'])

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
