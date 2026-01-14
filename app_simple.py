"""
Simple Football Analytics Dashboard

This dashboard loads the model trained in notebooks and provides predictions.
Data science focused - no complex classes, just straightforward Streamlit.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pickle
import json
import sys
sys.path.append('.')

from utils import load_data, engineer_features, predict_match

# =================================================================
# PAGE CONFIG
# =================================================================

st.set_page_config(
    page_title="Football Analytics",
    page_icon="⚽",
    layout="wide"
)

# =================================================================
# LOAD DATA & MODEL
# =================================================================

@st.cache_data
def load_match_data():
    """Load and prepare data."""
    df = load_data()
    df = engineer_features(df)
    return df

@st.cache_resource
def load_model():
    """Load trained model."""
    try:
        with open('models/simple_model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('models/features.json', 'r') as f:
            features = json.load(f)
        return model, features
    except FileNotFoundError:
        st.error("⚠️ Model not found! Please run notebook 03 to train the model first.")
        return None, None

# Load data
df = load_match_data()
model, features = load_model()

# =================================================================
# SIDEBAR NAVIGATION
# =================================================================

st.sidebar.title("⚽ Football Analytics")
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🔮 Match Predictor", "📈 Insights", "ℹ️ About"]
)

# =================================================================
# PAGE 1: DASHBOARD
# =================================================================

if page == "📊 Dashboard":
    st.title("Football Analytics Dashboard")
    st.markdown("Powered by machine learning and data science")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Matches", f"{len(df):,}")
    
    with col2:
        avg_goals = df['total_goals'].mean()
        st.metric("Avg Goals/Match", f"{avg_goals:.2f}")
    
    with col3:
        home_win_pct = (df['winner'].isin(['HOME_TEAM', 'H'])).mean() * 100
        st.metric("Home Win %", f"{home_win_pct:.1f}%")
    
    with col4:
        if model:
            st.metric("Model Accuracy", "52.8%")
        else:
            st.metric("Model Status", "Not Trained")
    
    # Visualizations
    st.subheader("📈 Recent Trends")
    
    # Goals over time
    recent = df.tail(100).copy()
    recent['match_num'] = range(len(recent))
    
    fig = px.line(recent, x='match_num', y='total_goals',
                  title='Total Goals (Last 100 Matches)')
    st.plotly_chart(fig, use_container_width=True)
    
    # Result distribution
    col1, col2 = st.columns(2)
    
    with col1:
        result_map = {'HOME_TEAM': 'Home Win', 'H': 'Home Win',
                      'AWAY_TEAM': 'Away Win', 'A': 'Away Win',
                      'DRAW': 'Draw', 'D': 'Draw'}
        df['result_clean'] = df['winner'].map(result_map)
        result_counts = df['result_clean'].value_counts()
        
        fig = px.pie(values=result_counts.values, names=result_counts.index,
                     title='Match Results Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Home vs Away goals
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=df['home_score'], name='Home Goals'))
        fig.add_trace(go.Histogram(x=df['away_score'], name='Away Goals'))
        fig.update_layout(title='Goal Distribution', barmode='overlay')
        fig.update_traces(opacity=0.7)
        st.plotly_chart(fig, use_container_width=True)

# =================================================================
# PAGE 2: MATCH PREDICTOR
# =================================================================

elif page == "🔮 Match Predictor":
    st.title("Match Outcome Predictor")
    
    if not model:
        st.warning("⚠️ Please train the model first by running notebook 03!")
        st.stop()
    
    st.markdown("Predict match outcomes using our trained model")
    
    # Team selection
    teams = sorted(df['home_team_name'].unique())
    
    col1, col2 = st.columns(2)
    
    with col1:
        home_team = st.selectbox("Home Team", teams, index=teams.index('Manchester City') if 'Manchester City' in teams else 0)
    
    with col2:
        away_team = st.selectbox("Away Team", teams, index=teams.index('Liverpool') if 'Liverpool' in teams else 1)
    
    if st.button("Predict Match", type="primary"):
        if home_team == away_team:
            st.error("Please select different teams!")
        else:
            # Make prediction
            result = predict_match(home_team, away_team, df)
            
            if 'error' in result:
                st.error(result['error'])
            else:
                # Determine winning team name and probability
                prediction = result['prediction']
                if prediction == 'Home Win':
                    winner = home_team
                    win_prob = result['home_win_prob'] * 100
                elif prediction == 'Away Win':
                    winner = away_team
                    win_prob = result['away_win_prob'] * 100
                else:  # Draw
                    winner = "Draw"
                    win_prob = result['draw_prob'] * 100
                
                # Display prediction with team name and probability
                if winner == "Draw":
                    st.success(f"### 🤝 Prediction: {winner}")
                    st.info(f"**Probability:** {win_prob:.1f}%")
                else:
                    st.success(f"### 🏆 Prediction: **{winner}** to Win")
                    st.info(f"**Win Probability:** {win_prob:.1f}%")
                
                # Show all probabilities
                st.markdown("### Outcome Probabilities")
                probs = pd.DataFrame({
                    'Outcome': [f'{home_team} Win', 'Draw', f'{away_team} Win'],
                    'Probability': [
                        result['home_win_prob'] * 100,
                        result['draw_prob'] * 100,
                        result['away_win_prob'] * 100
                    ]
                })
                
                fig = px.bar(probs, x='Outcome', y='Probability',
                            title='All Outcomes',
                            color='Probability',
                            color_continuous_scale='blues')
                st.plotly_chart(fig, use_container_width=True)
                
                # Show team stats
                st.subheader("Team Statistics")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**{home_team}** (Home)")
                    home_stats = df[df['home_team_name'] == home_team].tail(5)
                    if len(home_stats) > 0:
                        st.write(f"Recent Form: {home_stats['home_form'].iloc[-1]:.2f} pts/match")
                        st.write(f"ELO Rating: {home_stats['home_elo'].iloc[-1]:.0f}")
                
                with col2:
                    st.write(f"**{away_team}** (Away)")
                    away_stats = df[df['away_team_name'] == away_team].tail(5)
                    if len(away_stats) > 0:
                        st.write(f"Recent Form: {away_stats['away_form'].iloc[-1]:.2f} pts/match")
                        st.write(f"ELO Rating: {away_stats['away_elo'].iloc[-1]:.0f}")

# =================================================================
# PAGE 3: INSIGHTS
# =================================================================

elif page == "📈 Insights":
    st.title("Key Insights")
    
    st.subheader("🏠 Home Advantage")
    
    home_avg = df[df['home_team_name'].notna()].groupby('home_team_name')['home_score'].mean().mean()
    away_avg = df[df['away_team_name'].notna()].groupby('away_team_name')['away_score'].mean().mean()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Home Goals/Match", f"{home_avg:.2f}")
    with col2:
        st.metric("Away Goals/Match", f"{away_avg:.2f}")
    with col3:
        st.metric("Home Advantage", f"+{home_avg - away_avg:.2f} goals")
    
    st.markdown("---")
    
    st.subheader("📊 Model Performance")
    
    if model:
        # Feature importance (from model)
        if hasattr(model, 'feature_importances_'):
            importance = pd.DataFrame({
                'Feature': features,
                'Importance': model.feature_importances_
            }).sort_values('Importance', ascending=False)
            
            fig = px.bar(importance, x='Importance', y='Feature',
                        title='Feature Importance',
                        orientation='h')
            st.plotly_chart(fig, use_container_width=True)
        
        st.info("Model trained using XGBoost with 5-fold cross-validation")
    else:
        st.warning("Model not trained yet - run notebook 03 to train")

# =================================================================
# PAGE 4: ABOUT
# =================================================================

else:  # About page
    st.title("About This Project")
    
    st.markdown("""
    ## Football Analytics Platform
    
    **A data science project analyzing Premier League matches**
    
    ### Workflow
    
    ```
    📓 Notebooks → 🤖 Train Model → 📊 Dashboard
    ```
    
    **Data Pipeline:**
    1. Load 3,800 matches from database
    2. Engineer features (ELO, form, stats)
    3. Train XGBoost model with time-based validation
    4. Display predictions in this dashboard
    
    ### Technology Stack
    
    - **Data:** SQLite, pandas, SQL
    - **ML:** scikit-learn, XGBoost
    - **Visualization:** Plotly, Streamlit
    - **Workflow:** Jupyter notebooks
    
    ### Model Details
    
    - **Features:** 15 engineered features (80% custom)
    - **Algorithm:** XGBoost Classifier
    - **Accuracy:** 52.8% (time-based validation, no data leakage)
    - **Cross-Validation:** 47.4% ± 2.8% (5-fold)
    
    ### Data Science Approach
    
    This project emphasizes:
    - ✅ Clean, readable code
    - ✅ Reproducible analysis
    - ✅ Simple over complex
    - ✅ Business-focused insights
    
    **No complex classes or abstractions** - just straightforward data science!
    
    ### Files
    
    - `notebooks/` - Analysis and model training
    - `utils.py` - Helper functions
    - `app_simple.py` - This dashboard
    - `data/` - Match database
    - `models/` - Trained models
    
    ---
    
    Built with ❤️ for data science portfolio
    """)

# =================================================================
# FOOTER
# =================================================================

st.sidebar.markdown("---")
st.sidebar.caption("Football Analytics • Data Science Project")
