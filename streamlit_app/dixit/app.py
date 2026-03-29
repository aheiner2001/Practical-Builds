import streamlit as st
from supabase import create_client, Client
import time
import random

# --- 1. CONNECTION ---
supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- 2. IMAGE UPLOADER (Before Login) ---
st.title("🎨 Dixit Image Factory")
with st.expander("⬆️ Add New Cards to the Game Pool"):
    # Changed from file_input to file_uploader
    uploaded_file = st.file_uploader("Upload a surreal/abstract image", type=['png', 'jpg', 'jpeg'])
    
    if st.button("Upload to Database"):
        if uploaded_file:
            filename = f"{int(time.time())}_{uploaded_file.name}"
            # 1. Upload to Supabase Storage
            try:
                supabase.storage.from_('dixit_images').upload(filename, uploaded_file.read())
                url = supabase.storage.from_('dixit_images').get_public_url(filename)
                # 2. Save to Image Pool
                supabase.table("dixit_pool").insert({"url": url}).execute()
                st.success("Card added to the deck!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Upload failed: {e}")
        else:
            st.error("Select a file first.")

st.divider()

# --- 3. LOGIN ---
if 'player_name' not in st.session_state:
    st.session_state.player_name = None

if not st.session_state.player_name:
    with st.form("login"):
        name = st.text_input("Your Name").upper()
        group = st.text_input("Group Code").upper()
        if st.form_submit_button("Join Game"):
            st.session_state.player_name = name
            st.session_state.group_code = group
            st.rerun()
    st.stop()

# --- 4. GAME ENGINE ---
player = st.session_state.player_name
group = st.session_state.group_code

# Fetch Game State
game = supabase.table("dixit_games").select("*").eq("group_code", group).single().execute().data
if not game:
    supabase.table("dixit_games").insert({"group_code": group}).execute()
    st.rerun()

# Fetch Image Pool for the "Deck"
pool = [row['url'] for row in supabase.table("dixit_pool").select("url").execute().data]

# Generate a 6-card hand for the player (Pseudo-random based on name/time)
# In a professional build, you'd store hands in the DB to prevent 'cheating' by refreshing
random.seed(player + str(game['created_at']))
my_hand = random.sample(pool, 6) if len(pool) >= 6 else pool

# --- PHASE: LOBBY ---
if game['phase'] == "LOBBY":
    st.subheader(f"Lobby: {group}")
    if st.button("🚀 Start New Round"):
        supabase.table("dixit_games").update({
            "phase": "STORYTELLING", "storyteller_id": player, 
            "submitted_images": {}, "votes": {}, "clue": None
        }).eq("group_code", group).execute()
        st.rerun()

# --- PHASE: STORYTELLING ---
elif game['phase'] == "STORYTELLING":
    if player == game['storyteller_id']:
        st.subheader("🌟 You are the Storyteller!")
        st.write("Pick a card and give a clue:")
        cols = st.columns(3)
        for i, img_url in enumerate(my_hand):
            with cols[i % 3]:
                st.image(img_url, use_container_width=True)
                if st.button(f"Select Card {i+1}", key=f"sel_{i}"):
                    st.session_state.selected_card = img_url
        
        if 'selected_card' in st.session_state:
            st.image(st.session_state.selected_card, width=150, caption="Selected")
            clue = st.text_input("Your Sentence/Word:")
            if st.button("Confirm Clue"):
                supabase.table("dixit_games").update({
                    "clue": clue, "phase": "SUBMITTING",
                    "submitted_images": {player: st.session_state.selected_card}
                }).eq("group_code", group).execute()
                del st.session_state.selected_card
                st.rerun()
    else:
        st.info(f"Waiting for {game['storyteller_id']} to pick a card...")

# --- PHASE: SUBMITTING (Trick players) ---
elif game['phase'] == "SUBMITTING":
    st.subheader(f"Clue: '{game['clue']}'")
    if player in game['submitted_images']:
        st.success("Wait for others to submit their trick cards...")
    else:
        st.write("Pick a card from your deck that matches the clue to trick others:")
        cols = st.columns(3)
        for i, img_url in enumerate(my_hand):
            with cols[i % 3]:
                st.image(img_url, use_container_width=True)
                if st.button(f"Submit Card {i+1}", key=f"sub_{i}"):
                    new_subs = game['submitted_images']
                    new_subs[player] = img_url
                    supabase.table("dixit_games").update({"submitted_images": new_subs}).eq("group_code", group).execute()
                    st.rerun()

    if len(game['submitted_images']) >= 3: # Minimum 3 players to vote
        if st.button("Move to Voting"):
            supabase.table("dixit_games").update({"phase": "VOTING"}).eq("group_code", group).execute()
            st.rerun()

# --- PHASE: VOTING ---
elif game['phase'] == "VOTING":
    st.subheader(f"Clue: '{game['clue']}'")
    if player == game['storyteller_id']:
        st.info("Wait for others to vote...")
    elif player in game['votes']:
        st.success("Vote cast!")
    else:
        # Show all submitted cards (shuffled)
        all_submitted = list(game['submitted_images'].values())
        random.shuffle(all_submitted)
        
        cols = st.columns(3)
        for i, img_url in enumerate(all_submitted):
            with cols[i % 3]:
                st.image(img_url, use_container_width=True)
                if st.button(f"Vote for Card {i+1}", key=f"vote_{i}"):
                    new_votes = game['votes']
                    new_votes[player] = img_url
                    supabase.table("dixit_games").update({"votes": new_votes, "phase": "RESULTS" if len(new_votes) >= 2 else "VOTING"}).eq("group_code", group).execute()
                    st.rerun()

# --- PHASE: RESULTS ---
elif game['phase'] == "RESULTS":
    st.header("Results!")
    correct = game['submitted_images'][game['storyteller_id']]
    st.image(correct, width=200, caption="The Real Card")
    if st.button("Next Round"):
        supabase.table("dixit_games").update({"phase": "LOBBY"}).eq("group_code", group).execute()
        st.rerun()

# Sync refresh
time.sleep(3)
st.rerun()
