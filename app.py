import streamlit as st

st.set_page_config(page_title="EV Prop Finder", page_icon="📈", layout="centered")

st.title("📈 Daily +EV Player Prop Finder")
st.subheader("Targeting -105 or Better Odds")

st.write("Welcome to your sports betting dashboard! Your app pipeline is officially connected.")

# A placeholder sidebar for your API key later
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("Enter your Odds API Key", type="password")

if api_key:
    st.sidebar.success("API Key loaded successfully!")
else:
    st.sidebar.warning("Please enter your API Key to fetch live data.")
