import streamlit as st
from supabase import create_client, Client
import time
import random

# --- 1. CONNECTION ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception:
    st.error("Missing Supabase Secrets!")
    st.stop()

# --- 2. SESSION STATE & LOGIN ---
if 'player_name' not in st.session_state:
    st.session_state.player_name = None

if not st.session_state.player_name:
    st.title("🎨 Dixit: Family Edition")
    with st.form("login"):
        name = st.text_input("Your Name").strip().upper()
        group = st.text_input("Family Group Code").strip().upper()
        if st.form_submit_button("Join Game"):
            if name and group:
                st.session_state.player_name = name
                st.session_state.group_code = group
                st.rerun()
    st.stop()

# --- 3. SYNC GAME STATE ---
group_code = st.session_state.group_code
player = st.session_state.player_name

# Fetch game data
res = supabase.table("dixit_games").select("*").eq("group_code", group_code).execute()

if not res.data:
    # Initialize game if first time
    supabase.table("dixit_games").insert({"group_code": group_code}).execute()
    st.rerun()

game = res.data[0]
phase = game['phase']
submissions = game['submissions'] or {}
votes = game['votes'] or {}

# --- 4. GAME UI ---
st.title(f"🎮 Dixit - Group: {group_code}")
st.sidebar.write(f"Logged in as: **{player}**")

# --- PHASE: LOBBY ---
if phase == "LOBBY":
    st.subheader("Waiting for everyone to join...")
    st.info("When everyone is ready, someone click Start.")
    
    if st.button("🚀 START GAME", type="primary"):
        supabase.table("dixit_games").update({
            "phase": "STORYTELLING",
            "storyteller_id": player,
            "submissions": {},
            "votes": {},
            "clue": None
        }).eq("group_code", group_code).execute()
        st.rerun()

# --- PHASE: STORYTELLING ---
elif phase == "STORYTELLING":
    if player == game['storyteller_id']:
        st.subheader("🌟 You are the Storyteller!")
        # In a real version, this would be a random image. For now, it's a word.
        secret_word = "MIRAGE" 
        st.write(f"Your secret word is: **{secret_word}**")
        
        clue = st.text_input("Enter a cryptic clue:")
        if st.button("Submit Clue") and clue:
            new_subs = {player: secret_word}
            supabase.table("dixit_games").update({
                "clue": clue,
                "phase": "SUBMITTING",
                "submissions": new_subs
            }).eq("group_code", group_code).execute()
            st.rerun()
    else:
        st.subheader("Waiting for the Storyteller...")
        st.write(f"**{game['storyteller_id']}** is thinking of a clue...")

# --- PHASE: SUBMITTING ---
elif phase == "SUBMITTING":
    st.subheader(f"Clue: '{game['clue']}'")
    
    if player in submissions:
        st.success("Your word is submitted. Waiting for others...")
    else:
        decoy = st.text_input("Choose a decoy word to trick others:")
        if st.button("Submit Decoy") and decoy:
            submissions[player] = decoy
            supabase.table("dixit_games").update({"submissions": submissions}).eq("group_code", group_code).execute()
            st.rerun()

    # Anyone can trigger the move to voting if everyone is in (e.g. 3+ people)
    if len(submissions) > 1:
        if st.button("All players submitted? Move to Vote"):
            supabase.table("dixit_games").update({"phase": "VOTING"}).eq("group_code", group_code).execute()
            st.rerun()

# --- PHASE: VOTING ---
elif phase == "VOTING":
    st.subheader(f"Clue: '{game['clue']}'")
    
    if player == game['storyteller_id']:
        st.info("Storytellers can't vote. Waiting for the family...")
    elif player in votes:
        st.success("Vote recorded. Waiting for results...")
    else:
        # Show all words except the player's own
        options = [word for p, word in submissions.items() if p != player]
        choice = st.radio("Which word belongs to the storyteller?", options)
        
        if st.button("Cast Vote"):
            votes[player] = choice
            supabase.table("dixit_games").update({"votes": votes}).eq("group_code", group_code).execute()
            st.rerun()

    if st.button("Show Results"):
        supabase.table("dixit_games").update({"phase": "RESULTS"}).eq("group_code", group_code).execute()
        st.rerun()

# --- PHASE: RESULTS ---
elif phase == "RESULTS":
    st.header("🏆 Round Results")
    correct_word = submissions.get(game['storyteller_id'])
    st.write(f"The Storyteller's word was: **{correct_word}**")
    
    for p, v in votes.items():
        st.write(f"**{p}** voted for: *{v}* {'🎯' if v == correct_word else '❌'}")
    
    if st.button("Back to Lobby"):
        supabase.table("dixit_games").update({"phase": "LOBBY"}).eq("group_code", group_code).execute()
        st.rerun()

# --- AUTO-REFRESH ---
# This keeps everyone's screen in sync without manual refreshing
time.sleep(3)
st.rerun()
