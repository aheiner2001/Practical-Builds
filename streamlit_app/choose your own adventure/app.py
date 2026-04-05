import streamlit as st
import random
import os
import re
from dotenv import load_dotenv
from supabase import create_client
import google.generativeai as genai

# ── ENV ─────────────────────────────────────────────────────────────
load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# ── UTIL ────────────────────────────────────────────────────────────
def roll_dice(dice):
    match = re.match(r"(\\d+)d(\\d+)([+-]\\d+)?", dice)
    if not match:
        return 0
    num,sides,mod = match.groups()
    total = sum(random.randint(1,int(sides)) for _ in range(int(num)))
    if mod:
        total += int(mod)
    return total

def log(campaign_id, text, type="action"):
    supabase.table("game_log").insert({
        "campaign_id": campaign_id,
        "entry_type": type,
        "content": text
    }).execute()

# ── ENEMIES ─────────────────────────────────────────────────────────
TIER_WEIGHTS = {1:45,2:30,3:15,4:7,5:3}

ENEMIES = [
    {"name":"Goblin","tier":1,"hp":10,"ac":11,"dice":"1d6"},
    {"name":"Orc","tier":2,"hp":20,"ac":13,"dice":"1d8+2"},
    {"name":"Ogre","tier":3,"hp":50,"ac":11,"dice":"2d8"},
    {"name":"Lich","tier":4,"hp":70,"ac":17,"dice":"4d6"},
    {"name":"Dragon","tier":5,"hp":150,"ac":20,"dice":"4d10"},
]

def spawn_encounter(campaign_id):
    tier = random.choices(list(TIER_WEIGHTS), weights=TIER_WEIGHTS.values())[0]
    pool = [e for e in ENEMIES if e["tier"] == tier]
    enemies = [random.choice(pool)]

    supabase.table("combat_encounters").insert({
        "campaign_id": campaign_id,
        "enemies": enemies
    }).execute()

    log(campaign_id, f"⚔️ Encounter started: {enemies[0]['name']}", "combat")

# ── GEMINI ──────────────────────────────────────────────────────────
def generate_story(prompt):
    try:
        return model.generate_content(
            f"Create a short fantasy campaign: {prompt}"
        ).text
    except:
        return "A mysterious journey begins..."

# ── SESSION ─────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"

# ── HOME ────────────────────────────────────────────────────────────
if st.session_state.page == "home":
    st.title("⚔️ Realms of Legend")

    name = st.text_input("Your Name")
    prompt = st.text_area("Campaign Prompt")
    bot_count = st.slider("Bots", 0, 5, 0)

    if st.button("Create Campaign"):
        code = str(random.randint(100000,999999))

        story = generate_story(prompt)

        res = supabase.table("campaigns").insert({
            "code": code,
            "name": name,
            "creator_prompt": prompt,
            "full_story": story,
            "bot_count": bot_count,
            "status": "lobby"
        }).execute()

        campaign_id = res.data[0]["id"]

        # create player (DM)
        supabase.table("players").insert({
            "campaign_id": campaign_id,
            "name": name,
            "class_name": "Fighter",
            "race": "Human",
            "hp": 30, "max_hp": 30,
            "mp": 10, "max_mp": 10,
            "strength": 15, "dexterity": 12,
            "intelligence": 10, "constitution": 14,
            "charisma": 10, "wisdom": 10,
            "is_dm": True
        }).execute()

        st.session_state.campaign_id = campaign_id
        st.session_state.page = "lobby"
        st.rerun()

# ── LOBBY ───────────────────────────────────────────────────────────
elif st.session_state.page == "lobby":
    st.title("🧑‍🤝‍🧑 Lobby")

    campaign = supabase.table("campaigns").select("*")\
        .eq("id", st.session_state.campaign_id).execute().data[0]

    st.write(f"Join Code: {campaign['code']}")
    st.write(campaign["full_story"])

    name = st.text_input("Join as")

    if st.button("Join"):
        supabase.table("players").insert({
            "campaign_id": campaign["id"],
            "name": name,
            "class_name": "Fighter",
            "race": "Human",
            "hp": 30, "max_hp": 30,
            "mp": 10, "max_mp": 10,
            "strength": 15, "dexterity": 12,
            "intelligence": 10, "constitution": 14,
            "charisma": 10, "wisdom": 10
        }).execute()

    if st.button("Start Game"):
        supabase.table("campaigns").update({
            "status": "active"
        }).eq("id", campaign["id"]).execute()

        spawn_encounter(campaign["id"])

        st.session_state.page = "game"
        st.rerun()

# ── GAME ────────────────────────────────────────────────────────────
elif st.session_state.page == "game":
    st.title("🐉 Adventure")

    cid = st.session_state.campaign_id

    # load encounter
    encounter = supabase.table("combat_encounters")\
        .select("*").eq("campaign_id", cid)\
        .eq("status","active").execute()

    if encounter.data:
        enc = encounter.data[0]
        enemy = enc["enemies"][0]

        st.subheader(f"Enemy: {enemy['name']}")
        st.write(f"HP: {enemy['hp']}")

        if st.button("⚔️ Attack"):
            dmg = roll_dice(enemy["dice"])
            enemy["hp"] -= dmg

            log(cid, f"You hit {enemy['name']} for {dmg}", "combat")

            if enemy["hp"] <= 0:
                log(cid, f"{enemy['name']} defeated!", "combat")

                supabase.table("combat_encounters").update({
                    "status": "resolved"
                }).eq("id", enc["id"]).execute()

            else:
                supabase.table("combat_encounters").update({
                    "enemies": [enemy]
                }).eq("id", enc["id"]).execute()

            st.rerun()

    if st.button("🧭 Explore"):
        spawn_encounter(cid)
        st.rerun()

    # ── LOG ─────────────────────────────────────
    st.divider()
    st.subheader("📜 Story Log")

    logs = supabase.table("game_log")\
        .select("*").eq("campaign_id", cid)\
        .order("created_at", desc=True).limit(20).execute()

    for l in logs.data:
        st.write(l["content"])
