import streamlit as st
from supabase import create_client, Client
import time
import random

# --- MUST be first Streamlit call ---
st.set_page_config(page_title="Dixit Pro", layout="wide", page_icon="🎨")

# --- 1. CONNECTION ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Check your .streamlit/secrets.toml for SUPABASE_URL and SUPABASE_KEY!")
    st.stop()

# --- 2. IMAGE FACTORY (Admin only, shown at top) ---
st.title("🎨 Dixit Pro")

with st.expander("⬆️ Admin: Add Cards to the Pool"):
    uploaded_files = st.file_uploader(
        "Upload surreal images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="uploader",
    )
    if st.button("Upload All to Deck"):
        if uploaded_files:
            count = 0
            for i, f in enumerate(uploaded_files):
                fname = f"{int(time.time())}_{i}_{f.name}"
                try:
                    supabase.storage.from_("dixit_images").upload(fname, f.read())
                    public_url = supabase.storage.from_("dixit_images").get_public_url(fname)
                    supabase.table("dixit_pool").insert({"url": public_url}).execute()
                    count += 1
                except Exception as e:
                    st.warning(f"Failed to upload {f.name}: {e}")
            st.success(f"Added {count} cards!")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("No files selected.")

st.divider()

# --- 3. LOGIN ---
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "group_code" not in st.session_state:
    st.session_state.group_code = None

if not st.session_state.player_name:
    with st.form("login"):
        name = st.text_input("Your Name").strip().upper()
        group_input = st.text_input("Group Code").strip().upper()
        if st.form_submit_button("Join Game"):
            if name and group_input:
                st.session_state.player_name = name
                st.session_state.group_code = group_input
                st.rerun()
            else:
                st.warning("Please enter both your name and a group code.")
    st.stop()

player = st.session_state.player_name
group = st.session_state.group_code

# --- 4. LOAD / INIT GAME ---
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

# --- 5. HELPERS ---

def refill_hands():
    """Deal up to 6 cards to every player whose hand is short."""
    pool_res = supabase.table("dixit_pool").select("url").execute()
    pool = [r["url"] for r in pool_res.data]
    in_hands = [card for h in decks.values() for card in h]
    available = [c for c in pool if c not in discard and c not in in_hands]

    # If pool is exhausted, recycle discard (but keep cards still in hands)
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


def score_round(storyteller: str, submissions: dict, votes: dict, current_scores: dict) -> dict:
    """
    Official Dixit scoring:
    - If ALL non-storytellers found the real card, OR NONE did:
        storyteller gets 0, everyone else gets 2.
    - Otherwise:
        storyteller gets 3, plus 1 per correct voter.
        Each correct voter gets 3.
    - Each non-storyteller gets +1 for every vote their decoy card received.
    """
    real_card = submissions[storyteller]
    non_storytellers = [p for p in submissions if p != storyteller]
    correct_voters = [p for p, voted_card in votes.items() if voted_card == real_card]

    updated = dict(current_scores)
    for p in submissions:
        updated.setdefault(p, 0)

    all_correct = len(correct_voters) == len(non_storytellers)
    none_correct = len(correct_voters) == 0

    if all_correct or none_correct:
        # Storyteller scores 0; everyone else gets 2
        for p in non_storytellers:
            updated[p] = updated.get(p, 0) + 2
    else:
        # Storyteller scores 3 + 1 per correct voter
        updated[storyteller] = updated.get(storyteller, 0) + 3 + len(correct_voters)
        for p in correct_voters:
            updated[p] = updated.get(p, 0) + 3

    # Decoy bonuses: +1 per vote a non-storyteller's card received
    for voter, voted_card in votes.items():
        for submitter, card in submissions.items():
            if submitter != storyteller and card == voted_card and voter != submitter:
                updated[submitter] = updated.get(submitter, 0) + 1

    return updated


def show_scoreboard(scores: dict, order: list):
    st.sidebar.markdown("### 🏆 Scores")
    sorted_scores = sorted(order, key=lambda p: scores.get(p, 0), reverse=True)
    for p in sorted_scores:
        marker = " 👑" if p == sorted_scores[0] else ""
        st.sidebar.write(f"**{p}**: {scores.get(p, 0)}{marker}")


# --- 6. SIDEBAR INFO ---
if phase != "LOBBY":
    st.sidebar.info(f"**Group:** {group}\n\n**You:** {player}\n\n**Storyteller:** {game['storyteller_id']}\n\n**Round:** {game['round_number'] + 1}")
    show_scoreboard(scores, order)

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

# =====================================================================
# --- PHASE: LOBBY ---
# =====================================================================
if phase == "LOBBY":
    st.header("🏠 Lobby")
    st.write(f"**Group Code:** `{group}`  — share this with friends!")

    # Add player to order only if not already in it
    if player not in order:
        order.append(player)
        scores[player] = 0
        supabase.table("dixit_games").update({
            "player_order": order,
            "scores": scores,
        }).eq("group_code", group).execute()
        st.rerun()

    st.subheader("Players joined:")
    for p in order:
        st.write(f"👤 {p}")

    if len(order) < 3:
        st.warning("Need at least 3 players to start.")
    elif player == order[0]:  # Only first player (host) can start
        if st.button("🚀 Start Game"):
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
        st.info(f"Waiting for **{order[0]}** (the host) to start the game…")

    # Auto-refresh while waiting for others
    time.sleep(3)
    st.rerun()

# =====================================================================
# --- ACTIVE GAMEPLAY ---
# =====================================================================
else:
    my_hand = decks.get(player, [])
    storyteller = game["storyteller_id"]

    # ---- STORYTELLING ----
    if phase == "STORYTELLING":
        if player == storyteller:
            st.header("🌟 You are the Storyteller!")
            st.write("Pick a card and give a clue — a word, phrase, sound, or anything goes.")

            # Show hand
            cols = st.columns(min(len(my_hand), 3))
            selected = st.session_state.get("selected_card", None)

            for i, img in enumerate(my_hand):
                with cols[i % 3]:
                    st.image(img, use_container_width=True)
                    if st.button(f"Pick this card", key=f"s_{i}"):
                        st.session_state.selected_card = img
                        st.rerun()

            if selected and selected in my_hand:
                st.success("Card selected! ✅")
                st.image(selected, width=200)
                clue = st.text_input("Your clue:")
                if st.button("Submit Clue & Card") and clue.strip():
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
            st.header("⏳ Waiting for the Storyteller…")
            st.info(f"**{storyteller}** is choosing a card and writing a clue.")
            time.sleep(3)
            st.rerun()

    # ---- SUBMITTING ----
    elif phase == "SUBMITTING":
        clue = game["clue"]
        subs: dict = game["submissions"] or {}
        st.header(f"🃏 Submit a Decoy Card")
        st.subheader(f'Clue: *"{clue}"*')

        submitted_count = len(subs)
        st.write(f"Submitted so far: {submitted_count} / {len(order)}")

        if player == storyteller:
            st.info("You already submitted your card. Waiting for others…")
            time.sleep(3)
            st.rerun()
        elif player in subs:
            st.success("Your decoy is in! Waiting for others…")
            time.sleep(3)
            st.rerun()
        else:
            st.write("Pick the card from your hand that best fits (or tricks!) the clue:")
            cols = st.columns(min(len(my_hand), 3))
            for i, img in enumerate(my_hand):
                with cols[i % 3]:
                    st.image(img, use_container_width=True)
                    if st.button(f"Submit this", key=f"d_{i}"):
                        new_hand = [c for c in my_hand if c != img]
                        decks[player] = new_hand
                        subs[player] = img
                        new_phase = "VOTING" if len(subs) >= len(order) else "SUBMITTING"
                        supabase.table("dixit_games").update({
                            "submissions": subs,
                            "player_decks": decks,
                            "phase": new_phase,
                        }).eq("group_code", group).execute()
                        st.rerun()

    # ---- VOTING ----
    elif phase == "VOTING":
        clue = game["clue"]
        subs: dict = game["submissions"] or {}
        votes: dict = game["votes"] or {}
        st.header(f"🗳️ Vote for the Real Card!")
        st.subheader(f'Clue: *"{clue}"*')

        # Stable shuffle per round (deterministic per group+round, but not guessable mid-round)
        all_imgs = list(subs.values())
        seed_str = group + str(game["round_number"])
        rng = random.Random(seed_str)
        rng.shuffle(all_imgs)

        vote_count = len(votes)
        eligible = len(order) - 1  # storyteller doesn't vote
        st.write(f"Votes cast: {vote_count} / {eligible}")

        if player == storyteller:
            st.info("You can't vote — you are the storyteller!")
            time.sleep(3)
            st.rerun()
        elif player in votes:
            st.success("You voted! Waiting for others…")
            time.sleep(3)
            st.rerun()
        else:
            st.write("Which card do you think belongs to the storyteller?")
            my_decoy = subs.get(player)
            cols = st.columns(min(len(all_imgs), 3))
            for i, img in enumerate(all_imgs):
                with cols[i % 3]:
                    st.image(img, use_container_width=True)
                    # Can't vote for your own decoy
                    if img == my_decoy:
                        st.caption("_(your card)_")
                    else:
                        if st.button(f"Vote for this", key=f"v_{i}"):
                            votes[player] = img
                            new_phase = "RESULTS" if len(votes) >= eligible else "VOTING"
                            supabase.table("dixit_games").update({
                                "votes": votes,
                                "phase": new_phase,
                            }).eq("group_code", group).execute()
                            st.rerun()

    # ---- RESULTS ----
    elif phase == "RESULTS":
        clue = game["clue"]
        subs: dict = game["submissions"] or {}
        votes: dict = game["votes"] or {}
        st.header("📊 Round Results!")
        st.subheader(f'Clue was: *"{clue}"*')

        real_card = subs[storyteller]
        st.markdown(f"### The Storyteller's card was:")
        st.image(real_card, width=280)

        # Show who submitted what
        st.markdown("---")
        st.markdown("### All cards revealed:")
        all_imgs = list(subs.values())
        seed_str = group + str(game["round_number"])
        rng = random.Random(seed_str)
        rng.shuffle(all_imgs)
        cols = st.columns(min(len(all_imgs), 3))
        for i, img in enumerate(all_imgs):
            submitter = next(p for p, c in subs.items() if c == img)
            voters_for_this = [p for p, v in votes.items() if v == img]
            is_real = img == real_card
            with cols[i % 3]:
                st.image(img, use_container_width=True)
                label = f"**{submitter}**{'  🌟 (STORYTELLER)' if submitter == storyteller else ''}"
                st.markdown(label)
                if voters_for_this:
                    st.caption(f"Voted by: {', '.join(voters_for_this)}")
                else:
                    st.caption("No votes")

        # Compute and display scores
        st.markdown("---")
        new_scores = score_round(storyteller, subs, votes, scores)
        st.markdown("### 🏆 Scores after this round:")
        sorted_players = sorted(new_scores.keys(), key=lambda p: new_scores[p], reverse=True)
        for p in sorted_players:
            gained = new_scores[p] - scores.get(p, 0)
            st.write(f"**{p}**: {new_scores[p]} pts  (+{gained} this round)")

        # Only storyteller advances the round (prevents double-advance)
        if player == storyteller:
            if st.button("➡️ Next Round"):
                new_discard = discard + list(subs.values())
                new_round = game["round_number"] + 1
                next_st = order[new_round % len(order)]

                # Update scores & advance phase first
                supabase.table("dixit_games").update({
                    "phase": "STORYTELLING",
                    "storyteller_id": next_st,
                    "round_number": new_round,
                    "discard_pile": new_discard,
                    "submissions": {},
                    "votes": {},
                    "clue": None,
                    "scores": new_scores,
                    "player_decks": decks,  # keep current decks before refill
                }).eq("group_code", group).execute()

                # Refill hands after advancing
                refill_hands()
                st.rerun()
        else:
            st.info(f"Waiting for **{storyteller}** to start the next round…")
            time.sleep(3)
            st.rerun()
