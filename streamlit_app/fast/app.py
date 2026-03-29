import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
import time
import math

# --- 1. SUPABASE CONNECTION ---
try:
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception:
    st.error("Connect Supabase in .streamlit/secrets.toml first!")
    st.stop()

if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# --- 2. STYLING ---
st.set_page_config(page_title="Fast", page_icon="💧", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-header { color: #044389; text-align: center; font-weight: 800; }
    
    /* Group Impact Card */
    .group-impact-card {
        background: #044389; color: white; padding: 1.5rem; border-radius: 12px;
        text-align: center; margin-bottom: 2rem;
    }

    /* Progress Circle */
    .progress-circle { 
        width: 220px; height: 220px; border-radius: 50%; display: flex; 
        justify-content: center; align-items: center; position: relative; margin: auto;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .progress-circle::after {
        content: ""; position: absolute; width: 190px; height: 190px; 
        background-color: #f8f9fa; border-radius: 50%;
    }
    .stopwatch-display { z-index: 10; text-align: center; }
    .time-digits { font-size: 2.8rem; font-weight: bold; color: #044389; display: block; font-family: 'Courier New', monospace; }
    
    /* Benefit Timeline */
    .benefit-bar-bg { height: 8px; background: #e9ecef; border-radius: 4px; position: relative; margin: 45px 0 20px 0; }
    .benefit-bar-fill { height: 100%; background: #0081ff; border-radius: 4px; transition: width 0.5s; }
    .dot { position: absolute; top: -6px; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .dot-label { position: absolute; top: 25px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; transform: translateX(-40%); color: #495057; }

    /* Cards & Chat */
    .feature-card { background: white; padding: 25px; border-radius: 15px; border: 1px solid #dee2e6; height: 100%; }
    .chat-bubble { background: #f1f3f5; padding: 10px 15px; border-radius: 15px; margin-bottom: 8px; border-bottom-left-radius: 2px; }
    .chat-user { font-size: 0.7rem; font-weight: bold; color: #0081ff; text-transform: uppercase; margin-bottom: 2px; }
    .chat-text { font-size: 0.9rem; color: #343a40; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN ---
if not st.session_state.user_data:
    st.markdown("<h1 class='main-header'>Fasting</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        name = st.text_input("First Name").strip().upper()
        code = st.text_input("Family Group Code").strip().upper()
        goal = st.selectbox("Fast Goal (Hours)", [48, 72, 120])
        if st.form_submit_button("Enter Dashboard"):
            if name and code:
                res = supabase.table("fasting_groups").select("*").eq("user_name", name).eq("group_code", code).execute()
                if res.data: st.session_state.user_data = res.data[0]
                else:
                    new = {"user_name": name, "group_code": code, "start_time": datetime.now().isoformat(), "target_hours": goal}
                    ins = supabase.table("fasting_groups").insert(new).execute()
                    st.session_state.user_data = ins.data[0]
                st.rerun()
    st.stop()

# --- 4. DATA & MATH ---
user = st.session_state.user_data
all_members = supabase.table("fasting_groups").select("*").eq("group_code", user['group_code']).execute().data
now = datetime.now().astimezone()

def get_hours(iso_str):
    start = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    return max(0, (now - start).total_seconds() / 3600)

my_hours = get_hours(user['start_time'])
group_total = sum(get_hours(m['start_time']) for m in all_members)
prog_pct = min(100.0, (my_hours / user['target_hours']) * 100)
hunger_val = 50 + 35 * math.sin((my_hours - 4) * (math.pi / 6)) if my_hours > 0 else 0

# --- 5. RENDER UI ---

st.markdown(f"""
    <div class='group-impact-card'>
        <div style='font-size:0.8rem; letter-spacing:1px; opacity:0.8;'>{user['group_code']} COLLECTIVE STREAK</div>
        <div style='font-size:2.5rem; font-weight:bold;'>{group_total:.1f} Total Hours Fasted</div>
    </div>
""", unsafe_allow_html=True)

col_main, col_side = st.columns([1.4, 1])

with col_main:
    st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
    # Circle Timer
    conic = f"conic-gradient(#0081ff {prog_pct}%, #e9ecef {prog_pct}%)"
    h, m, s = int(my_hours), int((my_hours*60)%60), int((my_hours*3600)%60)
    
    st.markdown(f"""
        <div class='progress-circle' style='background:{conic};'>
            <div class='stopwatch-display'>
                <span class='time-digits'>{h:02d}:{m:02d}:{s:02d}</span>
                <span style='color:#adb5bd; font-size:0.9rem; font-weight:bold;'>{user['user_name']}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    
    # Benefit Checklist Bar
    
    checkpoints = [
    (0,  "Start"),
    (6,  "Post-meal"),
    (12, "Carb use"),
    (20, "Ketosis"),
    (30, "Fat burn"),
    (36, "Autophagy"),
    (48, "Ketosis stable"),
    (60, "Deep ketosis"),
    (72, "Extended fast")
]
    st.markdown("##### Progress Bar")
    cp_html = "".join([f"<div class='dot' style='left:{(hrs/user['target_hours'])*90}%; background:{'#0081ff' if my_hours>=hrs else '#e9ecef'};'></div><div class='dot-label' style='left:{(hrs/user['target_hours'])*90}%;'>{lab}</div>" for hrs, lab in checkpoints if (hrs/user['target_hours'])*100 <= 100])

    st.markdown(f"<div class='benefit-bar-bg'><div class='benefit-bar-fill' style='width:{prog_pct}%;'></div>{cp_html}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='padding: 30px 0;'></div>", unsafe_allow_html=True)
    Electrolyte = [
    (0,  "Drink water"),
    (12, "½ packet"),
    (20, "½ packet"),
    (36, "1 packet"),
    (44, "1 packet"),
    (60, "1 packet"),
    (72, "1 packet")
]
    st.markdown("##### Electrolyte Intake Checkpoints")
    st.caption("Spread intake until next checkpoint (6g packets)")
    cp_html = "".join([f"<div class='dot' style='left:{(hrs/user['target_hours'])*90}%; background:{'#0081ff' if my_hours>=hrs else '#e9ecef'};'></div><div class='dot-label' style='left:{(hrs/user['target_hours'])*90}%;'>{lab}</div>" for hrs, lab in Electrolyte if (hrs/user['target_hours'])*100 <= 100])

    st.markdown(f"<div class='benefit-bar-bg'><div class='benefit-bar-fill' style='width:{prog_pct}%;'></div>{cp_html}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='padding: 30px 0;'></div>", unsafe_allow_html=True)
    # Family Progress Bars
    st.write("#### 👥 Family Members")
    for member in all_members:
        m_h = get_hours(member['start_time'])
        m_p = min(1.0, m_h / member['target_hours'])
        st.caption(f"**{member['user_name']}** • {m_h:.1f} / {member['target_hours']} hrs")
        st.progress(m_p)

with col_side:
    # Hunger Forecast
    st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
    st.subheader("📉 Hunger Forecast")
    st.progress(min(1.0, max(0.0, hunger_val/100)))
    st.caption(f"Wave Intensity: **{'PEAK' if hunger_val > 70 else 'LOW'}**. Remember, it passes in 15 mins!")
    st.write("---")
    
    # LIVE FAMILY CHAT
    st.subheader("💬 Family Chat")
    
    # 1. Fetch Messages
    msgs = supabase.table("fasting_messages").select("*").eq("group_code", user['group_code']).order("created_at", desc=True).limit(5).execute().data
    
    # 2. Display Messages
    chat_container = st.container(height=200, border=False)
    with chat_container:
        for msg in reversed(msgs):
            st.markdown(f"""
                <div class='chat-bubble'>
                    <div class='chat-user'>{msg['user_name']}</div>
                    <div class='chat-text'>{msg['message_text']}</div>
                </div>
            """, unsafe_allow_html=True)

    # 3. Input Message
    with st.form("chat_form", clear_on_submit=True):
        new_msg = st.text_input("Send encouragement...", placeholder="You got this!")
        if st.form_submit_button("Send") and new_msg:
            supabase.table("fasting_messages").insert({
                "user_name": user['user_name'],
                "group_code": user['group_code'],
                "message_text": new_msg
            }).execute()
            st.rerun()

    # Controls
    st.write("---")
    if 'delete_confirm' not in st.session_state:
        st.session_state.delete_confirm = False
    if 'restart_confirm' not in st.session_state:
        st.session_state.restart_confirm = False
    c1, c2 ,c3= st.columns(3)
    if c1.button("🔄 Restart", use_container_width=True): 
        st.session_state.delete_confirm = False
        st.session_state.restart_confirm = True
    if c2.button("Log Out", use_container_width=True):
        st.session_state.restart_confirm = False
        st.session_state.delete_confirm = False
        st.session_state.user_data = None 
        st.rerun()
    if c3.button("🗑️ Delete", use_container_width=True, type="primary"):
    # Instead of showing the button immediately, we flip a switch
        st.session_state.restart_confirm = False
        st.session_state.delete_confirm = True

# 2. Check the "switch" in session state to show the second button
    if st.session_state.delete_confirm:
        st.warning("⚠️ This is permanent!")
        col_a, col_b = st.columns(2)
    
        if col_a.button("✅ Yes, Delete", use_container_width=True, type="primary"):
            supabase.table("fasting_groups").delete().eq("id", user['id']).execute()
            st.session_state.user_data = None
            st.session_state.delete_confirm = False # Reset the switch
            st.rerun()
        
        if col_b.button("❌ Cancel", use_container_width=True):
            st.session_state.delete_confirm = False # Close the confirmation
            st.rerun()
    if st.session_state.restart_confirm:
        
        st.warning("You will be logged out to ensure time displays properly")
        col_a, col_b = st.columns(2)
    
        if col_a.button("✅ Yes, Restart", use_container_width=True, type="primary"):
            new_ts = datetime.now().isoformat() 
            supabase.table("fasting_groups").update({"start_time": new_ts}).eq("id", user['id']).execute() 
            st.session_state.restart_confirm = False
            st.session_state.user_data = None 
            st.rerun()
        
        if col_b.button("❌ Cancel", use_container_width=True):
            st.session_state.restart_confirm = False # Close the confirmation
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Tick clock
time.sleep(.5)
st.rerun()
