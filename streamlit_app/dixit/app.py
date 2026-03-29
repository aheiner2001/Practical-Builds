import streamlit as st
from supabase import create_client, Client
import time
import random

# --- 1. CONNECTION ---
supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- 2. IMAGE FACTORY (Multi-Upload) ---
st.set_page_config(page_title="Dixit Pro", layout="wide")
with st.expander("⬆️ Upload New Cards"):
    files = st.file_uploader("Images", type=['png', 'jpg'], accept_multiple_files=True)
    if st.button("Upload All"):
        for f in files:
            fname = f"{int(time.time())}_{f.name}"
            supabase.storage.from_('dixit_images').upload(fname, f.read())
            url = supabase.storage.from_('dixit_images').get_public_url(fname)
            supabase.table("dixit_pool").insert({"url": url}).execute()
        st.success("Uploaded!")
        st.rerun()

# --- 3. LOGIN ---
if 'player_name' not in st.session_state:
    st.session_state.player_name = None

if not st.session_state.player_name:
    with st.form("login"):
        name = st.text_input("Name").upper().strip()
        group = st.text_input("Group Code").upper().strip()
        if st.form_submit_button("Join"):
            st.session_state.player_name, st.session_state.group_code = name, group
            st.rerun()
    st.stop()

player = st.session_state.player_name
group = st.session_state.group_code

# --- 4. GAME STATE ENGINE ---
game_res = supabase.table("dixit_games").select("*").eq("group_code", group).single().execute()
if not game_res.data:
    supabase.table("dixit_games").insert({"group_code": group}).execute()
    st.rerun()
game = game_res.data

# Helper: Refill player hands and handle Discard Pile
def manage_decks(current_game):
    pool = [r['url'] for r in supabase.table("dixit_pool").select("url").execute().data]
    discard = current_game['discard_pile'] or []
    decks = current_game['player_decks'] or {}
    order = current_game['player_order'] or []
    
    # Available = Pool - Discard - Cards currently in hands
    in_hands = [card for h in decks.values() for card in h]
    available = [c for c in pool if c not in discard and c not in in_hands]
    
    # If not enough cards, recycle discard pile
    if len(available) < (len(order) * 6):
        supabase.table("dixit_games").update({"discard_pile": []}).eq("group_code", group).execute()
        available = [c for c in pool if c not in in_hands]

    random.shuffle(available)
    updated = False
    for p in order:
        hand = decks.get(p, [])
        while len(hand) < 6 and available:
            hand.append(available.pop(0))
            updated = True
        decks[p] = hand
    
    if updated:
        supabase.table("dixit_games").update({"player_decks": decks}).eq("group_code", group).execute()

# --- PHASE: LOBBY ---
if game['phase'] == "LOBBY":
    st.header("Lobby")
    current_order = game['player_order'] or []
    if player not in current_order:
        current_order.append(player)
        supabase.table("dixit_games").update({"player_order": current_order}).eq("group_code", group).execute()
    
    st.write("Players joined in order:")
    for p in current_order: st.write(f"👤 {p}")
    
    if st.button("🚀 Start Game"):
        manage_decks(game)
        # Determine Storyteller by order
        st_id = current_order[0]
        supabase.table("dixit_games").update({"phase": "STORYTELLING", "storyteller_id": st_id, "round_number": 0}).eq("group_code", group).execute()
        st.rerun()

# --- PHASE: STORYTELLING / SUBMITTING / VOTING ---
else:
    my_hand = (game['player_decks'] or {}).get(player, [])
    st.sidebar.write(f"Turn: {game['storyteller_id']}")
    st.sidebar.write(f"Round: {game['round_number'] + 1}")

    if game['phase'] == "STORYTELLING":
        if player == game['storyteller_id']:
            st.header("You are the Storyteller!")
            cols = st.columns(3)
            for i, img in enumerate(my_hand):
                with cols[i%3]:
                    st.image(img)
                    if st.button(f"Pick Card {i+1}", key=f"s{i}"):
                        clue = st.text_input("Description:")
                        if st.button("Submit"):
                            # Remove from hand, add to submissions
                            my_hand.remove(img)
                            new_decks = game['player_decks']; new_decks[player] = my_hand
                            new_subs = {player: img}
                            supabase.table("dixit_games").update({
                                "clue": clue, "phase": "SUBMITTING", 
                                "submissions": new_subs, "player_decks": new_decks
                            }).eq("group_code", group).execute()
                            st.rerun()
        else: st.info(f"Waiting for {game['storyteller_id']}...")

    elif game['phase'] == "SUBMITTING":
        st.header(f"Clue: {game['clue']}")
        if player not in game['submissions']:
            cols = st.columns(3)
            for i, img in enumerate(my_hand):
                with cols[i%3]:
                    st.image(img)
                    if st.button(f"Trick with this {i+1}", key=f"d{i}"):
                        my_hand.remove(img)
                        new_decks = game['player_decks']; new_decks[player] = my_hand
                        new_subs = game['submissions']; new_subs[player] = img
                        supabase.table("dixit_games").update({
                            "submissions": new_subs, "player_decks": new_decks
                        }).eq("group_code", group).execute()
                        st.rerun()
        else:
            if len(game['submissions']) >= len(game['player_order']):
                if st.button("Everyone ready? Move to Voting"):
                    supabase.table("dixit_games").update({"phase": "VOTING"}).eq("group_code", group).execute()
                    st.rerun()
            else: st.write("Waiting for others...")

    elif game['phase'] == "VOTING":
        st.header(f"Vote! Clue: {game['clue']}")
        if player != game['storyteller_id'] and player not in (game['votes'] or {}):
            all_imgs = list(game['submissions'].values())
            random.shuffle(all_imgs)
            cols = st.columns(3)
            for i, img in enumerate(all_imgs):
                with cols[i%3]:
                    st.image(img)
                    if img != game['submissions'][player]:
                        if st.button(f"Vote {i+1}", key=f"v{i}"):
                            v = game['votes'] or {}; v[player] = img
                            supabase.table("dixit_games").update({"votes": v}).eq("group_code", group).execute()
                            st.rerun()
        elif len(game['votes'] or {}) >= (len(game['player_order']) - 1):
            if st.button("See Results"):
                supabase.table("dixit_games").update({"phase": "RESULTS"}).eq("group_code", group).execute()
                st.rerun()

    elif game['phase'] == "RESULTS":
        st.header("Results")
        st_card = game['submissions'][game['storyteller_id']]
        st.image(st_card, width=300, caption="The real card")
        
        if player == game['storyteller_id']:
            if st.button("Next Round"):
                # 1. Add used cards to discard pile
                new_discard = (game['discard_pile'] or []) + list(game['submissions'].values())
                # 2. Increment round and rotate storyteller
                new_round = game['round_number'] + 1
                next_st = game['player_order'][new_round % len(game['player_order'])]
                
                supabase.table("dixit_games").update({
                    "phase": "STORYTELLING", "storyteller_id": next_st, 
                    "round_number": new_round, "discard_pile": new_discard,
                    "submissions": {}, "votes": {}, "clue": None
                }).eq("group_code", group).execute()
                
                # Refill hands
                manage_decks(game)
                st.rerun()

    if st.sidebar.button("EXIT & RESET GAME"):
        supabase.table("dixit_games").update({
            "phase": "LOBBY", "player_order": [], "player_decks": {}, "discard_pile": []
        }).eq("group_code", group).execute()
        st.rerun()

time.sleep(3)
st.rerun()
