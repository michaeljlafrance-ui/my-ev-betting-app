import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="EV Prop Finder", page_icon="📈", layout="wide")

st.title("📈 Daily +EV MLB Player Prop Finder")
st.subheader("Filtering for Underdogs & Value (-105 or Better)")

# Sidebar for API Key & Settings
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Odds API Key", type="password")

# Let user choose a market
prop_market = st.sidebar.selectbox(
    "Choose Prop Market",
    ["pitcher_strikeouts", "batter_home_runs"]
)

if not api_key:
    st.sidebar.warning("Please enter your Odds API Key to fetch live data.")
    st.info("👋 Welcome! Please enter your Odds API key in the sidebar to load today's MLB player props.")
else:
    st.sidebar.success("API Key loaded!")
    st.write("🔄 Fetching live MLB data...")

    # 1. Fetch active MLB games to get IDs
    games_url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events?apiKey={api_key}"
    
    try:
        games_response = requests.get(games_url).json()
        
        if "error" in games_response:
            st.error(f"API Error: {games_response.get('message', 'Unknown error')}")
        elif len(games_response) == 0:
            st.warning("No MLB games found for today.")
        else:
            st.success(f"Found {len(games_response)} upcoming MLB games!")
            
            all_props = []

            # 2. Loop through games and pull the specific player prop market
            # For testing, we'll limit to the first few games so we don't burn your free API limit
            for game in games_response[:3]:
                game_id = game['id']
                teams = f"{game['home_team']} vs {game['away_team']}"
                
                odds_url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events/{game_id}/odds?apiKey={api_key}&regions=us&markets={prop_market}&oddsFormat=american"
                odds_response = requests.get(odds_url).json()
                
                if 'bookmakers' in odds_response:
                    for bookmaker in odds_response['bookmakers']:
                        book_name = bookmaker['title']
                        for market in bookmaker['markets']:
                            if market['key'] == prop_market:
                                for outcome in market['outcomes']:
                                    player_name = outcome['description']
                                    point = outcome.get('point', 'N/A')
                                    price = outcome['price']
                                    type_name = outcome['name'] # Over or Under
                                    
                                    # STICK TO STRATEGY: Only keep bets at -105 or better (+100, +110, etc)
                                    if price >= -105:
                                        all_props.append({
                                            "Matchup": teams,
                                            "Player": player_name,
                                            "Prop Type": prop_market.replace("_", " ").title(),
                                            "Bet": f"{type_name} {point}",
                                            "Odds": price,
                                            "Sportsbook": book_name
                                        })

            # 3. Display the curated list in a clean table
            if all_props:
                df = pd.DataFrame(all_props)
                # Sort so the highest plus-money payouts are at the top
                df = df.sort_values(by="Odds", ascending=False)
                
                st.write("### 🎯 Best Odds Targets Found (-105 or Better)")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No player props found matching your odds criteria (-105 or better) for the checked games yet. Check back closer to game times!")

    except Exception as e:
        st.error(f"An error occurred: {e}")
