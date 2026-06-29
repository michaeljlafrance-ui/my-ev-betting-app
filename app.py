import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Prop Hunt & Sim", page_icon="🎯", layout="wide")

st.title("🎯 Data-Backed MLB Prop Finder & Simulator")
st.subheader("Hunting Favorable Matchups (-105 or Better)")

# Initialize a virtual bankroll in the app's memory if it doesn't exist yet
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0
if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar Configuration
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Odds API Key", type="password")

# Expanded Market Dropdown
prop_market = st.sidebar.selectbox(
    "Choose Prop Market",
    [
        ["pitcher_strikeouts", "Pitcher Strikeouts"],
        ["batter_total_bases", "Batter Total Bases"],
        ["batter_hits", "Batter Hits"],
        ["batter_home_runs", "Batter Home Runs"]
    ],
    format_func=lambda x: x[1]
)[0]

# Display Bankroll Tracker in Sidebar
st.sidebar.markdown("---")
st.sidebar.metric(label="Virtual Bankroll", value=f"${st.session_state.bankroll:.2f}")
if st.sidebar.button("Reset Bankroll to $1,000"):
    st.session_state.bankroll = 1000.0
    st.session_state.history = []
    st.rerun()

# --- DATA BASELINE: MATCHUP MATRICES ---
high_k_teams = ["Seattle Mariners", "Colorado Rockies", "Oakland Athletics", "Boston Red Sox", "Minnesota Twins"]
low_k_teams = ["Houston Astros", "San Diego Padres", "Toronto Blue Jays", "Arizona Diamondbacks", "Cleveland Guardians"]
bad_pitching_teams = ["Colorado Rockies", "Chicago White Sox", "Miami Marlins", "Oakland Athletics", "Los Angeles Angels"]

if not api_key:
    st.sidebar.warning("Please enter your Odds API Key.")
    st.info("👋 Welcome! Input your API key in the sidebar to load today's MLB player props and start hunting.")
else:
    st.sidebar.success("API Key loaded!")
    st.write("📊 Analyzing today's matchups and scanning live odds...")

    games_url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events?apiKey={api_key}"
    
    try:
        games_response = requests.get(games_url).json()
        
        if "error" in games_response:
            st.error(f"API Error: {games_response.get('message', 'Unknown error')}")
        elif len(games_response) == 0:
            st.warning("No MLB games found for today.")
        else:
            hunt_list = []

            # Scan upcoming games
            for game in games_response[:5]:
                game_id = game['id']
                home_team = game['home_team']
                away_team = game['away_team']
                matchup_name = f"{away_team} @ {home_team}"
                
                odds_url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events/{game_id}/odds?apiKey={api_key}&regions=us&markets={prop_market}&oddsFormat=american"
                odds_response = requests.get(odds_url).json()
                
                if 'bookmakers' in odds_response:
                    for bookmaker in odds_response['bookmakers']:
                        book_name = bookmaker['title']
                        for market in bookmaker['markets']:
                            if market['key'] == prop_market:
                                for outcome in market['outcomes']:
                                    player = outcome['description']
                                    line = outcome.get('point', 'N/A')
                                    price = outcome['price']
                                    bet_type = outcome['name']
                                    
                                    is_solid_matchup = False
                                    matchup_grade = "Neutral"
                                    
                                    # Matchup Logic based on selected market
                                    if prop_market == "pitcher_strikeouts":
                                        if bet_type == "Over" and (home_team in high_k_teams or away_team in high_k_teams):
                                            matchup_grade = "🔥 Highly Favorable (High K Opponent)"
                                            is_solid_matchup = True
                                        elif bet_type == "Under" and (home_team in low_k_teams or away_team in low_k_teams):
                                            matchup_grade = "🔒 Favorable Under (Disciplined Opponent)"
                                            is_solid_matchup = True
                                    
                                    elif prop_market in ["batter_total_bases", "batter_hits", "batter_home_runs"]:
                                        if bet_type == "Over" and (home_team in bad_pitching_teams or away_team in bad_pitching_teams):
                                            matchup_grade = "💥 Favorable Hitting (Weak Pitching Def)"
                                            is_solid_matchup = True

                                    # Filter Strategy: Solid Matchup + Odds -105 or better
                                    if is_solid_matchup and price >= -105:
                                        hunt_list.append({
                                            "Matchup": matchup_name,
                                            "Player": player,
                                            "Target": f"{bet_type} {line}",
                                            "Grade": matchup_grade,
                                            "Odds": price,
                                            "Book": book_name
                                        })

            # Display Results & Simulation Interactive Panel
            if hunt_list:
                df = pd.DataFrame(hunt_list).drop_duplicates(subset=["Player", "Target", "Odds"])
                df = df.sort_values(by="Odds", ascending=False).reset_index(drop=True)
                
                st.write("### 🏹 Today's EV Hunt List")
                
                # Render the table with checkboxes or selection for simulation tracking
                for idx, row in df.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 2])
                    with col1:
                        st.markdown(f"**{row['Player']}** ({row['Matchup']})")
                    with col2:
                        st.markdown(f"`{row['Target']}` | {row['Grade']}")
                    with col3:
                        st.markdown(f"**{row['Odds']素}** ({row['Book']})")
                    with col4:
                        # Simple buttons to let user simulate grading the bet later
                        if st.button(f"Simulate Win (+$10)", key=f"win_{idx}"):
                            profit = 10.0 if row['Odds'] == 100 else (10.0 * (row['Odds']/100) if row['Odds'] > 0 else 10.0 / (abs(row['Odds'])/100))
                            st.session_state.bankroll += profit
                            st.session_state.history.append(f"✅ Won: {row['Player']} {row['Target']} ({row['Odds']})")
                            st.rerun()
                        if st.button(f"Simulate Loss (-$10)", key=f"loss_{idx}"):
                            st.session_state.bankroll -= 10.0
                            st.session_state.history.append(f"❌ Lost: {row['Player']} {row['Target']} ({row['Odds']})")
                            st.rerun()
                    st.markdown("---")
                
                if st.session_state.history:
                    st.write("### 📝 Simulation
