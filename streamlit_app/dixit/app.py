# --- DIXIT ENGINE ---

# 1. Get or Create Game State
game_res = supabase.table("dixit_games").select("*").eq("group_code", user['group_code']).execute()

if not game_res.data:
    # If no game exists for this family group, create one
    supabase.table("dixit_games").insert({"group_code": user['group_code']}).execute()
    st.rerun()

game = game_res.data[0]
phase = game['phase']
submissions = game['submissions']
votes = game['votes']

st.divider()
st.subheader(f"🎮 Dixit: {phase}")

# --- PHASE: LOBBY ---
if phase == "LOBBY":
    st.write("Waiting for the family to join the circle...")
    col1, col2 = st.columns([2, 1])
    with col1:
        for member in all_members:
            st.success(f"✅ {member['user_name']} is ready")
    with col2:
        if st.button("🚀 Start Game", use_container_width=True):
            supabase.table("dixit_games").update({
                "phase": "STORYTELLING",
                "storyteller_id": user['user_name'], # Current user is the first storyteller
                "submissions": {},
                "votes": {},
                "clue": None
            }).eq("group_code", user['group_code']).execute()
            st.rerun()

# --- PHASE: STORYTELLING (Wait for Clue) ---
elif phase == "STORYTELLING":
    if user['user_name'] == game['storyteller_id']:
        st.info("🎨 **You are the Storyteller!**")
        my_word = game['deck'][0] # Give them a word from the deck
        st.write(f"Your secret word is: **{my_word}**")
        clue_input = st.text_input("Give a cryptic clue...")
        if st.button("Submit Clue"):
            # Storyteller submits their word + clue
            new_subs = {user['user_name']: my_word}
            supabase.table("dixit_games").update({
                "clue": clue_input,
                "phase": "SUBMITTING",
                "submissions": new_subs
            }).eq("group_code", user['group_code']).execute()
            st.rerun()
    else:
        st.write(f"Waiting for **{game['storyteller_id']}** to think of a clue...")

# --- PHASE: SUBMITTING (Others pick decoys) ---
elif phase == "SUBMITTING":
    st.warning(f"The Clue is: **{game['clue']}**")
    
    if user['user_name'] in submissions:
        st.write("Wait for the others to pick their decoy words...")
    else:
        decoy = st.selectbox("Pick a decoy word to confuse others:", game['deck'][1:6])
        if st.button("Submit Decoy"):
            submissions[user['user_name']] = decoy
            # If everyone (storyteller + all members) has submitted
            next_phase = "VOTING" if len(submissions) >= len(all_members) else "SUBMITTING"
            supabase.table("dixit_games").update({
                "submissions": submissions,
                "phase": next_phase
            }).eq("group_code", user['group_code']).execute()
            st.rerun()

# --- PHASE: VOTING ---
elif phase == "VOTING":
    st.write(f"Clue: **{game['clue']}**")
    
    if user['user_name'] == game['storyteller_id']:
        st.write("You can't vote! Waiting for the family to decide...")
    elif user['user_name'] in votes:
        st.write("Vote cast! Waiting for results...")
    else:
        # Show all submitted words except the user's own decoy
        options = [word for player, word in submissions.items() if player != user['user_name']]
        choice = st.radio("Which one is the Storyteller's word?", options)
        
        if st.button("Cast Vote"):
            votes[user['user_name']] = choice
            next_phase = "RESULTS" if len(votes) >= (len(all_members) - 1) else "VOTING"
            supabase.table("dixit_games").update({
                "votes": votes,
                "phase": next_phase
            }).eq("group_code", user['group_code']).execute()
            st.rerun()

# --- PHASE: RESULTS ---
elif phase == "RESULTS":
    st.balloons()
    correct_word = submissions[game['storyteller_id']]
    st.header(f"The word was: **{correct_word}**")
    
    # Simple score display
    for player, v_word in votes.items():
        icon = "🎯" if v_word == correct_word else "❌"
        st.write(f"{player} voted for '{v_word}' {icon}")

    if st.button("Next Round / Back to Lobby"):
        supabase.table("dixit_games").update({"phase": "LOBBY"}).eq("group_code", user['group_code']).execute()
        st.rerun()
