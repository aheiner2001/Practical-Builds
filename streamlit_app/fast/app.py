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

# --- 2. SESSION STATE ---
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# --- 3. STYLING & UI COMPONENTS ---
st.set_page_config(page_title="FlowFast Family", page_icon="💧", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fdfcf9; }
    .main-header { color: #044389; text-align: center; font-family: sans-serif; }
    
    /* Group Impact Header */
    .group-impact-card {
        background: linear-gradient(135deg, #044389 0%, #0081ff 100%);
        color: white; padding: 20px; border-radius: 15px;
        text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,129,255,0.2);
    }

    /* Circle Progress */
    .progress-circle { 
        width: 220px; height: 220px; border-radius: 50%; display: flex; 
        justify-content: center; align-items: center; position: relative; margin: auto;
    }
    .progress-circle::after {
        content: ""; position: absolute; width: 190px; height: 190px; 
        background-color: #fdfcf9; border-radius: 50%;
    }
    .stopwatch-display { z-index: 10; text-align: center; }
    .time-digits { font-size: 2.6rem; font-weight: bold; color: #044389; display: block; font-family: monospace; }
    
    /* Benefit Timeline */
    .benefit-bar-bg { height: 10px; background: #e8dab2; border-radius: 5px; position: relative; margin: 40px 0; }
    .benefit-bar-fill { height: 100%; background: #0081ff; border-radius: 5px; transition: width 0.5s; }
    .dot { position: absolute; top: -5px; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; }
    .dot-label { position: absolute; top: 25px; font-size: 0.7rem; font-weight: bold; white-space: nowrap; transform: translateX(-40%); }

    /* Cards */
    .feature-card { background: white; padding: 20px; border-radius: 15px; border: 1px solid #e8dab2; height: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION / LOGIN ---
if not st.session_state.user_data:
    st.markdown("<h1 class='main-header'>🌊 FlowFast Family</h1>", unsafe_allow_html=True)
    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            with st.form("login_form"):
                name = st.text_input("First Name").strip().upper()
                code = st.text_input("Family Group Code").strip().upper()
                goal = st.selectbox("Fast Goal", [48, 72, 120])
                if st.form_submit_button("Join Group"):
                    if name and code:
                        # Logic: Get or Create
                        res = supabase.table("fasting_groups").select("*").eq("user_name", name).eq("group_code", code).execute()
                        if res.data:
                            st.session_state.user_data = res.data[0]
                        else:
                            new = {"user_name": name, "group_code": code, "start_time": datetime.now().isoformat(), "target_hours": goal}
                            ins = supabase.table("fasting_groups").insert(new).execute()
                            st.session_state.user_data = ins.data[0]
                        st.rerun()
        with col2:
            st.info("👋 **Family Sync Active**\n\nEnter your shared family code to see everyone's progress live!")
    st.stop()

# --- 5. DATA FETCHING & MATH ---
user = st.session_state.user_data
# Fetch ALL members to calculate collective impact
all_members = supabase.table("fasting_groups").select("*").eq("group_code", user['group_code']).execute().data

now = datetime.now().astimezone()
def get_hours(iso_str):
    start = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    return max(0, (now - start).total_seconds() / 3600)

my_hours = get_hours(user['start_time'])
group_total = sum(get_hours(m['start_time']) for m in all_members)
prog_pct = min(100.0, (my_hours / user['target_hours']) * 100)

# Hunger Forecast (Sine wave logic)
hunger_val = 50 + 35 * math.sin((my_hours - 4) * (math.pi / 6)) if my_hours > 0 else 0

# --- 6. RENDER UI ---

# Header: Collective Impact
st.markdown(f"""
    <div class='group-impact-card'>
        <div style='font-size:0.9rem; opacity:0.9;'>{user['group_code']} COLLECTIVE STREAK</div>
        <div style='font-size:2.2rem; font-weight:bold;'>{group_total:.1f} Total Hours</div>
    </div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
    # Circle Timer
    conic = f"conic-gradient(#0081ff {prog_pct}%, #e8dab2 {prog_pct}%)"
    h = int(my_hours)
    m = int((my_hours * 60) % 60)
    s = int((my_hours * 3600) % 60)
    
    st.markdown(f"""
        <div class='progress-circle' style='background:{conic};'>
            <div class='stopwatch-display'>
                <span class='time-digits'>{h:02d}:{m:02d}:{s:02d}</span>
                <span style='color:#676f54; font-weight:bold;'>{user['user_name']}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Benefit Checklist Bar
    checkpoints = [(12, "Sugar End"), (18, "Fat Burn"), (24, "Ketosis"), (48, "Autophagy"), (72, "Deep Cell")]
    cp_html = ""
    for hrs, lab in checkpoints:
        pos = (hrs / user['target_hours']) * 100
        color = "#0081ff" if my_hours >= hrs else "#e8dab2"
        cp_html += f"<div class='dot' style='left:{pos}%; background:{color};'></div><div class='dot-label' style='left:{pos}%;'>{lab}</div>"

    st.markdown(f"""
        <div class='benefit-bar-bg'>
            <div class='benefit-bar-fill' style='width:{prog_pct}%;'></div>
            {cp_html}
        </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    with st.container():
        st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
        st.subheader("📉 Hunger Forecast")
        st.write(f"Wave Intensity: **{'HIGH' if hunger_val > 70 else 'LOW'}**")
        st.progress(min(1.0, max(0.0, hunger_val/100)))
        st.caption("Hunger usually passes in 20 minutes. Drink water!")
        
        st.write("---")
        if st.button("🔄 Restart My Fast"):
            new_ts = datetime.now().isoformat()
            supabase.table("fasting_groups").update({"start_time": new_ts}).eq("id", user['id']).execute()
            st.session_state.user_data['start_time'] = new_ts
            st.rerun()
        
        if st.button("⏹ Stop & Logout"):
            st.session_state.user_data = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Family Section
st.write("### 👥 Family Circle")
family_cols = st.columns(len(all_members))
for i, member in enumerate(all_members):
    with family_cols[i]:
        m_h = get_hours(member['start_time'])
        m_p = min(1.0, m_h / member['target_hours'])
        st.markdown(f"**{member['user_name']}**")
        st.progress(m_p)
        if st.button(f"💧 Nudge", key=f"n_{i}"):
            st.toast(f"Nudged {member['user_name']}!")

# Tick every second
time.sleep(1)
st.rerun()
