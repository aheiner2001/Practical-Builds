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

# --- 2. IMAGE FACTORY (Multi-Upload) ---
st.set_page_config(page_title="Dixit Pro", layout="wide", page_icon="🎨")

st.title("🎨 Dixit Image Factory")
with st.expander("⬆️ Add New Cards to the Pool"):
    uploaded_files = st.file_uploader("Upload surreal images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    if st.button("Upload All to Deck"):
        if uploaded_files:
            for i, f in enumerate(uploaded_files):
                fname = f"{int(time.time())}_{i}_{f.name}"
                supabase.storage.from_('dixit_images').upload(fname, f.read())
                public_url = supabase.storage.from_('dixit_images').get_public_url(fname)
                supabase.table("dixit_pool").insert({"url": public_url}).execute()
            st.success(f"Added {len(uploaded_files)} cards!")
            time.sleep(1)
            st.rerun()

st.divider()

# --- 3. LOGIN ---
if 'player_name' not in st.session_state:
    st.session_state.player_name = None

if not st.session_state.player_name:
    with st.form("login"):
        name = st.text_input("Your Name").strip().upper()
        group = st.text_input("Group Code").strip().upper()
        if st.form_submit_button("Join Game"):
            if name and group:
                st.session_state.player_name = name
                st.session_state.group_code = group
                st.rerun()
    st.stop()

player = st.session_state.player_name
group = st.session_state.group_code

# --- 4. GAME ENGINE ---
game_res = supabase.table("dixit_games").select("*").eq("group_code", group).execute()

if not game_res.data:
    supabase.table("dixit_games").insert({"group_code": group, "phase": "LOBBY"}).execute()
    st.rerun()

game = game_res.data[0]
phase = game['phase']
order = game['player_order'] or []
decks = game['player_decks'] or {}
discard = game['discard_pile'] or []

def refill_hands():
    pool_res = supabase.table("dixit_pool").select("url").execute()
    pool = [r['url'] for r in pool_res.data]
    in_hands = [card for h in decks.values() for card in h]
    available = [c for c in pool if c not in discard and c not in in_hands]
    
    if len(available) < (len(order) * 6):
        supabase.table("dixit_games").update({"discard_pile": []}).eq("group_code", group).execute()
        available = [c for c in pool if c not in in_hands]

    random.shuffle(available)
    for p in order:
        hand = decks.get(p, [])
        while len(hand) < 6 and available:
            hand.append(available.pop(0))
        decks[p] = hand
    
    supabase.table("dixit_games").update({"player_decks": decks}).eq("group_code", group).execute()

# --- PHASE: LOBBY ---
if phase == "LOBBY":
    st.header("🏠 Lobby")
    if player not in order:
        order.append(player)
        supabase.table("dixit_games").update({"player_order": order}).eq("group_code", group).execute()
        st.rerun()
    
    for p in order: st.write(f"👤 {p}")
    if st.button("🚀 Start Game"):
        refill_hands()
        st_id = order[0]
        supabase.table("dixit_games").update({"phase": "STORYTELLING", "storyteller_id": st_id, "round_number": 0, "submissions": {}, "votes": {}}).eq("group_code", group).execute()
        st.rerun()

# --- ACTIVE GAMEPLAY ---
else:
    my_hand = decks.get(player, [])
    st.sidebar.info(f"Storyteller: **{game['storyteller_id']}**")

    if phase == "STORYTELLING":
        if player == game['storyteller_id']:
            st.header("🌟 Your Turn")
            cols = st.columns(3)
            for i, img in enumerate(my_hand):
                with cols[i % 3]:
                    st.image(img)
                    if st.button(f"Pick {i+1}", key=f"s{i}"):
                        st.session_state.selected = img
            if 'selected' in st.session_state:
                clue = st.text_input("Enter Clue:")
                if st.button("Submit Clue"):
                    my_hand.remove(st.session_state.selected)
                    decks[player] = my_hand
                    supabase.table("dixit_games").update({"clue": clue, "phase": "SUBMITTING", "submissions": {player: st.session_state.selected}, "player_decks": decks}).eq("group_code", group).execute()
                    del st.session_state.selected
                    st.rerun()
        else: st.info("Waiting for storyteller...")

    elif phase == "SUBMITTING":
        st.header(f"Clue: {game['clue']}")
        subs = game['submissions'] or {}
        if player not in subs:
            cols = st.columns(3)
            for i, img in enumerate(my_hand):
                with cols[i % 3]:
                    st.image(img)
                    if st.button(f"Trick with {i+1}", key=f"d{i}"):
                        my_hand.remove(img)
                        decks[player] = my_hand
                        subs[player] = img
                        p = "VOTING" if len(subs) >= len(order) else "SUBMITTING"
                        supabase.table("dixit_games").update({"submissions": subs, "player_decks": decks, "phase": p}).eq("group_code", group).execute()
                        st.rerun()
        else: st.write("Wait for others...")

    elif phase == "VOTING":
        st.header(f"Vote! Clue: {game['clue']}")
        v = game['votes'] or {}
        if player != game['storyteller_id'] and player not in v:
            all_imgs = list(game['submissions'].values())
            random.seed(group + game['clue'])
            random.shuffle(all_imgs)
            cols = st.columns(3)
            for i, img in enumerate(all_imgs):
                with cols[i % 3]:
                    st.image(img)
                    if img != game['submissions'][player]:
                        if st.button(f"Vote {i+1}", key=f"v{i}"):
                            v[player] = img
                            p = "RESULTS" if len(v) >= (len(order) - 1) else "VOTING"
                            supabase.table("dixit_games").update({"votes": v, "phase": p}).eq("group_code", group).execute()
                            st.rerun()
        else: st.write("Wait for results...")

    elif phase == "RESULTS":
        st.header("Results")
        st_card = game['submissions'][game['storyteller_id']]
        st.image(st_card, width=300, caption="The Real Card")
        if player == game['storyteller_id']:
            if st.button("Next Round"):
                new_discard = discard + list(game['submissions'].values())
                new_round = game['round_number'] + 1
                next_st = order[new_round % len(order)]
                supabase.table("dixit_games").update({"phase": "STORYTELLING", "storyteller_id": next_st, "round_number": new_round, "discard_pile": new_discard, "submissions": {}, "votes": {}, "clue": None}).eq("group_code", group).execute()
                refill_hands()
                st.rerun()

    if st.sidebar.button("EXIT & RESET"):
        supabase.table("dixit_games").update({"phase": "LOBBY", "player_order": [], "player_decks": {}, "discard_pile": []}).eq("group_code", group).execute()
        st.rerun()

time.sleep(3)
st.rerun()
