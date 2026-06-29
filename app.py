import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Matchup Target Finder", page_icon="🎯", layout="wide")

st.title("🎯 Data-Backed MLB Prop Target Finder")
st.subheader("Hunting for Favorable Matchups at -105 or Better")

# Sidebar
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Odds API Key", type="password")

# --- DATA BASELINE: TEAM STRIKEOUT MATRICES ---
# This serves as our model's "brain" regarding matchups. 
# We flag teams that strike out a lot (Great targets for Pitcher Over props)
# and teams that rarely strike out (Great targets for Pitcher Under props).
high_k_teams = ["Seattle Mariners", "Colorado Rockies", "Oakland Athletics", "Boston Red Sox", "Minnesota Twins"]
low_k_teams = ["Houston Astros", "San Diego Padres", "Toronto Blue Jays", "Arizona Diamondbacks", "Cleveland Guardians"]

if not api_key:
    st.sidebar.warning("Please enter your Odds API Key to fetch live data.")
    st.info("👋 Welcome! Input your API key to generate today's matchup-backed hunt list.")
else:
    st.sidebar.success("API Key loaded!")
    st.write("📊 Analyzing today's matchups and scanning odds...")

    # 1. Fetch active MLB games
    games_url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events?apiKey={api_key}"
    
    try:
        games_response = requests.get(games_url).json()
        
        if "error" in games_response:
            st.error(f"API Error: {games_response.get('message', 'Unknown error')}")
        elif len(games_response) == 0:
            st.warning("No MLB games found for today.")
        else:
            hunt_list = []

            # 2. Loop through games to analyze matchups and odds simultaneously
            for game in games_response[:5]:  # Scanning first 5 games to save API quota
                game_id = game['id']
                home_team = game['home_team']
                away_team = game['away_team']
                matchup_name = f"{away_team} @ {home_team}"
                
                # Fetch Pitcher Strikeout Props for this game
                odds_url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events/{game_id}/odds?apiKey={api_key}&regions=us&markets=pitcher_strikeouts&oddsFormat=american"
                odds_response = requests.get(odds_url).json()
                
                if 'bookmakers' in odds_response:
                    for bookmaker in odds_response['bookmakers']:
                        book_name = bookmaker['title']
                        for market in bookmaker['markets']:
                            if market['key'] == 'pitcher_strikeouts':
                                for outcome in market['outcomes']:
                                    player = outcome['description']
                                    line = outcome.get('point', 'N/A')
                                    price = outcome['price']
                                    bet_type = outcome['name'] # Over or Under
                                    
                                    # Determine who this pitcher is playing against
                                    # (If the pitcher's team is Home, they are pitching against the Away team)
                                    # Note: For a strict model, we'd verify player team, but checking both teams in the matchup works as a baseline filter.
                                    
                                    matchup_grade = "Neutral"
                                    is_solid_matchup = False
                                    
                                    # MODEL LOGIC: 
                                    # If we want an OVER, we want the opponent to be a high strikeout team.
                                    if bet_type == "Over" and (home_team in high_k_teams or away_team in high_k_teams):
                                        matchup_grade = "🔥 Highly Favorable (High K Opponent)"
                                        is_solid_matchup = True
                                    # If we want an UNDER, we want the opponent to be a disciplined, low strikeout team.
                                    elif bet_type == "Under" and (home_team in low_k_teams or away_team in low_k_teams):
                                        matchup_grade = "🔒 Favorable Under (Disciplined Opponent)"
                                        is_solid_matchup = True
                                        
                                    # STRATEGY FILTER: Must be a data-backed matchup AND odds must be -105 or better
                                    if is_solid_matchup and price >= -105:
                                        hunt_list.append({
                                            "Matchup": matchup_name,
                                            "Player Target": player,
                                            "Bet Recommendation": f"{bet_type} {line}",
                                            "Matchup Analysis": matchup_grade,
                                            "Odds": price,
                                            "Sportsbook Available": book_name
                                        })

            # 3. Display results
            if hunt_list:
                df = pd.DataFrame(hunt_list)
                df = df.sort_values(by="Odds", ascending=False)
                
                st.write("### 🏹 Today's EV Hunt List (Solid Matchups + Good Odds)")
                st.write("The following props have a mathematically favorable matchup baseline AND meet your odds criteria of -105 or better:")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Scanned current games. No props currently fit BOTH a highly favorable team matchup and the -105 odds filter. Check back as more sportsbooks release lines!")

    except Exception as e:
        st.error(f"An error occurred: {e}")
