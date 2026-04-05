import streamlit as st
import random
import os
import re
from dotenv import load_dotenv
from supabase import create_client
import google.generativeai as genai

# ── LOAD ENV ────────────────────────────────────────────────────────
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ── GAME ENGINE ─────────────────────────────────────────────────────
TIER_WEIGHTS = {1:45,2:30,3:15,4:7,5:3}

ENEMIES = [
    {"name":"Goblin","tier":1,"hp":10,"ac":11,"dice":"1d6"},
    {"name":"Orc","tier":2,"hp":20,"ac":13,"dice":"1d8+2"},
    {"name":"Ogre","tier":3,"hp":50,"ac":11,"dice":"2d8"},
    {"name":"Lich","tier":4,"hp":70,"ac":17,"dice":"4d6"},
    {"name":"Dragon","tier":5,"hp":150,"ac":20,"dice":"4d10"},
]

def roll_dice(dice):
    match = re.match(r"(\\d+)d(\\d+)([+-]\\d+)?", dice)
    if not match:
        return 0
    num,sides,mod = match.groups()
    total = sum(random.randint(1,int(sides)) for _ in range(int(num)))
    if mod:
        total += int(mod)
    return total

def spawn_enemy():
    tier = random.choices(list(TIER_WEIGHTS),weights=TIER_WEIGHTS.values())[0]
    pool = [e for e in ENEMIES if e["tier"]==tier]
    return random.choice(pool)

def attack(enemy):
    roll = random.randint(1,20)
    if roll >= enemy["ac"]:
        dmg = roll_dice(enemy["dice"])
        enemy["hp"] -= dmg
        return f"Hit for {dmg}"
    return "Miss"

# ── GEMINI ──────────────────────────────────────────────────────────
def generate_story(prompt):
    try:
        response = model.generate_content(
            f"Create a short fantasy DnD campaign story: {prompt}"
        )
        return response.text
    except:
        return "A mysterious adventure begins..."

# ── SUPABASE HELPERS ────────────────────────────────────────────────
def create_campaign(name, code, story):
    supabase.table("campaigns").insert({
        "name": name,
        "code": code,
        "story": story
    }).execute()

def add_player(code, player):
    supabase.table("players").insert({
        "campaign_code": code,
        "player": player
    }).execute()

def log_action(code, action):
    supabase.table("actions").insert({
        "campaign_code": code,
        "action": action
    }).execute()

def get_actions(code):
    return supabase.table("actions").select("*").eq("campaign_code", code).execute()

# ── SESSION STATE ───────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"

# ── HOME PAGE ───────────────────────────────────────────────────────
if st.session_state.page == "home":
    st.title("⚔️ Realms of Legend")

    name = st.text_input("Your Name")
    prompt = st.text_area("Story Prompt")

    if st.button("Create Campaign"):
        code = str(random.randint(1000,9999))
        story = generate_story(prompt)

        create_campaign(name, code, story)

        st.session_state.code = code
        st.session_state.story = story
        st.session_state.page = "lobby"
        st.rerun()

# ── LOBBY ───────────────────────────────────────────────────────────
elif st.session_state.page == "lobby":
    st.title("🧑‍🤝‍🧑 Lobby")

    code = st.session_state.code
    st.write(f"Join Code: {code}")

    name = st.text_input("Enter Name")

    if st.button("Join Game"):
        add_player(code, name)
        st.session_state.player = name
        st.session_state.page = "game"
        st.rerun()

# ── GAME ────────────────────────────────────────────────────────────
elif st.session_state.page == "game":
    st.title("🐉 Adventure")

    code = st.session_state.code
    player = st.session_state.player

    st.subheader("Story")
    st.write(st.session_state.get("story",""))

    # spawn enemy
    if "enemy" not in st.session_state:
        st.session_state.enemy = spawn_enemy()

    enemy = st.session_state.enemy

    st.subheader(f"Enemy: {enemy['name']}")
    st.write(f"HP: {enemy['hp']} | AC: {enemy['ac']}")

    # actions
    col1, col2 = st.columns(2)

    with col1:
        if st.button("⚔️ Attack"):
            result = attack(enemy)
            log_action(code, f"{player}: {result}")

            if enemy["hp"] <= 0:
                log_action(code, f"{enemy['name']} defeated!")
                st.session_state.enemy = spawn_enemy()

            st.rerun()

    with col2:
        action_text = st.text_input("Custom Action")

        if st.button("Do Action"):
            log_action(code, f"{player}: {action_text}")
            st.rerun()

    st.divider()

    st.subheader("📜 Game Log")
    actions = get_actions(code)

    if actions.data:
        for a in actions.data[::-1]:
            st.write(a["action"])
