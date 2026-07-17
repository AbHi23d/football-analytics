"""Match Predictor page."""

import streamlit as st
import sys
import os
import plotly.graph_objects as go

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'saved')

from src.data_collection import DatabaseManager
from src.models import MatchPredictor
from src.analysis import TeamAnalyzer
from src.visualization import create_prediction_gauge, create_comparison_radar, create_form_chart

c1, c2 = st.columns([6, 1])
with c1:
    st.title("Match Predictor")
    st.markdown("Predict the outcome of any Premier League fixture.")

with st.expander("ℹ️ How does the AI work?"):
    st.markdown("""
    **Data Foundation:** The predictor is built on 10 years of historical Premier League data, aggregated and transformed using advanced SQL pipelines.
    
    **Analytical Features:** We engineered 17 key performance indicators (KPIs) per match, including:
    - **Recent Form:** Rolling 5-match win/loss/draw rates
    - **Attacking/Defensive Stats:** Expected goals (xG) and average goals scored
    - **Context:** Home-field advantage and historical head-to-head dominance
    
    **Why it matters:** By analyzing these structured data points rather than relying on simple averages, we can generate statistically backed probabilities for any fixture.
    """)

try:
    db = DatabaseManager()
    teams = db.get_all_teams()

    if not teams:
        st.error("❌ No teams found. Database may be empty.")
    else:
        team_names = {team['name']: team['id'] for team in teams}
        sorted_names = sorted(team_names.keys())

        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                home_team_name = st.selectbox("Home Team", sorted_names, key="home_team")
            with col2:
                default_away = sorted_names[1] if sorted_names[0] == sorted_names[0] else sorted_names[0]
                away_idx = 1 if sorted_names[0] == home_team_name else 0
                away_team_name = st.selectbox("Away Team", sorted_names, index=away_idx, key="away_team")

        if home_team_name == away_team_name:
            st.warning("⚠️ Please select two different teams.")
        else:
            home_team_id = team_names[home_team_name]
            away_team_id = team_names[away_team_name]

            if st.button("Generate Prediction", type="primary"):
                with st.spinner("Analysing teams and running models…"):
                    predictor = MatchPredictor(db, model_path=MODEL_PATH)
                    try:
                        predictor.load_models()
                    except Exception:
                        st.info("⚙️ Training models on first run — this takes ~30 seconds…")
                        predictor.train_models()

                    prediction = predictor.predict_match(home_team_id, away_team_id)

                    st.divider()

                    # Predicted Score Card
                    st.subheader("Predicted Scoreline")
                    st.markdown(f"### {home_team_name} {prediction['predicted_score']} {away_team_name}")
                    
                    st.write("")

                    # Probabilities & Confidence
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Win Probabilities")
                        fig_gauge = create_prediction_gauge(prediction, home_team_name, away_team_name)
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        
                    with col2:
                        st.subheader("Model Confidence")
                        conf_pct = prediction['confidence'] * 100
                        st.metric(label="Confidence Level", value=f"{conf_pct:.0f}%")

                    st.divider()

                    # Team Comparison
                    st.subheader("Team Comparison")
                    analyzer = TeamAnalyzer(db)
                    comparison = analyzer.compare_teams(home_team_id, away_team_id)

                    if comparison:
                        fig_radar = create_comparison_radar(
                            comparison['team1']['stats'],
                            comparison['team2']['stats'],
                            home_team_name, away_team_name
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)

                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**{home_team_name} Form (Last 5)**")
                            form1 = comparison['team1'].get('form', [])
                            if form1:
                                st.plotly_chart(create_form_chart(form1, home_team_name), use_container_width=True)
                        with col2:
                            st.write(f"**{away_team_name} Form (Last 5)**")
                            form2 = comparison['team2'].get('form', [])
                            if form2:
                                st.plotly_chart(create_form_chart(form2, away_team_name), use_container_width=True)

                        h2h = comparison.get('head_to_head', {})
                        if h2h.get('total_matches', 0) > 0:
                            st.subheader("Head-to-Head History")
                            c1, c2, c3 = st.columns(3)
                            c1.metric(f"{home_team_name} Wins", h2h['team1_wins'])
                            c2.metric("Draws", h2h['draws'])
                            c3.metric(f"{away_team_name} Wins", h2h['team2_wins'])

                    # Features detail
                    with st.expander("View Raw Features"):
                        st.json(prediction.get('features', {}))

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
