import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import time
import math

# --- 1. SUPABASE CONNECTION ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Check your .streamlit/secrets.toml for SUPABASE_URL and SUPABASE_KEY!")
    st.stop()

if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# --- 2. STYLING ---
st.set_page_config(page_title="Family Fast & Game", page_icon="💧", layout="wide")

st.markdown("""
    <style>
    :root { --primary-color: #0081ff; }
    .stApp { background-color: #f8f9fa; }
    .main-header { color: #044389; text-align: center; font-weight: 800; }
    .feature-card { background: white; padding: 25px; border-radius: 15px; border: 1px solid #dee2e6; height: 100%; min-height: 400px; }
    .progress-circle { 
        width: 200px; height: 200px; border-radius: 50%; display: flex; 
        justify-content: center; align-items: center; position: relative; margin: auto;
    }
    .progress-circle::after {
        content: ""; position: absolute; width: 170px; height: 170px; 
        background-color: #f8f9fa; border-radius: 50%;
    }
    .time-digits { font-size: 2.5rem; font-weight: bold; color: #044389; z-index: 10; font-family: monospace; }
    .benefit-bar-bg { height: 8px; background: #e9ecef; border-radius: 4px; position: relative; margin: 40px 0 20px 0; }
    .benefit-bar-fill { height: 100%; background: #0081ff; border-radius: 4px; }
    .dot { position: absolute; top: -6px; width: 18px; height: 18px; border-radius: 50%; border: 3px solid white; }
    .dot-label { position: absolute; top: 22px; font-size: 0.7rem; white-space: nowrap; transform: translateX(-40%); }
    .chat-bubble { background: #f1f3f5; padding: 10px; border-radius: 10px; margin-bottom: 5px; }
    .chat-user { font-size: 0.7rem; font-weight: bold; color: #0081ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN LOGIC ---
if not st.session_state.user_data:
    st.markdown("<h1 class='main-header'>Family Fasting</h1>", unsafe_allow_html=True)
    with st.form("login"):
        name = st.text_input("Name").strip().upper()
        code = st.text_input("Group Code").strip().upper()
        goal = st.selectbox("Goal (Hrs)", [48, 72, 120])
        if st.form_submit_button("Enter"):
            if name and code:
                res = supabase.table("fasting_groups").select("*").eq("user_name", name).eq("group_code", code).execute()
                if res.data: st.session_state.user_data = res.data[0]
                else:
                    new = {"user_name": name, "group_code": code, "target_hours": goal, "start_time": datetime.now().isoformat()}
                    ins = supabase.table("fasting_groups").insert(new).execute()
                    st.session_state.user_data = ins.data[0]
                st.rerun()
    st.stop()

# --- 4. SHARED DATA ---
user = st.session_state.user_data
all_members = supabase.table("fasting_groups").select("*").eq("group_code", user['group_code']).execute().data
now = datetime.now().astimezone()

def get_hours(iso_str):
    start = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    return max(0, (now - start).total_seconds() / 3600)

my_hours = get_hours(user['start_time'])
prog_pct = min(100.0, (my_hours / user['target_hours']) * 100)

# --- 5. TABS NAVIGATION ---
tab1, tab2 = st.tabs(["🕒 Fasting Tracker", "🎮 Dixit Game"])

with tab1:
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
        # Circle Timer
        conic = f"conic-gradient(#0081ff {prog_pct}%, #e9ecef {prog_pct}%)"
        h, m, s = int(my_hours), int((my_hours*60)%60), int((my_hours*3600)%60)
        st.markdown(f"<div class='progress-circle' style='background:{conic};'><div class='time-digits'>{h:02d}:{m:02d}:{s:02d}</div></div>", unsafe_allow_html=True)
        
        # Fasting Progress Bar
        checkpoints = [(12, "Carbs"), (20, "Ketosis"), (36, "Autophagy"), (72, "Deep")]
        cp_html = "".join([f"<div class='dot' style='left:{(hrs/user['target_hours'])*95}%; background:{'#0081ff' if my_hours>=hrs else '#e9ecef'};'></div><div class='dot-label' style='left:{(hrs/user['target_hours'])*95}%;'>{lab}</div>" for hrs, lab in checkpoints if hrs <= user['target_hours']])
        st.markdown(f"<div class='benefit-bar-bg'><div class='benefit-bar-fill' style='width:{prog_pct}%;'></div>{cp_html}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
        st.subheader("💬 Family Chat")
        msgs = supabase.table("fasting_messages").select("*").eq("group_code", user['group_code']).order("created_at", desc=True).limit(20).execute().data
        chat_box = st.container(height=300)
        for m in reversed(msgs or []):
            chat_box.markdown(f"<div class='chat-bubble'><span class='chat-user'>{m['user_name']}</span><br>{m['message_text']}</div>", unsafe_allow_html=True)
        
        with st.form("chat", clear_on_submit=True):
            msg_text = st.text_input("Message...")
            if st.form_submit_button("Send") and msg_text:
                supabase.table("fasting_messages").insert({"user_name": user['user_name'], "group_code": user['group_code'], "message_text": msg_text}).execute()
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
    # DIXIT ENGINE
    game_res = supabase.table("dixit_games").select("*").eq("group_code", user['group_code']).execute()
    if not game_res.data:
        supabase.table("dixit_games").insert({"group_code": user['group_code']}).execute()
        st.rerun()
    
    game = game_res.data[0]
    phase = game['phase']
    
    if phase == "LOBBY":
        st.subheader("Waiting for Players...")
        for m in all_members: st.write(f"✅ {m['user_name']}")
        if st.button("🚀 Start Game"):
            supabase.table("dixit_games").update({"phase": "STORYTELLING", "storyteller_id": user['user_name'], "submissions": {}, "votes": {}}).eq("group_code", user['group_code']).execute()
            st.rerun()
            
    elif phase == "STORYTELLING":
        if user['user_name'] == game['storyteller_id']:
            word = "MIRROR" # Simplified: in real version, pull from game['deck']
            st.info(f"Your secret word: **{word}**")
            clue = st.text_input("Cryptic Clue:")
            if st.button("Submit"):
                supabase.table("dixit_games").update({"phase": "SUBMITTING", "clue": clue, "submissions": {user['user_name']: word}}).eq("group_code", user['group_code']).execute()
                st.rerun()
        else: st.write(f"Waiting for {game['storyteller_id']}...")

    elif phase == "SUBMITTING":
        st.warning(f"Clue: {game['clue']}")
        if user['user_name'] not in game['submissions']:
            decoy = st.text_input("Enter a decoy word:")
            if st.button("Submit Decoy"):
                subs = game['submissions']
                subs[user['user_name']] = decoy
                p = "VOTING" if len(subs) >= len(all_members) else "SUBMITTING"
                supabase.table("dixit_games").update({"submissions": subs, "phase": p}).eq("group_code", user['group_code']).execute()
                st.rerun()
        else: st.write("Waiting for others...")

    elif phase == "VOTING":
        if user['user_name'] != game['storyteller_id'] and user['user_name'] not in game['votes']:
            opts = [w for p, w in game['submissions'].items() if p != user['user_name']]
            vote = st.radio("Which is the Storyteller's?", opts)
            if st.button("Vote"):
                v = game['votes']
                v[user['user_name']] = vote
                p = "RESULTS" if len(v) >= (len(all_members)-1) else "VOTING"
                supabase.table("dixit_games").update({"votes": v, "phase": p}).eq("group_code", user['group_code']).execute()
                st.rerun()
        else: st.write("Waiting for results...")

    elif phase == "RESULTS":
        st.header("Results!")
        st.write(f"Storyteller chose: **{game['submissions'][game['storyteller_id']]}**")
        if st.button("Reset Game"):
            supabase.table("dixit_games").update({"phase": "LOBBY"}).eq("group_code", user['group_code']).execute()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Global Refresh for Multiplayer Sync
time.sleep(2)
st.rerun()
