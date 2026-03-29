import streamlit as st
from supabase import create_client, Client
import time
import random

# --- 1. CONNECTION ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Check your .streamlit/secrets.toml for SUPABASE_URL and SUPABASE_KEY!")
    st.stop()

# --- 2. IMAGE FACTORY (Uploader) ---
st.set_page_config(page_title="Dixit Family", page_icon="🎨", layout="wide")

st.title("🎨 Dixit Image Factory")
with st.expander("⬆️ Add New Cards to the Game Pool (Anyone can add!)"):
    uploaded_file = st.file_uploader("Upload a surreal/abstract image", type=['png', 'jpg', 'jpeg'])
    if st.button("Upload to Database"):
        if uploaded_file:
            filename = f"{int(time.time())}_{uploaded_file.name}"
            try:
                # 1. Upload file to Storage
                supabase.storage.from_('dixit_images').upload(filename, uploaded_file.read())
                public_url = supabase.storage.from_('dixit_images').get_public_url(filename)
                # 2. Save URL to Image Pool Table
                supabase.table("dixit_pool").insert({"url": public_url}).execute()
                st.success("Card added to the deck successfully!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Upload failed: {e}")
        else:
            st.error("Please select a file first.")

st.divider()

# --- 3. SESSION STATE & LOGIN ---
if 'player_name' not in st.session_state:
    st.session_state.player_name = None

if not st.session_state.player_name:
    with st.form("login"):
        name = st.text_input("Your Name").strip().upper()
        group = st.text_input("Family Group Code").strip().upper()
        if st.form_submit_button("Join Game"):
            if name and group:
                st.session_state.player_name = name
                st.session_state.group_code = group
                st.rerun()
    st.stop()

# --- 4. SHARED GAME DATA ---
player = st.session_state.player_name
group = st.session_state.group_code

# Fetch or Init Game State
game_res = supabase.table("dixit_games").select("*").eq("group_code", group).execute()
if not game_res.data:
    supabase.table("dixit_games").insert({"group_code": group}).execute()
    st.rerun()

game = game_res.data[0]
phase = game['phase']
submissions = game['submissions'] or {}
votes = game['votes'] or {}

# Fetch All Cards in Pool
all_cards = [row['url'] for row in supabase.table("dixit_pool").select("url").execute().data]

# --- 5. DECK GENERATION (No Duplicates Logic) ---
# We use the group_code to seed a master shuffle so players get unique cards
random.seed(group)
master_deck = all_cards.copy()
random.shuffle(master_deck)

# We use a simple hash of the player's name to give them a consistent slice of the deck
player_hash = sum(ord(char) for char in player) % 10
start_idx = (player_hash * 6) % max(1, len(master_deck) - 6)
my_hand = master_deck[start_idx : start_idx + 6]

# --- 6. GAME UI ---
st.sidebar.title("🎮 Dixit Game")
st.sidebar.write(f"**Player:** {player}")
st.sidebar.write(f"**Group:** {group}")
st.sidebar.write(f"**Phase:** {phase}")

if st.sidebar.button("🚪 Log Out"):
    st.session_state.player_name = None
    st.rerun()

# --- PHASE: LOBBY ---
if phase == "LOBBY":
    st.header("🏠 Game Lobby")
    st.write("Waiting for the family to gather. Once everyone is ready, start the round!")
    if st.button("🚀 Start Round", type="primary"):
        supabase.table("dixit_games").update({
            "phase": "STORYTELLING",
            "storyteller_id": player,
            "submissions": {},
            "votes": {},
            "clue": None
        }).eq("group_code", group).execute()
        st.rerun()

# --- PHASE: STORYTELLING ---
elif phase == "STORYTELLING":
    if player == game['storyteller_id']:
        st.header("🌟 You are the Storyteller!")
        st.write("Choose a card from your hand and give it a cryptic description.")
        
        cols = st.columns(3)
        for i, img in enumerate(my_hand):
            with cols[i % 3]:
                st.image(img, use_container_width=True)
                if st.button(f"Select Card {i+1}", key=f"story_sel_{i}"):
                    st.session_state.selected_card = img
        
        if 'selected_card' in st.session_state:
            st.divider()
            st.image(st.session_state.selected_card, width=200, caption="Your choice")
            clue = st.text_input("Enter your clue (word or sentence):")
            if st.button("Submit Clue") and clue:
                submissions[player] = st.session_state.selected_card
                supabase.table("dixit_games").update({
                    "clue": clue,
                    "phase": "SUBMITTING",
                    "submissions": submissions
                }).eq("group_code", group).execute()
                del st.session_state.selected_card
                st.rerun()
    else:
        st.header("⏳ Waiting for Storyteller")
        st.info(f"**{game['storyteller_id']}** is picking a card and writing a clue...")

# --- PHASE: SUBMITTING ---
elif phase == "SUBMITTING":
    st.header(f"📝 The Clue is: '{game['clue']}'")
    
    if player in submissions:
        st.success("You've submitted your decoy! Waiting for the others...")
    else:
        st.write("Pick a card from your hand to TRICK others into thinking it's the Storyteller's card.")
        cols = st.columns(3)
        for i, img in enumerate(my_hand):
            with cols[i % 3]:
                st.image(img, use_container_width=True)
                if st.button(f"Submit Card {i+1}", key=f"decoy_sub_{i}"):
                    submissions[player] = img
                    supabase.table("dixit_games").update({"submissions": submissions}).eq("group_code", group).execute()
                    st.rerun()
    
    # Storyteller can advance the game once there are enough decoys
    if player == game['storyteller_id'] and len(submissions) > 1:
        if st.button("Everybody in? Start Voting"):
            supabase.table("dixit_games").update({"phase": "VOTING"}).eq("group_code", group).execute()
            st.rerun()

# --- PHASE: VOTING ---
elif phase == "VOTING":
    st.header(f"🗳️ Vote! Clue: '{game['clue']}'")
    
    if player == game['storyteller_id']:
        st.info("Storytellers can't vote. Watch the results come in!")
    elif player in votes:
        st.success("Vote recorded. Waiting for results...")
    else:
        # Shuffle submitted images so position doesn't give away the storyteller
        all_subs = list(submissions.values())
        random.seed(group + game['clue']) # Shuffled same for everyone
        random.shuffle(all_subs)
        
        st.write("Which card do you think belongs to the storyteller?")
        cols = st.columns(3)
        for i, img in enumerate(all_subs):
            # Players shouldn't be able to vote for their own decoy
            if img == submissions.get(player):
                with cols[i % 3]:
                    st.image(img, use_container_width=True, caption="Your Decoy")
                    st.button("Cannot Vote", disabled=True, key=f"vote_dis_{i}")
            else:
                with cols[i % 3]:
                    st.image(img, use_container_width=True)
                    if st.button(f"Vote Card {i+1}", key=f"vote_btn_{i}"):
                        votes[player] = img
                        supabase.table("dixit_games").update({"votes": votes}).eq("group_code", group).execute()
                        st.rerun()

    if player == game['storyteller_id'] and len(votes) >= 1:
        if st.button("Close Voting & Show Results"):
            supabase.table("dixit_games").update({"phase": "RESULTS"}).eq("group_code", group).execute()
            st.rerun()

# --- PHASE: RESULTS ---
elif phase == "RESULTS":
    st.header("🏆 Results")
    storyteller_card = submissions.get(game['storyteller_id'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(storyteller_card, width=300, caption="The Correct Card")
    
    with col2:
        st.subheader("Votes:")
        for voter, card_voted in votes.items():
            result = "🎯 SUCCESS" if card_voted == storyteller_card else "❌ FOOLED"
            st.write(f"**{voter}**: {result}")

    st.divider()
    
    # Only the host/storyteller can reset the game
    if player == game['storyteller_id']:
        st.warning("Host Controls")
        if st.button("🔄 Restart & Exit to Lobby", type="primary"):
            supabase.table("dixit_games").update({
                "phase": "LOBBY",
                "clue": None,
                "submissions": {},
                "votes": {},
                "storyteller_id": None
            }).eq("group_code", group).execute()
            st.rerun()

# --- 7. GLOBAL REFRESH ---
# Auto-sync every 3 seconds so everyone sees phase changes
time.sleep(3)
st.rerun()
