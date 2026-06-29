import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Multi-Sport Prop Finder", page_icon="🎯", layout="wide")

st.title("🎯 Data-Backed Multi-Sport Target Finder")
st.subheader("Hunting Favorable Matchups & Value")

# Initialize virtual bankroll
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0
if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar Configuration
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Odds API Key", type="password")

# 1. SELECT THE SPORT
sport_choice = st.sidebar.selectbox("Choose Sport", ["MLB Baseball", "Wimbledon Tennis", "WNBA Basketball"])

# 2. DYNAMIC DROPDOWNS BASED ON SPORT
if sport_choice == "MLB Baseball":
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
    sport_key = "baseball_mlb"

elif sport_choice == "Wimbledon Tennis":
    tennis_tour = st.sidebar.selectbox("Tour", [["tennis_atp_wimbledon", "ATP (Men's)"], ["tennis_wta_wimbledon", "WTA (Women's)"]], format_func=lambda x: x[1])[0]
    prop_market = st.sidebar.selectbox(
        "Choose Betting Market",
        [
            ["h2h", "Moneyline (Winner)"],
            ["spreads", "Game Handicap (Spread)"],
            ["totals", "Total Match Games (O/U)"]
        ],
        format_func=lambda x: x[1]
    )[0]
    sport_key = tennis_tour

else:
    # WNBA Setup
    prop_market = st.sidebar.selectbox(
        "Choose Prop Market",
        [
            ["player_points", "Player Points"],
            ["player_rebounds", "Player Rebounds"],
            ["player_assists", "Player Assists"]
        ],
        format_func=lambda x: x[1]
    )[0]
    sport_key = "basketball_wnba"

# Display Bankroll Tracker
st.sidebar.markdown("---")
st.sidebar.metric(label="Virtual Bankroll", value=f"${st.session_state.bankroll:.2f}")
if st.sidebar.button("Reset Bankroll to $1,000"):
    st.session_state.bankroll = 1000.0
    st.session_state.history = []
    st.rerun()

# --- HARDCODED STRATEGY ARRAYS ---
high_k_teams = ["Seattle Mariners", "Colorado Rockies", "Oakland Athletics", "Boston Red Sox", "Minnesota Twins"]
low_k_teams = ["Houston Astros", "San Diego Padres", "Toronto Blue Jays", "Arizona Diamondbacks", "Cleveland Guardians"]
bad_pitching_teams = ["Colorado Rockies", "Chicago White Sox", "Miami Marlins", "Oakland Athletics", "Los Angeles Angels"]
elite_grass_players = ["Alcaraz", "Sinner", "Djokovic", "Hurkacz", "Sabalenka", "Swiatek", "Rybakina"]

# WNBA Strategy Targets
high_pace_teams = ["Las Vegas Aces", "Dallas Wings", "Phoenix Mercury", "Indiana Fever"]
elite_interior_players = ["Wilson", "Stewart", "Jones", "Collier", "Cardoso", "Boston"]

if not api_key:
    st.sidebar.warning("Please enter your Odds API Key.")
    st.info("👋 Welcome! Select your sport and input your API key in the sidebar to load the daily hunt list.")
else:
    st.sidebar.success("API Key loaded!")
    st.write(f"📊 Analyzing {sport_choice} markets and scanning live odds...")

    games_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events?apiKey={api_key}"
    
    try:
        games_response = requests.get(games_url).json()
        
        if "error" in games_response:
            st.error(f"API Error: {games_response.get('message', 'Unknown error')}")
        elif len(games_response) == 0:
            st.warning(f"No active events found for {sport_choice} right now.")
        else:
            hunt_list = []

            # Scan top 6 matches/games
            for game in games_response[:6]:
                game_id = game['id']
                home_team = game['home_team']
                away_team = game['away_team']
                matchup_name = f"{away_team} @ {home_team}" if sport_choice != "Wimbledon Tennis" else f"{home_team} vs {away_team}"
                
                odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events/{game_id}/odds?apiKey={api_key}&regions=us&markets={prop_market}&oddsFormat=american"
                odds_response = requests.get(odds_url).json()
                
                if 'bookmakers' in odds_response:
                    for bookmaker in odds_response['bookmakers']:
                        book_name = bookmaker['title']
                        for market in bookmaker['markets']:
                            if market['key'] == prop_market:
                                for outcome in market['outcomes']:
                                    player = outcome['description'] if 'description' in outcome else outcome['name']
                                    line = outcome.get('point', '')
                                    price = outcome['price']
                                    
                                    is_solid_matchup = False
                                    matchup_grade = "Neutral"
                                    odds_pass = True
                                    
                                    # --- MLB LOGIC ---
                                    if sport_choice == "MLB Baseball":
                                        if prop_market == "pitcher_strikeouts":
                                            if outcome['name'] == "Over" and (game['home_team'] in high_k_teams or game['away_team'] in high_k_teams):
                                                matchup_grade = "🔥 Favorable (High K Opponent)"
                                                is_solid_matchup = True
                                            elif outcome['name'] == "Under" and (game['home_team'] in low_k_teams or game['away_team'] in low_k_teams):
                                                matchup_grade = "🔒 Favorable Under (Disciplined Opponent)"
                                                is_solid_matchup = True
                                        elif prop_market in ["batter_total_bases", "batter_hits", "batter_home_runs"]:
                                            if outcome['name'] == "Over" and (game['home_team'] in bad_pitching_teams or game['away_team'] in bad_pitching_teams):
                                                matchup_grade = "💥 Favorable Hitting (Weak Pitching Def)"
                                                is_solid_matchup = True
                                        odds_pass = (price >= -105)

                                    # --- TENNIS LOGIC ---
                                    elif sport_choice == "Wimbledon Tennis":
                                        if prop_market == "h2h":
                                            if -180 <= price <= 140:
                                                matchup_grade = "⚖️ Competitive Value Zone"
                                                is_solid_matchup = True
                                                if any(elite in player for elite in elite_grass_players) and price < 0:
                                                    matchup_grade = "🌱 Elite Grass Favorite"
                                        elif prop_market == "spreads":
                                            if -4.5 <= float(line) <= 4.5:
                                                matchup_grade = "🎾 Tight Game Spread"
                                                is_solid_matchup = True
                                        elif prop_market == "totals":
                                            if outcome['name'] == "Over" and any(elite in matchup_name for elite in elite_grass_players):
                                                matchup_grade = "💣 High Server Matchup (Over Favored)"
                                                is_solid_matchup = True
                                            else:
                                                matchup_grade = "Standard Total"
                                                is_solid_matchup = True

                                    # --- WNBA LOGIC ---
                                    else:
                                        # Points: Look for game overs involving high pace teams
                                        if prop_market == "player_points":
                                            if outcome['name'] == "Over" and (game['home_team'] in high_pace_teams or game['away_team'] in high_pace_teams):
                                                matchup_grade = "⚡ High Pace Matchup (Points Over)"
                                                is_solid_matchup = True
                                        
                                        # Rebounds: Look for high volume paint players
                                        elif prop_market == "player_rebounds":
                                            if outcome['name'] == "Over" and any(elite in player for elite in elite_interior_players):
                                                matchup_grade = "💪 Elite Board-Crasher Baseline"
                                                is_solid_matchup = True
                                        
                                        # Assists: Standard filter to hunt price bugs
                                        elif prop_market == "player_assists":
                                            matchup_grade = "🏀 Playmaker Volume Line"
                                            is_solid_matchup = True
                                        
                                        # Target standard juice brackets to protect profit margins
                                        odds_pass = (-125 <= price <= 115)

                                    if is_solid_matchup and odds_pass:
                                        display_target = f"{outcome['name']} {line}".strip() if prop_market != "h2h" else "To Win Match"
                                        hunt_list.append({
                                            "Matchup": matchup_name,
                                            "Selection": player,
                                            "Bet": display_target,
                                            "Analysis": matchup_grade,
                                            "Odds": price,
                                            "Book": book_name
                                        })

            # Render Screen
            if hunt_list:
                df = pd.DataFrame(hunt_list).drop_duplicates(subset=["Selection", "Bet", "Odds"])
                df = df.sort_values(by="Odds", ascending=False).reset_index(drop=True)
                
                st.write(f"### 🏹 Today's {sport_choice} Hunt List")
                
                for idx, row in df.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 2])
                    with col1:
                        st.markdown(f"**{row['Selection']}** <br><small style='color:gray'>{row['Matchup']}</small>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"`{row['Bet']}` <br>*{row['Analysis']}*", unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"**{row['Odds']}** <br><small>{row['Book']}</small>", unsafe_allow_html=True)
                    with col4:
                        if st.button(f"Simulate Win (+$10)", key=f"win_{idx}"):
                            profit = 10.0 if row['Odds'] == 100 else (10.0 * (row['Odds']/100) if row['Odds'] > 0 else 10.0 / (abs(row['Odds'])/100))
                            st.session_state.bankroll += profit
                            st.session_state.history.append(f"✅ Won: {row['Selection']} - {row['Bet']} ({row['Odds']})")
                            st.rerun()
                        if st.button(f"Simulate Loss (-$10)", key=f"loss_{idx}"):
                            st.session_state.bankroll -= 10.0
                            st.session_state.history.append(f"❌ Lost: {row['Selection']} - {row['Bet']} ({row['Odds']})")
                            st.rerun()
                    st.markdown("---")
                
                if st.session_state.history:
                    st.write("### 📝 Simulation History")
                    for log in reversed(st.session_state.history):
                        st.write(log)
            else:
                st.info("No high-value projection gaps found for this market selection right now. Flip filters or check closer to tip-off!")

    except Exception as e:
        st.error(f"An error occurred: {e}")
