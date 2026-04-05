import streamlit as st
import random
import os
from dotenv import load_dotenv
from supabase import create_client

# ── SAFE IMPORT GEMINI (optional) ─────────────────────────────
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except:
    HAS_GEMINI = False

# ── ENV ──────────────────────────────────────────────────────
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if HAS_GEMINI:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-flash")

# ── HELPERS ──────────────────────────────────────────────────
def generate_story(prompt):
    if not HAS_GEMINI:
        return "A simple adventure begins..."
    try:
        return model.generate_content(
            f"Short fantasy story: {prompt}"
        ).text
    except:
        return "A mysterious adventure begins..."

def log(campaign_id, text):
    supabase.table("game_log").insert({
        "campaign_id": campaign_id,
        "entry_type": "action",
        "content": text
    }).execute()

# ── SESSION ──────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"

# ── HOME ─────────────────────────────────────────────────────
if st.session_state.page == "home":
    st.title("⚔️ Realms of Legend (Basic)")

    name = st.text_input("Your Name")
    prompt = st.text_area("Story Prompt")

    if st.button("Create Campaign"):
        code = str(random.randint(1000, 9999))

        story = generate_story(prompt)

        res = supabase.table("campaigns").insert({
            "code": code,
            "name": name,
            "creator_prompt": prompt,
            "full_story": story
        }).execute()

        campaign_id = res.data[0]["id"]

        supabase.table("players").insert({
            "campaign_id": campaign_id,
            "name": name,
            "class_name": "Fighter",
            "race": "Human",
            "hp": 30, "max_hp": 30,
            "mp": 10, "max_mp": 10,
            "strength": 15, "dexterity": 12,
            "intelligence": 10, "constitution": 14,
            "charisma": 10, "wisdom": 10
        }).execute()

        st.session_state.campaign_id = campaign_id
        st.session_state.page = "lobby"
        st.rerun()

# ── LOBBY ────────────────────────────────────────────────────
elif st.session_state.page == "lobby":
    st.title("🧑‍🤝‍🧑 Lobby")

    cid = st.session_state.campaign_id

    campaign = supabase.table("campaigns")\
        .select("*").eq("id", cid).execute().data[0]

    st.write("Join Code:", campaign["code"])
    st.write(campaign["full_story"])

    name = st.text_input("Join as")

    if st.button("Join"):
        supabase.table("players").insert({
            "campaign_id": cid,
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
        st.session_state.page = "game"
        st.rerun()

# ── GAME ─────────────────────────────────────────────────────
elif st.session_state.page == "game":
    st.title("🐉 Adventure")

    cid = st.session_state.campaign_id

    st.subheader("Actions")

    if st.button("⚔️ Attack"):
        dmg = random.randint(1, 8)
        log(cid, f"Attack dealt {dmg} damage")

    action = st.text_input("Custom Action")

    if st.button("Do Action"):
        log(cid, action)

    st.divider()

    st.subheader("📜 Log")

    logs = supabase.table("game_log")\
        .select("*")\
        .eq("campaign_id", cid)\
        .order("created_at", desc=True)\
        .limit(20)\
        .execute()

    for l in logs.data:
        st.write(l["content"])
