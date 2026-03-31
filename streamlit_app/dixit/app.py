import streamlit as st
from supabase import create_client, Client
import time
import random
import re
import os

st.set_page_config(page_title="Dixit Pro", layout="wide", page_icon="🎨")

# --- 1. CONNECTION ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Check your .streamlit/secrets.toml for SUPABASE_URL and SUPABASE_KEY!")
    st.stop()

# ============================================================
# GLOBAL CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700&family=Nunito:wght@300;400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
}

/* Deep starry background */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 20% 30%, #1a0040 0%, #0d1433 50%, #060b1a 100%) !important;
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #120030 0%, #0a0f25 100%) !important;
    border-right: 1px solid rgba(180,120,255,0.2);
}

/* Headings */
h1, h2, h3 {
    font-family: 'Cinzel Decorative', cursive !important;
    color: #e8c8ff !important;
}
p, label, .stMarkdown, [data-testid="stText"] { color: #c8b8e8 !important; }

/* ── LOGIN CARD ── */
.login-wrap {
    max-width: 460px;
    margin: 30px auto 0;
    background: linear-gradient(135deg, rgba(80,20,140,0.55) 0%, rgba(20,10,60,0.85) 100%);
    border: 1px solid rgba(180,100,255,0.4);
    border-radius: 24px;
    padding: 40px 36px 16px;
    box-shadow: 0 0 60px rgba(140,60,255,0.25), 0 0 120px rgba(80,20,140,0.15);
    text-align: center;
}
.login-title {
    font-family: 'Cinzel Decorative', cursive;
    font-size: 2.2rem;
    background: linear-gradient(135deg, #e8c8ff, #a060ff, #60c8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 4px;
    line-height: 1.2;
}
.login-sub {
    color: rgba(180,140,255,0.7) !important;
    font-size: 0.8rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 20px;
}
.login-emoji {
    font-size: 3.5rem;
    margin-bottom: 12px;
    display: block;
    filter: drop-shadow(0 0 20px rgba(180,100,255,0.7));
}

/* ── PHASE BANNER ── */
.phase-banner {
    background: linear-gradient(90deg, rgba(80,20,140,0.6), rgba(20,60,120,0.6));
    border: 1px solid rgba(140,100,255,0.3);
    border-radius: 16px;
    padding: 16px 24px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.phase-banner .phase-icon { font-size: 2rem; }
.phase-banner .phase-text { color: #e8c8ff !important; font-size: 1.1rem; font-weight: 800; margin-bottom: 2px; }
.phase-banner .phase-sub  { color: rgba(180,140,255,0.7) !important; font-size: 0.82rem; }

/* ── CLUE DISPLAY ── */
.clue-display {
    background: linear-gradient(90deg, rgba(80,20,140,0.4), rgba(20,60,120,0.4));
    border-left: 4px solid #a060ff;
    border-radius: 0 12px 12px 0;
    padding: 14px 20px;
    margin: 12px 0 20px;
    font-size: 1.3rem;
    color: #e8c8ff !important;
    font-weight: 700;
    font-style: italic;
}

/* ── CLUE POPUP ── */
.clue-popup {
    background: linear-gradient(135deg, rgba(60,20,100,0.95), rgba(10,20,60,0.98));
    border: 2px solid rgba(140,80,255,0.6);
    border-radius: 20px;
    padding: 24px 24px 18px;
    margin: 16px 0;
    box-shadow: 0 0 40px rgba(120,60,255,0.3);
}
.clue-popup-title {
    color: #b880ff !important;
    font-size: 0.8rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    font-weight: 800;
    margin-bottom: 12px;
}

/* ── STATUS PILLS ── */
.status-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 18px; }
.pill { border-radius: 20px; padding: 5px 14px; font-size: 0.8rem; font-weight: 700; }
.pill-done {
    background: rgba(40,180,80,0.2);
    border: 1px solid rgba(40,180,80,0.5);
    color: #60ff99 !important;
}
.pill-waiting {
    background: rgba(220,140,0,0.15);
    border: 1px solid rgba(220,140,0,0.4);
    color: #ffcc55 !important;
}

/* ── SELECTED CARD BADGE ── */
.selected-badge {
    text-align: center;
    background: #44ff88;
    color: #003318;
    border-radius: 8px;
    padding: 3px 0;
    font-size: 12px;
    font-weight: 800;
    margin-top: 3px;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #6020c0, #3060c0) !important;
    color: white !important;
    border: 1px solid rgba(180,120,255,0.4) !important;
    border-radius: 12px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #7830d8, #4070d8) !important;
    box-shadow: 0 4px 20px rgba(120,60,255,0.4) !important;
    transform: translateY(-1px);
}
[data-testid="baseButton-primary"] > button,
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #a040ff, #4080ff) !important;
    box-shadow: 0 4px 24px rgba(160,64,255,0.35) !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(140,80,255,0.4) !important;
    border-radius: 10px !important;
    color: #e8e0ff !important;
    font-family: 'Nunito', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: #a060ff !important;
    box-shadow: 0 0 0 2px rgba(160,96,255,0.2) !important;
}

/* ── DIVIDER ── */
hr { border-color: rgba(140,80,255,0.2) !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] * { color: #c8b0f0 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #e0c8ff !important; }

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    background: rgba(140,60,255,0.1) !important;
    border-radius: 10px !important;
    color: #c8a0ff !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# APP TITLE
# ============================================================
st.markdown(
    '<h1 style="text-align:center;font-size:2.6rem;margin-bottom:2px;">🎨 Dixit Pro</h1>',
    unsafe_allow_html=True
)
st.markdown(
    '<p style="text-align:center;color:rgba(180,140,255,0.55);letter-spacing:5px;font-size:0.75rem;margin-bottom:20px;">THE STORYTELLING CARD GAME</p>',
    unsafe_allow_html=True
)

# ============================================================
# ADMIN UPLOAD
# ============================================================
with st.expander("⬆️ Admin: Add Cards to the Pool"):
    uploaded_files = st.file_uploader(
        "Upload surreal images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="uploader",
    )
    progress_placeholder = st.empty()
    status_text_placeholder = st.empty()

    if st.button("Upload All to Deck"):
        if uploaded_files:
            total_files = len(uploaded_files)
            count = 0
            progress_bar = progress_placeholder.progress(0)
            for i, f in enumerate(uploaded_files):
                raw_filename = f.name
                filename_base, file_extension = os.path.splitext(raw_filename)
                clean_base = re.sub(r'[^a-zA-Z0-9.\-_]', '', filename_base)
                clean_filename = f"{clean_base}{file_extension}"
                file_content = f.read()
                fname = f"{int(time.time())}_{i}_{clean_filename}"
                status_text_placeholder.text(f"Processing ({i+1}/{total_files}): {raw_filename}")
                progress_bar.progress((i+1) / total_files)
                try:
                    supabase.storage.from_("dixit_images").upload(fname, file_content)
                    public_url = supabase.storage.from_("dixit_images").get_public_url(fname)
                    supabase.table("dixit_pool").insert({"url": public_url}).execute()
                    count += 1
                except Exception as e:
                    st.warning(f"Failed to upload {raw_filename}: {e}")
            status_text_placeholder.empty()
            progress_bar.progress(1.0)
            st.success(f"✨ Added {count} cards successfully out of {total_files} selected!")
            time.sleep(2)
            st.rerun()
        else:
            st.warning("No files selected.")

st.divider()


# ============================================================
# SESSION STATE INIT
# ============================================================
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "group_code" not in st.session_state:
    st.session_state.group_code = None


# ============================================================
# LOGIN
# ============================================================
if not st.session_state.player_name:
    st.markdown("""
    <div class="login-wrap">
        <span class="login-emoji">🌙</span>
        <div class="login-title">Enter the Dream</div>
        <div class="login-sub">✦ Dixit Pro ✦</div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        with st.form("login"):
            st.markdown('<p style="color:#b880ff;font-weight:700;margin-bottom:2px;">Your Name</p>', unsafe_allow_html=True)
            name = st.text_input("name", placeholder="e.g. LUNA", label_visibility="collapsed").strip().upper()
            st.markdown('<p style="color:#b880ff;font-weight:700;margin-bottom:2px;margin-top:8px;">Group Code</p>', unsafe_allow_html=True)
            group_input = st.text_input("group", placeholder="e.g. DREAM42", label_visibility="collapsed").strip().upper()
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("✨  Enter the Dream", use_container_width=True, type="primary")
            if submitted:
                if name and group_input:
                    st.session_state.player_name = name
                    st.session_state.group_code = group_input
                    st.rerun()
                else:
                    st.warning("Please enter both your name and a group code.")
    st.stop()

player = st.session_state.player_name
group = st.session_state.group_code


# ============================================================
# LOAD / INIT GAME
# ============================================================
game_res = supabase.table("dixit_games").select("*").eq("group_code", group).execute()

if not game_res.data:
    supabase.table("dixit_games").insert({
        "group_code": group,
        "phase": "LOBBY",
        "player_order": [],
        "player_decks": {},
        "discard_pile": [],
        "scores": {},
        "submissions": {},
        "votes": {},
        "clue": None,
        "storyteller_id": None,
        "round_number": 0,
    }).execute()
    st.rerun()

game = game_res.data[0]
phase = game["phase"]
order: list = game["player_order"] or []
decks: dict = game["player_decks"] or {}
discard: list = game["discard_pile"] or []
scores: dict = game["scores"] or {}


# ============================================================
# HELPERS
# ============================================================
def refill_hands():
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


def score_round(storyteller, submissions, votes, current_scores):
    real_card = submissions[storyteller]
    non_storytellers = [p for p in submissions if p != storyteller]
    correct_voters = [p for p, voted_card in votes.items() if voted_card == real_card]
    updated = dict(current_scores)
    for p in submissions:
        updated.setdefault(p, 0)
    all_correct = len(correct_voters) == len(non_storytellers)
    none_correct = len(correct_voters) == 0
    if all_correct or none_correct:
        for p in non_storytellers:
            updated[p] = updated.get(p, 0) + 2
    else:
        updated[storyteller] = updated.get(storyteller, 0) + 3 + len(correct_voters)
        for p in correct_voters:
            updated[p] = updated.get(p, 0) + 3
    for voter, voted_card in votes.items():
        for submitter, card in submissions.items():
            if submitter != storyteller and card == voted_card and voter != submitter:
                updated[submitter] = updated.get(submitter, 0) + 1
    return updated


def show_scoreboard(scores, order):
    st.sidebar.markdown("### 🏆 Scores")
    sorted_scores = sorted(order, key=lambda p: scores.get(p, 0), reverse=True)
    for i, p in enumerate(sorted_scores):
        pts = scores.get(p, 0)
        crown = "👑 " if i == 0 else ""
        bg = "rgba(220,180,0,0.12)" if i == 0 else "rgba(255,255,255,0.04)"
        border = "rgba(220,180,0,0.3)" if i == 0 else "rgba(140,80,255,0.15)"
        st.sidebar.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:8px 12px;border-radius:10px;'
            f'margin-bottom:5px;background:{bg};border:1px solid {border};">'
            f'<span>{crown}{p}</span><span style="font-weight:800;color:#e8c8ff">{pts} pts</span></div>',
            unsafe_allow_html=True
        )


def status_pills(players, done_set, label_done="✓", label_waiting="⏳"):
    pills = '<div class="status-row">'
    for p in players:
        if p in done_set:
            pills += f'<span class="pill pill-done">{label_done} {p}</span>'
        else:
            pills += f'<span class="pill pill-waiting">{label_waiting} {p}</span>'
    pills += '</div>'
    st.markdown(pills, unsafe_allow_html=True)


def render_card_grid(cards, selectable=False, selected_card=None, key_prefix="card", exclude=None):
    """Renders cards in a 3-col grid. Returns clicked card or None."""
    clicked = None
    display_cards = [c for c in cards if c != exclude] if exclude else cards
    cols = st.columns(3)
    for i, img in enumerate(display_cards):
        is_sel = (img == selected_card)
        with cols[i % 3]:
            border_style = "3px solid #44ff88" if is_sel else "2px solid transparent"
            st.markdown(
                f'<div style="border:{border_style};border-radius:12px;overflow:hidden;'
                f'box-shadow:{"0 0 16px rgba(68,255,136,0.4)" if is_sel else "none"};">',
                unsafe_allow_html=True
            )
            st.image(img, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if is_sel:
                st.markdown('<div class="selected-badge">✓ SELECTED</div>', unsafe_allow_html=True)
            if selectable:
                lbl = "✓ Selected" if is_sel else "Pick this card"
                if st.button(lbl, key=f"{key_prefix}_{i}", use_container_width=True):
                    clicked = img
    return clicked


# ============================================================
# SIDEBAR (during active game)
# ============================================================
if phase != "LOBBY":
    st.sidebar.markdown(f"### 👤 {player}")
    st.sidebar.markdown(f"**Group:** `{group}`")
    st.sidebar.markdown(f"**Storyteller:** {game['storyteller_id']}")
    st.sidebar.markdown(f"**Round:** {game['round_number'] + 1}")
    st.sidebar.divider()
    show_scoreboard(scores, order)
    st.sidebar.divider()

    # Always-visible deck viewer
    my_hand_sidebar = decks.get(player, [])
    with st.sidebar.expander(f"🃏 My Deck  ({len(my_hand_sidebar)} cards)"):
        if my_hand_sidebar:
            for i in range(0, len(my_hand_sidebar), 2):
                c1, c2 = st.sidebar.columns(2)
                with c1:
                    st.image(my_hand_sidebar[i], use_container_width=True)
                if i + 1 < len(my_hand_sidebar):
                    with c2:
                        st.image(my_hand_sidebar[i + 1], use_container_width=True)
        else:
            st.sidebar.caption("No cards in hand.")

    st.sidebar.divider()
    if st.sidebar.button("🚪 Exit & Reset Game"):
        supabase.table("dixit_games").update({
            "phase": "LOBBY",
            "player_order": [],
            "player_decks": {},
            "discard_pile": [],
            "scores": {},
            "submissions": {},
            "votes": {},
            "clue": None,
            "storyteller_id": None,
            "round_number": 0,
        }).eq("group_code", group).execute()
        st.session_state.player_name = None
        st.rerun()


# ============================================================
# PHASE: LOBBY
# ============================================================
if phase == "LOBBY":
    st.markdown("""
    <div class="phase-banner">
        <span class="phase-icon">🏠</span>
        <div>
            <div class="phase-text">Waiting Room</div>
            <div class="phase-sub">Share the group code with your friends to join</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<p style="text-align:center;font-size:1rem;color:#c8a0ff;margin-bottom:20px;">'
        f'Group Code: <span style="font-family:monospace;font-size:1.4rem;color:#e8c8ff;'
        f'background:rgba(140,60,255,0.2);padding:4px 16px;border-radius:8px;">{group}</span></p>',
        unsafe_allow_html=True
    )

    if player not in order:
        order.append(player)
        scores[player] = 0
        supabase.table("dixit_games").update({
            "player_order": order,
            "scores": scores,
        }).eq("group_code", group).execute()
        st.rerun()

    st.markdown("#### Players Joined")
    avatars = ["🌙", "⭐", "🌟", "💫", "🌈", "🔮", "🎭", "🃏"]
    for i, p in enumerate(order):
        host_tag = " &nbsp;<small style='color:#ffcc55;font-size:0.75rem;'>HOST</small>" if i == 0 else ""
        you_tag = " &nbsp;<small style='color:#88ccff;font-size:0.75rem;'>YOU</small>" if p == player else ""
        st.markdown(
            f'<div style="padding:10px 16px;margin:5px 0;background:rgba(140,60,255,0.15);'
            f'border-radius:12px;border:1px solid rgba(140,60,255,0.25);color:#e8d8ff;">'
            f'{avatars[i % len(avatars)]} <b>{p}</b>{host_tag}{you_tag}</div>',
            unsafe_allow_html=True
        )

    st.markdown("")
    if len(order) < 3:
        st.warning("✦ Need at least 3 players to begin the dream…")
    elif player == order[0]:
        if st.button("🚀  Begin the Dream!", type="primary", use_container_width=True):
            refill_hands()
            supabase.table("dixit_games").update({
                "phase": "STORYTELLING",
                "storyteller_id": order[0],
                "round_number": 0,
                "submissions": {},
                "votes": {},
                "clue": None,
                "scores": {p: 0 for p in order},
            }).eq("group_code", group).execute()
            st.rerun()
    else:
        st.info(f"⏳ Waiting for **{order[0]}** (host) to start the game…")

    time.sleep(3)
    st.rerun()


# ============================================================
# ACTIVE GAMEPLAY
# ============================================================
else:
    my_hand = decks.get(player, [])
    storyteller = game["storyteller_id"]

    # ── STORYTELLING ──
    if phase == "STORYTELLING":
        if player == storyteller:
            st.markdown("""
            <div class="phase-banner">
                <span class="phase-icon">🌟</span>
                <div>
                    <div class="phase-text">You are the Storyteller!</div>
                    <div class="phase-sub">Pick a card below, then give a clue — a word, phrase, sound, or feeling</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            selected = st.session_state.get("selected_card", None)

            clicked = render_card_grid(my_hand, selectable=True, selected_card=selected, key_prefix="st")
            if clicked:
                st.session_state.selected_card = clicked
                st.rerun()

            # Clue popup — appears right after grid when card is selected
            if selected and selected in my_hand:
                st.markdown("""
                <div class="clue-popup">
                    <div class="clue-popup-title">✦ Your Clue</div>
                </div>
                """, unsafe_allow_html=True)
                # Re-render inside real Streamlit widgets (can't nest inputs in raw HTML)
                st.markdown(
                    '<div style="background:linear-gradient(135deg,rgba(60,20,100,0.95),rgba(10,20,60,0.98));'
                    'border:2px solid rgba(140,80,255,0.6);border-radius:20px;padding:20px 24px 16px;'
                    'margin:0 0 16px;box-shadow:0 0 40px rgba(120,60,255,0.3);">',
                    unsafe_allow_html=True
                )
                st.markdown('<p class="clue-popup-title">✦ &nbsp;WRITE YOUR CLUE</p>', unsafe_allow_html=True)
                clue = st.text_input(
                    "clue",
                    placeholder="e.g. melancholy afternoon… lonely giant… forgotten music…",
                    label_visibility="collapsed",
                    key="clue_input"
                )
                c1, c2 = st.columns([3, 1])
                with c1:
                    if st.button("✨  Submit Clue & Card", type="primary", use_container_width=True):
                        if clue.strip():
                            new_hand = [c for c in my_hand if c != selected]
                            decks[player] = new_hand
                            supabase.table("dixit_games").update({
                                "clue": clue.strip(),
                                "phase": "SUBMITTING",
                                "submissions": {player: selected},
                                "player_decks": decks,
                                "votes": {},
                            }).eq("group_code", group).execute()
                            del st.session_state["selected_card"]
                            st.rerun()
                        else:
                            st.warning("Please write a clue first!")
                with c2:
                    if st.button("✗ Different card", use_container_width=True):
                        del st.session_state["selected_card"]
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        else:
            st.markdown(f"""
            <div class="phase-banner">
                <span class="phase-icon">⏳</span>
                <div>
                    <div class="phase-text">Waiting for the Storyteller…</div>
                    <div class="phase-sub"><b>{storyteller}</b> is choosing a card and crafting a clue</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(3)
            st.rerun()

    # ── SUBMITTING ──
    elif phase == "SUBMITTING":
        clue = game["clue"]
        subs: dict = game["submissions"] or {}

        st.markdown(f"""
        <div class="phase-banner">
            <span class="phase-icon">🃏</span>
            <div>
                <div class="phase-text">Submit a Decoy Card</div>
                <div class="phase-sub">Pick the card that best fits — or tricks! — the storyteller's clue</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="clue-display">✦ &nbsp;"{clue}"</div>', unsafe_allow_html=True)

        st.markdown("**Who's submitted:**")
        status_pills(order, set(subs.keys()), label_done="✓ Done", label_waiting="⏳ Picking")

        if player == storyteller:
            st.info("🌟 Your card is in. Waiting for everyone else to submit their decoys…")
            time.sleep(3)
            st.rerun()
        elif player in subs:
            st.success("✅ Your decoy is in! Waiting for others…")
            time.sleep(3)
            st.rerun()
        else:
            st.markdown("**Your Hand — pick your decoy:**")
            clicked = render_card_grid(my_hand, selectable=True, key_prefix="sub")
            if clicked:
                new_hand = [c for c in my_hand if c != clicked]
                decks[player] = new_hand
                subs[player] = clicked
                new_phase = "VOTING" if len(subs) >= len(order) else "SUBMITTING"
                supabase.table("dixit_games").update({
                    "submissions": subs,
                    "player_decks": decks,
                    "phase": new_phase,
                }).eq("group_code", group).execute()
                st.rerun()

    # ── VOTING ──
    elif phase == "VOTING":
        clue = game["clue"]
        subs: dict = game["submissions"] or {}
        votes: dict = game["votes"] or {}

        st.markdown(f"""
        <div class="phase-banner">
            <span class="phase-icon">🗳️</span>
            <div>
                <div class="phase-text">Vote for the Real Card!</div>
                <div class="phase-sub">Which card do you think belongs to the storyteller?</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="clue-display">✦ &nbsp;"{clue}"</div>', unsafe_allow_html=True)

        eligible = len(order) - 1
        non_st_order = [p for p in order if p != storyteller]
        st.markdown("**Who's voted:**")
        status_pills(non_st_order, set(votes.keys()), label_done="✓ Voted", label_waiting="⏳ Voting")

        all_imgs = list(subs.values())
        seed_str = group + str(game["round_number"])
        rng = random.Random(seed_str)
        rng.shuffle(all_imgs)

        if player == storyteller:
            st.info("🌟 You're the storyteller — you can't vote. Watch the tension build!")
            time.sleep(3)
            st.rerun()
        elif player in votes:
            st.success("✅ Vote locked in! Waiting for others…")
            time.sleep(3)
            st.rerun()
        else:
            my_decoy = subs.get(player)
            st.markdown("**All submitted cards — tap to vote:**")
            cols = st.columns(3)
            for i, img in enumerate(all_imgs):
                with cols[i % 3]:
                    st.image(img, use_container_width=True)
                    if img == my_decoy:
                        st.markdown(
                            '<div style="text-align:center;color:rgba(180,140,255,0.5);'
                            'font-size:11px;padding:2px 0;">your card</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        if st.button("Vote for this", key=f"v_{i}", use_container_width=True):
                            votes[player] = img
                            new_phase = "RESULTS" if len(votes) >= eligible else "VOTING"
                            supabase.table("dixit_games").update({
                                "votes": votes,
                                "phase": new_phase,
                            }).eq("group_code", group).execute()
                            st.rerun()

    # ── RESULTS ──
    elif phase == "RESULTS":
        clue = game["clue"]
        subs: dict = game["submissions"] or {}
        votes: dict = game["votes"] or {}

        st.markdown(f"""
        <div class="phase-banner">
            <span class="phase-icon">📊</span>
            <div>
                <div class="phase-text">Round Results!</div>
                <div class="phase-sub">Let's see who fooled who…</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="clue-display">✦ &nbsp;"{clue}"</div>', unsafe_allow_html=True)

        real_card = subs[storyteller]
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            st.markdown(
                '<p style="text-align:center;color:#ffcc55;font-weight:800;'
                'letter-spacing:2px;font-size:0.8rem;margin-bottom:8px;">✦ THE STORYTELLER\'S CARD ✦</p>',
                unsafe_allow_html=True
            )
            st.image(real_card, use_container_width=True)

        st.markdown("---")
        st.markdown("#### All Cards Revealed")

        all_imgs = list(subs.values())
        seed_str = group + str(game["round_number"])
        rng = random.Random(seed_str)
        rng.shuffle(all_imgs)

        cols = st.columns(3)
        for i, img in enumerate(all_imgs):
            submitter = next(p for p, c in subs.items() if c == img)
            voters_for_this = [p for p, v in votes.items() if v == img]
            is_real = (img == real_card)
            with cols[i % 3]:
                border = "3px solid #ffcc55" if is_real else "2px solid rgba(140,80,255,0.3)"
                st.markdown(f'<div style="border:{border};border-radius:12px;overflow:hidden;">', unsafe_allow_html=True)
                st.image(img, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                name_color = "#ffcc55" if submitter == storyteller else "#e8c8ff"
                st_tag = " 🌟" if submitter == storyteller else ""
                st.markdown(
                    f'<div style="text-align:center;color:{name_color};font-weight:700;'
                    f'font-size:0.85rem;padding:4px 0;">{submitter}{st_tag}</div>',
                    unsafe_allow_html=True
                )
                if voters_for_this:
                    st.markdown(
                        f'<div style="text-align:center;color:#80e8a0;font-size:0.75rem;">'
                        f'Voted by: {", ".join(voters_for_this)}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<div style="text-align:center;color:rgba(180,140,255,0.4);font-size:0.75rem;">No votes</div>',
                        unsafe_allow_html=True
                    )

        st.markdown("---")
        new_scores = score_round(storyteller, subs, votes, scores)
        st.markdown("#### 🏆 Scores After This Round")
        sorted_players = sorted(new_scores.keys(), key=lambda p: new_scores[p], reverse=True)
        for i, p in enumerate(sorted_players):
            gained = new_scores[p] - scores.get(p, 0)
            is_leader = (i == 0)
            bg = "rgba(220,180,0,0.12)" if is_leader else "rgba(255,255,255,0.04)"
            border = "rgba(220,180,0,0.3)" if is_leader else "rgba(140,80,255,0.15)"
            crown = "👑 " if is_leader else ""
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:10px 16px;border-radius:12px;margin-bottom:6px;'
                f'background:{bg};border:1px solid {border};">'
                f'<span style="color:#e8c8ff;font-weight:700;">{crown}{p}</span>'
                f'<span style="color:#e8c8ff;font-weight:800;">{new_scores[p]} pts &nbsp;'
                f'<span style="color:#60ff99;font-size:0.85rem;">(+{gained})</span></span>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown("")
        if player == storyteller:
            if st.button("➡️  Next Round", type="primary", use_container_width=True):
                new_discard = discard + list(subs.values())
                new_round = game["round_number"] + 1
                next_st = order[new_round % len(order)]
                supabase.table("dixit_games").update({
                    "phase": "STORYTELLING",
                    "storyteller_id": next_st,
                    "round_number": new_round,
                    "discard_pile": new_discard,
                    "submissions": {},
                    "votes": {},
                    "clue": None,
                    "scores": new_scores,
                    "player_decks": decks,
                }).eq("group_code", group).execute()
                refill_hands()
                st.rerun()
        else:
            st.info(f"⏳ Waiting for **{storyteller}** to start the next round…")
            time.sleep(3)
            st.rerun()
