import streamlit as st
from supabase import create_client, Client
import time
import random
import re
import os

# --- 1. CONFIG & CONNECTION ---
st.set_page_config(page_title="Dixit Pro", layout="wide", page_icon="🎨")

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Missing Supabase Secrets! Add SUPABASE_URL and SUPABASE_KEY to your secrets.toml.")
    st.stop()

# ============================================================
# 2. GLOBAL UI PROTOCOL (CONTRAST & BOARD GAME THEME)
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700&family=Nunito:wght@400;700;800&display=swap');

/* COLOR GUIDE:
   --background: #0f171e (Deep Midnight)
   --card-bg:    rgba(255, 255, 255, 0.05)
   --text-main:  #f6f0ed (Parchment - High Contrast)
   --accent:     #c2948a (Muted Rose Gold)
   --border:     rgba(126, 168, 190, 0.4) (Steel Blue)
*/

/* ── BASE RESET ── */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top, #1a2a36 0%, #0f171e 100%) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
    background-color: #0d1318 !important;
    border-right: 1px solid rgba(194, 148, 138, 0.2);
}

/* ── TYPOGRAPHY ── */
h1, h2, h3, .game-title {
    font-family: 'Cinzel Decorative', cursive !important;
    color: #f6f0ed !important;
    text-shadow: 0px 4px 10px rgba(0,0,0,0.5);
}
p, span, label, .stMarkdown { 
    color: #f6f0ed !important; /* Forces light text on dark backgrounds */
}

/* ── TACTILE BOARD GAME ELEMENTS ── */
.game-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(126, 168, 190, 0.3);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5), inset 0 1px 1px rgba(255,255,255,0.1);
    margin-bottom: 20px;
}

.phase-banner {
    background: linear-gradient(90deg, rgba(194, 148, 138, 0.1) 0%, rgba(126, 168, 190, 0.1) 100%);
    border-left: 5px solid #c2948a;
    padding: 15px 25px;
    border-radius: 4px 12px 12px 4px;
    margin-bottom: 25px;
}

/* ── BUTTONS (TOKEN STYLE) ── */
.stButton > button {
    background: #28536b !important; /* Steel base */
    color: #f6f0ed !important; /* Parchment text */
    border: 1px solid #7ea8be !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.stButton > button:hover {
    background: #c2948a !important; /* Rose Gold on hover */
    color: #1a1a1a !important; /* Dark text for contrast */
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(194, 148, 138, 0.4) !important;
}

/* Primary Action Buttons */
[data-testid="baseButton-primary"] > button {
    background: #f6f0ed !important; /* High contrast white-ish */
    color: #1a1a1a !important; /* Dark on light */
    border: none !important;
}

/* ── INPUTS (PARCHMENT STYLE) ── */
.stTextInput > div > div > input {
    background: rgba(15, 23, 30, 0.8) !important;
    color: #f6f0ed !important;
    border: 1px solid #c2948a !important;
    border-radius: 8px !important;
}

/* ── STATUS PILLS ── */
.pill {
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    display: inline-block;
    margin: 4px;
}
.pill-done {
    background: #688b58 !important; /* Olive */
    color: #f6f0ed !important;
    border: 1px solid rgba(255,255,255,0.2);
}
.pill-waiting {
    background: transparent !important;
    color: #c2948a !important;
    border: 1px solid #c2948a !important;
}

/* ── CARD GRID SELECTION ── */
.card-container {
    border-radius: 12px;
    overflow: hidden;
    transition: 0.3s;
    border: 3px solid transparent;
}
.card-selected {
    border-color: #c2948a !important;
    box-shadow: 0 0 20px rgba(194, 148, 138, 0.6);
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================
def refill_hands(group, order, decks, discard):
    pool_res = supabase.table("dixit_pool").select("url").execute()
    pool = [r["url"] for r in pool_res.data]
    in_hands = [card for h in decks.values() for card in h]
    available = [c for c in pool if c not in discard and c not in in_hands]
    
    if len(available) < len(order):
        supabase.table("dixit_games").update({"discard_pile": []}).eq("group_code", group).execute()
        available = [c for c in pool if c not in in_hands]
    
    random.shuffle(available)
    for p in order:
        hand = decks.get(p, [])
        while len(hand) < 6 and available:
            hand.append(available.pop(0))
        decks[p] = hand
    
    supabase.table("dixit_games").update({"player_decks": decks}).eq("group_code", group).execute()

def render_card_grid(cards, selectable=False, selected_card=None, key_prefix="card"):
    clicked = None
    cols = st.columns(3)
    for i, img in enumerate(cards):
        is_sel = (img == selected_card)
        with cols[i % 3]:
            # Board game card border logic
            border_cls = "card-selected" if is_sel else ""
            st.markdown(f'<div class="card-container {border_cls}">', unsafe_allow_html=True)
            st.image(img, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            if selectable:
                lbl = "✦ SELECTED" if is_sel else "PICK CARD"
                if st.button(lbl, key=f"{key_prefix}_{i}", use_container_width=True):
                    clicked = img
    return clicked

def status_pills(players, done_set):
    html = '<div style="margin: 10px 0;">'
    for p in players:
        status = "pill-done" if p in done_set else "pill-waiting"
        icon = "✓" if p in done_set else "⏳"
        html += f'<span class="pill {status}">{icon} {p}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ============================================================
# 4. GAME ENGINE
# ============================================================
st.markdown('<h1 style="text-align:center; margin-bottom:0;">DIXIT PRO</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#c2948a; letter-spacing:5px; font-weight:bold; font-size:0.8rem;">THE DREAMER\'S CIRCLE</p>', unsafe_allow_html=True)

# Admin Upload
with st.expander("🛠 Admin: Deck Management"):
    up = st.file_uploader("Add Surreal Cards", type=["png", "jpg"], accept_multiple_files=True)
    if st.button("Add to Deck") and up:
        for f in up:
            fname = f"{int(time.time())}_{f.name}"
            supabase.storage.from_("dixit_images").upload(fname, f.read())
            url = supabase.storage.from_("dixit_images").get_public_url(fname)
            supabase.table("dixit_pool").insert({"url": url}).execute()
        st.success("Cards added!")

# Session Init
if "player_name" not in st.session_state:
    st.session_state.player_name = None

# --- LOGIN ---
if not st.session_state.player_name:
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        st.markdown('<div class="game-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align:center;">Enter the Dream</h3>', unsafe_allow_html=True)
        with st.form("login"):
            name = st.text_input("YOUR NAME").strip().upper()
            code = st.text_input("GROUP CODE").strip().upper()
            if st.form_submit_button("ENTER CIRCLE", use_container_width=True, type="primary"):
                if name and code:
                    st.session_state.player_name = name
                    st.session_state.group_code = code
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Load Game State
player = st.session_state.player_name
group = st.session_state.group_code

game_res = supabase.table("dixit_games").select("*").eq("group_code", group).execute()
if not game_res.data:
    supabase.table("dixit_games").insert({"group_code": group, "phase": "LOBBY", "player_order": [], "scores": {}, "round_number": 0}).execute()
    st.rerun()

game = game_res.data[0]
phase = game["phase"]
order = game["player_order"] or []
decks = game["player_decks"] or {}
scores = game["scores"] or {}

# Sidebar Info
st.sidebar.markdown(f"### 👤 {player}")
st.sidebar.markdown(f"**Group:** `{group}`")
if phase != "LOBBY":
    st.sidebar.markdown(f"**Storyteller:** {game['storyteller_id']}")
    st.sidebar.divider()
    st.sidebar.markdown("### 🏆 Scores")
    for p, pts in scores.items():
        st.sidebar.markdown(f"**{p}:** {pts} pts")

# --- PHASE: LOBBY ---
if phase == "LOBBY":
    st.markdown('<div class="phase-banner"><h3>🏠 The Waiting Room</h3><p>Wait for your fellow dreamers to join the circle.</p></div>', unsafe_allow_html=True)
    
    if player not in order:
        order.append(player)
        scores[player] = 0
        supabase.table("dixit_games").update({"player_order": order, "scores": scores}).eq("group_code", group).execute()
        st.rerun()

    st.markdown("#### Players Joined")
    status_pills(order, order)

    if len(order) >= 3 and player == order[0]:
        if st.button("🚀 BEGIN THE DREAM", type="primary"):
            refill_hands(group, order, decks, [])
            supabase.table("dixit_games").update({
                "phase": "STORYTELLING", 
                "storyteller_id": order[0],
                "round_number": 0,
                "submissions": {},
                "votes": {}
            }).eq("group_code", group).execute()
            st.rerun()
    else:
        st.info("Waiting for host to start...")
        time.sleep(3)
        st.rerun()

# --- ACTIVE GAMEPLAY ---
else:
    my_hand = decks.get(player, [])
    storyteller = game["storyteller_id"]

    # 1. STORYTELLING
    if phase == "STORYTELLING":
        if player == storyteller:
            st.markdown('<div class="phase-banner"><h3>🌟 You are the Storyteller</h3><p>Choose a card and give a cryptic clue.</p></div>', unsafe_allow_html=True)
            selected = st.session_state.get("selected_card")
            clicked = render_card_grid(my_hand, selectable=True, selected_card=selected)
            
            if clicked:
                st.session_state.selected_card = clicked
                st.rerun()
            
            if selected:
                clue = st.text_input("ENTER CLUE", placeholder="A word, a feeling, a song title...")
                if st.button("SUBMIT CLUE & CARD", type="primary"):
                    if clue:
                        new_hand = [c for c in my_hand if c != selected]
                        decks[player] = new_hand
                        supabase.table("dixit_games").update({
                            "clue": clue, "phase": "SUBMITTING", 
                            "submissions": {player: selected}, "player_decks": decks
                        }).eq("group_code", group).execute()
                        del st.session_state["selected_card"]
                        st.rerun()
        else:
            st.markdown(f'<div class="phase-banner"><h3>⏳ Waiting for {storyteller}</h3><p>The storyteller is weaving a new tale...</p></div>', unsafe_allow_html=True)
            time.sleep(3)
            st.rerun()

    # 2. SUBMITTING DECOYS
    elif phase == "SUBMITTING":
        subs = game["submissions"] or {}
        st.markdown(f'<div class="phase-banner"><h3>🃏 The Decoy Phase</h3><p>Clue: <b style="color:#f6f0ed; font-size:1.4rem;">"{game["clue"]}"</b></p></div>', unsafe_allow_html=True)
        status_pills(order, set(subs.keys()))

        if player not in subs:
            st.markdown("#### Pick a card from your hand that fits the clue:")
            clicked = render_card_grid(my_hand, selectable=True)
            if clicked:
                new_hand = [c for c in my_hand if c != clicked]
                decks[player] = new_hand
                subs[player] = clicked
                new_phase = "VOTING" if len(subs) >= len(order) else "SUBMITTING"
                supabase.table("dixit_games").update({"submissions": subs, "player_decks": decks, "phase": new_phase}).eq("group_code", group).execute()
                st.rerun()
        else:
            st.info("Waiting for decoys...")
            time.sleep(3)
            st.rerun()

    # 3. VOTING
    elif phase == "VOTING":
        votes = game["votes"] or {}
        subs = game["submissions"] or {}
        st.markdown(f'<div class="phase-banner"><h3>🗳️ Cast Your Vote</h3><p>Find the storyteller\'s card for the clue: <b>"{game["clue"]}"</b></p></div>', unsafe_allow_html=True)
        
        all_cards = list(subs.values())
        random.Random(group + str(game["round_number"])).shuffle(all_cards)

        if player == storyteller:
            st.info("Storytellers cannot vote. Watching the results...")
            status_pills([p for p in order if p != storyteller], set(votes.keys()))
            time.sleep(3)
            st.rerun()
        elif player in votes:
            st.success("Vote locked. Waiting for others...")
            time.sleep(3)
            st.rerun()
        else:
            my_decoy = subs.get(player)
            cols = st.columns(3)
            for i, img in enumerate(all_cards):
                with cols[i%3]:
                    st.image(img, use_container_width=True)
                    if img == my_decoy:
                        st.caption("Your Decoy")
                    elif st.button("VOTE", key=f"v_{i}", use_container_width=True):
                        votes[player] = img
                        new_phase = "RESULTS" if len(votes) >= (len(order) - 1) else "VOTING"
                        supabase.table("dixit_games").update({"votes": votes, "phase": new_phase}).eq("group_code", group).execute()
                        st.rerun()

    # 4. RESULTS (Placeholders for logic)
    elif phase == "RESULTS":
        st.markdown('<div class="phase-banner"><h3>📊 Round Results</h3></div>', unsafe_allow_html=True)
        if st.button("NEXT ROUND", type="primary"):
            # Reset logic for next round storyteller shift
            next_idx = (order.index(storyteller) + 1) % len(order)
            refill_hands(group, order, decks, [])
            supabase.table("dixit_games").update({
                "phase": "STORYTELLING",
                "storyteller_id": order[next_idx],
                "submissions": {},
                "votes": {},
                "round_number": game["round_number"] + 1
            }).eq("group_code", group).execute()
            st.rerun()

# Exit Button
if st.sidebar.button("EXIT GAME"):
    st.session_state.player_name = None
    st.rerun()
